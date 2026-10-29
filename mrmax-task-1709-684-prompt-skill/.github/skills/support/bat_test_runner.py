#!/usr/bin/env python3
"""
BAT Test Runner — Executes BAT test cases via HTTP and records pass/fail results.

Usage:
    python3 bat_test_runner.py <json_input> <json_output> [--base-url URL] [--cookie COOKIE]

Reads BAT test case JSON (same format as bat_excel_generator.py input),
parses each test_items field for route/method/expected behavior,
executes HTTP requests, and writes results back into the JSON.

Exit codes:
    0 — All tests passed (OK)
    1 — Some tests failed (NG)
    2 — Input/configuration error

New field added to each test case in output JSON:
    "result_dev1": "OK" | "NG" | "NE"
    "result_comment": "Auto-test: <detail>"
"""

import json
import re
import sys
import os
import urllib.request
import urllib.error
import ssl
import argparse
from urllib.parse import urljoin


# ── Constants ────────────────────────────────────────────────────────────────

RESULT_OK = "OK"
RESULT_NG = "NG"
RESULT_NE = "NE"  # Not Executed — could not parse or could not reach

TIMEOUT_SECONDS = 10

# Pattern to extract route, method, and expected behavior from test_items
# Example: "Verify stock check at /mypage/purchase/reorder (POST) — should reject out-of-stock items"
ITEM_PATTERN = re.compile(
    r"(?:Verify|Check|Ensure|Confirm|Test)\s+.+?\s+at\s+"  # "Verify ... at "
    r"(/\S+)"                                                # capture route
    r"\s*\((\w+)\)"                                          # capture (METHOD)
    r"\s*[—–-]\s*should\s+"                                  # " — should "
    r"(.+)",                                                 # capture expected behavior
    re.IGNORECASE,
)

# Patterns to infer expected HTTP status from the "should ..." clause
EXPECT_REDIRECT_LOGIN = re.compile(
    r"redirect\s+to\s+login|redirect.*login", re.IGNORECASE
)
EXPECT_REDIRECT = re.compile(
    r"redirect|302", re.IGNORECASE
)
EXPECT_ERROR_4XX = re.compile(
    r"reject|error|validation\s+error|fail|403|404|400|4\d\d|denied|forbidden",
    re.IGNORECASE,
)
EXPECT_SUCCESS = re.compile(
    r"display|show|return\s+success|render|load|appear|list|200|success|add|create|update|save|process",
    re.IGNORECASE,
)


def parse_test_item(test_items_text):
    """
    Parse a BAT test_items string to extract route, HTTP method, and expected behavior.

    Returns:
        dict with keys: route, method, expected_text, expected_status_range
        or None if the pattern doesn't match.
    """
    match = ITEM_PATTERN.search(test_items_text)
    if not match:
        return None

    route = match.group(1).strip()
    method = match.group(2).strip().upper()
    expected_text = match.group(3).strip()

    # Infer expected HTTP status range from the "should ..." text
    if EXPECT_REDIRECT_LOGIN.search(expected_text):
        expected_status_range = (300, 399)
        expected_detail = "redirect_to_login"
    elif EXPECT_REDIRECT.search(expected_text):
        expected_status_range = (300, 399)
        expected_detail = "redirect"
    elif EXPECT_ERROR_4XX.search(expected_text):
        expected_status_range = (400, 499)
        expected_detail = "client_error"
    else:
        expected_status_range = (200, 299)
        expected_detail = "success"

    return {
        "route": route,
        "method": method,
        "expected_text": expected_text,
        "expected_status_range": expected_status_range,
        "expected_detail": expected_detail,
    }


def execute_request(base_url, route, method, cookie=None):
    """
    Execute an HTTP request and return (status_code, redirect_location, error_msg).

    Returns:
        tuple: (status_code: int | None, location: str | None, error: str | None)
    """
    url = urljoin(base_url.rstrip("/") + "/", route.lstrip("/"))

    # Build request
    headers = {
        "User-Agent": "BAT-Test-Runner/1.0",
        "Accept": "text/html,application/json",
    }
    if cookie:
        headers["Cookie"] = cookie

    data = None
    if method == "POST":
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = b""  # Empty POST body for smoke test

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    # Create SSL context that doesn't verify (for local dev servers)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        # Use a custom opener that doesn't follow redirects
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(
            NoRedirectHandler,
            urllib.request.HTTPSHandler(context=ctx),
        )
        response = opener.open(req, timeout=TIMEOUT_SECONDS)
        return (response.getcode(), response.headers.get("Location"), None)

    except urllib.error.HTTPError as e:
        return (e.code, e.headers.get("Location"), None)

    except urllib.error.URLError as e:
        return (None, None, f"Connection error: {e.reason}")

    except Exception as e:
        return (None, None, f"Unexpected error: {str(e)}")


def evaluate_result(status_code, location, error, parsed):
    """
    Compare HTTP response against expected behavior.

    Returns:
        tuple: (result: "OK"|"NG"|"NE", comment: str)
    """
    if error:
        return (RESULT_NE, f"Auto-test: {error}")

    if status_code is None:
        return (RESULT_NE, "Auto-test: No response received")

    low, high = parsed["expected_status_range"]

    # Special case: redirect to login
    if parsed["expected_detail"] == "redirect_to_login":
        if 300 <= status_code <= 399:
            if location and "login" in location.lower():
                return (RESULT_OK, f"Auto-test: {status_code} → {location}")
            # Redirect but not to login — still partial pass
            return (RESULT_NG, f"Auto-test: {status_code} → {location} (expected login redirect)")
        # Not a redirect at all
        return (RESULT_NG, f"Auto-test: HTTP {status_code} (expected 3xx redirect to login)")

    # General status range check
    if low <= status_code <= high:
        return (RESULT_OK, f"Auto-test: HTTP {status_code}")

    # Mismatch
    expected_label = f"{low}-{high}"
    return (RESULT_NG, f"Auto-test: HTTP {status_code} (expected {expected_label})")


def check_server(base_url):
    """Check if the dev server is reachable. Returns (reachable: bool, error: str|None)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(base_url, method="HEAD")
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        opener.open(req, timeout=5)
        return (True, None)
    except urllib.error.HTTPError:
        # Server responded (even with an error) — it's reachable
        return (True, None)
    except Exception as e:
        return (False, str(e))


def run_tests(data, base_url, cookie=None):
    """
    Execute all test cases and add result_dev1 + result_comment to each.

    Returns:
        dict: summary with counts {ok, ng, ne, total}
    """
    summary = {"ok": 0, "ng": 0, "ne": 0, "total": 0, "skipped_parse": 0}
    test_cases = data.get("test_cases", [])

    for tc in test_cases:
        summary["total"] += 1
        test_items = tc.get("test_items", "")

        parsed = parse_test_item(test_items)
        if not parsed:
            tc["result_dev1"] = RESULT_NE
            tc["result_comment"] = "Auto-test: Could not parse route/method from test item"
            summary["ne"] += 1
            summary["skipped_parse"] += 1
            continue

        status_code, location, error = execute_request(
            base_url, parsed["route"], parsed["method"], cookie
        )
        result, comment = evaluate_result(status_code, location, error, parsed)

        tc["result_dev1"] = result
        tc["result_comment"] = comment

        if result == RESULT_OK:
            summary["ok"] += 1
        elif result == RESULT_NG:
            summary["ng"] += 1
        else:
            summary["ne"] += 1

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="BAT Test Runner — execute BAT test cases via HTTP"
    )
    parser.add_argument("json_input", help="Path to BAT test case JSON file")
    parser.add_argument("json_output", help="Path to write results JSON file")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8080",
        help="Base URL of the dev server (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--cookie",
        default=None,
        help="Session cookie string for authenticated routes (e.g., 'PHPSESSID=abc123')",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if server is reachable, don't run tests",
    )

    args = parser.parse_args()

    # Check server reachability
    reachable, err = check_server(args.base_url)
    if not reachable:
        print(f"ERROR: Server not reachable at {args.base_url}: {err}", file=sys.stderr)
        sys.exit(2)

    if args.check_only:
        print(f"Server reachable at {args.base_url}")
        sys.exit(0)

    # Load input JSON
    with open(args.json_input, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Running {len(data.get('test_cases', []))} test cases against {args.base_url}...")

    # Execute tests
    summary = run_tests(data, args.base_url, args.cookie)

    # Write output JSON (same structure with result_dev1 + result_comment added)
    os.makedirs(os.path.dirname(args.json_output) or ".", exist_ok=True)
    with open(args.json_output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n{'='*50}")
    print(f"BAT Test Results: {summary['total']} total")
    print(f"  OK: {summary['ok']}  |  NG: {summary['ng']}  |  NE: {summary['ne']}")
    if summary["skipped_parse"] > 0:
        print(f"  ({summary['skipped_parse']} items could not be parsed for auto-test)")
    print(f"{'='*50}")
    print(f"Results written to: {args.json_output}")

    # Exit code: 0 if all OK/NE, 1 if any NG
    sys.exit(1 if summary["ng"] > 0 else 0)


if __name__ == "__main__":
    main()
