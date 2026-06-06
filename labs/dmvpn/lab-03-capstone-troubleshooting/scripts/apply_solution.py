"""
apply_solution.py — DMVPN Lab 03: Capstone II

Loads the correct working solution configurations onto all devices.
Run this after completing the troubleshooting exercise to verify the expected
final state, or to restore the lab for a second attempt.

Usage:
    python3 scripts/apply_solution.py --host <eve-ng-ip>
"""

import argparse
import sys
from pathlib import Path

from eve_ng import EveNgError, connect_node, discover_ports, find_open_lab, require_host

DEVICES = ["R1", "R2", "R3", "R4"]
CONFIGS_DIR = Path(__file__).resolve().parent.parent / "solutions"


def load_config(host: str, lab_path: str, ports: dict, device: str) -> bool:
    cfg_file = CONFIGS_DIR / f"{device}.cfg"
    if not cfg_file.exists():
        print(f"[ERROR] Solution file not found: {cfg_file}")
        return False
    config_text = cfg_file.read_text()
    try:
        connect_node(host, lab_path, ports[device], config_text)
        print(f"[OK] {device} restored to solution state")
        return True
    except EveNgError as exc:
        print(f"[FAIL] {device}: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore DMVPN Lab 03 to working solution state")
    parser.add_argument("--host", required=True, help="EVE-NG server IP or hostname")
    parser.add_argument("--lab-path", help="EVE-NG lab path (auto-discovered if omitted)")
    args = parser.parse_args()

    host = require_host(args.host)

    if args.lab_path:
        lab_path = args.lab_path
    else:
        lab_path = find_open_lab(host, node_names=DEVICES)

    print(f"Lab path: {lab_path}")

    try:
        ports = discover_ports(host, lab_path)
    except EveNgError as exc:
        print(f"[ERROR] Cannot discover ports: {exc}")
        return 3

    results = [load_config(host, lab_path, ports, d) for d in DEVICES]
    failed = results.count(False)

    if failed == 0:
        print("\nAll devices restored to working solution state.")
        print("Wait ~30s for OSPF/NHRP to reconverge before verifying.")
        return 0
    else:
        print(f"\n{failed}/{len(DEVICES)} device(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
