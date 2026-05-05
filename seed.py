import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def seed_exercises():
    # 1. الـ URI الخاص بك (يفضل مستقبلاً وضعه في ملف .env)
    uri = "mongodb+srv://staqem_admin:staqem1042026@staqem.393jjgr.mongodb.net/staqem?retryWrites=true&w=majority&appName=Staqem"
    client = AsyncIOMotorClient(uri)
    
    # 2. تحديد الداتا بيز
    db = client['staqem_db'] 

    exercises = [
        {
            "title": "ثني الذقن للداخل (Chin Tucks)",
            "category": "Posture",
            "image_url": "/exercises/chin-tucks.gif",
            "description": "تمرين أساسي لتصحيح وضعية الرقبة وتقوية العضلات العميقة.",
            "reps_sets": "3 مجموعات × 12 عدة",
            "instructions": "اسحب ذقنك للداخل مستخدماً عضلات الرقبة الأمامية دون إمالة الرأس للأسفل، تخيل أنك تحاول صنع 'ذقن مزدوجة'."
        },
        {
            "title": "إطالة الرقبة الجانبية (Side Stretch)",
            "category": "Stretching",
            "image_url": "/exercises/side-neck-stretch.jpg",
            "description": "إطالة جانبية لعضلات الرقبة لتحسين المرونة وتقليل الشد العضلي.",
            "reps_sets": "مجموعتين × 30 ثانية لكل جانب",
            "instructions": "اجلس بظهر مستقيم، أمل رأسك ببطء نحو كتفك حتى تشعر بإطالة خفيفة، ثبت الوضعية ثم كرر للجانب الآخر."
        },
        {
            "title": "دوران الرقبة (Neck Rotation)",
            "category": "Mobility",
            "image_url": "/exercises/neck-rotation.gif",
            "description": "تحسين مدى حركة الرقبة وتقليل التيبس الصباحي.",
            "reps_sets": "مجموعتين × 10 عدات",
            "instructions": "قم بتدوير رأسك ببطء جهة اليمين حتى أقصى مدى مريح، ثم جهة اليسار. حافظ على كتفيك ثابتين."
        },
        {
            "title": "عصر لوحي الكتف (Scapular Squeezes)",
            "category": "Strengthening",
            "image_url": "/exercises/scapular-squeezes.gif",
            "description": "تقوية عضلات ما بين الكتفين لدعم القوام العلوي.",
            "reps_sets": "3 مجموعات × 10 عدات",
            "instructions": "قم بضم لوحي الكتف للخلف وللأسفل كأنك تحاول عصر ليمونة بينهما، ثبت الوضعية لثانيتين ثم استرخِ."
        },
        {
            "title": "المقاومة الأمامية الثابتة (Isometric Front)",
            "category": "Isometric",
            "image_url": "/exercises/isometric-neck-front.gif",
            "description": "تقوية عضلات الرقبة بدون حركة لتقليل الضغط على الفقرات.",
            "reps_sets": "مجموعتين × ثبات 10 ثوانٍ",
            "instructions": "ضع يديك على جبهتك، حاول دفع رأسك للأمام بينما تقاوم يداك الحركة. حافظ على استقامة الرقبة تماماً."
        },
        {
            "title": "إطالة العضلة الرافعة (Levator Scapulae)",
            "category": "Stretching",
            "image_url": "/exercises/levator-scapulae-stretch.gif",
            "description": "إطالة متخصصة للعضلة الرافعة للكتف لتقليل آلام أعلى الظهر.",
            "reps_sets": "3 مجموعات × ثبات 30 ثانية",
            "instructions": "أمل رأسك بزاوية 45 درجة وانظر لأسفل باتجاه الإبط، استخدم يدك بضغط خفيف جداً لزيادة الإطالة."
        },
        {
            "title": "دوران الكتف للخلف (Shoulder Rolls)",
            "category": "Warm-up",
            "image_url": "/exercises/shoulder-rolls.jpg",
            "description": "تمرين إحماء سريع لفك تشنجات الكتف والرقبة.",
            "reps_sets": "مجموعتين × 15 تكرار",
            "instructions": "ارفع كتفيك للأعلى باتجاه أذنيك، ثم حركهما للخلف وللأسفل في حركة دائرية واسعة وسلسة."
        },
        {
            "title": "إطالة عضلات الصدر (Doorway Stretch)",
            "category": "Postural",
            "image_url": "/exercises/doorway-stretch.jpg",
            "description": "فتح عضلات الصدر لتحسين وضعية الأكتاف المنحنية للأمام.",
            "reps_sets": "3 مجموعات × ثبات 30 ثانية",
            "instructions": "قف عند فتحة الباب، ضع ذراعيك على الإطار، وتقدم بجسمك للأمام ببطء حتى تشعر بإطالة في صدرك وأكتافك."
        }
    ]

    try:
        # مسح التمارين القديمة عشان نحدث المكتبة بالكامل
        await db.exercises.delete_many({})
        # حقن التمارين الجديدة
        await db.exercises.insert_many(exercises)
        print(f"✅ تم تحديث مكتبة 'استقم' بـ {len(exercises)} تمرين بنجاح!")
    except Exception as e:
        print(f"❌ حدث خطأ أثناء الحقن: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(seed_exercises())