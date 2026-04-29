# 1. بنبدأ بنسخة بايثون خفيفة وسريعة
FROM python:3.10-slim

# 2. منع بايثون من إنشاء ملفات مؤقتة وتسريع الـ Logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. تحديد مكان العمل جوه الحاوية
WORKDIR /app

# 4. Keep the image independent from OS package mirrors.
# Runtime dependencies are installed from Python wheels below.

# 5. نسخ ملف المتطلبات وتثبيته
# بنسخ الملف من مساره اللي شفناه في الـ .bat
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. نسخ ملفات runtime فقط لتقليل build context وتحسين الكاش
COPY backend ./backend
COPY telegram_bot ./telegram_bot
COPY app_config.json ./app_config.json
COPY bot_config.json ./bot_config.json

RUN addgroup --system ragmind \
    && adduser --system --ingroup ragmind --home /app ragmind \
    && mkdir -p /app/uploads /app/tmp \
    && chown -R ragmind:ragmind /app/uploads /app/tmp

USER ragmind

# 7. البورت اللي الباكند هيشتغل عليه
EXPOSE 8000

# 8. أمر التشغيل النهائي (بديل لآخر سطر في ملف الـ .bat)
# لاحظ إننا ثبتنا البورت على 8000 لتوحيد الشغل
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
