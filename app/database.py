import motor.motor_asyncio
import os
import certifi
from dotenv import load_dotenv

# تحميل البيانات من .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# الحصول على مسار الشهادات (احتياطي)
ca = certifi.where()

# الاتصال مع تفعيل خيار "تجاهل الشهادات غير الصالحة"
# ده هيحل مشكلة الـ TLS Internal Error فوراً
client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGO_URI,
    tlsCAFile=ca,
    tlsAllowInvalidCertificates=True # ✅ ضفنا السطر ده عشان نتخطى فحص الـ SSL
)

# تحديد اسم قاعدة البيانات
db = client.staqem_db

# دالة التأكد من الاتصال
async def test_db_connection():
    try:
        await client.admin.command('ping')
        print("✅ Staqem is connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ Error: Could not connect to MongoDB. Details: {e}")

def get_db():
    return db