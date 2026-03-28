from fastapi import APIRouter, HTTPException, Body
from app.models import UserCreate, NDIAssessment 
from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token
from datetime import datetime
from bson import ObjectId
from typing import Optional

router = APIRouter(prefix="/users", tags=["Users"])

# 1. إنشاء حساب جديد - كما هو
@router.post("/signup")
async def signup(user: UserCreate):
    db = get_db()
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="البريد الإلكتروني مسجل بالفعل")
    
    if user.phone:
        existing_phone = await db.users.find_one({"phone": user.phone})
        if existing_phone:
            raise HTTPException(status_code=400, detail="رقم الهاتف مسجل بالفعل")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    user_dict["is_onboarded"] = False
    user_dict["assigned_exercises"] = [] 
    user_dict["completed_today"] = []    
    user_dict["has_new_notification"] = False 
    
    new_user = await db.users.insert_one(user_dict)
    return {"message": "User created successfully", "user_id": str(new_user.inserted_id)}

# 2. تسجيل الدخول - كما هو
@router.post("/login")
async def login(login_data: dict):
    db = get_db()
    identifier = login_data.get("email") 
    password = login_data.get("password")

    if not identifier or not password:
        raise HTTPException(status_code=400, detail="البيانات المطلوبة ناقصة")

    user = await db.users.find_one({
        "$or": [
            {"email": identifier},
            {"phone": identifier}
        ]
    })
    
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")
    
    token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "full_name": user["full_name"],
        "email": user["email"], 
        "is_onboarded": user.get("is_onboarded", False)
    }

# 3. قائمة الدكاترة - كما هو
@router.get("/doctors-list")
async def get_all_doctors():
    db = get_db()
    doctors_cursor = db.users.find({"role": "doctor"}, {"full_name": 1, "email": 1})
    doctors = await doctors_cursor.to_list(length=100)
    for doc in doctors:
        doc["id"] = str(doc.pop("_id"))
    return doctors

# 4. حفظ التقييم (Onboarding/Re-assessment) - تم التعديل لإغلاق الطلب المعلق ✅
@router.post("/onboarding")
async def save_onboarding(data: NDIAssessment):
    db = get_db()
    assessment_dict = data.dict()
    await db.assessments.insert_one(assessment_dict)
    # تعديل: بنخلي الـ pending_assessment بـ False عشان التنبيه يختفي
    await db.users.update_one(
        {"email": data.patient_id},
        {"$set": {
            "is_onboarded": True,
            "pending_assessment": False 
        }}
    )
    return {"message": "NDI Assessment saved successfully!"}

# 5. بيانات المستخدم الحالية - تم إضافة حقل التقييم المعلق ✅
@router.get("/me/{email}")
async def get_user_data(email: str):
    db = get_db()
    user = await db.users.find_one({"email": email}, {"password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["id"] = str(user.pop("_id"))
    assigned = user.get("assigned_exercises", [])
    completed = user.get("completed_today", [])
    has_notif = user.get("has_new_notification", False)

    if has_notif:
        await db.users.update_one({"email": email}, {"$set": {"has_new_notification": False}})

    latest_assessment = await db.assessments.find_one(
        {"patient_id": email},
        sort=[("created_at", -1)]
    )
    
    if latest_assessment:
        latest_assessment["id"] = str(latest_assessment.pop("_id"))
        if isinstance(latest_assessment.get("created_at"), datetime):
            latest_assessment["created_at"] = latest_assessment["created_at"].isoformat()
    
    doctor_info = None
    if user.get("role") == "patient" and user.get("doctor_id"):
        doctor_info = await db.users.find_one(
            {"email": user["doctor_id"]}, 
            {"_id": 0, "full_name": 1, "email": 1} 
        )
    
    return {
        "user": user,
        "doctor": doctor_info, 
        "latest_assessment": latest_assessment,
        "full_name": user.get("full_name"),
        "phone": user.get("phone"),
        "role": user.get("role"),
        "email": user.get("email"),
        "profile_picture": user.get("profile_picture"),
        "pending_assessment": user.get("pending_assessment", False), # إضافة للفرونت إند
        "exercise_stats": {
            "total": len(assigned),
            "completed": len(completed),
            "has_notification": has_notif
        }
    }

# 6. تمارين المريض - كما هو
@router.get("/my-exercises/{email}")
async def get_my_exercises(email: str):
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user or not user.get("assigned_exercises"):
        return []

    exercise_ids = [ObjectId(id) for id in user["assigned_exercises"]]
    exercises_cursor = db.exercises.find({"_id": {"$in": exercise_ids}})
    exercises = await exercises_cursor.to_list(length=100)
    
    completed_list = user.get("completed_today", [])
    for ex in exercises:
        ex["id"] = str(ex.pop("_id"))
        ex["is_completed"] = ex["id"] in completed_list
    return exercises

# 7. تسجيل إنجاز تمرين - كما هو
@router.post("/complete-exercise")
async def complete_exercise(payload: dict = Body(...)):
    db = get_db()
    email = payload.get("email")
    exercise_id = payload.get("exercise_id")
    today = datetime.now().strftime("%Y-%m-%d")

    await db.users.update_one(
        {"email": email},
        {"$addToSet": {"completed_today": exercise_id}}
    )
    await db.exercise_logs.update_one(
        {"patient_id": email, "date": today},
        {"$addToSet": {"completed_exercises": exercise_id}},
        upsert=True
    )
    return {"message": "Exercise recorded in history!"}

# 8. سجل الالتزام - كما هو
@router.get("/exercise-logs/{email}")
async def get_exercise_logs(email: str):
    db = get_db()
    logs_cursor = db.exercise_logs.find({"patient_id": email}).sort("date", -1)
    logs = await logs_cursor.to_list(length=30)
    for log in logs:
        log["id"] = str(log.pop("_id"))
        log["count"] = len(log.get("completed_exercises", []))
    return logs

# 9. تحديث البروفايل - كما هو
@router.put("/update/{email}")
async def update_user_profile(email: str, update_data: dict):
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user: raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
    update_fields = {}
    if update_data.get("full_name"): update_fields["full_name"] = update_data.get("full_name")
    if update_data.get("phone"): update_fields["phone"] = update_data.get("phone")
    if update_data.get("profile_picture"): update_fields["profile_picture"] = update_data.get("profile_picture")

    if not update_fields: return {"message": "No changes detected"}
    await db.users.update_one({"email": email}, {"$set": update_fields})
    return {"message": "تم تحديث البيانات بنجاح"}

# 10. --- الجديد: طلب تقييم NDI من الدكتور للمريض --- ✨
@router.post("/request-assessment/{patient_email}")
async def request_assessment(patient_email: str):
    db = get_db()
    # تحديث حساب المريض بطلب معلق وإشعار جديد
    result = await db.users.update_one(
        {"email": patient_email},
        {"$set": {
            "pending_assessment": True,
            "has_new_notification": True
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="المريض غير موجود")
    return {"message": "تم إرسال طلب إعادة التقييم بنجاح"}