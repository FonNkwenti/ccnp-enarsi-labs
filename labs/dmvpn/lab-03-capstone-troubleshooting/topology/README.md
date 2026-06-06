# Topology — DMVPN Lab 03: Capstone II

## Diagram

Open `topology.drawio` in draw.io (desktop or web) to view the full topology.

## Network Overview

```
                         ┌─────────────────────┐
                         │         R4           │
                         │   Simulated ISP      │
                         │   Lo0: 4.4.4.4/32    │
                         └──┬────────┬────────┬─┘
                  Gi0/0     │Gi0/1   │Gi0/2   │
           203.0.113.2/30   │  198.51.100.2/30│192.0.2.2/30
                            │        │        │
         203.0.113.1/30     │198.51  │        │192.0.2.1/30
              Gi0/0         │.100.1/30Gi0/0   │Gi0/0
    ┌─────────────────┐     │        │        │┌─────────────────┐
    │      R1         │─────┘        │        └│      R3         │
    │  Hub / NHS      │              │         │  Spoke 2        │
    │  Tu0: 10.100.0.1│              │         │  Tu0: 10.100.0.3│
    │  Lo0: 10.1.1.1  │              │         │  Lo0: 10.3.3.3  │
    └─────────────────┘              │         └─────────────────┘
                          ┌──────────┘
                          │┌────────────────┐
                          ││     R2         │
                          │  Spoke 1        │
                          │  Tu0: 10.100.0.2│
                          │  Lo0: 10.2.2.2  │
                          └─────────────────┘

  Overlay (mGRE): 10.100.0.0/24
  NHRP: network-id 100, auth ENARSI
  OSPF: process 100, area 0, point-to-multipoint
  IPsec: IKEv1 PSK (cisco123), AES-256/SHA-256/DH14, transport mode
```

## Physical Links

| Link | Endpoints | Subnet |
|------|-----------|--------|
| L1 | R1 Gi0/0 ↔ R4 Gi0/0 | 203.0.113.0/30 |
| L2 | R2 Gi0/0 ↔ R4 Gi0/1 | 198.51.100.0/30 |
| L3 | R3 Gi0/0 ↔ R4 Gi0/2 | 192.0.2.0/30 |

## Logical Overlay (mGRE Tunnel)

| Device | Role | Tunnel IP | LAN (Lo0) |
|--------|------|-----------|-----------|
| R1 | Hub / NHS | 10.100.0.1/24 | 10.1.1.1/24 |
| R2 | Spoke 1 | 10.100.0.2/24 | 10.2.2.2/24 |
| R3 | Spoke 2 | 10.100.0.3/24 | 10.3.3.3/24 |
| R4 | ISP only | — | 4.4.4.4/32 |

## Fault Impact Map

```
Fault 1: R2 no default route
  → R2 cannot reach R4 or R1 NBMA
  → All GRE packets from R2 are blackholed
  → No NHRP registration, no OSPF, no IPsec

Fault 2: R1 wrong PSK (badkey123)
  → IKE Phase 1 fails (MM_KEY_EXCH) between R1 and all peers
  → Tunnel protection blocks GRE before NHRP packets reach R1
  → Visible after Fault 1 is fixed

Fault 3: R3 NHRP network-id 200
  → R3 registration packets discarded by R1 (silent)
  → R3 never appears in R1 NHRP table
  → Visible after Fault 2 is fixed

Fault 4: R1 missing ip nhrp redirect
  → Hub forwards spoke-to-spoke traffic but never sends redirects
  → Spokes cannot learn each other's NBMA address
  → Phase 3 shortcuts never form
  → Visible after Fault 3 is fixed
```
