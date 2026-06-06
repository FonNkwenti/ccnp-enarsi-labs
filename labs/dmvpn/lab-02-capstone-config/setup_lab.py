"""
setup_lab.py — DMVPN Lab 02: Capstone I — Full Configuration Mastery

Loads initial configurations (IP addressing only — clean slate) onto R1, R2, R3, R4
in the EVE-NG lab. Discovers the open lab automatically via find_open_lab.

Usage:
    python3 setup_lab.py --host <eve-ng-ip>
    python3 setup_lab.py --host <eve-ng-ip> --lab-path /api/v1/labs/dmvpn/lab-02-capstone-config.unl
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
        print(f"[OK] {device} configured")
        return True
    except EveNgError as exc:
        print(f"[FAIL] {device}: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup DMVPN Lab 02 — Capstone I")
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
        print("\nAll devices configured. Start lab and wait ~60s for IOS to boot.")
        print("IP addressing is pre-loaded; all DMVPN/IPsec config is yours to build.")
        return 0
    else:
        print(f"\n{failed}/{len(DEVICES)} device(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
