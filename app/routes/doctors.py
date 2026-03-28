from fastapi import APIRouter, HTTPException, Body
from app.database import get_db
from datetime import datetime
from typing import List
from bson import ObjectId

router = APIRouter(prefix="/doctors", tags=["Doctors"])

# 1. جلب قائمة المرضى (تم إصلاح ظهور تاريخ آخر تقييم) ✅
@router.get("/patients/{doctor_id}")
async def get_patients(doctor_id: str):
    db = get_db()
    # doctor_id هنا هو إيميل الدكتور
    patients_cursor = db.users.find({"doctor_id": doctor_id, "role": "patient"})
    patients = await patients_cursor.to_list(length=100)
    
    results = []
    for p in patients:
        # أ. جلب آخر تقييم NDI للمريض
        latest_ndi = await db.assessments.find_one(
            {"patient_id": p["email"]},
            sort=[("created_at", -1)]
        )
        
        # ب. حساب نسبة إنجاز التمارين اليومية
        assigned = p.get("assigned_exercises", [])
        completed = p.get("completed_today", [])
        total_count = len(assigned)
        completed_count = len(completed)
        progress = (completed_count / total_count * 100) if total_count > 0 else 0
        
        # ج. عد الرسائل غير المقروءة
        unread_count = await db.messages.count_documents({
            "sender_email": p["email"],
            "receiver_email": doctor_id,
            "is_read": False
        })
        
        # تجهيز تاريخ آخر تقييم (تحويله لـ string)
        last_date = None
        if latest_ndi and "created_at" in latest_ndi:
            dt = latest_ndi["created_at"]
            last_date = dt.isoformat() if isinstance(dt, datetime) else dt

        p_id = str(p.pop("_id"))
        results.append({
            "id": p_id,
            "full_name": p.get("full_name"),
            "email": p.get("email"),
            "latest_score": latest_ndi["total_score"] if latest_ndi else None,
            "last_assessment_date": last_date, # --- التعديل هنا: ضفنا التاريخ للرد --- ✅
            "daily_progress": round(progress),
            "is_done_today": progress == 100 and total_count > 0,
            "unread_messages": unread_count 
        })
    return results

# باقي الدوال (get_patient_detail, get_exercises_library, assign_exercises) - كما هي
@router.get("/patient-detail/{email}")
async def get_patient_detail(email: str):
    db = get_db()
    user = await db.users.find_one({"email": email}, {"password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    assessments_cursor = db.assessments.find({"patient_id": email}).sort("created_at", 1)
    assessments = await assessments_cursor.to_list(length=100)
    
    assigned_ids = user.get("assigned_exercises", [])
    completed_ids = user.get("completed_today", [])
    
    assigned_exercises = []
    if assigned_ids:
        ex_cursor = db.exercises.find({"_id": {"$in": [ObjectId(id) for id in assigned_ids]}})
        assigned_exercises = await ex_cursor.to_list(length=100)
        for ex in assigned_exercises:
            ex["id"] = str(ex.pop("_id"))
            ex["is_completed"] = ex["id"] in completed_ids

    user["id"] = str(user.pop("_id"))
    for a in assessments:
        a["id"] = str(a.pop("_id"))
        if "created_at" in a and isinstance(a["created_at"], datetime):
            a["created_at"] = a["created_at"].isoformat()
            
    return {
        "patient": user,
        "history": assessments,
        "current_plan": assigned_exercises
    }

@router.get("/exercises-library")
async def get_exercises_library():
    db = get_db()
    exercises_cursor = db.exercises.find({})
    exercises = await exercises_cursor.to_list(length=100)
    for ex in exercises:
        ex["id"] = str(ex.pop("_id"))
    return exercises

@router.post("/assign-exercises")
async def assign_exercises(data: dict):
    from app.main import manager 
    db = get_db()
    patient_email = data.get("patient_email")
    exercise_ids = data.get("exercise_ids")
    
    if not patient_email:
        raise HTTPException(status_code=400, detail="Patient email is required")

    result = await db.users.update_one(
        {"email": patient_email},
        {"$set": {"assigned_exercises": exercise_ids, "has_new_notification": True, "completed_today": []}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        await manager.send_personal_message({
            "type": "NEW_EXERCISES",
            "title": "تحديث في خطتك! 📋",
            "message": "قام الدكتور بتعديل تمارينك اليومية."
        }, patient_email)
    except Exception as e:
        print(f"⚠️ [WS] Could not send: {e}")
        
    return {"message": "Exercises assigned and patient notified!"}