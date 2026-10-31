"""
Mindustry Tool (mindustry-tool.com) API v4 Client.
Provides Discord OAuth device/app login, token management,
and schematic publishing functionality.
Pure Python standard library only (zero external dependencies).
Strictly <= 70 columns formatting for all outputs and messages.
"""

import os
import sys
import time
import json
import base64
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Tuple

API_BASE = "https://api.mindustry-tool.com/api/v4"
WEB_BASE = "https://mindustry-tool.com"
AUTH_DIR = os.path.expanduser("~/.config/mindustry")
AUTH_FILE = os.path.join(AUTH_DIR, "tool-auth.json")


def _get_auth_file_path() -> str:
    """Return path to tool-auth.json, allowing override via env."""
    return os.environ.get("MINDUSTRY_TOOL_AUTH", AUTH_FILE)


def _make_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    timeout: int = 15,
) -> Dict[str, Any]:
    """Execute HTTP request against Mindustry Tool API v4."""
    url = f"{API_BASE}{endpoint}" if endpoint.startswith("/") else f"{API_BASE}/{endpoint}"
    headers = {
        "User-Agent": "MindustrySchematicMaker/1.0",
        "Accept": "application/json",
    }
    payload_bytes = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        payload_bytes = json.dumps(data).encode("utf-8")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            if not body.strip():
                return {}
            return json.loads(body)
    except urllib.error.HTTPError as err:
        error_msg = f"HTTP {err.code}: {err.reason}"
        try:
            err_body = err.read().decode("utf-8")
            err_json = json.loads(err_body)
            if "message" in err_json:
                error_msg = err_json["message"]
            elif "error" in err_json:
                error_msg = str(err_json["error"])
        except Exception:
            pass
        raise RuntimeError(f"API Error ({error_msg})")
    except urllib.error.URLError as err:
        raise RuntimeError(f"Network Error: {err.reason}")


def request_login_uri() -> Dict[str, str]:
    """
    Request OAuth login URI for Mindustry Tool app flow.
    Returns dict containing 'sessionKey' and 'loginUri'.
    """
    resp = _make_request("/auth/app/login-uri", method="GET")
    session_key = resp.get("sessionKey") or resp.get("session_key") or ""
    login_uri = resp.get("loginUri") or resp.get("login_uri") or resp.get("url") or ""
    if not session_key or not login_uri:
        raise RuntimeError("API returned invalid login-uri response payload.")
    return {
        "sessionKey": session_key,
        "loginUri": login_uri,
    }


def poll_login_token(
    session_key: str,
    timeout: int = 120,
    interval: int = 2,
) -> Dict[str, Any]:
    """
    Poll for access token after user authorizes in browser.
    Returns token dictionary and saves credentials upon success.
    """
    start_time = time.time()
    payload = {"sessionKey": session_key}

    while (time.time() - start_time) < timeout:
        try:
            resp = _make_request(
                "/auth/app/login-token",
                method="POST",
                data=payload,
                timeout=10,
            )
            # Check if token received
            access_tok = resp.get("accessToken") or resp.get("access_token") or resp.get("token")
            if access_tok:
                save_auth(resp)
                return resp
        except RuntimeError as err:
            # 400 or pending message while waiting for user confirmation
            err_str = str(err).lower()
            if "wait" not in err_str and "pending" not in err_str and "400" not in err_str:
                # Unexpected error, retry anyway until timeout
                pass

        time.sleep(interval)

    raise TimeoutError("Authentication timed out waiting for authorization.")


def save_auth(tokens: Dict[str, Any]) -> str:
    """Save authentication tokens to ~/.config/mindustry/tool-auth.json."""
    auth_path = _get_auth_file_path()
    auth_dir = os.path.dirname(auth_path)
    os.makedirs(auth_dir, mode=0o700, exist_ok=True)

    access_tok = tokens.get("accessToken") or tokens.get("access_token") or tokens.get("token")
    refresh_tok = tokens.get("refreshToken") or tokens.get("refresh_token")
    expires_in = tokens.get("expiresIn") or tokens.get("expires_in")
    expires_at = tokens.get("expiresAt") or tokens.get("expires_at")

    if expires_in and not expires_at:
        expires_at = time.time() + float(expires_in)

    auth_data = {
        "accessToken": access_tok,
        "refreshToken": refresh_tok,
        "expiresAt": expires_at,
        "user": tokens.get("user") or tokens.get("profile") or {},
        "updatedAt": time.time(),
    }

    # Write file and restrict permissions to 0600
    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)

    try:
        os.chmod(auth_path, 0o600)
    except Exception:
        pass

    return auth_path


def load_auth() -> Optional[Dict[str, Any]]:
    """Load authentication tokens if file exists."""
    auth_path = _get_auth_file_path()
    if not os.path.isfile(auth_path):
        return None
    try:
        with open(auth_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def refresh_token(refresh_tok: str) -> Dict[str, Any]:
    """Refresh access token using refreshToken."""
    payload = {"refreshToken": refresh_tok}
    resp = _make_request("/auth/app/refresh", method="POST", data=payload)
    save_auth(resp)
    return resp


def get_valid_token() -> str:
    """
    Retrieve valid access token, auto-refreshing if expired or within 60s.
    Raises RuntimeError if not logged in or refresh fails.
    """
    auth = load_auth()
    if not auth or not auth.get("accessToken"):
        raise RuntimeError("Not logged in. Run 'msch login' to authenticate.")

    expires_at = auth.get("expiresAt")
    if expires_at and time.time() >= (float(expires_at) - 60):
        # Token expired or about to expire
        refresh_tok = auth.get("refreshToken")
        if not refresh_tok:
            raise RuntimeError("Session expired. Run 'msch login' to re-authenticate.")
        try:
            new_auth = refresh_token(refresh_tok)
            return new_auth.get("accessToken") or ""
        except Exception as err:
            raise RuntimeError(f"Session refresh failed: {err}. Please run 'msch login'.")

    return auth["accessToken"]


def publish_schematic(
    msch_path: str,
    tags: Optional[List[str]] = None,
    description: Optional[str] = None,
    name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Publish a Mindustry schematic (.msch) to mindustry-tool.com.
    Validates magic bytes 'msch\x01' (Base64 bXNjaAF).
    Returns response dict with 'id' and 'url'.
    """
    # 1. Read and validate schematic content
    if os.path.isfile(msch_path):
        with open(msch_path, "rb") as f:
            raw_bytes = f.read()

        if raw_bytes.startswith(b"msch"):
            # Binary .msch file
            b64_str = base64.b64encode(raw_bytes).decode("utf-8")
        elif raw_bytes.startswith(b"bXNja"):
            # ASCII Base64 text file
            b64_str = raw_bytes.decode("utf-8").strip()
        else:
            raise ValueError("Invalid file format: Missing 'msch' binary magic header.")
    elif msch_path.startswith("bXNja"):
        b64_str = msch_path.strip()
    else:
        raise ValueError(f"Schematic file not found: {msch_path}")

    # Validate Base64 magic prefix (bXNja is base64 for 'msch')
    if not b64_str.startswith("bXNja"):
        raise ValueError("Invalid schematic data: Does not start with 'bXNja'.")

    # 2. Extract metadata if not provided
    if not name or description is None:
        try:
            from core.codec import decode_schematic
            decoded = decode_schematic(b64_str)
            if not name:
                name = decoded.get("name")
            if description is None:
                description = decoded.get("description", "")
        except Exception:
            pass

    if not name:
        if os.path.isfile(msch_path):
            base = os.path.basename(msch_path)
            name = os.path.splitext(base)[0]
        else:
            name = "Synthesized Schematic"

    # 3. Retrieve valid token and submit
    token = get_valid_token()
    payload = {
        "data": b64_str,
        "name": name,
        "description": description or "",
        "tags": tags or [],
    }

    resp = _make_request("/schematics", method="POST", data=payload, token=token)

    # Resolve ID and Web URL
    schem_id = resp.get("id") or resp.get("schematic", {}).get("id") or resp.get("data", {}).get("id")
    if schem_id:
        resp["id"] = str(schem_id)
        resp["url"] = f"{WEB_BASE}/schematics/{schem_id}"

    return resp


def check_status() -> Dict[str, Any]:
    """Check current authentication status and user details."""
    auth = load_auth()
    if not auth or not auth.get("accessToken"):
        return {
            "logged_in": False,
            "message": "Not logged in to mindustry-tool.com.",
            "auth_file": _get_auth_file_path(),
        }

    user = auth.get("user") or {}
    username = user.get("username") or user.get("name") or "Authorized User"
    expires_at = auth.get("expiresAt")
    is_valid = True
    if expires_at and time.time() > float(expires_at):
        is_valid = False

    return {
        "logged_in": True,
        "valid": is_valid,
        "username": username,
        "user_id": user.get("id", ""),
        "expires_at": expires_at,
        "auth_file": _get_auth_file_path(),
    }


def logout() -> bool:
    """Log out by removing saved credentials file."""
    auth_path = _get_auth_file_path()
    if os.path.isfile(auth_path):
        os.remove(auth_path)
        return True
    return False
