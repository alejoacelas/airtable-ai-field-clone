#!/usr/bin/env python3
"""
Simple checker for Google Sheets integration via SheetsManager.

This script performs two checks:
1) Verify .streamlit/secrets.toml contains the required credentials
2) Attempt to initialize and exercise core SheetsManager methods

Note: The connection step typically requires a Streamlit runtime. If you see
      a runtime-related error, run this script with Streamlit:
      streamlit run scripts/check_sheets_manager.py
"""

from __future__ import annotations

import os
import sys
import traceback
from typing import Any, Dict, List

SECRETS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml"))


def load_toml(path: str) -> Dict[str, Any]:
    try:
        import tomllib  # Python 3.11+
        with open(path, "rb") as f:
            return tomllib.load(f)
    except ModuleNotFoundError:
        try:
            import toml  # type: ignore
            with open(path, "r", encoding="utf-8") as f:
                return toml.load(f)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Failed to parse TOML at {path}: {e}") from e


def validate_gsheets_secrets(secrets: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    connections = secrets.get("connections") or {}
    gsheets = connections.get("gsheets") or {}

    if not gsheets:
        errors.append("[connections.gsheets] section is missing in secrets.toml")
        return errors

    spreadsheet = gsheets.get("spreadsheet")
    if not isinstance(spreadsheet, str) or not spreadsheet.strip():
        errors.append("connections.gsheets.spreadsheet is missing or empty")

    acct_type = gsheets.get("type")
    if acct_type != "service_account":
        errors.append("connections.gsheets.type should be 'service_account'")

    # Minimal required service account fields
    required_fields = [
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "token_uri",
    ]
    for field in required_fields:
        if not gsheets.get(field):
            errors.append(f"connections.gsheets.{field} is missing")

    return errors


def validate_openai_secrets(secrets: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    openai_sec = secrets.get("openai") or {}
    if not openai_sec.get("api_key"):
        errors.append("[openai].api_key is missing (only needed if you run AI calls)")
    return errors


def print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> int:
    print_header("1) Checking secrets file presence")
    print(f"Looking for secrets at: {SECRETS_PATH}")
    if not os.path.exists(SECRETS_PATH):
        print("ERROR: secrets.toml not found.")
        return 1
    print("Found secrets.toml")

    print_header("2) Validating secrets structure")
    try:
        secrets = load_toml(SECRETS_PATH)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: Failed to read secrets: {e}")
        return 1

    gsheets_errors = validate_gsheets_secrets(secrets)
    if gsheets_errors:
        print("Google Sheets secrets issues:")
        for err in gsheets_errors:
            print(f" - {err}")
    else:
        print("Google Sheets secrets look OK.")

    openai_errors = validate_openai_secrets(secrets)
    if openai_errors:
        print("OpenAI secrets notes:")
        for err in openai_errors:
            print(f" - {err}")
    else:
        print("OpenAI secrets present.")

    # Warn about sheets_manager expectation vs secrets location
    print_header("3) Cross-checking sheets_manager expectations")
    try:
        from sheets_manager import SheetsManager  # type: ignore

        # Inspect initialize_connection code path expectations
        # It uses st.connection("gsheets", type=GSheetsConnection) and checks st.secrets["gsheets"].
        # Our secrets are under [connections.gsheets]. This is OK for st.connection,
        # but the explicit st.secrets["gsheets"] check may not find the spreadsheet key.
        print(
            "Note: secrets are under [connections.gsheets]. st.connection will work, \n"
            "but direct access via st.secrets['gsheets'] inside SheetsManager may not."
        )
    except Exception:
        print("WARNING: Could not import SheetsManager for inspection.")

    print_header("4) Attempting live connection and operations")
    try:
        import streamlit as st  # type: ignore
        from sheets_manager import SheetsManager  # type: ignore

        mgr = SheetsManager()
        ok = mgr.initialize_connection()
        print(f"initialize_connection(): {ok}")
        if not ok:
            print(
                "If you see runtime errors here, run this script via Streamlit so the runtime is initialized:\n"
                "  streamlit run scripts/check_sheets_manager.py\n"
            )
            return 1

        # Validate structure (create worksheets if missing)
        structure_ok = mgr.validate_sheet_structure()
        print(f"validate_sheet_structure(): {structure_ok}")

        # Load and save prompt config
        prompt_cfg = mgr.load_prompt_config()
        print(f"load_prompt_config(): rows={len(prompt_cfg)}")
        saved_cfg = mgr.save_prompt_config(prompt_cfg)
        print(f"save_prompt_config(): {saved_cfg}")

        # Load and save main data
        main_df = mgr.load_main_data()
        print(f"load_main_data(): rows={len(main_df)}")
        saved_main = mgr.save_main_data(main_df)
        print(f"save_main_data(): {saved_main}")

        # Connection status
        status = mgr.get_connection_status()
        print("get_connection_status():")
        for k, v in status.items():
            print(f"  - {k}: {v}")

        print("\nAll checks completed.")
        return 0

    except Exception as e:  # noqa: BLE001
        print("Encountered an error during live checks:")
        print(str(e))
        traceback.print_exc()
        print(
            "\nIf this appears to be a Streamlit runtime error, run:\n"
            "  streamlit run scripts/check_sheets_manager.py\n"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())


