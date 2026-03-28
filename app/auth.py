from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone # أضفنا timezone
import os
from dotenv import load_dotenv

load_dotenv() # التأكد من تحميل الملف

# إعداد تشفير الباسورد
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# جلب الإعدادات مع حماية ضد القيم الفارغة
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-fallback-key-for-dev")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    
    # الطريقة الأحدث والأضمن للتعامل مع الوقت في بايثون 3.12+
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- حتة صياعة: دالة فك التشفير (نحتاجها لحماية الـ Routes لاحقاً) ---
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload # هترجع الإيميل والـ role اللي خزناهم
    except JWTError:
        return None