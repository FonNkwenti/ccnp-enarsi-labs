# OSPF Routing (v2 and v3) — Lab Specification

## Exam Reference
- **Exam:** Implementing Cisco Enterprise Advanced Routing and Services (300-410)
- **Blueprint Bullets:**
  - **1.10** Troubleshoot OSPF (v2/v3)
  - **1.10.a** Address families (IPv4, IPv6)
  - **1.10.b** Neighbor relationship and authentication
  - **1.10.c** Network types, area types, and router types
  - **1.10.c.i** Point-to-point, multipoint, broadcast, nonbroadcast
  - **1.10.c.ii** Area type: backbone, normal, transit, stub, NSSA, totally stub
  - **1.10.c.iii** Internal router, backbone router, ABR, ASBR
  - **1.10.c.iv** Virtual link
  - **1.10.d** Path preference

## Topology Summary

Three-router chain (R1 — R2 — R3) across Area 0 and Area 1 forms the core. Two optional routers (R4, R5) are introduced together in Lab 03 to create a two-router Area 2, attached to Area 1 only via R4 — so Area 2 is disconnected from the backbone and requires a virtual link. **R4 is pure ABR(1↔2); R5 is the ASBR inside Area 2**, redistributing Lo100 (172.16.100.0/24) so the Type-7 → Type-5 translation is observable on a different router than the one that generates it. All devices run `iosv` 15.9(3)M6.

```
        Area 0                       Area 1                            Area 2
┌──────────────────────┐ ┌──────────────────────────────┐ ┌──────────────────────────┐
│                      │ │                              │ │                          │
│  ┌────┐      ┌────┐  │ │   ┌────┐          ┌────┐     │ │    ┌────┐      ┌────┐    │
│  │ R1 │──L1──│ R2 │──┼─┼───│ R3 │────L3───│ R4 │─────┼─┼────│ R4 │──L4──│ R5 │    │
│  └────┘      └────┘  │ │   └────┘         └────┘     │ │    │(ABR)│     │(ASBR)    │
│  Lo0         ABR     │ │   Internal       ABR(1↔2)   │ │    └────┘      └────┘    │
│  10.1.1.1            │ │   10.3.3.3       10.4.4.4   │ │    Lo0         Lo0 / Lo100│
└──────────────────────┘ └──────────────────────────────┘ │    10.4.4.4    10.5.5.5  │
            L1: 10.0.12/30      L2: 10.0.23/30            │    (Area 2)    + ext     │
            (Area 0)            (Area 1)                  └──────────────────────────┘
                                       L3: 10.0.34/30 (Area 1, vl-transit)
                                                          L4: 10.0.45/30 (Area 2)

Virtual link (Lab 03+):   R2 ═════════════ Area 1 transit ═════════════ R4
                          RID 10.2.2.2                                  RID 10.4.4.4
```

- **Core devices (all labs):** R1 (Area 0 internal), R2 (ABR 0↔1), R3 (Area 1 internal)
- **Optional devices (Lab 03+):** R4 (ABR 1↔2) and R5 (Area 2 internal + ASBR)
- **Dual-stack** enabled from Lab 04 onward; OSPFv2 (IPv4) and OSPFv3 (IPv4 AF + IPv6 AF)
- **RAM budget:** 5 × 512 MB = 2.5 GB

## Lab Progression

| # | Folder | Title | Difficulty | Time | Type | Blueprint Refs | Devices |
|---|---|---|---|---|---|---|---|
| 00 | lab-00-single-area-foundation | OSPFv2 Single-Area Foundation | Foundation | 60m | progressive | 1.10, 1.10.b, 1.10.c.iii | R1, R2 |
| 01 | lab-01-multi-area-path-preference | Multi-Area OSPFv2 and Path Preference | Foundation | 75m | progressive | 1.10, 1.10.c.iii, 1.10.d | R1, R2, R3 |
| 02 | lab-02-network-types | OSPF Network Types | Intermediate | 75m | progressive | 1.10.c, 1.10.c.i | R1, R2, R3 |
| 03 | lab-03-area-types-virtual-link | Area Types, Virtual Link, and ASBR | Advanced | 120m | progressive | 1.10.c.ii, 1.10.c.iii, 1.10.c.iv | R1, R2, R3, R4, R5 |
| 04 | lab-04-ospfv3-dual-stack | OSPFv3 and Dual-Stack Address Families | Advanced | 90m | progressive | 1.10, 1.10.a | R1, R2, R3, R4, R5 |
| 05 | lab-05-capstone-config | OSPF Capstone I — Full Configuration | Advanced | 120m | capstone_i | all | R1, R2, R3, R4, R5 |
| 06 | lab-06-capstone-troubleshooting | OSPF Capstone II — Comprehensive Troubleshooting | Advanced | 120m | capstone_ii | all | R1, R2, R3, R4, R5 |

## Blueprint Coverage Matrix

| Blueprint Bullet | Description | Covered In |
|---|---|---|
| 1.10 | OSPF v2/v3 general | lab-00, lab-01, lab-02, lab-04, capstones |
| 1.10.a | Address families (IPv4, IPv6) | lab-04, capstones |
| 1.10.b | Neighbor relationship and authentication | lab-00, capstones |
| 1.10.c | Network types, area types, router types | lab-02, lab-03, capstones |
| 1.10.c.i | P2P, multipoint, broadcast, nonbroadcast | lab-02, capstones |
| 1.10.c.ii | Backbone, normal, transit, stub, NSSA, totally stub | lab-03, capstones |
| 1.10.c.iii | Internal, backbone, ABR, ASBR | lab-00, lab-01, lab-03, capstones |
| 1.10.c.iv | Virtual link | lab-03, capstones |
| 1.10.d | Path preference | lab-01, lab-03, capstones |

All 9 blueprint refs are covered in at least one non-capstone lab and re-exercised in both capstones.

## Design Decisions

- **7 labs, matching the topic-plan estimate.** Network types (Lab 02) and area types (Lab 03) are intentionally kept as separate labs — each is an exam-weighted concept that deserves its own progressive position rather than being collapsed into a "types" omnibus.
- **Progression starts single-area, adds areas and routers incrementally.** Lab 00 brings R1+R2 up in Area 0 only; Lab 01 adds R3 in Area 1 (R2 promoted to ABR); Lab 03 adds R4+R5 in Area 2 together. Every transition ADDS an area or router — honoring "only add configuration between labs, never remove."
- **Network types demonstrated on the existing R1↔R2 link.** No multi-access switch node is added. Students iterate `ip ospf network-type {broadcast | point-to-point | non-broadcast | point-to-multipoint}` on a single interface pair and observe DR/BDR behavior, timer defaults, and neighbor-command requirements. Final committed type at end of Lab 02 is `point-to-point` (most appropriate for a /30) — carried forward.
- **R4 and R5 introduced together at Lab 03, with split roles.** R4 is pure ABR(1↔2); R5 is Area 2 internal and holds the ASBR role (redistributes Lo100 into OSPF as an external). This split means the Type-7 → Type-5 translation can be directly observed: `show ip ospf database nssa-external` on **R5** shows Type-7 origin, while `show ip ospf database external` on **R4** (and Area 0/1 routers) shows Type-5 after R4's N-bit translation. The pedagogical contrast collapses if the same router holds both roles.
- **Area 2 is a two-router network with a transit link (R4↔R5).** Richer than a single-router loopback: Area 2's LSDB contains Type-1 router LSAs from both R4 and R5, a Type-2 network LSA for L4, the two loopbacks as stub prefixes, and the Type-7 external — a realistic Area 2 slice.
- **OSPFv3 via address-family mode, not traditional `ipv6 router ospf`.** The blueprint 1.10.a explicitly calls out an IPv4 AF under v3; only the AF-mode `router ospfv3` supports carrying IPv4 over OSPFv3. Traditional v3 (`ipv6 router ospf`) is IPv6-only and would miss half of 1.10.a.
- **Modern authentication from Lab 00.** OSPFv2 uses HMAC-SHA-256 via key-chain (`cryptographic-algorithm hmac-sha-256` + `ip ospf authentication key-chain`) from day one, not MD5. Available on IOSv 15.9 since IOS 15.4(1)T. MD5 still appears in Capstone II as a troubleshooting fault class — brownfield deployments exist in production and on the exam — but is never the teaching default. Lab 04 adds OSPFv3 IPsec authentication (`ospfv3 authentication ipsec spi … sha1 …`) to every adjacency.
- **Path preference (1.10.d) introduced at Lab 01, expanded at Lab 03.** Lab 01 demonstrates intra-area > inter-area using R3's loopback as intra-area (from R3's perspective) and R1's loopback as inter-area. External types (E1/E2) are introduced properly at Lab 03 once R5 ASBR comes online — both preferences are then re-exercised in Capstone I's RIB inspection step.
- **`iosv` only.** IOL 15.7 has known OSPFv3-AF config-mode quirks; IOSv 15.9 handles the full `router ospfv3` / address-family / `cryptographic-algorithm hmac-sha-256` syntax cleanly.
