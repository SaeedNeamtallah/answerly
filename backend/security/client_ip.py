"""Client IP extraction with explicit trusted-proxy handling."""
from __future__ import annotations

from ipaddress import ip_address, ip_network
from typing import Optional

from fastapi import Request

from backend.config import settings


def _configured_trusted_proxies() -> list[str]:
    raw_value = str(getattr(settings, "security_trusted_proxy_ips", "") or "")
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _host_matches_trusted_proxy(host: str, trusted_entries: list[str]) -> bool:
    try:
        peer_ip = ip_address(host)
    except ValueError:
        return host in trusted_entries

    for entry in trusted_entries:
        try:
            if peer_ip in ip_network(entry, strict=False):
                return True
        except ValueError:
            if host == entry:
                return True
    return False


def _direct_client_host(request: Request | None) -> Optional[str]:
    if request is None or request.client is None or not request.client.host:
        return None
    return str(request.client.host).strip() or None


def _first_forwarded_for(request: Request) -> Optional[str]:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    forwarded_ip = forwarded_for.split(",", 1)[0].strip()
    return forwarded_ip or None


def get_client_ip(request: Request | None) -> str:
    """Return the request IP, honoring X-Forwarded-For only from trusted peers."""
    direct_host = _direct_client_host(request)
    if request is not None and direct_host:
        if _host_matches_trusted_proxy(direct_host, _configured_trusted_proxies()):
            forwarded_ip = _first_forwarded_for(request)
            if forwarded_ip:
                return forwarded_ip
        return direct_host
    return "unknown"


def get_optional_client_ip(request: Request | None, *, max_length: int | None = None) -> Optional[str]:
    client_ip = get_client_ip(request)
    if client_ip == "unknown":
        return None
    if max_length is not None:
        return client_ip[:max_length]
    return client_ip
