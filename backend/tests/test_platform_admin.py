"""Platform owner admin route dependency tests."""

import inspect
import unittest

from fastapi.params import Depends as DependsParam

from backend.routes import admin_console
from backend.security.auth import require_platform_owner_access


class PlatformAdminTests(unittest.TestCase):
    def test_admin_overview_requires_platform_owner(self):
        signature = inspect.signature(admin_console.admin_overview)
        dependency = signature.parameters["_"].default

        self.assertIsInstance(dependency, DependsParam)
        self.assertIs(dependency.dependency, require_platform_owner_access)


if __name__ == "__main__":
    unittest.main()

