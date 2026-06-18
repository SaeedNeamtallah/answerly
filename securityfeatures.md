# Security Features Extracted — Merged Explanation + Code

Main source: `all_project_code(3).txt`

---

## 1. Security Configuration Layer

### Explanation

The project has a centralized security configuration layer that controls JWT secrets, JWT algorithm, token expiration, admin credentials, mutation protection, default suspension duration, rate limiting, brute-force protection, upload inspection, CORS origins, and service-account credentials.

### Path

`backend/config.py`

```python
# Authentication and Security Configuration
auth_jwt_secret_key: str = Field(default="change-me-in-env", alias="AUTH_JWT_SECRET_KEY")
auth_jwt_algorithm: str = Field(default="HS256", alias="AUTH_JWT_ALGORITHM")
auth_access_token_expire_minutes: int = Field(default=60, alias="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES")
auth_admin_username: str = Field(default="admin", alias="AUTH_ADMIN_USERNAME")
auth_admin_password: str = Field(default="admin123", alias="AUTH_ADMIN_PASSWORD")
auth_admin_password_hash: str = Field(default="", alias="AUTH_ADMIN_PASSWORD_HASH")
security_require_auth_for_mutations: bool = Field(default=False, alias="SECURITY_REQUIRE_AUTH_FOR_MUTATIONS")
security_user_suspension_default_minutes: int = Field(
    default=30,
    alias="SECURITY_USER_SUSPENSION_DEFAULT_MINUTES"
)
security_login_bruteforce_enabled: bool = Field(
    default=True,
    alias="SECURITY_LOGIN_BRUTEFORCE_ENABLED"
)
security_rate_limit_enabled: bool = Field(default=True, alias="SECURITY_RATE_LIMIT_ENABLED")
security_upload_validate_magic: bool = Field(default=True, alias="SECURITY_UPLOAD_VALIDATE_MAGIC")
security_upload_max_scan_bytes: int = Field(default=8192, alias="SECURITY_UPLOAD_MAX_SCAN_BYTES")
```

---

## 2. JWT Authentication

### Explanation

The backend uses JWT-based authentication. After login, the system issues a signed access token containing `sub`, `roles`, `iat`, and `exp`. Token expiration is enforced, and tokens missing required fields or containing invalid data are rejected. The JWT subject is resolved against the database on every protected request, so deleted or invalid users cannot continue using old tokens.

### Path

`backend/security/jwt_utils.py`

```python
def create_jwt_access_token(
    *,
    subject: str,
    roles: Optional[List[str]] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    ttl_minutes = int(expires_minutes or settings.auth_access_token_expire_minutes or 60)
    issued_at = _now_utc()
    expires_at = issued_at + timedelta(minutes=max(1, ttl_minutes))

    payload = {
        "sub": subject,
        "roles": roles or ["user"],
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.auth_jwt_secret_key,
        algorithm=settings.auth_jwt_algorithm,
    )


def decode_jwt_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(
        token,
        settings.auth_jwt_secret_key,
        algorithms=[settings.auth_jwt_algorithm],
        options={"require": ["sub", "exp"]},
    )
```

---

## 3. Password Security

### Explanation

Passwords are never stored in plain text. The system hashes passwords using `bcrypt`, validates password length and format, rejects control characters, and prevents leading or trailing spaces. Password verification uses `bcrypt.checkpw`. Changing a password requires the current password, and the new password must be different from the old one.

### Path

`backend/services/auth_service.py`

```python
def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise SignupValidationError("Password must be at least 8 characters")

    if len(password.encode("utf-8")) > 72:
        raise SignupValidationError("Password is too long")

    if password != password.strip():
        raise SignupValidationError("Password cannot start or end with spaces")

    if _PASSWORD_CONTROL_CHAR_RE.search(password):
        raise SignupValidationError("Password contains invalid control characters")


@staticmethod
def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@staticmethod
def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )
```

---

## 4. Username Validation and Normalization

### Explanation

Usernames are sanitized and converted to lowercase before database use. The system enforces a strict username format using a regex that allows only lowercase letters, numbers, dots, underscores, and hyphens. Reserved service-account usernames are blocked from normal signup, and duplicate username checks are handled case-insensitively.

### Path

`backend/services/auth_service.py`

```python
_USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,50}$")

def _normalize_username(username: str) -> str:
    cleaned = sanitize_text(
        username,
        max_length=150,
        strip_html=True,
        allow_newlines=False,
    ).lower()

    if not cleaned:
        raise SignupValidationError("Username is required")

    if not _USERNAME_RE.match(cleaned):
        raise SignupValidationError(
            "Username must be 3-50 chars and contain only lowercase letters, numbers, ., _, or -"
        )

    return cleaned
```

---

## 5. Service Account Security

### Explanation

The project includes managed service-account logic for admin and bot accounts. These usernames are reserved and cannot be used by normal users during signup. Successful service-account login can provision or sync a real database-backed user row. Admin passwords support either plain comparison or PBKDF2-SHA256 hash verification, with constant-time comparison to reduce timing-attack risk.

### Path

`backend/security/auth.py`

```python
def get_service_account_credentials(username: str) -> ServiceAccountCredentials | None:
    normalized_username = _normalize_username(username)
    if not normalized_username:
        return None

    bot_account = _configured_bot_service_account()
    if bot_account and bot_account.username == normalized_username:
        return bot_account

    admin_account = _configured_admin_service_account()
    if admin_account and admin_account.username == normalized_username:
        return admin_account

    return None


def get_reserved_service_account_usernames() -> Set[str]:
    reserved_usernames: Set[str] = set()
    for account in (_configured_bot_service_account(), _configured_admin_service_account()):
        if account is not None and account.username:
            reserved_usernames.add(account.username)
    return reserved_usernames


def verify_service_account_password(
    service_account: ServiceAccountCredentials,
    password: str,
) -> bool:
    if service_account.password_hash:
        return _verify_pbkdf2_sha256(password, service_account.password_hash)
    if service_account.plain_password is None:
        return False
    return compare_digest(password, service_account.plain_password)
```

---

## 6. Role-Based Access Control

### Explanation

The system supports role-based access control with roles such as `user`, `admin`, `security_engineer`, and `cybersecurity_engineer`. Normal users can access standard application features, while admins and security engineers can access Security Center and incident-management features. Unauthorized role checks are logged as `AUTHZ_DENIED`.

### Path

`backend/security/auth.py`

```python
ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_SECURITY_ENGINEER = "security_engineer"
ROLE_CYBERSECURITY_ENGINEER = "cybersecurity_engineer"


def resolve_roles_for_username(username: str) -> List[str]:
    normalized_username = _normalize_username(username)
    resolved_roles: List[str] = []

    if normalized_username and normalized_username == _normalize_username(settings.auth_admin_username):
        resolved_roles.append(ROLE_ADMIN)

    if normalized_username and normalized_username in _configured_cybersecurity_engineer_usernames():
        resolved_roles.append(ROLE_SECURITY_ENGINEER)
        resolved_roles.append(ROLE_CYBERSECURITY_ENGINEER)

    resolved_roles.append(ROLE_USER)
    return list(dict.fromkeys(resolved_roles))


async def require_security_center_access(
    request: Request,
    current_user: User = Depends(get_current_db_user),
) -> User:
    roles = resolve_roles_for_username(current_user.username)
    if has_security_engineer_role(roles) or has_role(roles, ROLE_ADMIN):
        return current_user

    log_event({
        "event_type": SecurityEventType.AUTHZ_DENIED,
        "severity": SecuritySeverity.HIGH,
        "user_id": current_user.id,
        "username": current_user.username,
        "message": "Security Center access denied",
    })
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
```

---

## 7. Account Status Enforcement

### Explanation

User accounts support security states such as `ACTIVE`, `SUSPENDED`, and `BLOCKED`. The account status is enforced on every authenticated request, not only during login. Blocked users are denied access, suspended users are denied access until suspension expiry, and expired suspensions can be automatically restored.

### Path

`backend/security/auth.py`

```python
async def _enforce_account_status_policy(
    *,
    db: AsyncSession,
    request: Request,
    auth_service: AuthService,
    user: User,
) -> None:
    user_status, suspended_until, auto_restored = await auth_service.evaluate_user_status(
        db,
        user=user,
        allow_auto_restore=True,
    )

    if user_status == UserAccountStatus.BLOCKED:
        log_event({
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": user.id,
            "username": user.username,
            "message": "Access denied for blocked account",
        })
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account blocked due to security violation",
        )

    if user_status == UserAccountStatus.SUSPENDED:
        log_event({
            "event_type": SecurityEventType.AUTHZ_DENIED,
            "severity": SecuritySeverity.HIGH,
            "user_id": user.id,
            "username": user.username,
            "message": "Access denied for suspended account",
        })
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
```

---

## 8. Login Brute-Force Protection

### Explanation

Login is protected against brute-force attacks by tracking failed attempts per username and per IP address. The system uses sliding-window thresholds, temporary blocking, retry-after calculations, and progressive delays. Repeated suspicious login failures are logged as `BRUTE_FORCE` and can lead to suspension or blocking.

### Paths

`backend/services/login_security_service.py`

```python
def record_failed_login(
    self,
    *,
    username: str,
    ip_address: str | None,
    reason: str,
    message: str,
    severity: str = SecuritySeverity.MEDIUM,
) -> FailureRegistration:
    normalized_username = self.normalize_username(username)
    normalized_ip = self.normalize_ip(ip_address)

    log_event({
        "event_type": SecurityEventType.LOGIN_FAIL,
        "severity": severity,
        "username": normalized_username,
        "ip_address": normalized_ip,
        "message": message,
        "metadata": {"username": normalized_username, "reason": reason},
    })

    failure_state = self._tracker.register_failure(
        username_key=normalized_username,
        ip_key=normalized_ip,
    )

    if failure_state.threshold_crossed or failure_state.newly_blocked:
        log_event({
            "event_type": SecurityEventType.BRUTE_FORCE,
            "severity": SecuritySeverity.HIGH,
            "username": normalized_username,
            "ip_address": normalized_ip,
            "message": "Multiple failed login attempts detected",
        })

    return failure_state
```

`backend/routes/auth.py`

```python
async def _apply_progressive_login_delay(failure_state: FailureRegistration) -> None:
    delay_seconds = _resolve_progressive_login_delay_seconds(failure_state)
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)
```

---

## 9. Rate Limiting

### Explanation

The backend has a dedicated `SecurityRateLimitMiddleware` for abuse-sensitive endpoints such as login, chat/query, document upload, and project creation. It supports endpoint-specific sliding-window limits, optional global fallback limits, exempt paths such as `/health` and `/docs`, JWT-subject-based keys for authenticated users, IP-based keys for anonymous users, max in-flight request limits, and rate-limit response headers.

### Path

`backend/security/middleware.py`

```python
class SecurityRateLimitMiddleware(BaseHTTPMiddleware):
    """Apply configurable, endpoint-focused throttling for abuse-sensitive actions."""

    _RATE_LIMIT_ABUSE_THRESHOLD = 3
    _RATE_LIMIT_ABUSE_WINDOW_SECONDS = 300

    def __init__(self, app):
        super().__init__(app)

        self._rules: list[EndpointRateRule] = []

        self._rules.append(
            EndpointRateRule(
                name="chat",
                methods={"POST"},
                path_pattern=re.compile(r"^/projects/\d+/query(?:/stream)?/?$"),
                limiter=InMemoryRateLimiter(
                    max_requests=settings.security_rate_limit_chat_requests_per_window,
                    window_seconds=settings.security_rate_limit_chat_window_seconds,
                ),
                max_in_flight=max(0, settings.security_rate_limit_chat_max_in_flight),
            )
        )

        self._rules.append(
            EndpointRateRule(
                name="auth_login",
                methods={"POST"},
                path_pattern=re.compile(r"^/auth/login/?$"),
                limiter=InMemoryRateLimiter(
                    max_requests=settings.security_rate_limit_login_requests_per_window,
                    window_seconds=settings.security_rate_limit_login_window_seconds,
                ),
                max_in_flight=max(0, settings.security_rate_limit_login_max_in_flight),
            )
        )
```

---

## 10. Input Sanitization

### Explanation

The project uses centralized input sanitization. It is applied to usernames, project names, descriptions, query text, metadata, filenames, incident notes, reasons, bot profile names, and runtime configuration values. Sanitization removes control characters, script blocks, and HTML tags, normalizes line endings, trims and truncates text, collapses excessive whitespace, and limits metadata sizes.

### Path

`backend/security/sanitization.py`

```python
def sanitize_text(
    value: Any,
    *,
    max_length: int = 4000,
    strip_html: bool = True,
    allow_newlines: bool = True,
) -> str:
    if value is None:
        return ""

    text = str(value)
    text = _CONTROL_CHARS_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if strip_html:
        text = _SCRIPT_TAG_RE.sub("", text)
        text = _HTML_TAG_RE.sub("", text)

    if not allow_newlines:
        text = text.replace("\n", " ")

    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text[:max_length]
```

---

## 11. Filename Sanitization

### Explanation

Uploaded filenames are hardened before storage. The system uses only the basename, removes control characters, replaces unsafe characters, strips leading/trailing spaces and dots, preserves the extension when possible, and falls back to `upload.bin` if the filename becomes empty. This helps prevent path traversal and unsafe filename handling.

### Path

`backend/security/sanitization.py`

```python
def sanitize_filename(filename: str, *, max_length: int = 255) -> str:
    """Sanitize user-supplied filenames to prevent path/control abuse."""
    base_name = Path(str(filename or "")).name
    base_name = _CONTROL_CHARS_RE.sub("", base_name)
    base_name = base_name.replace("\n", "").replace("\r", "").strip()
    base_name = _SAFE_FILENAME_RE.sub("_", base_name)
    base_name = _MULTI_SPACE_RE.sub(" ", base_name).strip(" .")

    if not base_name:
        return "upload.bin"

    if len(base_name) <= max_length:
        return base_name

    suffix = Path(base_name).suffix
    stem = Path(base_name).stem
    max_stem_len = max(1, max_length - len(suffix))
    return f"{stem[:max_stem_len]}{suffix}"
```

---

## 12. File Upload Security

### Explanation

File upload validation is one of the strongest security areas in the project. The system rejects empty files, enforces a maximum file size, blocks dangerous extensions such as `.php`, `.exe`, `.js`, and `.sh`, checks all suffixes to catch double-extension attacks, allows only supported document types, validates MIME/content type, and optionally validates magic bytes to confirm the real file format.

### Path

`backend/services/file_service.py`

```python
self.blocked_extensions = {".php", ".exe", ".js", ".sh"}
self.allowed_mime_types = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
}
```

```python
def _validate_magic_signature(self, extension: str, file_content: bytes) -> tuple[bool, Optional[str]]:
    if not settings.security_upload_validate_magic:
        return True, None

    sample = file_content[: self.magic_scan_bytes]

    if extension == ".pdf":
        if not sample.startswith(b"%PDF-"):
            return False, "File content does not match PDF format"

    if extension == ".docx":
        if not sample.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
            return False, "File content does not match DOCX format"

    if extension == ".txt":
        if b"\x00" in sample:
            return False, "Text file appears to contain binary content"

    return True, None
```

```python
blocked_match = sorted(file_suffixes.intersection(self.blocked_extensions))
if blocked_match:
    _log_blocked(f"blocked_extension:{blocked_match[0]}")
    return False, f"Blocked file extension detected: {blocked_match[0]}"

if file_size > self.max_size_bytes:
    _log_blocked("file_too_large")
    return False, f"File too large. Maximum size is {settings.max_file_size_mb}MB"

if file_content is not None:
    valid_signature, signature_error = self._validate_magic_signature(file_ext, file_content)
    if not valid_signature:
        _log_blocked("invalid_file_signature")
        return False, signature_error
```

---

## 13. Project Ownership Isolation

### Explanation

Project access is consistently scoped by the owner derived from the JWT-authenticated user. The system does not trust client-supplied owner IDs. Project create, list, get, update, delete, indexing, and stats operations are owner-scoped. Unauthorized project access is logged as `AUTHZ_DENIED`.

### Path

`backend/controllers/project_controller.py`

```python
async def get_project(
    self,
    db: AsyncSession,
    project_id: int,
    owner_id: int,
) -> Optional[Project]:
    stmt = select(Project).where(
        Project.id == project_id,
        Project.owner_id == owner_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

```python
async def list_projects(
    self,
    db: AsyncSession,
    owner_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Project]:
    stmt = (
        select(Project)
        .where(Project.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
```

---

## 14. Document Ownership Isolation

### Explanation

Document routes enforce ownership isolation. Uploading requires an owned project, and listing, reading, processing, indexing, deleting documents, and checking task status all require ownership verification. Unauthorized document or task access is rejected and logged.

### Path

`backend/controllers/document_controller.py`

```python
# SECURITY RULE: all user-facing document queries must be scoped by JWT owner_id.

async def upload_document(
    self,
    db: AsyncSession,
    owner_id: int,
    project_id: int,
    file_content: bytes,
    filename: str,
    file_size: int,
    content_type: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Asset:
    project_stmt = select(Project).where(
        Project.id == project_id,
        Project.owner_id == owner_id,
    )
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if not project:
        raise ValueError("Forbidden")
```

---

## 15. Query/RAG Access Control

### Explanation

The query/RAG pipeline is protected against cross-user data leakage. The query endpoint requires authentication, verifies that the project belongs to the current user, sanitizes query text, bounds retrieval parameters, passes `owner_id` to the query service, and scopes vector retrieval by `owner_id`, `project_id`, and optionally `asset_id`.

### Paths

`backend/routes/query.py`

```python
@router.post("/projects/{project_id}/query", response_model=QueryResponse)
async def query_project(
    project_id: int,
    query_data: QueryRequest,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_query_scope(
        db=db,
        project_id=project_id,
        current_user=current_user,
        project_controller=project_controller,
        document_controller=document_controller,
        asset_id=query_data.asset_id,
    )

    clean_query = sanitize_text(query_data.query, max_length=4000, strip_html=True, allow_newlines=True)

    result = await query_controller.answer_query(
        db=db,
        owner_id=current_user.id,
        project_id=project_id,
        query=clean_query,
        asset_id=query_data.asset_id,
    )
```

`backend/services/query_service.py`

```python
filter_dict = {
    'owner_id': owner_id,
    'project_id': project_id,
}
if asset_id:
    filter_dict['asset_id'] = asset_id

results = await vector_db.search(
    collection_name=f"project_{project_id}",
    query_vector=query_embedding,
    top_k=candidate_k,
    filter_dict=filter_dict
)
```

---

## 16. Vector Database Security

### Explanation

Both PGVector and Qdrant enforce ownership-aware retrieval. Search operations require `owner_id`, and missing ownership filtering is treated as an error. PGVector filters by project owner through SQL joins, while Qdrant uses payload filters for `owner_id`, `project_id`, and `asset_id`. Qdrant vector deletion also refuses empty filters to prevent accidental broad deletion.

### Paths

`backend/providers/vectordb/pgvector_provider.py`

```python
class PGVectorProvider(VectorDBInterface):
    """PostgreSQL pgvector implementation."""

    # SECURITY RULE: retrieval queries must include owner_id filtering.

    async def collection_exists(
        self,
        collection_name: str,
        **kwargs
    ) -> bool:
        stmt = select(Project).where(Project.id == project_id)
        owner_id = kwargs.get('owner_id')
        if owner_id is not None:
            stmt = stmt.where(Project.owner_id == owner_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None
```

`backend/providers/vectordb/qdrant_provider.py`

```python
async def delete_vectors(
    self,
    collection_name: str,
    *,
    filter_dict: Dict[str, Any],
    **kwargs
) -> bool:
    if not filter_dict:
        raise ValueError("filter_dict is required when deleting vectors")

    conditions = []
    for key, value in filter_dict.items():
        conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

    await asyncio.to_thread(
        self.client.delete,
        collection_name=collection_name,
        points_selector=Filter(must=conditions),
        wait=True,
    )
```

---

## 17. Background Task Security

### Explanation

Celery background workflows include ownership protection. Task ownership is persisted, task status access verifies ownership, processing and indexing tasks include owner metadata, and vector metadata includes `owner_id`, `project_id`, `asset_id`, and chunk/document metadata. Failed processing also cleans stale chunks and vectors.

### Paths

`backend/utils/task_tracking.py`

```python
async def record_task_owner(
    db: AsyncSession,
    *,
    task_id: str,
    owner_id: int,
    task_name: str,
    task_args: dict[str, Any] | None,
) -> None:
    _TASK_OWNER_MAP[task_id] = owner_id

    payload_args = dict(task_args or {})
    payload_args["owner_id"] = owner_id

    manager = IdempotencyManager()
    await manager.upsert_task_record(
        db=db,
        task_name=task_name,
        task_args=payload_args,
        celery_task_id=task_id,
        status="PENDING",
    )
```

`backend/tasks/data_indexing.py`

```python
vector_metadata = [
    {
        "owner_id": project.owner_id,
        "asset_id": chunk.asset_id,
        "project_id": chunk.project_id,
        "chunk_index": chunk.chunk_index,
    }
    for chunk in chunks
]

await vector_db.add_vectors(
    collection_name=collection_name,
    vectors=embeddings,
    ids=chunk_ids,
    metadata=vector_metadata,
    session_maker=session_maker,
)
```

---

## 18. Security Event Logging

### Explanation

The project has centralized security event logging for login success/failure, signup success/failure, password changes, brute-force attempts, blocked uploads, rate limiting, authorization failures, invalid tokens, simulated XSS/SQL injection attempts, user suspension, blocking, and restoration. Events are stored in an in-memory ring buffer with a maximum of 5,000 events, and actionable events can automatically create incidents.

### Paths

`backend/security/security_event.py`

```python
class SecurityEventType:
    LOGIN_FAIL = "LOGIN_FAIL"
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    PASSWORD_CHANGE_SUCCESS = "PASSWORD_CHANGE_SUCCESS"
    PASSWORD_CHANGE_FAIL = "PASSWORD_CHANGE_FAIL"
    SIGNUP_FAIL = "SIGNUP_FAIL"
    SIGNUP_SUCCESS = "SIGNUP_SUCCESS"
    BRUTE_FORCE = "BRUTE_FORCE"
    FILE_UPLOAD_BLOCKED = "FILE_UPLOAD_BLOCKED"
    ATTACK_SIMULATION = "ATTACK_SIMULATION"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTHZ_DENIED = "AUTHZ_DENIED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    RATE_LIMITED = "RATE_LIMITED"
    XSS_ATTEMPT = "XSS_ATTEMPT"
    SQL_INJECTION = "SQL_INJECTION"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_BLOCKED = "USER_BLOCKED"
    USER_RESTORED = "USER_RESTORED"
```

`backend/security/event_service.py`

```python
_MAX_EVENTS = 5000
_EVENTS: Deque[SecurityEvent] = deque(maxlen=_MAX_EVENTS)

def log_event(event_data: SecurityEventCreate | Dict[str, Any]) -> SecurityEvent:
    payload = (
        event_data
        if isinstance(event_data, SecurityEventCreate)
        else SecurityEventCreate.model_validate(event_data)
    )

    event = SecurityEvent(
        event_type=_normalize_event_type(payload.event_type),
        severity=_normalize_severity(payload.severity),
        user_id=payload.user_id,
        username=normalized_username,
        ip_address=_normalize_ip(payload.ip_address),
        message=payload.message,
        metadata=payload.metadata or {},
    )

    with _EVENTS_LOCK:
        _EVENTS.append(event)

    incident_service.trigger_auto_creation(event)

    return event
```

---

## 19. Incident Management System

### Explanation

The project includes a full incident-management subsystem. Incidents are persisted in PostgreSQL and include severity, status, actor, assignment, description, notes, and false-positive fields. The system supports incident timelines, audit logs, assignment to security engineers, notes, false-positive handling, and reopening. Incidents can be automatically created from security events such as `BRUTE_FORCE`, `FILE_UPLOAD_BLOCKED`, and `RATE_LIMITED`.

### Paths

`backend/database/models.py`

```python
class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(120), nullable=False, index=True)
    severity = Column(
        SAEnum(IncidentSeverity, name="incident_severity", native_enum=False),
        nullable=False,
        default=IncidentSeverity.MEDIUM,
    )
    status = Column(
        SAEnum(IncidentStatus, name="incident_status", native_enum=False),
        nullable=False,
        default=IncidentStatus.OPEN,
        index=True,
    )

    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(String(64), nullable=True, index=True, default="system")
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    description = Column(Text, nullable=False)
    notes = Column(Text, nullable=True, default="")
    false_positive = Column(Boolean, nullable=False, default=False, index=True)
```

`backend/services/incident_service.py`

```python
class IncidentService:
    _TYPE_MAP = {
        SecurityEventType.BRUTE_FORCE: "Brute Force",
        SecurityEventType.FILE_UPLOAD_BLOCKED: "Upload Attack",
        SecurityEventType.RATE_LIMITED: "Rate Limit Abuse",
    }

    _SEVERITY_MAP = {
        SecurityEventType.BRUTE_FORCE: IncidentSeverity.HIGH,
        SecurityEventType.FILE_UPLOAD_BLOCKED: IncidentSeverity.HIGH,
        SecurityEventType.RATE_LIMITED: IncidentSeverity.MEDIUM,
    }
```

---

## 20. Incident Lifecycle Enforcement

### Explanation

Incident status transitions are controlled. The normal lifecycle is `OPEN → INVESTIGATING → RESOLVED → CLOSED`. Invalid transitions are rejected. Reopening is a special case allowed only from `CLOSED → OPEN` and requires a reason. Every major status change creates incident log entries and audit records.

### Path

`backend/services/incident_management_service.py`

```python
_ALLOWED_STATUS_TRANSITIONS: Dict[IncidentStatus, IncidentStatus] = {
    IncidentStatus.OPEN: IncidentStatus.INVESTIGATING,
    IncidentStatus.INVESTIGATING: IncidentStatus.RESOLVED,
    IncidentStatus.RESOLVED: IncidentStatus.CLOSED,
}

_REOPEN_ALLOWED_FROM: set = {IncidentStatus.CLOSED}
```

```python
if next_allowed is None or payload.status != next_allowed:
    raise HTTPException(
        status_code=400,
        detail=(
            f"Invalid transition from {self._enum_value(current_status)} "
            f"to {self._enum_value(payload.status)}"
        ),
    )

incident.status = payload.status

await self._append_incident_log(
    db=db,
    incident=incident,
    actor=current_user,
    event_type="STATUS_UPDATED",
    severity="LOW",
    message=f"Incident status updated from {previous_status} to {next_status}",
    metadata=status_log_metadata,
)
```

---

## 21. Incident Response Actions

### Explanation

Security engineers and admins can take response actions against incident actors, including suspending users, blocking users, restoring users, or ignoring incidents as false positives. Suspension duration must be positive, blocking remains active until manual restoration, and all actions are stored in incident logs and audit logs.

### Paths

`backend/models/incident_models.py`

```python
class IncidentActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: Literal["block_user", "suspend_user", "reactivate_user", "ignore"]
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

`backend/services/incident_management_service.py`

```python
_ACTION_LABELS: Dict[str, str] = {
    "block_user": "Block user",
    "suspend_user": "Suspend user",
    "reactivate_user": "Restore user",
    "ignore": "Ignore",
}

_AUDIT_ACTIONS: Dict[str, str] = {
    "block_user": "user_blocked",
    "suspend_user": "user_suspended",
    "reactivate_user": "user_reactivated",
    "ignore": "incident_ignored",
}
```

---

## 22. Admin User Controls

### Explanation

The backend provides admin-only APIs for suspending, blocking, and restoring users. These routes are protected by `require_admin_access`. Reasons are sanitized, suspension duration is bounded, and actions are performed through the central incident/account-management service while emitting security events and audit logs.

### Path

`backend/routes/admin_users.py`

```python
router = APIRouter(
    prefix="/admin/users",
    tags=["Admin"],
)

@router.post("/{user_id}/suspend", response_model=AdminUserStatusActionResponse)
async def admin_suspend_user(
    payload: AdminSuspendUserRequest,
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(AuthService),
    incident_management_service: IncidentManagementService = Depends(IncidentManagementService),
):
    updated_user = await incident_management_service.suspend_user(
        user_id,
        reason,
        int(payload.duration_minutes),
        actor=current_admin.username,
        db=db,
        auth_service=auth_service,
    )
```

```python
@router.post("/{user_id}/block", response_model=AdminUserStatusActionResponse)
async def admin_block_user(
    payload: AdminBlockUserRequest,
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await incident_management_service.block_user(
        user_id,
        reason,
        actor=current_admin.username,
        db=db,
        auth_service=auth_service,
    )
```

```python
@router.post("/{user_id}/restore", response_model=AdminUserStatusActionResponse)
async def admin_restore_user(
    user_id: int = Path(..., gt=0),
    current_admin: User = Depends(require_admin_access),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await incident_management_service.restore_user(
        user_id,
        actor=current_admin.username,
        db=db,
        auth_service=auth_service,
    )
```

---

## 23. Security Center Dashboard APIs

### Explanation

Security Center APIs are protected by security-engineer/admin RBAC. They include security stats, security events, event export, user account status summary, recent user status events, real-time events through Server-Sent Events, and attack simulation. The event stream uses no-cache headers and keepalive behavior.

### Path

`backend/routes/security.py`

```python
@router.get("/stats", response_model=SecurityStatsResponse)
async def security_stats(
    _current_user: User = Depends(require_security_center_access),
):
    return SecurityStatsResponse(**security_dashboard_service.get_stats())


@router.get("/events", response_model=List[SecurityEventResponse])
async def security_events(
    limit: int = Query(default=20, ge=1, le=50),
    _current_user: User = Depends(require_security_center_access),
):
    payload = security_dashboard_service.get_dashboard_payload(limit=limit)
    return _to_event_responses(payload["events"])


@router.get("/users/status-summary", response_model=SecurityUserStatusSummaryResponse)
async def security_users_status_summary(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_security_center_access),
):
    return SecurityUserStatusSummaryResponse(
        **await security_dashboard_service.get_user_status_summary(db=db)
    )
```

---

## 24. Security Event CSV Export

### Explanation

The backend supports exporting security events as CSV. The export includes a UTF-8 BOM for Excel compatibility, supports up to 5,000 events, and sends `Cache-Control: no-store` to prevent caching. This is useful for reporting, evidence collection, and security reviews.

### Path

`backend/routes/security.py`

```python
@router.get("/events/export")
async def security_events_export(
    limit: int = Query(default=1000, ge=1, le=5000),
    _current_user: User = Depends(require_security_center_access),
):
    events = security_dashboard_service.get_events_for_export(limit=limit)
    csv_payload = _to_events_export_csv(events)
    filename = f"security-events-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=f"\ufeff{csv_payload}",
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
```

---

## 25. Attack Simulation / SOC Demo Mode

### Explanation

The project includes a safe SOC/demo attack simulation mode. It can generate login-failure events, brute-force events, XSS attempt events, SQL injection events, attack simulation events, and optional account-block escalation. Simulated events are tagged with `simulation: true`, allowing the frontend to separate them from real security events. XSS and SQL injection appear mainly as simulated events; the actual general defense is sanitization, not a full WAF-style detection engine.

### Paths

`backend/routes/security.py`

```python
@router.post("/simulate", response_model=SecuritySimulationResponse)
async def simulate_security_attack(
    request: Request,
    target_user_id: Optional[int] = Query(default=None, gt=0),
    escalate_to_block: bool = Query(default=True),
    current_user: User = Depends(require_security_center_access),
    db: AsyncSession = Depends(get_db),
):
    simulation_result = await security_dashboard_service.simulate_attack_with_user_control(
        db=db,
        actor_username=current_user.username,
        actor_user_id=current_user.id,
        ip_address=_extract_client_ip(request),
        target_user_id=resolved_target_user_id,
        escalate_to_block=escalate_to_block,
        block_reason="attack_simulation_escalation",
    )
```

`backend/services/security_dashboard_service.py`

```python
log_event({
    "event_type": SecurityEventType.BRUTE_FORCE,
    "severity": SecuritySeverity.HIGH,
    "user_id": user_id,
    "username": username,
    "ip_address": ip_address,
    "message": "Credential stuffing pattern detected (simulation)",
    "metadata": {
        "simulation": True,
        "attack": "credential_stuffing",
    },
})
```

---

## 26. Frontend Security Behavior

### Explanation

The frontend includes security-related behavior such as storing JWT access tokens in localStorage, adding Bearer tokens to API requests, decoding token expiration client-side, redirecting to login when tokens are missing or expired, clearing tokens after authentication failure, and hiding Security Center UI unless the user has an admin or security-engineer role.

### Path

`frontend/app.js`

```javascript
const ROLE_USER = 'user';
const ROLE_ADMIN = 'admin';
const ROLE_SECURITY_ENGINEER = 'security_engineer';
const ROLE_CYBERSECURITY_ENGINEER = 'cybersecurity_engineer';

function getAccessToken() {
    return (localStorage.getItem(ACCESS_TOKEN_KEY) || '').trim();
}

function parseJwtPayload(token) {
    const parts = String(token || '').split('.');
    if (parts.length !== 3) return null;
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(padded));
}

function isTokenExpired(token) {
    const payload = parseJwtPayload(token);
    if (!payload || typeof payload.exp !== 'number') return true;
    return Date.now() >= payload.exp * 1000;
}
```

```javascript
function withAuthHeaders(extraHeaders = {}) {
    const token = getAccessToken();
    const headers = { ...extraHeaders };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return headers;
}

function canAccessSecurityCenter(user = state.currentUser) {
    const roles = normalizeUserRoles(user);
    return roles.includes(ROLE_SECURITY_ENGINEER)
        || roles.includes(ROLE_CYBERSECURITY_ENGINEER)
        || roles.includes(ROLE_ADMIN);
}
```

---

## 27. Runtime Configuration Security

### Explanation

The runtime configuration update endpoint validates provider names and configuration values. Provider names are sanitized, then checked against allowed provider registries. Chunk strategy and numeric runtime values are bounded, and configuration inputs use strict Pydantic models. Protection depends on `SECURITY_REQUIRE_AUTH_FOR_MUTATIONS`; in the example environment it is enabled, but the code supports disabling it.

### Path

`backend/routes/app_config.py`

```python
@router.post("/providers")
async def update_providers(
    payload: ProviderUpdate,
    _auth: Optional[AuthUser] = Depends(require_mutation_auth_if_enabled),
) -> Dict[str, object]:
    llm_provider = sanitize_text(payload.llm_provider, max_length=64, strip_html=True, allow_newlines=False).lower()
    embedding_provider = sanitize_text(payload.embedding_provider, max_length=64, strip_html=True, allow_newlines=False).lower()

    llm_available = set(LLMProviderFactory.get_available_providers())
    embedding_available = set(LLMProviderFactory.get_available_embedding_providers())
    vector_available = set(VectorDBProviderFactory.get_available_providers())

    if llm_provider not in llm_available:
        raise HTTPException(status_code=400, detail="Unsupported LLM provider")
    if embedding_provider not in embedding_available:
        raise HTTPException(status_code=400, detail="Unsupported embedding provider")
    if vector_db_provider is not None and vector_db_provider not in vector_available:
        raise HTTPException(status_code=400, detail="Unsupported vector DB provider")
```

---

## 28. Bot Configuration Security

### Explanation

Bot configuration updates require a JWT-authenticated database user. The `active_project_id` must be positive, and the selected project must belong to the allowed user or service-account context. Unauthorized project selection returns `403 Forbidden`. Bot profile names are sanitized before being used with the Telegram API.

### Path

`backend/routes/bot_config.py`

```python
@router.post("/config")
async def update_bot_config(
    config: BotConfig,
    current_user: User = Depends(get_current_db_user),
    db: AsyncSession = Depends(get_db),
):
    if config.active_project_id is None:
        raise HTTPException(status_code=400, detail="active_project_id is required")

    if config.active_project_id <= 0:
        raise HTTPException(status_code=400, detail="active_project_id must be a positive integer")

    stmt = select(Project.id).where(
        Project.id == config.active_project_id,
        Project.owner_id == config_owner_id,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Forbidden")
```

```python
@router.post("/profile")
async def update_bot_profile(
    name: str = Form(...),
    current_user: User = Depends(get_current_db_user),
):
    clean_name = sanitize_text(name, max_length=64, strip_html=True, allow_newlines=False)
    if not clean_name:
        raise HTTPException(status_code=400, detail="Bot name cannot be empty")
```

---

## 29. Error Handling Hardening

### Explanation

Several backend routes catch unexpected exceptions and return generic error messages such as `Internal server error`, `Login failed`, or `Forbidden`. This prevents leaking stack traces or internal implementation details to clients, while detailed logs are still recorded server-side for debugging and monitoring.

### Paths

`backend/routes/auth.py`

```python
except Exception as exc:
    logger.exception("Unexpected error during login")
    log_event({
        "event_type": SecurityEventType.LOGIN_FAIL,
        "severity": SecuritySeverity.HIGH,
        "username": tracking_username,
        "ip_address": tracking_ip,
        "message": "Login failed due to internal error",
        "metadata": {"username": tracking_username, "reason": "internal_error"},
    })
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Login failed",
    ) from exc
```

`backend/routes/query.py`

```python
except Exception:
    logger.exception("Unexpected error while querying project")
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 30. CORS Hardening

### Explanation

The application uses explicit CORS origins from configuration instead of unrestricted wildcard origins. This is especially important because `allow_credentials=True` is enabled. The setup supports controlled frontend/backend deployments without exposing authenticated cross-origin requests to arbitrary domains.

### Path

`backend/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 31. Operational Security / Availability Checks

### Explanation

The health-readiness checks verify that the system is not only running but also operationally ready. They check the database, Celery broker, Redis result backend, shared configuration path, and vector store. This helps prevent exposing a partially broken system as healthy.

### Path

`backend/routes/health.py`

```python
broker_status, result_backend_status, shared_config_status, vector_store_status = (
    await asyncio.gather(
        _probe_tcp_endpoint(settings.celery_broker_url),
        _probe_tcp_endpoint(settings.celery_result_backend),
        _probe_shared_config(),
        _probe_vector_store(db_status),
    )
)

overall_status = "healthy"
if not all(
    (
        db_status == "connected",
        broker_status == "connected",
        result_backend_status == "connected",
        shared_config_status == "ready",
        vector_store_status == "connected",
    )
):
    overall_status = "unhealthy"
```

```python
@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    return await _build_health_response(db, include_deep_checks=False)


@router.get("/health/full", response_model=HealthResponse)
async def health_check_full(db: AsyncSession = Depends(get_db)):
    return await _build_health_response(db, include_deep_checks=True)
```

---

# Limitations Found

These are not missing features from the extraction list, but visible limitations in the current code/design:

* No MFA.
* Security event feed is in-memory with a maximum of 5,000 events and may be lost after restart.
* RBAC is username/config-driven, not a full database-backed role-management system.
* No external SIEM integration.
* Simulation can block a real user when escalation is enabled.
* Security Center is suitable for demo/SOC workflow, but it is not a production-grade SIEM.
* `GET /bot/config` appears to be read-only/open, while mutation is protected.
* XSS and SQL injection are mainly represented through simulation and input sanitization; there is no full WAF-style detector.

---

# Best One-Line Summary

The code includes security across **JWT authentication, bcrypt password hashing, RBAC, account suspension/blocking, brute-force protection, endpoint rate limiting, upload hardening, ownership isolation, vector-search tenant isolation, security event logging, incident management, SOC dashboard features, attack simulation, admin response actions, sanitized errors, CORS controls, and frontend role-aware security behavior**.

---

## Footer — 31 Points Only

1. Security configuration layer
2. JWT authentication
3. Password security
4. Username validation and normalization
5. Service account security
6. Role-Based Access Control
7. Account status enforcement
8. Login brute-force protection
9. Rate limiting
10. Input sanitization
11. Filename sanitization
12. File upload security
13. Project ownership isolation
14. Document ownership isolation
15. Query/RAG access control
16. Vector database security
17. Background task security
18. Security event logging
19. Incident management system
20. Incident lifecycle enforcement
21. Incident response actions
22. Admin user controls
23. Security Center dashboard APIs
24. Security event CSV export
25. Attack simulation / SOC demo mode
26. Frontend security behavior
27. Runtime configuration security
28. Bot configuration security
29. Error handling hardening
30. CORS hardening
31. Operational security / availability checks
