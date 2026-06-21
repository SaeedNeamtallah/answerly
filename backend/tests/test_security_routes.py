"""Regression tests for security route permissions."""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from backend.database.models import User, UserRole
from backend.security.auth import AuthUser, require_security_center_access

class SecurityRoutesTests(unittest.IsolatedAsyncioTestCase):
    async def test_require_security_center_access_allows_security_engineer(self):
        user = User(id=1, username="sec_eng", role="security_engineer")
        request = SimpleNamespace(
            state=SimpleNamespace(auth_user=AuthUser(username="sec_eng", roles=[])),
            url=SimpleNamespace(path="/security/events"),
            method="GET",
            headers={},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        result = await require_security_center_access(request=request, current_user=user)
        self.assertEqual(result.id, 1)

    async def test_require_security_center_access_allows_admin(self):
        user = User(id=2, username="admin_user", role="admin")
        request = SimpleNamespace(
            state=SimpleNamespace(auth_user=AuthUser(username="admin_user", roles=["admin"])),
            url=SimpleNamespace(path="/security/events"),
            method="GET",
            headers={},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        with patch("backend.security.auth.has_role", return_value=True):
            result = await require_security_center_access(request=request, current_user=user)
        self.assertEqual(result.id, 2)

    async def test_require_security_center_access_denies_company_admin(self):
        user = User(id=3, username="admin", role=UserRole.COMPANY_ADMIN.value)
        request = SimpleNamespace(
            state=SimpleNamespace(auth_user=AuthUser(username="admin", roles=[])),
            url=SimpleNamespace(path="/security/events"),
            method="GET",
            headers={},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        
        with self.assertRaises(HTTPException) as exc:
            await require_security_center_access(request=request, current_user=user)
            
        self.assertEqual(exc.exception.status_code, 403)
        self.assertEqual(exc.exception.detail, "Security Center access is restricted to security_engineer, admin, and platform_owner roles")

    async def test_require_security_center_access_allows_platform_owner(self):
        user = User(id=4, username="owner", role=UserRole.PLATFORM_OWNER.value)
        request = SimpleNamespace(
            state=SimpleNamespace(auth_user=AuthUser(username="owner", roles=[])),
            url=SimpleNamespace(path="/security/events"),
            method="GET",
            headers={},
            client=SimpleNamespace(host="127.0.0.1"),
        )
        result = await require_security_center_access(request=request, current_user=user)
        self.assertEqual(result.id, 4)

if __name__ == "__main__":
    unittest.main()
