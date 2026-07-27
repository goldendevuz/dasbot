import os
import unittest
from unittest.mock import MagicMock
from dasbot.db.database import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        mock_settings = MagicMock(
            DB_ADDRESS="postgresql://user:pass@test:5432/dasbot",
            DB_USERNAME="username",
            DB_PASSWORD="password",
        )
        mock_settings.get.side_effect = lambda name, default=None: getattr(mock_settings, name, default)
        self.db = Database(mock_settings)

    def test_url(self):
        self.assertEqual("postgresql://user:pass@test:5432/dasbot", self.db.url())

    def test_connect_test_mode(self):
        os.environ["ENV_FOR_DYNACONF"] = "test"
        db = self.db.connect()
        self.assertIn("chats", db)
        self.assertIn("scores", db)
        self.assertIn("stats", db)
        self.assertIn("dictionary_v3", db)


if __name__ == "__main__":
    unittest.main()
