#!/usr/bin/env python3
"""
Fault Injection: Scenario 03 — ISAKMP DH Group Mismatch on R3

Target:     R3 (ISAKMP policy 10)
Injects:    Changes R3's ISAKMP policy 10 DH group from 14 to 5
Fault Type: IKE Phase 1 Policy Mismatch (spoke-to-spoke only)

Result:     Spoke-to-spoke IKE Phase 1 fails. When R2 attempts to build a
            direct IPsec tunnel to R3 (Phase 3 shortcut), the IKE negotiation
            fails because R2 proposes DH group 14 and R3 only accepts group 5.
            Hub-to-spoke sessions between R1 and R3 are unaffected because R1's
            policy also includes group 14 and IOS selects the first match.
            Traceroute from R2 to R3's loopback shows traffic falling back
            through R1 indefinitely.

Before running, ensure the lab is in the SOLUTION state:
    python3 apply_solution.py --host <eve-ng-ip>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# Depth: scripts/fault-injection -> scripts -> lab-02-capstone-config -> dmvpn -> labs/
sys.path.insert(0, str(SCRIPT_DIR.parents[3] / "common" / "tools"))
from eve_ng import EveNgError, connect_node, discover_ports, find_open_lab, require_host  # noqa: E402

DEVICE_NAME = "R3"
FAULT_COMMANDS = [
    "crypto isakmp policy 10",
    " group 5",
]

# Pre-flight: check ISAKMP policy on R3 to verify solution state before injecting.
PREFLIGHT_CMD = "show running-config | section crypto isakmp policy"
# If this string is absent → not in solution state, bail out.
PREFLIGHT_SOLUTION_MARKER = "group 14"
# If this string is already present → fault already injected, bail out.
PREFLIGHT_FAULT_MARKER = "group 5"


def preflight(conn) -> bool:
    output = conn.send_command(PREFLIGHT_CMD)
    if PREFLIGHT_SOLUTION_MARKER not in output:
        print(f"[!] Pre-flight failed: '{PREFLIGHT_SOLUTION_MARKER}' not found.")
        print("    Run apply_solution.py first to restore the known-good config.")
        return False
    if PREFLIGHT_FAULT_MARKER in output:
        print(f"[!] Pre-flight failed: '{PREFLIGHT_FAULT_MARKER}' already present.")
        print("    Scenario 03 appears already injected. Restore with apply_solution.py.")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject Scenario 03 fault")
    parser.add_argument("--host", required=True, help="EVE-NG server IP")
    parser.add_argument("--lab-path", default=None,
                        help="Lab .unl path in EVE-NG (auto-discovered if omitted)")
    parser.add_argument("--skip-preflight", action="store_true",
                        help="Skip sanity check — use only if lab state is known-good")
    args = parser.parse_args()

    host = require_host(args.host)

    print("=" * 60)
    print("Fault Injection: Scenario 03")
    print("=" * 60)

    if args.lab_path:
        lab_path = args.lab_path
    else:
        print("[*] Detecting open lab in EVE-NG...")
        lab_path = find_open_lab(host, node_names=[DEVICE_NAME])
        if lab_path is None:
            print(f"[!] No running lab found with {DEVICE_NAME}. Start all nodes first.", file=sys.stderr)
            return 3

    try:
        ports = discover_ports(host, lab_path)
    except EveNgError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 3

    port = ports.get(DEVICE_NAME)
    if port is None:
        print(f"[!] {DEVICE_NAME} not found in lab '{lab_path}'.")
        return 3

    print(f"[*] Connecting to {DEVICE_NAME} on {host}:{port} ...")
    try:
        conn = connect_node(host, port)
    except Exception as exc:
        print(f"[!] Connection failed: {exc}", file=sys.stderr)
        return 3

    try:
        if not args.skip_preflight and not preflight(conn):
            return 4
        print("[*] Injecting fault configuration ...")
        conn.send_config_set(FAULT_COMMANDS)
        conn.save_config()
    finally:
        conn.disconnect()

    print(f"[+] Fault injected on {DEVICE_NAME}. Scenario 03 is now active.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
