"""Auth helper tests for product roles."""

import unittest

from backend.database.models import User
from backend.security.auth import (
    ROLE_COMPANY_ADMIN,
    ROLE_PLATFORM_OWNER,
    get_product_role_for_user,
)


class SaaSAuthTests(unittest.TestCase):
    def test_product_role_defaults_to_company_admin(self):
        user = User(username="company", hashed_password="hash")

        self.assertEqual(get_product_role_for_user(user), ROLE_COMPANY_ADMIN)

    def test_product_role_recognizes_platform_owner(self):
        user = User(username="owner", hashed_password="hash", role=ROLE_PLATFORM_OWNER)

        self.assertEqual(get_product_role_for_user(user), ROLE_PLATFORM_OWNER)

    def test_unknown_product_role_falls_back_to_company_admin(self):
        user = User(username="weird", hashed_password="hash", role="admin")

        self.assertEqual(get_product_role_for_user(user), ROLE_COMPANY_ADMIN)


if __name__ == "__main__":
    unittest.main()

