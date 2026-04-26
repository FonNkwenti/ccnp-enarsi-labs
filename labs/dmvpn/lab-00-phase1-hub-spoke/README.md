# DMVPN Lab 00 — Phase 1: Hub-and-Spoke with mGRE and NHRP

Foundation lab. Build a single-hub DMVPN overlay using mGRE tunnels, NHRP dynamic registration, and OSPF as the overlay IGP.

## Blueprint Coverage

- 2.3 — Configure and verify DMVPN (single hub)
- 2.3.a — GRE/mGRE
- 2.3.b — NHRP (registration, NHS/NHC, dynamic spoke mapping)
- 2.3.d — Dynamic neighbor (spokes register without hub reconfiguration)

## Prerequisites

- EVE-NG lab imported and all nodes started
- Python 3.8+ with `netmiko` installed (`pip install netmiko`)
- No prior DMVPN lab required (first lab in the series)

## Quick Start

```bash
# 1. Import the topology into EVE-NG (see topology/README.md)

# 2. Push initial configs to all nodes
python3 setup_lab.py --host <eve-ng-ip>

# 3. Open the workbook and follow the tasks
workbook.md
```

## Files

```
lab-00-phase1-hub-spoke/
├── workbook.md                     # Student workbook (11 sections)
├── setup_lab.py                    # Pushes initial configs to EVE-NG nodes
├── README.md                       # This file
├── initial-configs/                # Pre-loaded IP addressing (no tunnels/routing)
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   └── R4.cfg
├── solutions/                      # Full verified solution configs
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   └── R4.cfg
├── topology/
│   ├── topology.drawio             # EVE-NG topology diagram
│   └── README.md                   # EVE-NG import/export instructions
└── scripts/fault-injection/
    ├── inject_scenario_01.py       # Ticket 1: missing underlay default route
    ├── inject_scenario_02.py       # Ticket 2: NHRP network-id mismatch
    ├── inject_scenario_03.py       # Ticket 3: OSPF passive-interface on hub tunnel
    ├── apply_solution.py           # Restore to known-good state
    └── README.md                   # Fault injection instructions
```
