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
