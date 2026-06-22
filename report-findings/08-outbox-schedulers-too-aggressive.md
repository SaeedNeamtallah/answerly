# 8. Outbox Schedulers Are Too Aggressive By Default

Date: 2026-06-20  
Source: `report.md`

## Evidence

- Worker logs show Telegram and WhatsApp outbox tasks firing every 2 seconds while claiming zero messages.
- `backend/celery_app.py:164-171` schedules both outbox tasks from settings.
- `backend/config.py:327-353` default outbox poll intervals are 2 seconds.

## Impact

This is acceptable for a short local demo, but it creates noisy logs and unnecessary DB/Celery traffic in production, especially as worker count grows.

## Best Fix

Raise production defaults or split local/demo defaults from production:

- Local/demo: 2 seconds.
- Production: 10-30 seconds, or event-driven enqueue for immediate delivery plus slower recovery sweep for stale `sending` rows.

