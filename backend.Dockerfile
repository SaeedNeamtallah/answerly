# 1. بنبدأ بنسخة بايثون خفيفة وسريعة
FROM python:3.10-slim

# 2. منع بايثون من إنشاء ملفات مؤقتة وتسريع الـ Logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. تحديد مكان العمل جوه الحاوية
WORKDIR /app

# 4. تثبيت مكتبات النظام (مهمة جداً للـ PDF والمكتبات التقنية)
RUN apt-get update && apt-get install -y \
    build-essential \
    libmagic-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 5. نسخ ملف المتطلبات وتثبيته
# بنسخ الملف من مساره اللي شفناه في الـ .bat
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. نسخ كل ملفات المشروع لداخل الحاوية
COPY . .

# 7. البورت اللي الباكند هيشتغل عليه
EXPOSE 8000

# 8. أمر التشغيل النهائي (بديل لآخر سطر في ملف الـ .bat)
# لاحظ إننا ثبتنا البورت على 8000 لتوحيد الشغل
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]