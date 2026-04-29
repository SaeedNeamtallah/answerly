دي القائمة النهائية المجمعة من **الـ logs + الكود + docker-compose**. فيها المشاكل كلها مرقمة بدون شرح طويل. التفاصيل اللي فاتت كانت مبنية على اللوجز والكود والـ compose اللي بعتهم.  

# Issues List

## P0 — تكسر التطبيق أو تسبب فقد بيانات

1. **`incidents` table missing**
   الكود بيحاول يعمل `INSERT INTO incidents` لكن الجدول مش موجود. محتاج Alembic migration لـ `incidents`, `incident_logs`, `audit_logs`.

2. **Security/Incidents dashboard feature موجودة لكن schema ناقصة**
   عندك models/routes/services للـ incidents، يعني feature مطلوبة، لكنها مش متزامنة مع DB.

3. **حذف old chunks/vectors قبل نجاح embedding الجديدة**
   خطر جدًا: لو reprocess فشل، الملف القديم يبقى غير searchable.

4. **Gemini embedding failure**
   الـ worker فشل في الاتصال بـ `generativelanguage.googleapis.com:443`.

5. **Gemini provider error handling ضعيف**
   بيرفع raw exceptions من غير retry واضح، timeout policy، أو error classification.

6. **Celery task failure ممكن يرجع errors غير نظيفة/غير user-friendly**
   محتاج تحويل provider exceptions لرسائل واضحة وآمنة.

7. **Runtime provider switching ممكن يكون كاذب بسبب caching**
   تغيير provider من UI ممكن لا يطبق فعليًا على worker/query بسبب cached services/controllers.

8. **`.env` فيه secrets حقيقية مكشوفة**
   Gemini, Cohere, Voyage, OpenRouter, Groq, Cerebras, Telegram token وغيرهم. لازم rotate/revoke.

9. **`AUTH_JWT_SECRET_KEY` ضعيف/default**
   مستخدم `change-me-in-env` أو secret أقل من المطلوب. لازم secret قوي 32+ bytes.

---

## P1 — مشاكل مهمة جدًا في التشغيل والأمان

10. **Start script بيقول “RAGMind is running” بدون E2E smoke test**
    بيتأكد من `/health` فقط، مش upload/search/generation.

11. **`/health` مش كافي لإثبات إن التطبيق شغال end-to-end**
    محتاج `/health/full` أو smoke test حقيقي.

12. **Docker frontend شغال على port 80 + local frontend شغال على 8080**
    ده يعمل لخبطة: ممكن تختبر نسخة غير اللي متبنية في Docker.

13. **Frontend mode غير واضح**
    لازم تختار: local frontend أو Docker frontend، مش الاتنين معًا.

14. **PowerShell logging بيطلع `NativeCommandError` رغم HTTP 200**
    غالبًا بسبب redirection غلط لـ Python HTTP server.

15. **Logs encoding بايظ / UTF-16 أو NUL chars**
    اللوجز صعبة القراءة والتحليل. لازم UTF-8.

16. **docker_stack.log فيه timestamps قديمة ومختلطة**
    اللوج بيخلط logs قديمة وجديدة. لازم `--since` أو `--tail`.

17. **Services حساسة exposed على `0.0.0.0`**
    Postgres, Redis, RabbitMQ, Qdrant, Prometheus, Grafana مفتوحين public لو السيرفر عليه IP عام.

18. **Compose hardcodes passwords**
    Postgres/RabbitMQ/Redis/Grafana passwords مكتوبة صريح في compose.

19. **`env_file: ../.env` بيحقن كل الأسرار في backend/worker/scheduler/bot**
    محتاج env separation أو على الأقل تأمين `.env`.

20. **Redis و Qdrant مفيش healthcheck حقيقي**
    مستخدمين `service_started` مش `service_healthy`.

21. **Backend مفيهوش compose healthcheck**
    frontend/prometheus ممكن يبدأوا قبل backend readiness الحقيقي.

22. **Celery worker شغال root غالبًا**
    ظاهر من اللوجز، والـ compose مفيهوش `user:`. محتاج non-root user في Dockerfile.

23. **Dockerfile مش ظاهر في snapshot رغم إن compose معتمد عليه**
    لازم تتأكد من وجود `docker/backend.Dockerfile` و`docker/front.Dockerfile`.

24. **Uploads/config/logs permissions ممكن تتكسر بعد non-root**
    لو عملت `USER app` لازم `/app/uploads`, `/app/tmp`, `/app/uploads/config`, `/app/uploads/logs` تبقى writable.

25. **Telegram bot container idle لكنه ظاهر Up**
    مش bug لو مقصود، لكنه misleading. الأفضل profile اسمه `legacy-bot`.

26. **Telegram mode محتاج قرار واضح**
    Production webhook أو dev polling. ماينفعش الاتنين بنفس token بدون إدارة webhook.

---

## P2 — تحسينات جودة/Production readiness

27. **Grafana `xychart` duplicate warning**
    ظهر في logs. أولوية منخفضة إلا لو dashboard panel مش شغال.

28. **Monitoring موجود لكنه سطحي**
    محتاج business metrics: processing failures, embedding failures, query failures, Celery duration, incidents count.

29. **Prometheus/Grafana مفتوحين بدون حماية كافية**
    ينفع local، لكن على Azure خطر إلا لو خلف auth/reverse proxy.

30. **postgres-exporter مفتوح host port بدون داعي**
    Prometheus يقدر يشوفه داخليًا. الأفضل `expose` بدل `ports`.

31. **Security/incident access roles محتاجة تبسيط**
    لازم تحدد مين يدخل Security Center/Incidents: `platform_owner` فقط؟ ولا `company_admin` scoped؟

32. **Legacy scripts لسه موجودة**
    مثل `start_backend.bat` رغم إن المدعوم هو `scripts/dev/start.bat`. ده يلخبط الـ agents.

33. **AGENTS.md ممكن يبقى out-of-sync لو ما اتحدثش بعد الإصلاحات**
    خصوصًا بعد migrations/provider/frontend mode changes.

34. **compose مناسب dev أكثر من production**
    محتاج profiles وفصل واضح بين local/dev وAzure/production.

---

# الترتيب الصح للإصلاح

1. **Add incidents/audit Alembic migration.**
2. **Fix embedding pipeline data-loss risk.**
3. **Fix Gemini provider retry/error handling/preflight.**
4. **Fix runtime provider cache invalidation.**
5. **Rotate secrets + fix JWT secret.**
6. **Add real smoke test.**
7. **Choose one frontend mode.**
8. **Fix logs encoding/redirection.**
9. **Harden ports.**
10. **Run Celery/backend as non-root.**
11. **Add Docker healthchecks.**
12. **Improve monitoring metrics/dashboard.**
