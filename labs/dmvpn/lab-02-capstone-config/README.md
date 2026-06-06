# Lab 02 — DMVPN Full Configuration Mastery (Capstone I)

**Topic:** DMVPN (single hub)
**Difficulty:** Advanced
**Estimated time:** 120 minutes
**Type:** Capstone I — full configuration from clean slate

## Exam Objectives

- 2.3 Configure and verify DMVPN (single hub)
- 2.3.a Configure and verify GRE/mGRE
- 2.3.b Configure and verify NHRP
- 2.3.c Configure and verify IPsec
- 2.3.d Configure and verify dynamic neighbor
- 2.3.e Configure and verify spoke-to-spoke

## Objective

Build a complete DMVPN Phase 3 + IPsec deployment from a clean slate. IP addressing is pre-configured; every other protocol layer — underlay routing, mGRE, NHRP, OSPF overlay, IKEv1, IPsec — must be configured from scratch.

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
    │  Lo0: 10.1.1.1   │                    │  Lo0: 10.3.3.3   │
    └──────────────────┘                    └──────────────────┘
                        ┌──────────────────┐
                        │       R2  (Sp1)  │
                        │  Tu0: 10.100.0.2 │
                        │  Lo0: 10.2.2.2   │
                        └──────────────────┘
```

## Quick Start

```bash
# Load initial configs (IP addressing only)
python3 setup_lab.py --host <eve-ng-ip>

# After configuring the full DMVPN solution, verify with:
# R1: show ip nhrp | show ip ospf neighbor | show dmvpn
# R2: show crypto isakmp sa | show crypto ipsec sa | traceroute 10.3.3.3 source Loopback0

# To inject and clear fault scenarios:
python3 scripts/fault-injection/inject_scenario_01.py --host <eve-ng-ip>
python3 scripts/fault-injection/apply_solution.py --host <eve-ng-ip>
```

## Files

```
lab-02-capstone-config/
├── workbook.md                          # Lab guide (capstone format)
├── setup_lab.py                         # Load initial configs
├── initial-configs/                     # IP-only starting state
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   └── R4.cfg
├── solutions/                           # Complete Phase 3 + IPsec configs
│   ├── R1.cfg
│   ├── R2.cfg
│   ├── R3.cfg
│   └── R4.cfg
├── topology/
│   ├── topology.drawio
│   └── README.md
└── scripts/
    └── fault-injection/
        ├── inject_scenario_01.py        # NHRP multicast map missing on spokes
        ├── inject_scenario_02.py        # NHRP network-id mismatch on R3
        ├── inject_scenario_03.py        # ISAKMP DH group mismatch on R3
        ├── apply_solution.py            # Restore from solutions/
        └── README.md
```

## Key Parameters

| Parameter | Value |
|-----------|-------|
| NHRP network-id | 100 |
| NHRP auth key | ENARSI |
| Tunnel key | 100 |
| Overlay subnet | 10.100.0.0/24 |
| OSPF process | 100, area 0 |
| OSPF network type | point-to-multipoint |
| IKEv1 policy | AES-256, SHA-256, DH 14, 86400s |
| IPsec PSK | cisco123 (wildcard) |
| Transform-set | esp-aes 256 esp-sha256-hmac, transport mode |
| IPsec profile | DMVPN-PROFILE |

## Prerequisites

- lab-00 and lab-01 are strongly recommended before attempting this capstone
- EVE-NG lab with R1, R2, R3, R4 (IOSv) deployed and powered on
- Python 3.8+ with `eve_ng` library installed
