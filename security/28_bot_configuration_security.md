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
