 **Security Engineer / Cybersecurity Engineer** عنده صلاحيات المستخدم العادي + صلاحيات الـ Security Center والـ Incident Management. لكن **مش Admin كامل**؛ يعني لا يقدر يستخدم endpoints الأدمن المباشرة `/admin/users/...` إلا لو معاه role `admin`. الكود عامل roles: `user`, `admin`, `security_engineer`, `cybersecurity_engineer`، والـ Security Engineer بيتسمح له بالدخول لـ Security Center و Incidents، بينما admin-only routes محتاجة `require_admin_access`.

## صلاحيات Security Engineer

| الصلاحية                                    |           متاحة؟ | التفاصيل                                                                                        |
| ------------------------------------------- | ---------------: | ----------------------------------------------------------------------------------------------- |
| دخول النظام JWT login                       |              نعم | نفس أي user عادي.                                                                               |
| Dashboard                                   |              نعم | يشوف إحصائيات مشاريعه ومستنداته.                                                                |
| Projects                                    |              نعم | يقدر يعمل create/list/get/update/delete للمشاريع الخاصة به فقط.                                 |
| Documents                                   |              نعم | يرفع ويحذف ويعالج مستندات داخل مشاريعه فقط.                                                     |
| Chat / RAG Query                            |              نعم | يسأل داخل مشاريعه فقط، والـ retrieval مربوط بـ `owner_id`.                                      |
| Bot Config                                  |              نعم | يختار active project للبوت بشرط يكون project مملوك له.                                          |
| AI Config                                   |  نعم/حسب الإعداد | لو `SECURITY_REQUIRE_AUTH_FOR_MUTATIONS=true` فالتعديل يحتاج auth، وهو authenticated.           |
| Account Settings                            |              نعم | يشوف بياناته ويغير password.                                                                    |
| Security Center                             |              نعم | لأن عنده `security_engineer` أو `cybersecurity_engineer`.                                       |
| Security Events                             |              نعم | يشوف events/stats/live stream/export.                                                           |
| Incidents                                   |              نعم | يشوف incidents، يفتح التفاصيل، يغير lifecycle، يضيف notes، يعمل assign، ويعمل response actions. |
| Attack Simulation                           |              نعم | يقدر يشغل simulation من Security Center.                                                        |
| Suspend/Block/Restore من داخل Incident      |              نعم | عبر `/incidents/{id}/action`.                                                                   |
| Suspend/Block/Restore أي User مباشر بالـ ID | لا، إلا لو Admin | دي endpoints تحت `/admin/users/...` ومحمية بـ `require_admin_access`.                           |

الكود موضح أن Security Center و Incidents محميين بـ `require_security_center_access` و `require_incident_access`، وهما يسمحان لـ `security_engineer/cybersecurity_engineer/admin`. أما admin direct user controls فمحميين بـ `require_admin_access`.

---

# عدد صفحات/Views الفرونت المتاحة له

في الـ frontend عنده **7 صفحات رئيسية من الـ sidebar**، ومعاهم **صفحة داخلية واحدة** بتفتح من projects.

يعني:
**7 Main Pages + 1 Internal Page = 8 Views فعليًا**

الصفحات العامة `login.html` و `signup.html` مش محسوبة هنا لأنها قبل الدخول ومش خاصة بالـ Security Engineer.

---

# خريطة الصفحات والمحتوى والربط بالـ Backend

## 1. Dashboard

**المحتوى:**

* إجمالي المشاريع.
* إجمالي المستندات.
* إجمالي chunks.
* آخر 3 مشاريع recent projects.
* زر/لينك View All يروح لصفحة Projects.

**Backend المرتبط:**

```http
GET /projects/
GET /auth/me
```

الـ dashboard في frontend بيعمل `fetchUserProjects()`، ويحسب stats من projects الخاصة بالمستخدم الحالي فقط.

---

## 2. Security Center

دي أهم صفحة للـ Security Engineer.

**المحتوى العام:**

* زر Start Attack Simulation.
* زر Reset Simulation View.
* Security Overview counters.
* Events Feed tab.
* Incidents tab.
* Live Feed.
* Export logs.
* Refresh events.
* Incident details panel.
* Incident timeline.
* Incident actions.

**Backend المرتبط:**

```http
GET  /security/stats
GET  /security/events?limit=20
GET  /security/users/status-summary
GET  /security/events/export?limit=5000
GET  /security/events/stream?limit=20
POST /security/simulate
```

الـ frontend بيعمل تحميل للـ stats والـ events من `/security/stats` و`/security/events`، وبيجيب user status summary من `/security/users/status-summary`، وبيفتح SSE stream من `/security/events/stream`.

---

## 3. Security Center — Events Feed Tab

**المحتوى:**

* جدول Security Events.
* الأعمدة:

  * Timestamp
  * Actor
  * Event Type
  * Severity
  * Message
* Live Feed لآخر الأحداث.
* Refresh button.
* Export button.
* Last updated label.
* فصل simulated events عن real events.

**Backend المرتبط:**

```http
GET /security/events?limit=20
GET /security/events/stream?limit=20
GET /security/events/export?limit=5000
GET /security/stats
```

**أمثلة events المعروضة:**

* `LOGIN_FAIL`
* `LOGIN_SUCCESS`
* `BRUTE_FORCE`
* `FILE_UPLOAD_BLOCKED`
* `RATE_LIMITED`
* `AUTHZ_DENIED`
* `AUTH_TOKEN_INVALID`
* `USER_SUSPENDED`
* `USER_BLOCKED`
* `USER_RESTORED`
* `ATTACK_SIMULATION`

الملف بيأكد إن Security Center APIs تشمل stats، events، export CSV، user status summary، real-time stream، وattack simulation.

---

## 4. Security Center — Incidents Tab

**المحتوى:**

* جدول incidents.
* filters:

  * Status: `OPEN`, `INVESTIGATING`, `RESOLVED`, `CLOSED`
  * Severity: `LOW`, `MEDIUM`, `HIGH`
  * Source: real / simulated
  * False Positive: true / false
* Refresh.
* Mark simulated as reviewed.
* Incident table columns:

  * Incident ID
  * Type
  * Severity
  * Status
  * False Positive
  * Created At

**Backend المرتبط:**

```http
GET /incidents
GET /incidents?status=OPEN
GET /incidents?severity=HIGH
GET /incidents?false_positive=true
GET /incidents/{incident_id}
```

Incidents route كله محمي بـ `require_incident_access`، وده متاح للـ security engineer/admin.

---

## 5. Security Center — Incident Details Panel

**المحتوى:**

* Incident ID.
* Type.
* Severity.
* Status.
* False Positive.
* Created At.
* Actor Info.
* Investigation Notes.
* Actions.
* Timeline / logs.

**Backend المرتبط:**

```http
GET   /incidents/{incident_id}
PATCH /incidents/{incident_id}/notes
PATCH /incidents/{incident_id}
PATCH /incidents/{incident_id}/false-positive
POST  /incidents/{incident_id}/assign
POST  /incidents/{incident_id}/reopen
POST  /incidents/{incident_id}/action
```

---

## 6. Security Center — Incident Actions

دي مش صفحة لوحدها، لكنها جزء من Incident Details.

**المحتوى / الأزرار:**

* Assign to me.
* Mark as Investigating.
* Resolve.
* Close.
* Reopen Incident.
* Mark False Positive.
* Clear False Positive.
* Ignore.
* Suspend User.
* Block User.
* Restore User.

**Backend المرتبط:**

```http
POST  /incidents/{incident_id}/assign
PATCH /incidents/{incident_id}
PATCH /incidents/{incident_id}/notes
PATCH /incidents/{incident_id}/false-positive
POST  /incidents/{incident_id}/reopen
POST  /incidents/{incident_id}/action
```

**Payload أمثلة:**

```json
{ "status": "INVESTIGATING" }
```

```json
{ "status": "RESOLVED" }
```

```json
{
  "action_type": "suspend_user",
  "metadata": {
    "reason": "suspicious activity",
    "suspension_minutes": 30
  }
}
```

```json
{
  "action_type": "block_user",
  "metadata": {
    "reason": "confirmed abuse"
  }
}
```

الملف بيذكر أن Security Engineers/Admins يقدروا يعملوا suspend/block/restore/ignore على incident actor، وأن الإجراءات بتتسجل في incident logs وaudit logs.

---

## 7. Projects

**المحتوى:**

* عرض كل مشاريع المستخدم.
* Empty state لو مفيش مشاريع.
* Project cards.
* إنشاء project جديد من زر New Project.
* حذف project.
* الدخول لتفاصيل project.

**Backend المرتبط:**

```http
GET    /projects/
POST   /projects/
GET    /projects/{project_id}
PUT    /projects/{project_id}
DELETE /projects/{project_id}
GET    /projects/{project_id}/stats
POST   /projects/{project_id}/index
```

كل routes المشاريع مربوطة بـ `get_current_db_user`، يعني Security Engineer يشوف مشاريعه فقط، مش كل مشاريع النظام.

---

## 8. Project Detail

دي صفحة داخلية مش موجودة كـ sidebar item، بتفتح لما تضغط على project.

**المحتوى:**

* اسم المشروع.
* Back to projects.
* Upload area.
* File input يقبل:

  * `.pdf`
  * `.txt`
  * `.docx`
* Upload progress.
* قائمة documents الحالية.
* حذف document.
* polling لحالة المعالجة.

**Backend المرتبط:**

```http
GET    /projects/{project_id}
GET    /projects/{project_id}/documents
POST   /projects/{project_id}/documents
GET    /documents/{asset_id}
POST   /documents/{asset_id}/process
POST   /documents/{asset_id}/process-and-index
DELETE /documents/{asset_id}
GET    /tasks/{task_id}
GET    /health
```

الملف بيأكد إن upload flow يبدأ من `POST /projects/{project_id}/documents` ثم `DocumentController.upload_document()` ثم `FileService.save_upload_file()` ثم Celery processing.

---

## 9. Chat

**المحتوى:**

* اختيار project.
* اختيار اللغة.
* chat messages.
* suggestion chips.
* textarea للرسالة.
* send/cancel.
* disclaimer إن الإجابة من المستندات فقط.

**Backend المرتبط:**

```http
GET  /projects/
POST /projects/{project_id}/query
```

**ملاحظة مهمة من الكود:**
الـ frontend بيحاول يستخدم:

```http
POST /projects/{project_id}/query/stream
```

لكن في route inventory الموجود في الملف، الموجود صراحة هو:

```http
POST /projects/{project_id}/query
```

ولم أجد route واضحة لـ `/query/stream` داخل backend routes المعروضة. فلو stream مش موجود في جزء آخر، دي نقطة mismatch بين frontend والbackend. الـ route layer المذكور في الملف يعرض `query_project()` فقط تحت `backend/routes/query.py`.

---

## 10. Bot Config

**المحتوى:**

* اختيار active project للبوت.
* حفظ إعدادات البوت.
* تحديث اسم البوت على Telegram.
* input لاسم البوت.

**Backend المرتبط:**

```http
GET  /bot/config
POST /bot/config
POST /bot/profile
GET  /projects/
```

**الصلاحية:**
تحديث bot config يحتاج JWT DB user، والـ `active_project_id` لازم يكون positive ولازم يكون project مملوك للمستخدم/السياق المسموح.

---

## 11. AI Config

**المحتوى:**

* اختيار LLM provider.
* اختيار embedding provider.
* اختيار vector DB provider.
* embedding size.
* chunk strategy.
* chunk size.
* chunk overlap.
* parent chunk size.
* parent chunk overlap.
* retrieval top K.
* candidate K.
* hybrid search toggle.
* hybrid alpha.
* query rewrite toggle.
* rerank toggle.
* rerank top K.
* save settings.

**Backend المرتبط:**

```http
GET  /config/providers
POST /config/providers
```

**الصلاحية:**
التعديل محمي اختياريًا بـ `SECURITY_REQUIRE_AUTH_FOR_MUTATIONS`. في `.env.example` القيمة `true`، فالتعديل يحتاج auth.

---

## 12. Account Settings

**المحتوى:**

* Username.
* Role.
* Created at.
* Session expiry.
* Language.
* Theme.
* API base URL.
* Save preferences.
* Change password:

  * current password
  * new password
  * confirm password
  * password strength meter
  * show passwords toggle

**Backend المرتبط:**

```http
GET  /auth/me
POST /auth/change-password
POST /auth/update-password
GET  /health
```

**ملاحظة:**
Language/theme/API base غالبًا localStorage/frontend preferences، أما تغيير كلمة المرور فهو backend call. الـ auth routes الموجودة في الملف تشمل `me()` و`change_password()`.

---

# الخلاصة المختصرة

**Security Engineer عنده 8 Views فعلية:**

1. Dashboard
2. Security Center
3. Security Center / Events Feed
4. Security Center / Incidents
5. Projects
6. Project Detail
7. Chat
8. Bot Config
9. AI Config
10. Account Settings

لو هنحسب Security Center كصفحة واحدة بتابات داخلية، يبقى العدد العملي: **8 views**
لو هنفصل Events وIncidents كصفحات/شاشات مستقلة داخل Security Center، يبقى العدد التحليلي: **10 screens**.

**أهم صلاحياته الأمنية:**
يشوف security stats/events، يفتح live security stream، يصدر CSV، يشغل attack simulation، يدير incidents، يضيف notes، يغير lifecycle، يعمل assign، يحدد false positive، ويعمل suspend/block/restore للـ incident actor. لكنه لا يملك admin-only direct user management إلا لو كان عنده role `admin`.
