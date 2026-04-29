"""Runtime config atomic write regression tests."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import backend.runtime_config as runtime_config


class RuntimeConfigAtomicWriteTests(unittest.TestCase):
    def test_save_runtime_config_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "app_config.json"

            with patch("backend.runtime_config.get_app_config_path", return_value=config_path):
                runtime_config.save_runtime_config({"llm_provider": "gemini"})

            data = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(data["llm_provider"], "gemini")

    def test_update_runtime_config_preserves_existing_keys(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "app_config.json"
            config_path.write_text(json.dumps({"a": 1, "b": 2}), encoding="utf-8")

            with patch("backend.runtime_config.get_app_config_path", return_value=config_path):
                result = runtime_config.update_runtime_config({"b": 3})

            self.assertEqual(result, {"a": 1, "b": 3})
            data = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(data, {"a": 1, "b": 3})

    def test_failed_atomic_write_raises_runtime_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "app_config.json"

            with (
                patch("backend.runtime_config.get_app_config_path", return_value=config_path),
                patch("backend.runtime_config.os.replace", side_effect=OSError("disk full")),
            ):
                with self.assertRaisesRegex(RuntimeError, "Runtime config write failed"):
                    runtime_config.save_runtime_config({"llm_provider": "gemini"})


if __name__ == "__main__":
    unittest.main()

