"""Service layer for security dashboard data, simulation, and realtime stream payloads."""
from __future__ import annotations

import asyncio
import json
import random
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import Request

from backend.security.event_service import get_security_stats, list_events, log_event
from backend.security.security_event import SecurityEventType, SecuritySeverity


class SecurityDashboardService:
    """Central security dashboard business logic built on the shared event system."""

    @staticmethod
    def normalize_limit(limit: int) -> int:
        return 50 if int(limit) == 50 else 20

    def get_stats(self) -> Dict[str, int]:
        return get_security_stats()

    def get_events(self, *, limit: int = 20) -> List[Dict[str, Any]]:
        safe_limit = self.normalize_limit(limit)
        return [event.model_dump(mode="json") for event in list_events(limit=safe_limit)]

    def get_dashboard_payload(self, *, limit: int = 20) -> Dict[str, Any]:
        safe_limit = self.normalize_limit(limit)
        return {
            "stats": self.get_stats(),
            "events": self.get_events(limit=safe_limit),
        }

    def simulate_attack(self, *, user_id: int, username: Optional[str], ip_address: Optional[str]) -> int:
        """Generate demo attack events exclusively through the central event logger."""
        login_failures = random.randint(5, 10)
        generated_count = 0

        for attempt in range(1, login_failures + 1):
            log_event(
                {
                    "event_type": SecurityEventType.LOGIN_FAIL,
                    "severity": SecuritySeverity.MEDIUM,
                    "user_id": user_id,
                    "username": username,
                    "ip_address": ip_address,
                    "message": f"Invalid password attempt #{attempt} (simulation)",
                    "metadata": {
                        "simulation": True,
                        "attack": "credential_stuffing",
                        "attempt": attempt,
                    },
                }
            )
            generated_count += 1

        log_event(
            {
                "event_type": SecurityEventType.BRUTE_FORCE,
                "severity": SecuritySeverity.HIGH,
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "message": "Multiple attempts detected (simulation)",
                "metadata": {
                    "simulation": True,
                    "attack": "brute_force",
                },
            }
        )
        generated_count += 1

        log_event(
            {
                "event_type": SecurityEventType.XSS_ATTEMPT,
                "severity": SecuritySeverity.HIGH,
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "message": "Reflected XSS payload detected (simulation)",
                "metadata": {
                    "simulation": True,
                    "attack": "xss",
                    "payload": "<script>alert(1)</script>",
                },
            }
        )
        generated_count += 1

        log_event(
            {
                "event_type": SecurityEventType.SQL_INJECTION,
                "severity": SecuritySeverity.CRITICAL,
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "message": "SQL injection pattern detected (simulation)",
                "metadata": {
                    "simulation": True,
                    "attack": "sql_injection",
                    "payload": "' OR 1=1 --",
                },
            }
        )
        generated_count += 1

        return generated_count

    async def stream_dashboard_updates(
        self,
        *,
        request: Request,
        limit: int = 20,
    ) -> AsyncIterator[str]:
        """Yield SSE chunks containing dashboard payload updates from the event system."""
        safe_limit = self.normalize_limit(limit)
        last_signature: Optional[str] = None
        idle_ticks = 0

        while True:
            if await request.is_disconnected():
                break

            payload = self.get_dashboard_payload(limit=safe_limit)
            stats = payload["stats"]
            events = payload["events"]

            newest_id = events[0]["id"] if events else "none"
            signature = (
                f"{newest_id}:{stats['total_events']}:{stats['login_failures']}:"
                f"{stats['brute_force_attempts']}:{stats['blocked_uploads']}"
            )

            if signature != last_signature:
                yield f"event: security-update\ndata: {json.dumps(payload, ensure_ascii=True)}\n\n"
                last_signature = signature
                idle_ticks = 0
            else:
                idle_ticks += 1

            if idle_ticks >= 15:
                yield ": keep-alive\n\n"
                idle_ticks = 0

            await asyncio.sleep(1)


security_dashboard_service = SecurityDashboardService()
