#!/usr/bin/env python3
"""
Fault Injection: Scenario 01 — Missing NHRP Multicast Map on R2 and R3

Targets:    R2 and R3 (Tunnel0)
Injects:    Removes 'ip nhrp map multicast 203.0.113.1' from both spokes
Fault Type: NHRP Multicast Misconfiguration

Result:     OSPF hello packets cannot be delivered across the DMVPN tunnel.
            NHRP registration itself still works (unicast to the hub) so the
            tunnels remain up, but OSPF adjacencies fail to form and routing
            tables go stale. Unicast traffic already in the forwarding table
            may continue briefly; new destinations are unreachable.

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

DEVICE_NAMES = ["R2", "R3"]

FAULT_COMMANDS = [
    "interface Tunnel0",
    " no ip nhrp map multicast 203.0.113.1",
]

# Pre-flight: check Tunnel0 on each spoke to verify solution state before injecting.
# This is a removal fault — after injection no negated line appears in running-config.
# The SOLUTION_MARKER absence carries the idempotency check.
PREFLIGHT_CMD = "show running-config | section Tunnel0"
# If this string is absent → not in solution state, bail out.
PREFLIGHT_SOLUTION_MARKER = "map multicast 203.0.113.1"
# Sentinel — will never appear in IOS output; preserves structural contract.
PREFLIGHT_FAULT_MARKER = "__SENTINEL_FAULT_01_INJECTED__"


def preflight(conn, device_name: str) -> bool:
    output = conn.send_command(PREFLIGHT_CMD)
    if PREFLIGHT_SOLUTION_MARKER not in output:
        print(f"[!] Pre-flight failed on {device_name}: '{PREFLIGHT_SOLUTION_MARKER}' not found.")
        print("    Run apply_solution.py first to restore the known-good config.")
        return False
    # Sentinel check — structural no-op but preserved for consistency.
    if PREFLIGHT_FAULT_MARKER in output:
        print(f"[!] Pre-flight failed on {device_name}: sentinel fault marker unexpectedly present.")
        print(f"    Scenario 01 appears already injected. Restore with apply_solution.py.")
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject Scenario 01 fault")
    parser.add_argument("--host", required=True, help="EVE-NG server IP")
    parser.add_argument("--lab-path", default=None,
                        help="Lab .unl path in EVE-NG (auto-discovered if omitted)")
    parser.add_argument("--skip-preflight", action="store_true",
                        help="Skip sanity check — use only if lab state is known-good")
    args = parser.parse_args()

    host = require_host(args.host)

    print("=" * 60)
    print("Fault Injection: Scenario 01")
    print("=" * 60)

    if args.lab_path:
        lab_path = args.lab_path
    else:
        print("[*] Detecting open lab in EVE-NG...")
        lab_path = find_open_lab(host, node_names=DEVICE_NAMES)
        if lab_path is None:
            print(
                f"[!] No running lab found with {DEVICE_NAMES}. Start all nodes first.",
                file=sys.stderr,
            )
            return 3

    try:
        ports = discover_ports(host, lab_path)
    except EveNgError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 3

    for name in DEVICE_NAMES:
        if ports.get(name) is None:
            print(f"[!] {name} not found in lab '{lab_path}'.")
            return 3

    # Open connections for all targets upfront so we can preflight both
    # before making any change — avoids a half-injected state.
    connections: dict[str, object] = {}
    try:
        for name in DEVICE_NAMES:
            port = ports[name]
            print(f"[*] Connecting to {name} on {host}:{port} ...")
            try:
                connections[name] = connect_node(host, port)
            except Exception as exc:
                print(f"[!] Connection to {name} failed: {exc}", file=sys.stderr)
                return 3

        # Phase 1: preflight both devices before touching either.
        if not args.skip_preflight:
            for name in DEVICE_NAMES:
                if not preflight(connections[name], name):
                    return 4

        # Phase 2: inject fault on all targets.
        print("[*] Injecting fault configuration ...")
        for name in DEVICE_NAMES:
            connections[name].send_config_set(FAULT_COMMANDS)
            connections[name].save_config()
    finally:
        for conn in connections.values():
            try:
                conn.disconnect()
            except Exception:
                pass

    print("[+] Fault injected on R2 and R3. Scenario 01 is now active.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
