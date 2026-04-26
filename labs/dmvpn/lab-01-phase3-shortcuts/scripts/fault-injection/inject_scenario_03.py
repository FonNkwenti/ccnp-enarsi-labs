#!/usr/bin/env python3
"""
Fault Injection: Scenario 03 — Missing Tunnel Protection on R3

Target:     R3 (Tunnel0 — IPsec tunnel protection)
Injects:    Removes 'tunnel protection ipsec profile DMVPN-PROFILE' from R3's Tunnel0
Fault Type: IPsec Misconfiguration (Missing Tunnel Protection)

Result:     Spoke-to-spoke shortcuts still form and traffic reaches R3, but GRE packets
            on the R2-to-R3 path are not encrypted. R3 sends unencrypted GRE; the
            compliance requirement for IPsec protection is violated on the direct
            spoke-to-spoke path. 'show crypto ipsec sa peer 192.0.2.1' on R2 shows
            zero encaps/decaps.

Before running, ensure the lab is in the SOLUTION state:
    python3 apply_solution.py --host <eve-ng-ip>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# Depth: scripts/fault-injection -> scripts -> lab-01-phase3-shortcuts -> dmvpn -> labs/
sys.path.insert(0, str(SCRIPT_DIR.parents[3] / "common" / "tools"))
from eve_ng import EveNgError, connect_node, discover_ports, find_open_lab, require_host  # noqa: E402

DEVICE_NAME = "R3"
FAULT_COMMANDS = [
    "interface Tunnel0",
    " no tunnel protection ipsec profile DMVPN-PROFILE",
]

# Pre-flight: check Tunnel0 config on R3 to verify solution state before injecting.
PREFLIGHT_CMD = "show running-config interface Tunnel0"
# This is a removal fault — running-config will NOT contain a "negated" line after
# injection. The sentinel below is a string that will never appear in Cisco show
# output; the PREFLIGHT_SOLUTION_MARKER alone carries the actual idempotency check.
PREFLIGHT_FAULT_MARKER = "__SENTINEL_FAULT_03_INJECTED__"
# If this string is absent → not in solution state, bail out.
PREFLIGHT_SOLUTION_MARKER = "tunnel protection ipsec profile DMVPN-PROFILE"


def preflight(conn) -> bool:
    output = conn.send_command(PREFLIGHT_CMD)
    if PREFLIGHT_SOLUTION_MARKER not in output:
        print(f"[!] Pre-flight failed: '{PREFLIGHT_SOLUTION_MARKER}' not found.")
        print("    Run apply_solution.py first to restore the known-good config.")
        return False
    # PREFLIGHT_FAULT_MARKER is a sentinel — it will never appear; check is a no-op
    # but preserves the structural contract of the preflight pattern.
    if PREFLIGHT_FAULT_MARKER in output:
        print(f"[!] Pre-flight failed: sentinel fault marker unexpectedly present.")
        print("    Scenario 03 appears already injected. Restore with apply_solution.py.")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject Scenario 03 fault")
    parser.add_argument("--host", default="192.168.x.x",
                        help="EVE-NG server IP (required)")
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
