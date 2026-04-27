"""Admin route/service smoke tests for platform operations."""

import inspect
import unittest

from fastapi.params import Depends as DependsParam

from backend.routes import admin_console, admin_users
from backend.security.auth import require_platform_owner_access
from backend.services.admin_service import AdminService


class AdminServiceTests(unittest.TestCase):
    def test_admin_service_boundary_exists(self):
        service = AdminService()

        self.assertIsInstance(service, AdminService)
        self.assertTrue(callable(service.overview))
        self.assertTrue(callable(service.list_companies))
        self.assertTrue(callable(service.set_company_status))

    def test_admin_company_mutations_require_platform_owner(self):
        for endpoint in (
            admin_console.activate_company,
            admin_console.suspend_company,
            admin_console.block_company,
        ):
            signature = inspect.signature(endpoint)
            dependency = signature.parameters["current_user"].default
            self.assertIsInstance(dependency, DependsParam)
            self.assertIs(dependency.dependency, require_platform_owner_access)

    def test_admin_user_status_mutations_require_platform_owner(self):
        for endpoint in (
            admin_users.admin_suspend_user,
            admin_users.admin_block_user,
            admin_users.admin_restore_user,
        ):
            signature = inspect.signature(endpoint)
            dependency = signature.parameters["current_admin"].default
            self.assertIsInstance(dependency, DependsParam)
            self.assertIs(dependency.dependency, require_platform_owner_access)


if __name__ == "__main__":
    unittest.main()
