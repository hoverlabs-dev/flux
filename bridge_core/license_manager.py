from __future__ import annotations

import hashlib
import json
import urllib.request
import urllib.parse
import uuid


def get_hardware_id() -> str:
    """Generate a unique SHA-256 system hardware ID based on the network MAC address."""
    mac = str(uuid.getnode())
    return hashlib.sha256(mac.encode("utf-8")).hexdigest()[:16]


def verify_gumroad_license(product_permalink: str, license_key: str) -> dict:
    """Query Gumroad's license validation endpoint.

    Returns a dict with 'success' and 'message' or other details.
    """
    if not license_key:
        return {"success": False, "message": "License key cannot be empty."}

    # Dev bypass check
    if license_key.upper().startswith("FLUX-DEV-"):
        return {"success": True, "message": "Development activation bypass successful."}

    url = "https://api.gumroad.com/v2/licenses/verify"
    params = {
        "product_permalink": product_permalink,
        "product_id": product_permalink,
        "license_key": license_key,
        "increment_uses_count": "true"
    }
    print(f"GUMROAD VERIFY REQUEST: url={url} params={params}")
    data = urllib.parse.urlencode(params).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8.0) as response:
            res_body = response.read().decode("utf-8")
            print(f"GUMROAD VERIFY SUCCESS: body={res_body}")
            res_data = json.loads(res_body)
            if res_data.get("success"):
                return {"success": True, "res": res_data}
            return {"success": False, "message": "Invalid license key or limit exceeded."}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            print(f"GUMROAD VERIFY HTTP ERROR {e.code}: body={err_body}")
            err_data = json.loads(err_body)
            return {"success": False, "message": err_data.get("message", "Validation failed.")}
        except Exception as exc:
            print(f"GUMROAD VERIFY HTTP ERROR PARSE FAIL: {exc}")
            return {"success": False, "message": f"HTTP Error: {e.code}"}
    except Exception as exc:
        print(f"GUMROAD VERIFY ERROR: {exc}")
        return {"success": False, "message": f"Connection error: {exc}"}


def check_license(license_key: str | None, cached_hwid: str | None) -> bool:
    """Validate if the saved license key match coordinates with this machine."""
    if not license_key:
        return False
    if license_key.upper().startswith("FLUX-DEV-"):
        return True
    return cached_hwid == get_hardware_id()
