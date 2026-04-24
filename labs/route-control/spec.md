# Route Control and Redistribution — Lab Specification

## Exam Reference

- **Exam:** Implementing Cisco Enterprise Advanced Routing and Services (300-410)
- **Blueprint Bullets:**
  - 1.1 — Troubleshoot administrative distance (all routing protocols)
  - 1.2 — Troubleshoot route map for any routing protocol (attributes, tagging, filtering)
  - 1.3 — Troubleshoot loop prevention mechanisms (filtering, tagging, split horizon, route poisoning)
  - 1.4 — Troubleshoot redistribution between any routing source (connected, static, and routing protocol)
  - 1.5 — Troubleshoot manual and autosummarization with any routing protocol

## Topology Summary

A 5-router dual-domain redistribution ring. Two ASBRs (R2 and R3) sit between an OSPF domain and an EIGRP domain, performing mutual redistribution. A fifth router (R5) peers eBGP with R2 as an external source of BGP prefixes.

- **OSPF-only:** R1 (internal), R2/R3 (as ASBRs), OSPF area 0, process 1.
- **EIGRP-only:** R4 (internal), R2/R3 (as ASBRs), EIGRP AS 100, **named mode** (instance `ENARSI`).
- **BGP:** eBGP between R2 (AS 65000) and R5 (AS 65001) over L5.
- **Platforms:** iosv (all five routers).

### Physical layout

```
                         ┌──────────┐
                         │    R1    │   OSPF-only
                         │ Lo0 .1.1 │
                         └──┬────┬──┘
                 Gi0/1 (L1) │    │ Gi0/2 (L2)
                10.12.0.0/30│    │10.13.0.0/30
                   OSPF a0  │    │  OSPF a0
                            │    │
                ┌───────────┴┐  ┌┴───────────┐
                │     R2     │  │     R3     │
                │  ASBR #1   │  │  ASBR #2   │
                │ OSPF+EIGRP │  │ OSPF+EIGRP │
                │  +eBGP→R5  │  │ Lo0 .3.3   │
                │ Lo0 .2.2   │  └┬───────────┘
                └┬──────────┬┘   │ Gi0/2 (L4)
     Gi0/3 (L5) │   Gi0/2(L3)    │ 10.34.0.0/30
   172.16.25/30 │  10.24.0.0/30  │  EIGRP 100
     eBGP       │   EIGRP 100    │
         65000  │                │
         65001  │                │
                │                │
         ┌──────┴──────┐  ┌──────┴──────┐
         │     R5      │  │     R4      │
         │  AS 65001   │  │ EIGRP-only  │
         │ Lo0 192.168 │  │ Lo0 .4.4    │
         │     .5.5    │  └─────────────┘
         └─────────────┘
```

### Interface-level IP plan

| Link | Interface (A) | Interface (B) | Subnet | Protocol |
|------|---------------|---------------|--------|----------|
| L1 | R1 Gi0/1 (.1) | R2 Gi0/1 (.2) | 10.12.0.0/30 | OSPF area 0 |
| L2 | R1 Gi0/2 (.1) | R3 Gi0/1 (.2) | 10.13.0.0/30 | OSPF area 0 |
| L3 | R2 Gi0/2 (.1) | R4 Gi0/1 (.2) | 10.24.0.0/30 | EIGRP AS 100 |
| L4 | R3 Gi0/2 (.1) | R4 Gi0/2 (.2) | 10.34.0.0/30 | EIGRP AS 100 |
| L5 | R2 Gi0/3 (.1) | R5 Gi0/1 (.2) | 172.16.25.0/30 | eBGP 65000<->65001 |

Loopback0: R1 10.1.1.1/32, R2 10.2.2.2/32, R3 10.3.3.3/32, R4 10.4.4.4/32, R5 192.168.5.5/32.

### Protocol plan

- **OSPF:** process 1, area 0 on L1, L2, and the loopbacks of R1/R2/R3. R2 and R3 are the ASBRs that inject EIGRP routes as OSPF externals.
- **EIGRP:** named-mode, instance `ENARSI`, AS 100 on L3, L4, and the loopbacks of R2/R3/R4. R2 and R3 inject OSPF routes as EIGRP externals. Named-mode matches the `eigrp` topic and is the current IOS default; classic mode is *not* reintroduced here solely to demonstrate auto-summary (see design decisions).
- **BGP:** R2 (AS 65000) and R5 (AS 65001) form a single eBGP session over L5. R5 originates `192.168.5.0/24`; R2 may redistribute that prefix into OSPF and/or EIGRP to exercise BGP->IGP redistribution.

### Loop-prevention techniques in scope

| Technique | Where demonstrated | Blueprint coverage |
|-----------|-------------------|--------------------|
| Distribute-list / prefix-list filtering on redistribution | lab-02 | 1.3 |
| Route tagging + deny-on-tag match in route-maps | lab-02 (canonical dual-ASBR design) | 1.3 |
| EIGRP split horizon | lab-02 | 1.3 |
| Route poisoning (infinite metric on redistribution) | lab-02 | 1.3 |

**Out of scope:** OSPF downward bit (DN-bit). DN-bit is an L3VPN PE-CE loop-prevention mechanism that only appears when OSPF is the PE-CE protocol inside a VRF — it is covered in the `mpls-l3vpn` spec, not here. A 5-router IGP-only topology cannot demonstrate it authentically.

## Lab Progression

| # | Folder | Title | Difficulty | Time | Type | Blueprint Refs | Devices |
|---|--------|-------|-----------|------|------|----------------|---------|
| 00 | lab-00-admin-distance | Administrative Distance Fundamentals and Troubleshooting | Foundation | 75m | progressive | 1.1 | R1, R2, R3, R4 |
| 01 | lab-01-route-maps | Route Maps — Match, Set, Attribute Manipulation, and Tagging | Intermediate | 90m | progressive | 1.2 | R1, R2, R3, R4, R5 |
| 02 | lab-02-loop-prevention | Loop Prevention: Filtering, Tagging, Split Horizon, and Route Poisoning | Intermediate | 90m | progressive | 1.3 | R1, R2, R3, R4 |
| 03 | lab-03-redistribution-summarization | Redistribution and Summarization (paired) | Advanced | 105m | progressive | 1.4, 1.5 | R1, R2, R3, R4, R5 |
| 04 | lab-04-capstone-config | Route Control and Redistribution — Capstone I | Advanced | 120m | capstone_i | 1.1–1.5 | all |
| 05 | lab-05-capstone-troubleshooting | Route Control and Redistribution — Capstone II | Advanced | 120m | capstone_ii | 1.1–1.5 | all |

### lab-00 — Administrative Distance (75 min)

Establish OSPF on R1-R2-R3 and EIGRP (named-mode) on R2-R3-R4. No mutual redistribution yet — that is lab-02's domain. Create a scenario where the *same prefix* is learned by both protocols (inject a shared loopback on R2 and R3 into both processes) and predict which entry wins the RIB purely on AD. Then use `distance` under each routing process to override defaults and watch the RIB change. The takeaway is a mental model of AD as a per-source tiebreaker, applied *before* the protocol's own metric.

### lab-01 — Route Maps (90 min)

Bring R5 online, form the eBGP session R2<->R5, and advertise `192.168.5.0/24`. Write route-maps that (a) match with a prefix-list and set a tag, (b) match on tag and set a metric/metric-type, and (c) apply inbound and outbound on the BGP neighbor to manipulate local-preference, MED, and community. The lab teaches route-map *mechanics* (ordered clauses, implicit deny, match-vs-set) in isolation before lab-02 uses them for loop prevention.

### lab-02 — Loop Prevention (90 min)

Enable mutual redistribution on BOTH R2 and R3 (OSPF<->EIGRP). The ring topology means a prefix redistributed into EIGRP at R2 can travel R2->R4->R3, be redistributed back into OSPF at R3 with a different AD, and re-enter the OSPF domain — the classic suboptimal/loop condition. The fix is the textbook dual-ASBR pattern: each ASBR *tags* routes on egress into the foreign protocol, and *denies* any incoming route that carries the tag it stamps on egress. The lab also demonstrates `ip summary-address` route poisoning (infinite metric) and EIGRP split horizon.

### lab-03 — Redistribution + Summarization (105 min)

With the tagging framework in place, broaden the redistribution matrix: redistribute connected, static, and BGP-learned (`192.168.5.0/24`) prefixes into both IGPs. Set seed metrics with `default-metric` and per-statement `metric` under `redistribute`. Observe E1 vs E2 (OSPF) and internal vs external (EIGRP). Then summarize: `summary-address` at the OSPF ASBRs, `ip summary-address eigrp` at the EIGRP ASBRs, `aggregate-address` at the BGP speaker. Note the Null0 discard route each one installs — and why it exists (loop prevention for the summarized block). Demonstrate that auto-summary is OFF by default in EIGRP named-mode.

### lab-04 — Capstone I (120 min)

Clean slate. Build the whole topology from addressing upward, apply the tag/deny loop-prevention framework at every redistribution point, and summarize at all ASBR/BGP boundaries. Success criterion: every router's RIB contains the expected prefixes with the expected source (C/S/O/O E1/O E2/D/D EX/B) and no duplicate-redistribution artefacts.

### lab-05 — Capstone II (120 min)

Clean working config is pre-loaded, then faults are injected by the `fault-injector` skill in Phase 3. The student troubleshoots layer by layer.

#### Planned fault categories for Capstone II

The fault-injector will select ~5 faults from the candidate list below, one per layer where possible.

| Layer | Candidate faults |
|-------|------------------|
| Administrative Distance (1.1) | `distance` override that silently prefers the wrong protocol; backdoor static with AD 1 shadowing a dynamic route. |
| Route-map logic (1.2) | Permit/deny order inversion; `match` clause references a non-existent prefix-list (implicit permit everything); `set metric-type` typo. |
| Redistribution direction (1.4) | `redistribute ospf 1` missing `subnets` keyword — classful externals only; missing `default-metric` causing EIGRP to refuse non-connected externals. |
| Loop prevention (1.3) | Tag applied on egress but the deny-on-tag clause is missing on the opposite ASBR — routing loop returns; prefix-list filter applied in the wrong direction. |
| Summarization (1.5) | Summary covers too much (includes a prefix that should be individually advertised); summary configured on the wrong ASBR (creates a sub-optimal path); auto-summary accidentally re-enabled on a classic-mode neighbor. |

Each fault is chosen so the end-to-end symptom (wrong path, missing prefix, loop, or suboptimal traceroute) is visible but the root cause sits at a specific layer, forcing students to use layer-appropriate show commands instead of guessing.

## Blueprint Coverage Matrix

| Blueprint Bullet | Description | Covered In |
|------------------|-------------|------------|
| 1.1 | Administrative distance | lab-00 (primary), lab-04 (applied), lab-05 (troubleshoot) |
| 1.2 | Route map (attributes, tagging, filtering) | lab-01 (primary), lab-02+03+04 (applied), lab-05 (troubleshoot) |
| 1.3 | Loop prevention (filtering, tagging, split horizon, route poisoning) | lab-02 (primary), lab-04 (applied), lab-05 (troubleshoot) |
| 1.4 | Redistribution between any routing source | lab-03 (primary), lab-04 (applied), lab-05 (troubleshoot) |
| 1.5 | Manual and autosummarization | lab-03 (primary), lab-04 (applied), lab-05 (troubleshoot) |

## Design Decisions

- **5-router dual-ASBR ring, not a star.** A single ASBR cannot demonstrate the redistribution loop/suboptimal-path conditions that dominate real exam scenarios. Two ASBRs between two IGP domains is the minimum topology that makes 1.3 (loop prevention) a real phenomenon rather than a vocabulary drill.
- **EIGRP in named-mode, not classic-mode.** The `eigrp` topic standardised on named-mode (its lab-01 is named-mode dual-stack), and named-mode is the current IOS default. Regressing to classic-mode here solely to demonstrate `auto-summary` would contradict the rest of the curriculum. Auto-summary is covered correctly by showing that named-mode disables it by default, noting where the CLI knob lives, and explaining why the default changed.
- **Downward bit (DN-bit) explicitly deferred to `mpls-l3vpn`.** DN-bit is a loop-prevention mechanism that only exists when OSPF is used as the PE-CE protocol inside a VRF (RFC 4577). It cannot be authentically demonstrated on an IGP-only topology, and attempting it here would either require a fake VRF or mis-teach the mechanism. The `mpls-l3vpn` spec notes DN-bit as L3VPN-OSPF loop prevention.
- **eBGP (R5) instead of iBGP.** A single eBGP session gives the minimum BGP surface needed for redistribution labs (BGP<->OSPF, BGP<->EIGRP) without pulling in route reflectors, full-mesh iBGP, or next-hop-self discussions that belong in the `bgp` topic.
- **Ring topology (R1-R2-R4-R3-R1), not hub-and-spoke.** The ring ensures every prefix has two paths — one through each ASBR — which is exactly what makes both suboptimal routing and routing loops possible. A hub-and-spoke would eliminate the redundancy that the troubleshooting scenarios depend on.
- **Progressive chain for labs 00–03; clean slate for capstones.** Each of lab-01, lab-02, lab-03 only *adds* configuration on top of the previous lab's end-state (per project rule). The capstones reset to clean slate because they are summative.
- **Out of scope (deliberately).** PBR (topic `pbr-vrf-bfd`), VRF-Lite (same), BFD (same), MP-BGP VPNv4 / RD / RT (`mpls-l3vpn`), full BGP policy design (`bgp`), AD on static with track (`pbr-vrf-bfd`). Route-control is the *shared glue* between the per-protocol topics; anything protocol-specific stays in its home topic.
- **Dependency on `eigrp`, `ospf`, `bgp`.** The learner is assumed to be able to bring up each protocol on its own. This topic teaches what happens where they meet.
