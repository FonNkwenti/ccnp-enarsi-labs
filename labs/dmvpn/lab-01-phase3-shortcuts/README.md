# DMVPN Lab 01 — Phase 3: Spoke-to-Spoke Shortcuts with IPsec Protection

Progressive extension of lab-00. Adds Phase 3 NHRP shortcuts and IKEv1/IPsec encryption — without changing any existing tunnel mode or NHRP registration config.

## Blueprint Coverage

- 2.3 — Configure and verify DMVPN (single hub)
- 2.3.a — GRE/mGRE (unchanged from lab-00)
- 2.3.b — NHRP (Phase 3: redirect + shortcut)
- 2.3.c — IPsec (IKEv1 PSK, AES-256/SHA-256/DH14, transport mode)
- 2.3.e — Spoke-to-spoke (NHRP-resolved direct tunnels)

## Prerequisites

- lab-00 solution configs loaded (or use `setup_lab.py` which pushes lab-00 solutions as initial state)
- Python 3.8+ with `netmiko` installed

## Quick Start

```bash
# 1. Import the topology into EVE-NG (same topology as lab-00)

# 2. Push initial configs (lab-00 solutions — Phase 1 working state)
python3 setup_lab.py --host <eve-ng-ip>

# 3. Open the workbook and follow the tasks
workbook.md
```

## Files

```
lab-01-phase3-shortcuts/
├── workbook.md                     # Student workbook (11 sections)
├── setup_lab.py                    # Pushes lab-00 solutions as initial state
├── README.md                       # This file
├── initial-configs/                # lab-00 solutions (Phase 1 working state)
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   └── R4.cfg
├── solutions/                      # Full Phase 3 + IPsec solution configs
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   └── R4.cfg
├── topology/
│   ├── topology.drawio             # EVE-NG topology diagram (same as lab-00)
│   └── README.md                   # EVE-NG import/export instructions
└── scripts/fault-injection/
    ├── inject_scenario_01.py       # Ticket 1: ISAKMP DH group mismatch on R2
    ├── inject_scenario_02.py       # Ticket 2: ip nhrp redirect removed from R1
    ├── inject_scenario_03.py       # Ticket 3: tunnel protection removed from R3
    ├── apply_solution.py           # Restore to known-good state
    └── README.md                   # Fault injection instructions
```
