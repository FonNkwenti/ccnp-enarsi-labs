"""
setup_lab.py — DMVPN Lab 03: Capstone II — Comprehensive Troubleshooting

Loads the BROKEN initial configurations onto R1, R2, R3, R4 in the EVE-NG lab.
The configs contain four deliberate faults that the student must find and fix.

Run this script to reset the lab to the broken starting state.
To restore the correct working configuration, run scripts/apply_solution.py.

Usage:
    python3 setup_lab.py --host <eve-ng-ip>
    python3 setup_lab.py --host <eve-ng-ip> --lab-path /api/v1/labs/dmvpn/lab-03-capstone-troubleshooting.unl
"""

import argparse
import sys
from pathlib import Path

from eve_ng import EveNgError, connect_node, discover_ports, find_open_lab, require_host

DEVICES = ["R1", "R2", "R3", "R4"]
CONFIGS_DIR = Path(__file__).parent / "initial-configs"


def load_config(host: str, lab_path: str, ports: dict, device: str) -> bool:
    cfg_file = CONFIGS_DIR / f"{device}.cfg"
    if not cfg_file.exists():
        print(f"[ERROR] Config file not found: {cfg_file}")
        return False
    config_text = cfg_file.read_text()
    try:
        connect_node(host, lab_path, ports[device], config_text)
        print(f"[OK] {device} loaded (broken state)")
        return True
    except EveNgError as exc:
        print(f"[FAIL] {device}: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup DMVPN Lab 03 — Capstone II (broken state)")
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
        print("\nAll devices loaded. Start lab and wait ~60s for IOS to boot.")
        print("DMVPN is broken — find and fix all four faults.")
        print("To restore working config: python3 scripts/apply_solution.py --host <eve-ng-ip>")
        return 0
    else:
        print(f"\n{failed}/{len(DEVICES)} device(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
