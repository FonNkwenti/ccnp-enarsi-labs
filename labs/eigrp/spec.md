# EIGRP Routing — Lab Specification

## Exam Reference
- **Exam:** Implementing Cisco Enterprise Advanced Routing and Services (300-410)
- **Blueprint Bullets:**
  - **1.9** Troubleshoot EIGRP (classic and named mode; VRF and global)
  - **1.9.a** Address families (IPv4, IPv6)
  - **1.9.b** Neighbor relationship and authentication
  - **1.9.c** Loop-free path selections (RD, FD, FC, successor, feasible successor, stuck in active)
  - **1.9.d** Stubs
  - **1.9.e** Load balancing (equal and unequal cost)
  - **1.9.f** Metrics

## Topology Summary

Three-router triangle (R1, R2, R3) forms the core present in every lab. One optional router (R4) is introduced in Lab 02 — first as a full neighbor for the DUAL/SIA demonstration, then reconfigured mid-lab as a stub. All devices run `iosv` (IOS 15.9(3)M6) — required for named-mode EIGRP, HMAC-SHA-256 authentication, and the IPv6 address family.

```
            ┌────────┐
            │  R1    │  Lo0 10.1.1.1/32 · 2001:db8:1::1/128
            │ (Hub)  │
            └────┬───┘
          Gi0/0  │  Gi0/1          Gi0/2 (from Lab 02)
      ┌─────────┼─────────┐         │
  L1 10.0.12/30 │ L2 10.0.13/30  L4 10.0.14/30
      │         │                    │
   ┌──▼──┐   ┌──▼──┐               ┌─▼──┐
   │ R2  │   │ R3  │               │ R4 │  Lo0 10.4.4.4/32
   │Gi0/0│   │Gi0/0│               │Gi0/0│
   └──┬──┘   └──┬──┘               └────┘
      │Gi0/1    │Gi0/1
      └─────────┘
       L3 10.0.23/30
```

- **Core devices (all labs):** R1, R2, R3 — full triangle at Gi0/0/Gi0/1
- **Optional device (Lab 02+):** R4 connected to R1 via Gi0/2 ↔ Gi0/0
- **IPv6 dual-stack** enabled from Lab 01 onward on every core link
- **RAM budget:** 4 × 512 MB = 2 GB (negligible on the 64 GB host)

## Lab Progression

| # | Folder | Title | Difficulty | Time | Type | Blueprint Refs | Devices |
|---|---|---|---|---|---|---|---|
| 00 | lab-00-classic-adjacency | EIGRP Fundamentals — Classic Mode | Foundation | 60m | progressive | 1.9, 1.9.b | R1, R2, R3 |
| 01 | lab-01-named-mode-dual-stack | Named Mode and Dual-Stack Address Families | Foundation | 75m | progressive | 1.9, 1.9.a, 1.9.b | R1, R2, R3 |
| 02 | lab-02-dual-and-stubs | DUAL and Stub Operation | Intermediate | 90m | progressive | 1.9.c, 1.9.d | R1, R2, R3, R4 |
| 03 | lab-03-load-balancing-vrf | Load Balancing, Metrics, and VRF-Lite | Advanced | 120m | progressive | 1.9, 1.9.e, 1.9.f | R1, R2, R3, R4 |
| 04 | lab-04-capstone-config | EIGRP Capstone I — Full Configuration | Advanced | 120m | capstone_i | all | R1, R2, R3, R4 |
| 05 | lab-05-capstone-troubleshooting | EIGRP Capstone II — Comprehensive Troubleshooting | Advanced | 120m | capstone_ii | all | R1, R2, R3, R4 |

## Blueprint Coverage Matrix

| Blueprint Bullet | Description | Covered In |
|---|---|---|
| 1.9 | EIGRP classic and named mode; VRF and global | lab-00, lab-01, lab-03, capstones |
| 1.9.a | Address families (IPv4, IPv6) | lab-01, capstones |
| 1.9.b | Neighbor relationship and authentication | lab-00, lab-01, capstones |
| 1.9.c | Loop-free path selections (RD, FD, FC, successor, FS, SIA) | lab-02, capstones |
| 1.9.d | Stubs | lab-02, capstones |
| 1.9.e | Load balancing (equal and unequal cost) | lab-03, capstones |
| 1.9.f | Metrics | lab-03, capstones |

All 7 blueprint refs are covered in at least one non-capstone lab and re-exercised in both capstones.

## Design Decisions

- **6 labs, not 7.** Per topic-plan revision, DUAL+stubs are paired in Lab 02, and load-balancing+metrics+VRF-Lite are combined in Lab 03. Lab 03 is intentionally sized at 120 min to give all three blueprint refs real hands-on time — it is the most demanding non-capstone lab.
- **Classic mode first, named mode at Lab 01.** Named mode is the modern config surface, but exam troubleshooting routinely involves brownfield classic-mode deployments. Lab 00 teaches the classic syntax + MD5 auth; Lab 01 migrates via `eigrp upgrade-cli`, giving students literal experience with the upgrade path and the new HMAC-SHA-256 authentication that only exists under named mode.
- **R4 does double duty in Lab 02.** Introduced first as a full neighbor so R1 can be driven SIA when R1↔R4 is broken (R2/R3 have no alternative path to 10.4.4.4/32). Then reconfigured mid-lab as a stub to demonstrate query-scope reduction and the four stub variants (connected / summary / static / receive-only).
- **VRF-Lite via loopback CEs, not dedicated CE routers.** Customer-A and Customer-B VRFs on R1/R2/R3 advertise per-VRF loopback prefixes under named-mode EIGRP. VRF isolation is proven by per-VRF topology tables — no new physical devices needed.
- **`iosv` platform only, no `iol`.** Per LESSONS_LEARNED.md: named-mode EIGRP and IPv6 AF require IOS 15.0+, and the installed IOL 15.7 image has known gaps on wide-metric (`metric version 64bit`) accounting. IOSv 15.9(3)M6 handles every bullet cleanly. Cost: +256 MB RAM per router, trivial at 4-router scale.
- **Optional device IPs pre-reserved.** R4's loopback (10.4.4.4/32, 2001:db8:4::4/128) and the R1–R4 link subnets (10.0.14.0/30, 2001:db8:0:14::/64) are assigned in `baseline.yaml` from the start, even though R4 is not active until Lab 02 — honoring the "optional devices handled explicitly at introduction" lesson.
