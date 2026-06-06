# Topology — DMVPN Lab 02: Capstone I

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

## Phase 3 Behavior

```
R2 ──── (NHRP shortcut resolves) ────► R3
         ↑ bypasses hub after first packet
         IKE negotiates spoke-to-spoke SA (R2 NBMA: 198.51.100.1 ↔ R3 NBMA: 192.0.2.1)
```

## Key Relationships

- R4 provides underlay transit only — it is not a DMVPN member and has no tunnel/NHRP/IPsec config
- All three members (R1, R2, R3) use `tunnel mode gre multipoint` — this does not change between Phase 1 and Phase 3
- Phase 3 is activated by two NHRP additions only: `ip nhrp redirect` on the hub, `ip nhrp shortcut` on spokes
- OSPF hellos travel as multicast over the tunnel; the hub's `ip nhrp map multicast dynamic` distributes them to registered spokes; spoke `ip nhrp map multicast 203.0.113.1` ensures hellos reach the hub
