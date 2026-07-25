import os
import unittest
from unittest.mock import patch

from config import get_app_mode


class AppModeTests(unittest.TestCase):
    def test_defaults_to_local_mode(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_app_mode(), "local")

    def test_accepts_demo_mode(self) -> None:
        with patch.dict(os.environ, {"APP_MODE": "demo"}, clear=True):
            self.assertEqual(get_app_mode(), "demo")

    def test_falls_back_to_local_for_unknown_mode(self) -> None:
        with patch.dict(os.environ, {"APP_MODE": "production"}, clear=True):
            self.assertEqual(get_app_mode(), "local")


if __name__ == "__main__":
    unittest.main()
