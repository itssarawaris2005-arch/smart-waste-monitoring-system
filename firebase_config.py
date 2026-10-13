
"""Firebase Realtime Database helpers for Smart Waste Monitoring.

Configuration priority:
1. FIREBASE_DATABASE_URL environment variable
2. firebase_url in google-services.json
3. FALLBACK_DATABASE_URL

A missing google-services.json file is not fatal when a valid
database URL is otherwise configured.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOOGLE_SERVICES_FILE = os.path.join(
    BASE_DIR, "google-services.json"
)


# Keep this URL aligned with your current Firebase project.
FALLBACK_DATABASE_URL = (
    "https://smart-waste-monitoring-s-f24d7-default-rtdb.firebaseio.com"
)


def _normalize_database_url(url):
    """Return a valid HTTPS database URL, or an empty string."""
    if not isinstance(url, str):
        return ""

    url = url.strip().rstrip("/")
    if not url:
        return ""

    try:
        parsed = urllib.parse.urlparse(url)

        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            return ""

        return url
    except (ValueError, TypeError):
        return ""


def _load_database_url():
    """Load the database URL without requiring a JSON config file."""

    # 1. Explicit environment configuration.
    env_url = _normalize_database_url(
        os.environ.get("FIREBASE_DATABASE_URL", "")
    )

    if env_url:
        return env_url

    # 2. Read the JSON configuration when it exists.
    if os.path.isfile(GOOGLE_SERVICES_FILE):
        try:
            with open(
                GOOGLE_SERVICES_FILE, "r", encoding="utf-8"
            ) as file:
                config = json.load(file)

            project_info = config.get("project_info") or {}
            json_url = _normalize_database_url(
                project_info.get("firebase_url", "")
            )

            if json_url:
                return json_url

            print(
                "[Firebase Config] No valid firebase_url in "
                "google-services.json. Checking fallback URL."
            )

        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            print(
                "[Firebase Config] Could not read "
                f"google-services.json: {exc}"
            )
    else:
        print(
            "[Firebase Config] google-services.json is missing. "
            "Checking configured database URL fallback."
        )

    # 3. Fallback URL.
    fallback_url = _normalize_database_url(
        FALLBACK_DATABASE_URL
    )

    if fallback_url:
        return fallback_url

    raise ValueError(
        "No valid Firebase Realtime Database URL is configured. "
        "Set FIREBASE_DATABASE_URL or correct FALLBACK_DATABASE_URL."
    )


DATABASE_URL = _load_database_url()


def _auth_token():
    """Get the current Firebase ID token, if a user is signed in."""
    try:
        from firebase_auth import get_id_token
        return get_id_token()
    except (ImportError, AttributeError) as exc:
        print(f"[Firebase Config] Authentication unavailable: {exc}")
        return None


def _url(path):
    """Build a Firebase REST URL with correctly encoded path segments."""
    path = str(path or "").strip("/")

    safe_path = "/".join(
        urllib.parse.quote(segment, safe="")
        for segment in path.split("/")
        if segment
    )

    if safe_path:
        url = f"{DATABASE_URL}/{safe_path}.json"
    else:
        url = f"{DATABASE_URL}/.json"

    token = _auth_token()

    if token:
        separator = "&" if "?" in url else "?"
        url += separator + urllib.parse.urlencode(
            {"auth": token}
        )

    return url


def _request(method, path, data=None):
    """Send a request to Firebase Realtime Database."""
    try:
        body = (
            None if data is None
            else json.dumps(data).encode("utf-8")
        )

        request = urllib.request.Request(
            _url(path),
            data=body,
            headers={"Content-Type": "application/json"},
            method=method,
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return True, json.loads(raw) if raw else None

    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8")
            detail = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            detail = {}

        if isinstance(detail, dict):
            message = detail.get(
                "error", f"HTTP {exc.code}"
            )
        else:
            message = str(detail) or f"HTTP {exc.code}"

        return False, str(message)

    except urllib.error.URLError as exc:
        return False, (
            f"Internet/Firebase connection error: {exc.reason}"
        )

    except (TimeoutError, OSError) as exc:
        return False, f"Firebase connection failed: {exc}"

    except (TypeError, ValueError) as exc:
        return False, f"Invalid Firebase request or data: {exc}"

    except Exception as exc:
        return False, f"Unexpected Firebase error: {exc}"


def set_data(path, data):
    """Replace the value at a database path."""
    return _request("PUT", path, data)


def update_data(path, data):
    """Update selected fields at a database path."""
    return _request("PATCH", path, data)


def push_data(path, data):
    """Create a new child using an auto-generated Firebase key."""
    return _request("POST", path, data)


def get_data(path):
    """Read a value from a database path."""
    return _request("GET", path)


def delete_data(path):
    """Delete a value from a database path."""
    return _request("DELETE", path)


def update_location(latitude, longitude, user_id="staff_1"):
    """Save the latest staff GPS position."""
    user_id = str(user_id or "staff_1")

    try:
        payload = {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        return update_data(
            f"staff_locations/{user_id}", payload
        )

    except (TypeError, ValueError) as exc:
        return False, f"Invalid GPS coordinates: {exc}"


def get_location(user_id="staff_1"):
    """Return (latitude, longitude), or (None, None)."""
    user_id = str(user_id or "staff_1")

    ok, result = get_data(
        f"staff_locations/{user_id}"
    )

    if not ok or not isinstance(result, dict):
        return None, None

    try:
        latitude = float(result["latitude"])
        longitude = float(result["longitude"])

        if not (
            -90 <= latitude <= 90
            and -180 <= longitude <= 180
        ):
            return None, None

        return latitude, longitude

    except (KeyError, TypeError, ValueError):
        return None, None
