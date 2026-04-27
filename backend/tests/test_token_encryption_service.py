"""TokenEncryptionService tests."""

import unittest

from backend.services.token_encryption_service import TokenEncryptionService


class TokenEncryptionServiceTests(unittest.TestCase):
    def test_encrypt_decrypt_and_hash_secret(self):
        service = TokenEncryptionService(TokenEncryptionService.generate_key())
        token = "123456:telegram-secret-token"

        encrypted = service.encrypt_secret(token)

        self.assertNotEqual(encrypted, token)
        self.assertEqual(service.decrypt_secret(encrypted), token)
        self.assertEqual(service.hash_secret(token), service.hash_secret(token))
        self.assertNotEqual(service.hash_secret(token), token)


if __name__ == "__main__":
    unittest.main()

