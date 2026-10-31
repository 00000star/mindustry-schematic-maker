"""
Unit Test Suite for Mindustry Tool API v4 Client & CLI Integration.
Tests OAuth login-uri, token polling, save/load, auto-refresh,
schematic publishing, status reporting, and mobile width constraints (<= 70 cols).
Pure Python standard library only.
"""

import os
import sys
import time
import json
import base64
import unittest
import tempfile
import subprocess
from unittest.mock import patch, MagicMock

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CUR_DIR)
if CUR_DIR not in sys.path:
    sys.path.insert(0, CUR_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from core.mindustry_tool import (
        request_login_uri,
        poll_login_token,
        save_auth,
        load_auth,
        refresh_token,
        get_valid_token,
        publish_schematic,
        check_status,
        logout,
        _get_auth_file_path,
    )
except ImportError:
    from mindustry_tool import (
        request_login_uri,
        poll_login_token,
        save_auth,
        load_auth,
        refresh_token,
        get_valid_token,
        publish_schematic,
        check_status,
        logout,
        _get_auth_file_path,
    )


class TestMindustryToolAPI(unittest.TestCase):
    """Test suite for mindustry-tool.com v4 API integration."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.auth_file = os.path.join(self.temp_dir.name, "tool-auth.json")
        self.env_patcher = patch.dict(os.environ, {"MINDUSTRY_TOOL_AUTH": self.auth_file})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    @patch("urllib.request.urlopen")
    def test_request_login_uri(self, mock_urlopen):
        """Verify request_login_uri executes GET /auth/app/login-uri."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "sessionKey": "sess_test_12345",
            "loginUri": "https://mindustry-tool.com/auth/app?session=sess_test_12345"
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = request_login_uri()
        self.assertEqual(res["sessionKey"], "sess_test_12345")
        self.assertIn("sess_test_12345", res["loginUri"])

        # Check request url
        req = mock_urlopen.call_args[0][0]
        self.assertTrue(req.full_url.endswith("/auth/app/login-uri"))
        self.assertEqual(req.get_method(), "GET")

    @patch("urllib.request.urlopen")
    def test_poll_login_token_success(self, mock_urlopen):
        """Verify poll_login_token polls and saves credentials upon confirmation."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "accessToken": "acc_tok_999",
            "refreshToken": "ref_tok_888",
            "expiresIn": 3600,
            "user": {"id": "usr_42", "username": "Starboy"}
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = poll_login_token("sess_test_12345", timeout=5, interval=0.1)
        self.assertEqual(res["accessToken"], "acc_tok_999")
        self.assertEqual(res["user"]["username"], "Starboy")

        # Verify credentials were automatically saved to disk
        auth = load_auth()
        self.assertIsNotNone(auth)
        self.assertEqual(auth["accessToken"], "acc_tok_999")
        self.assertEqual(auth["refreshToken"], "ref_tok_888")
        self.assertEqual(auth["user"]["username"], "Starboy")

    def test_save_load_auth_permissions(self):
        """Verify saved credentials file has strict 0600 permissions."""
        tokens = {
            "accessToken": "secret_access_token",
            "refreshToken": "secret_refresh_token",
            "expiresIn": 7200,
            "user": {"id": "100", "username": "Admin"},
        }
        saved_path = save_auth(tokens)
        self.assertTrue(os.path.isfile(saved_path))

        mode = os.stat(saved_path).st_mode & 0o777
        self.assertEqual(mode, 0o600)

        auth = load_auth()
        self.assertEqual(auth["accessToken"], "secret_access_token")
        self.assertEqual(auth["refreshToken"], "secret_refresh_token")
        self.assertGreater(auth["expiresAt"], time.time())

    @patch("urllib.request.urlopen")
    def test_get_valid_token_auto_refresh(self, mock_urlopen):
        """Verify token auto-refreshes when expired."""
        # Save expired token
        expired_tokens = {
            "accessToken": "old_expired_token",
            "refreshToken": "valid_refresh_token",
            "expiresAt": time.time() - 300,  # 5 minutes ago
            "user": {"username": "Admin"},
        }
        save_auth(expired_tokens)

        # Mock refresh response
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "accessToken": "new_fresh_token",
            "refreshToken": "valid_refresh_token",
            "expiresIn": 3600,
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        tok = get_valid_token()
        self.assertEqual(tok, "new_fresh_token")

        # Verify refreshed token saved to disk
        updated = load_auth()
        self.assertEqual(updated["accessToken"], "new_fresh_token")

    @patch("urllib.request.urlopen")
    def test_publish_schematic(self, mock_urlopen):
        """Verify publish_schematic encodes binary and formats POST payload."""
        # 1. Setup valid auth
        save_auth({
            "accessToken": "publish_bearer_token",
            "expiresAt": time.time() + 3600,
            "user": {"username": "Creator"},
        })

        # 2. Create test .msch binary file using bytes literal without null bytes in code
        dummy_msch = os.path.join(self.temp_dir.name, "test_schem.msch")
        raw_msch_data = b"msch" + bytes([1, 0, 0, 0, 5]) + b"hello"
        with open(dummy_msch, "wb") as f:
            f.write(raw_msch_data)

        # 3. Mock publish response
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "id": "schem_abc123",
            "name": "Test Factory",
            "success": True,
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # 4. Publish
        res = publish_schematic(
            dummy_msch,
            tags=["silicon", "defense"],
            description="High efficiency silicon facility",
            name="Test Factory",
        )

        self.assertEqual(res["id"], "schem_abc123")
        self.assertEqual(res["url"], "https://mindustry-tool.com/schematics/schem_abc123")

        # 5. Assert request headers and payload
        req = mock_urlopen.call_args[0][0]
        self.assertTrue(req.full_url.endswith("/schematics"))
        self.assertEqual(req.get_header("Authorization"), "Bearer publish_bearer_token")
        self.assertEqual(req.get_header("Content-type"), "application/json")

        payload = json.loads(req.data.decode("utf-8"))
        self.assertTrue(payload["data"].startswith("bXNja"))
        self.assertEqual(payload["name"], "Test Factory")
        self.assertEqual(payload["description"], "High efficiency silicon facility")
        self.assertEqual(payload["tags"], ["silicon", "defense"])

    def test_status_and_logout(self):
        """Verify check_status and logout lifecycle."""
        # Initial status: logged out
        st1 = check_status()
        self.assertFalse(st1["logged_in"])

        # Save tokens
        save_auth({
            "accessToken": "tok_xyz",
            "expiresAt": time.time() + 1800,
            "user": {"id": "1", "username": "MindustryGeneral"},
        })

        st2 = check_status()
        self.assertTrue(st2["logged_in"])
        self.assertTrue(st2["valid"])
        self.assertEqual(st2["username"], "MindustryGeneral")

        # Logout
        self.assertTrue(logout())
        self.assertFalse(os.path.isfile(self.auth_file))

        st3 = check_status()
        self.assertFalse(st3["logged_in"])

    def test_column_width_constraint(self):
        """Assert all CLI status display lines adhere strictly to <= 70 cols."""
        save_auth({
            "accessToken": "tok_xyz",
            "expiresAt": time.time() + 1800,
            "user": {"id": "1", "username": "MindustryGeneral"},
        })

        msch_path = os.path.join(CUR_DIR, "msch")
        if not os.path.exists(msch_path):
            msch_path = os.path.join(PARENT_DIR, "msch")

        res = subprocess.run(
            [sys.executable, msch_path, "login", "--status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "MINDUSTRY_TOOL_AUTH": self.auth_file}
        )

        self.assertEqual(res.returncode, 0)
        self.assertIn("Mindustry Tool Authentication Status", res.stdout)
        self.assertIn("MindustryGeneral", res.stdout)

        for line_num, line in enumerate(res.stdout.splitlines(), start=1):
            self.assertLessEqual(
                len(line),
                70,
                f"Line {line_num} in 'msch login --status' exceeds 70 cols: '{line}'"
            )


if __name__ == "__main__":
    unittest.main()
