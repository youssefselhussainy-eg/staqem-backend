from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import test_db_connection, get_db
from app.routes import users, doctors, chat 
from typing import Dict
import datetime
import json

app = FastAPI(
    title="Staqem API 🩺",
    description="Backend for Staqem - Upper Crossed Syndrome Rehabilitation App",
    version="1.2.0"
)

# --- 1. إعداد الـ CORS (مهم جداً للـ WebSocket) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # في الإنتاج يفضل تحديد الدومين
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. مدير الاتصالات اللحظية (WebSocket Manager) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, email: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[email] = websocket
        print(f"📡 [WS] Connected: {email}")

    def disconnect(self, email: str):
        if email in self.active_connections:
            del self.active_connections[email]
            print(f"🔌 [WS] Disconnected: {email}")

    async def send_personal_message(self, message: dict, email: str):
        if email in self.active_connections:
            await self.active_connections[email].send_json(message)

manager = ConnectionManager()

# --- 3. وظائف الجدولة (Scheduled Tasks) ---

async def reset_daily_exercises():
    try:
        db = get_db()
        result = await db.users.update_many(
            {"role": "patient"},
            {"$set": {"completed_today": []}}
        )
        print(f"🌅 [System] Daily reset done. Patients updated: {result.modified_count}")
    except Exception as e:
        print(f"❌ [Error] Daily reset failed: {e}")

async def check_reminders():
    try:
        db = get_db()
        lazy_patients = await db.users.find({
            "role": "patient",
            "$expr": { "$lt": [{ "$size": "$completed_today" }, { "$size": "$assigned_exercises" }] }
        }).to_list(length=100)

        for patient in lazy_patients:
            email = patient["email"]
            await manager.send_personal_message({
                "type": "REMINDER",
                "title": "استقم يناديك! 🧘‍♂️",
                "message": f"يا {patient['full_name']}، لسه مخلصتش تمارينك. يلا بلاش كسل!"
            }, email)
    except Exception as e:
        print(f"❌ [Error] Reminder task failed: {e}")

# --- 4. أحداث التشغيل ---
@app.on_event("startup")
async def startup_event():
    await test_db_connection()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(reset_daily_exercises, 'cron', hour=0, minute=0)
    scheduler.add_job(check_reminders, 'cron', hour=18, minute=0)
    scheduler.start()
    print("⏰ [Scheduler] Background jobs active.")

# --- 5. الـ WebSocket Endpoint للشات والاشعارات ---
@app.websocket("/ws/{email}")
async def websocket_endpoint(websocket: WebSocket, email: str):
    await manager.connect(email, websocket)
    try:
        while True:
            # استقبال البيانات كـ JSON مباشرة (أفضل وأسرع)
            data = await websocket.receive_json()
            
            if data.get("type") == "CHAT":
                receiver_email = data.get("receiver_email")
                # توجيه الرسالة للمستلم فوراً
                await manager.send_personal_message({
                    "type": "NEW_MESSAGE",
                    "sender_email": email,
                    "content": data.get("content"),
                    "created_at": datetime.datetime.now().isoformat()
                }, receiver_email)
                print(f"📩 [Chat] From {email} to {receiver_email}")

    except WebSocketDisconnect:
        manager.disconnect(email)
    except Exception as e:
        print(f"⚠️ [WS Error] for {email}: {e}")
        manager.disconnect(email)

# --- تسجيل الـ Routers ---
app.include_router(users.router)
app.include_router(doctors.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"status": "Online", "message": "Staqem AI Backend is running 🩺"}