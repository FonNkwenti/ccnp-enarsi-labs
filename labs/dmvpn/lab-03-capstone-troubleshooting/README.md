# Lab 03 — DMVPN Comprehensive Troubleshooting (Capstone II)

**Topic:** DMVPN (single hub)
**Difficulty:** Advanced
**Estimated time:** 120 minutes
**Type:** Capstone II — full-stack troubleshooting

## Exam Objectives

- 2.3 Configure and verify DMVPN (single hub)
- 2.3.a Configure and verify GRE/mGRE
- 2.3.b Configure and verify NHRP
- 2.3.c Configure and verify IPsec
- 2.3.d Configure and verify dynamic neighbor
- 2.3.e Configure and verify spoke-to-spoke

## Objective

Diagnose and repair a broken DMVPN Phase 3 + IPsec deployment. The lab loads a nearly-complete configuration with four deliberate faults embedded across the devices. Each fault is at a different protocol layer — the student must troubleshoot systematically from the bottom up to find all four.

## Topology

```
                    ┌──────────────────────────────┐
                    │             R4               │
                    │      Simulated ISP/Transit   │
                    └────────┬────────┬────────────┘
             Gi0/0           │        │           Gi0/2
      203.0.113.2/30         │Gi0/1   │       192.0.2.2/30
                    198.51.100.2/30   │
                             │        │
    ┌──────────────────┐     │        │     ┌──────────────────┐
    │       R1  (Hub)  │─────┘        └─────│       R3  (Sp2)  │
    │  Tu0: 10.100.0.1 │                    │  Tu0: 10.100.0.3 │
    └──────────────────┘                    └──────────────────┘
                        ┌──────────────────┐
                        │       R2  (Sp1)  │
                        │  Tu0: 10.100.0.2 │
                        └──────────────────┘
```

## Quick Start

```bash
# Load broken initial configs
python3 setup_lab.py --host <eve-ng-ip>

# After fixing all faults — load working solutions to verify
python3 scripts/apply_solution.py --host <eve-ng-ip>
```

## Files

```
lab-03-capstone-troubleshooting/
├── workbook.md                          # Lab guide (capstone II format)
├── setup_lab.py                         # Load broken initial configs
├── initial-configs/                     # Broken deployment (4 faults)
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   └── R4.cfg
├── solutions/                           # Correct working configs
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   └── R4.cfg
├── topology/
│   ├── topology.drawio
│   └── README.md
├── scripts/
│   └── apply_solution.py                # Load correct solutions
└── README.md
```

## Fault Locations (instructor reference)

| Fault | Device | Layer | Description |
|-------|--------|-------|-------------|
| 1 | R2 | Underlay | Default route missing |
| 2 | R1 | IPsec/IKEv1 | Wrong pre-shared key (`badkey123`) |
| 3 | R3 | NHRP | network-id `200` instead of `100` |
| 4 | R1 | Phase 3 | `ip nhrp redirect` missing from Tunnel0 |

## Prerequisites

- lab-00, lab-01, lab-02 are strongly recommended before attempting this capstone
- EVE-NG lab with R1, R2, R3, R4 (IOSv) deployed and powered on
- Python 3.8+ with `eve_ng` library installed
