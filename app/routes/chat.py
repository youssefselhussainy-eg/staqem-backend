from fastapi import APIRouter, HTTPException, Body
from app.database import get_db # استيراد الدالة اللي بتجيب الداتابيز من ملفك
from app.models import Message   # استيراد الموديل بالاسم اللي اخترته في models.py
from datetime import datetime
from typing import List

router = APIRouter(prefix="/chat", tags=["Chat & Notifications"])

# 1. إرسال رسالة جديدة
@router.post("/send")
async def send_message(msg: Message):
    db = get_db() # بنجيب الداتابيز من ملف database.py بتاعك
    message_dict = msg.dict()
    
    # تأكد إننا بنستخدم نفس اسم الحقل في الـ Model (created_at)
    message_dict["created_at"] = datetime.utcnow()
    
    result = await db.messages.insert_one(message_dict)
    if result.inserted_id:
        return {"status": "success", "message_id": str(result.inserted_id)}
    raise HTTPException(status_code=500, detail="فشل في إرسال الرسالة")

# 2. جلب تاريخ المحادثة بين مستخدمين
@router.get("/history/{user1}/{user2}")
async def get_chat_history(user1: str, user2: str):
    db = get_db()
    query = {
        "$or": [
            {"sender_email": user1, "receiver_email": user2},
            {"sender_email": user2, "receiver_email": user1}
        ]
    }
    # ترتيب حسب وقت الإنشاء (من الأقدم للأحدث)
    cursor = db.messages.find(query).sort("created_at", 1)
    messages = await cursor.to_list(length=100)
    
    # تحويل الـ ObjectIds لنصوص عشان الـ JSON ميزعلش
    for m in messages:
        m["_id"] = str(m["_id"])
    return messages

# 3. جلب عدد الرسائل غير المقروءة لمستخدم معين
@router.get("/unread-count/{email}")
async def get_unread_count(email: str):
    db = get_db()
    count = await db.messages.count_documents({
        "receiver_email": email,
        "is_read": False
    })
    return {"unread_count": count}

# 4. تحديث الرسائل كـ "مقروءة" عند فتح المحادثة
@router.patch("/mark-as-read")
async def mark_as_read(sender: str = Body(..., embed=True), receiver: str = Body(..., embed=True)):
    db = get_db()
    result = await db.messages.update_many(
        {"sender_email": sender, "receiver_email": receiver, "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"status": "success", "modified_count": result.modified_count}