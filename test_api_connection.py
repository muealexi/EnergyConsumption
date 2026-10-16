#!/usr/bin/env python3
"""
Step 2: Verify Wiener Netze Smart Meter API credentials.

Usage (from project root, with .venv activated):
    python test_api_connection.py

Requires a local .env file — see .env.example.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"

REQUIRED_VARS = (
    "WN_CLIENT_ID",
    "WN_CLIENT_SECRET",
    "WN_API_KEY",
    "WN_METER_ID",
)


def load_config() -> dict[str, str]:
    if not ENV_FILE.exists():
        print(f"Missing {ENV_FILE.name}. Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    load_dotenv(ENV_FILE)
    missing = [name for name in REQUIRED_VARS if not os.getenv(name, "").strip()]
    if missing:
        print("Missing or empty variables in .env:")
        for name in missing:
            print(f"  - {name}")
        sys.exit(1)

    return {name: os.environ[name].strip() for name in REQUIRED_VARS}


def print_meter_readings(readings) -> None:
    if readings is None:
        print("  (no readings returned)")
        return
    if isinstance(readings, dict):
        readings = [readings]
    if not readings:
        print("  (empty list)")
        return
    for row in readings[-5:]:
        print(f"  {row}")


def main() -> None:
    config = load_config()
    meter_id = config["WN_METER_ID"]

    print("Loading Wiener Netze API client...")
    try:
        from wiener_netze_smart_meter_api import WNAPIClient
    except ImportError:
        print("Package not installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    client = WNAPIClient(
        client_id=config["WN_CLIENT_ID"],
        client_secret=config["WN_CLIENT_SECRET"],
        api_key=config["WN_API_KEY"],
        max_retries=3,
        retry_delay=5,
        timeout=30,
    )

    print("\n1) Anlagendaten (all meters on your account)")
    try:
        all_meters = client.get_anlagendaten()
        if isinstance(all_meters, list):
            print(f"   Found {len(all_meters)} meter(s)")
            for m in all_meters:
                print(f"   - {m}")
        else:
            print(f"   {all_meters}")
    except Exception as exc:
        print(f"   FAILED: {exc}")
        sys.exit(1)

    print(f"\n2) Anlagendaten for configured meter: {meter_id}")
    try:
        meter = client.get_anlagendaten(meter_id)
        print(f"   {meter}")
    except Exception as exc:
        print(f"   FAILED: {exc}")
        print("   Check WN_METER_ID in .env matches a meter from step 1.")
        sys.exit(1)

    end = datetime.now().date()
    start = end - timedelta(days=7)
    start_s, end_s = start.isoformat(), end.isoformat()

    print(f"\n3) Zählerstände (meter readings) {start_s} → {end_s}")
    try:
        readings = client.get_meter_readings(meter_id, start_s, end_s)
        print_meter_readings(readings)
        if isinstance(readings, list) and readings:
            print(f"   Latest of {len(readings)} reading(s) shown above (max 5).")
    except Exception as exc:
        print(f"   FAILED: {exc}")
        sys.exit(1)

    print("\nAPI connection OK.")


if __name__ == "__main__":
    main()
