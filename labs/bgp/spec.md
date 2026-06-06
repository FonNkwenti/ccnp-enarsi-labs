# BGP Routing (iBGP and eBGP) — Lab Specification

## Exam Reference
- **Exam:** Implementing Cisco Enterprise Advanced Routing and Services (300-410)
- **Blueprint Bullets:**
  - **1.11** Troubleshoot BGP (Internal and External; unicast and VRF-lite)
  - **1.11.a** Address families (IPv4, IPv6)
  - **1.11.b** Neighbor relationship and authentication (next-hop, multihop, 4-byte AS, private AS, route refresh, synchronization, operation, peer group, states and timers)
  - **1.11.c** Path preference (attributes and best-path)
  - **1.11.d** Route reflector (excluding multiple route reflectors, confederations, dynamic peer)
  - **1.11.e** Policies (inbound/outbound filtering, path manipulation)

## Topology Summary

Three-router iBGP domain (AS 65001: R1, R2, R3) in a linear chain forms the core. R4 (AS 65002) connects to R1 via eBGP from Lab 00 as the sole external neighbor. R5 (AS 64512 — private) is introduced in Lab 02 via eBGP to R3, creating dual-homed connectivity that enables meaningful path-preference demonstrations. R2 is promoted to the single route reflector for AS 65001 in Lab 03. All devices run `iosv` 15.9(3)M6.

```
                      AS 65001
┌──────────────────────────────────────────────────────┐
│                                                      │
│  ┌────┐    L1: 10.0.12.0/30    ┌────┐              │
│  │ R1 ├────────────────────────┤ R2 │              │
│  └────┘                        └──┬─┘              │
│  Lo0: 10.1.1.1                    │ L2: 10.0.23.0/30│
│  Gi0/0 · Gi0/1                    │                 │
│                                ┌──▼──┐              │
│                                │ R3  │              │
│                                └─────┘              │
│                            Lo0: 10.3.3.3            │
│                            Gi0/0 · Gi0/1            │
└──────────────┬──────────────────────────┬───────────┘
               │ L3: 10.0.14.0/30         │ L4: 10.0.35.0/30
               │ (eBGP)                   │ (eBGP, optional Lab 02+)
      ┌────────▼──────────┐      ┌────────▼──────────────┐
      │    AS 65002        │      │    AS 64512 (private)  │
      │    ┌────┐          │      │    ┌────┐              │
      │    │ R4 │          │      │    │ R5 │              │
      │    └────┘          │      │    └────┘              │
      │  Lo0: 10.4.4.4/32  │      │  Lo0: 10.5.5.5/32     │
      └───────────────────┘      └───────────────────────┘
      L3: R1:Gi0/1 ↔ R4:Gi0/0   L4: R3:Gi0/1 ↔ R5:Gi0/0
```

- **Core devices (all labs):** R1 (AS 65001, iBGP + eBGP to R4), R2 (AS 65001, iBGP; RR from Lab 03), R3 (AS 65001, iBGP; eBGP to R5 from Lab 02), R4 (AS 65002, eBGP)
- **Optional device (Lab 02+):** R5 (AS 64512, private AS, eBGP to R3)
- **IPv6 dual-stack** added in Lab 01; eBGP IPv6 AF in Lab 02+
- **RAM budget:** 4 × 512 MB = 2.0 GB (Labs 00–01); 5 × 512 MB = 2.5 GB (Labs 02+)

## Lab Progression

| # | Folder | Title | Difficulty | Time | Type | Blueprint Refs | Devices |
|---|---|---|---|---|---|---|---|
| 00 | lab-00-ebgp-ibgp-foundation | eBGP and iBGP Fundamentals | Foundation | 60m | progressive | 1.11, 1.11.b | R1, R2, R3, R4 |
| 01 | lab-01-neighbor-features-dual-stack | BGP Neighbor Features and Dual-Stack | Foundation | 75m | progressive | 1.11, 1.11.a, 1.11.b | R1, R2, R3, R4 |
| 02 | lab-02-path-preference | BGP Path Preference and Best-Path | Intermediate | 90m | progressive | 1.11.c | R1, R2, R3, R4, R5 |
| 03 | lab-03-rr-policies-vrf | Route Reflectors, Policies, and VRF-Lite | Advanced | 120m | progressive | 1.11.d, 1.11.e, 1.11 | R1, R2, R3, R4, R5 |
| 04 | lab-04-capstone-config | BGP Capstone I — Full Configuration | Advanced | 120m | capstone_i | all | R1, R2, R3, R4, R5 |
| 05 | lab-05-capstone-troubleshooting | BGP Capstone II — Comprehensive Troubleshooting | Advanced | 120m | capstone_ii | all | R1, R2, R3, R4, R5 |

## Blueprint Coverage Matrix

| Blueprint Bullet | Description | Covered In |
|---|---|---|
| 1.11 | BGP Internal/External; unicast and VRF-lite | lab-00, lab-01, lab-03, capstones |
| 1.11.a | Address families (IPv4, IPv6) | lab-01, lab-02, capstones |
| 1.11.b | Neighbor relationship and authentication | lab-00, lab-01, capstones |
| 1.11.c | Path preference (attributes and best-path) | lab-02, capstones |
| 1.11.d | Route reflector (single RR scope) | lab-03, capstones |
| 1.11.e | Policies (inbound/outbound filtering, path manipulation) | lab-03, capstones |

All 6 blueprint refs are covered in at least one non-capstone lab and re-exercised in both capstones.

## Design Decisions

- **6 labs, matching the topic-plan estimate.** RR and policies are paired in Lab 03 per the topic-plan scope note — both are policy-tier features that build on a functioning multi-path topology. Lab 02 must come first to establish dual-external connectivity needed for meaningful policy demonstration.
- **Four core devices from Lab 00.** R4 is part of the core topology from day one — eBGP is essential even in foundation labs. A BGP lab with only iBGP would teach a protocol in a vacuum.
- **Interface-based sessions in Lab 00, loopback-based from Lab 01.** Lab 00 uses directly-connected interface IPs for all BGP sessions (R1↔R2, R2↔R3, R1↔R4). This keeps the foundation lab simple and defers the IGP-dependency question. Lab 01 adds OSPF Area 0, migrates all iBGP sessions to loopback-based (`update-source Loopback0`, `next-hop-self`), and completes the full-mesh by adding R1↔R3 (previously unreachable without IGP). The progression makes the IGP dependency explicit and teachable.
- **iBGP chain in Lab 00, not full-mesh.** Without IGP, R1 and R3 have no routed path to each other's interface IPs across R2. Lab 00 therefore establishes only R1↔R2 and R2↔R3 iBGP sessions — an intentionally incomplete mesh that motivates Lab 01's IGP addition. This is a real-world pattern: iBGP partial-mesh is a common misconfiguration in brownfield networks.
- **R5 introduced in Lab 02 with AS 64512 (private).** Dual external connections (R1↔R4 via L3, R3↔R5 via L4) are required to demonstrate MED, AS-path prepend, and local-pref influencing inter-AS path selection. R5 uses a private AS specifically so `remove-private-as` can be demonstrated as an outbound policy in Lab 03.
- **BGP authentication is MD5 throughout.** IOSv 15.9 supports only `neighbor X password Y` (MD5 HMAC) for BGP authentication — there is no HMAC-SHA-256 option in classic IOS BGP. TCP Authentication Option (TCP-AO / SHA-256) requires IOS-XE 17.x. This is a platform constraint, not a legacy choice. All sessions use MD5 with password `ENARSI-BGP` from Lab 00. MD5 misconfiguration (wrong key, missing on one side) appears as a Capstone II fault class.
- **4-byte AS demonstrated as an in-lab exercise in Lab 01, not a permanent topology change.** IOSv 15.9 negotiates the 4-Octet AS Capability automatically on every session. Lab 01 includes a guided exercise: temporarily reconfigure R4 as AS 65537 (a 4-byte AS), verify adjacency re-forms, observe `show bgp neighbors | include 4-Octet`, then restore AS 65002 for topology continuity. This covers the exam objective without permanently diverging the progressive topology.
- **R2 as route reflector from Lab 03.** R2 is the natural RR candidate — it is the central router in the iBGP chain with pre-existing sessions to both R1 and R3. Adding `bgp route-reflector-client` to R2's neighbor configs is purely additive; the direct R1↔R3 session added in Lab 01 is retained (RR + retained direct session is valid and observable). This honors the "only add" constraint.
- **OSPF Area 0 as underlying IGP (pre-configured in Lab 01 initial-configs).** BGP labs focus on BGP. OSPF is included in initial-configs students receive from Lab 01 onward — infrastructure for loopback reachability, not a teaching objective of this topic.
- **VRF-Lite in Lab 03 via per-VRF BGP address families on R1/R3.** Customer-A VRF loopbacks (172.16.1.0/24 on R1, 172.16.3.0/24 on R3) are pre-reserved. Lab 03 activates `address-family ipv4 vrf Customer-A` under the BGP process and establishes intra-VRF reachability, demonstrating the blueprint's "unicast and VRF-lite" requirement.
- **`iosv` only.** All features needed (BGP IPv4/IPv6 AF, peer groups, RR, VRF-Lite, MD5 auth) are fully supported on IOSv 15.9(3)M6.
