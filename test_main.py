import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# main.py 的浏览器依赖在工作流中安装；单元测试只替换导入所需的模块。
playwright_module = MagicMock()
playwright_sync = MagicMock()
playwright_module.sync_api.sync_playwright = playwright_sync
sys.modules.setdefault("playwright", playwright_module)
sys.modules.setdefault("playwright.sync_api", playwright_module.sync_api)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import extract_server_identity, fetch_server_identity, load_env_file


class MainHelpersTest(unittest.TestCase):
    def test_extract_server_identity_from_servers_api_response(self):
        payload = {
            "success": True,
            "data": [{
                "uuidShort": "5515686b",
                "uuid": "5515686b-2beb-4edf-9144-d5769c940fe1",
            }],
        }

        self.assertEqual(
            extract_server_identity(payload),
            (
                "5515686b-2beb-4edf-9144-d5769c940fe1",
                "5515686b",
            ),
        )

    def test_load_env_file_does_not_overwrite_existing_environment(self):
        env_path = Path(__file__).with_name(".test.env")
        env_path.write_text("TEST_NEW=value\nTEST_EXISTING=from-file\n", encoding="utf-8")
        old_new = os.environ.get("TEST_NEW")
        old_existing = os.environ.get("TEST_EXISTING")
        try:
            os.environ.pop("TEST_NEW", None)
            os.environ["TEST_EXISTING"] = "from-environment"
            load_env_file(env_path)
            self.assertEqual(os.environ["TEST_NEW"], "value")
            self.assertEqual(os.environ["TEST_EXISTING"], "from-environment")
        finally:
            env_path.unlink(missing_ok=True)
            if old_new is None:
                os.environ.pop("TEST_NEW", None)
            else:
                os.environ["TEST_NEW"] = old_new
            if old_existing is None:
                os.environ.pop("TEST_EXISTING", None)
            else:
                os.environ["TEST_EXISTING"] = old_existing

    def test_fetch_server_identity_calls_servers_api_with_bearer(self):
        payload = {
            "success": True,
            "data": [{
                "uuidShort": "5515686b",
                "uuid": "5515686b-2beb-4edf-9144-d5769c940fe1",
            }],
        }
        mock_response = MagicMock()
        mock_response.json.return_value = payload

        with patch("main.requests.get", return_value=mock_response) as mocked_get:
            full_uuid, short_id = fetch_server_identity("ptlc_dummy")

        self.assertEqual(full_uuid, "5515686b-2beb-4edf-9144-d5769c940fe1")
        self.assertEqual(short_id, "5515686b")
        self.assertIn("/api/v2/servers", mocked_get.call_args.args[0])
        self.assertEqual(
            mocked_get.call_args.kwargs["headers"]["Authorization"],
            "Bearer ptlc_dummy",
        )


if __name__ == "__main__":
    unittest.main()
