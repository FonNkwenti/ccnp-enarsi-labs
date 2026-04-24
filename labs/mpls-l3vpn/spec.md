# MPLS and Layer 3 VPN — Lab Specification

## Exam Reference

- **Exam:** Implementing Cisco Enterprise Advanced Routing and Services (300-410)
- **Blueprint Bullets:**
  - 2.1 — Describe MPLS operations (LSR, LDP, label switching, LSP)
  - 2.2 — Describe MPLS Layer 3 VPN

Both bullets are describe-only in the official blueprint, so the series stays at the minimum size (one foundation + two capstones) and emphasises control-plane/data-plane reasoning over feature breadth.

## Topology Summary

A 3-router Service Provider MPLS core with two optional customer-edge routers:

- **Core (always active):** R1 (PE1), R2 (P), R3 (PE2) — forms the MPLS backbone with OSPF area 0 and LDP-distributed labels.
- **Optional (lab-01+):** R4 (CE1, AS 65001) attached to R1, R5 (CE2, AS 65002) attached to R3 — both in the *same* customer VRF (`CUST-A`) so VPNv4 traffic can flow end-to-end.
- **Platforms:** iosv (all five routers; EVE-NG supports MPLS and MP-BGP on iosv).

### Physical layout

```
                        ┌──────────┐
                        │    R2    │   P (MPLS LSR only)
                        │ Lo0 .0.2 │
                        └────┬─────┘
                             │ Gi0/1 (L1)     Gi0/2 (L2)
                   10.12.0.0/30               10.23.0.0/30
                             │                    │
           ┌─────────────────┴────┐      ┌────────┴─────────────┐
           │         R1           │      │         R3           │
           │ PE1  Lo0 10.0.0.1/32 │      │ PE2  Lo0 10.0.0.3/32 │
           │ VRF CUST-A           │      │ VRF CUST-A           │
           └──────────┬───────────┘      └──────────┬───────────┘
              Gi0/2 (L3, optional)          Gi0/2 (L4, optional)
                 10.14.0.0/30                     10.35.0.0/30
                      │                                │
               ┌──────┴──────┐                 ┌──────┴──────┐
               │     R4      │                 │     R5      │
               │ CE1 AS65001 │                 │ CE2 AS65002 │
               │ Lo0 .4.4    │                 │ Lo0 .5.5    │
               └─────────────┘                 └─────────────┘
```

### Interface-level IP plan

| Link | Interface (A) | Interface (B) | Subnet | Purpose |
|------|---------------|---------------|--------|---------|
| L1 | R1 Gi0/1 (.1) | R2 Gi0/1 (.2) | 10.12.0.0/30 | SP backbone PE1<->P, OSPF + LDP |
| L2 | R2 Gi0/2 (.1) | R3 Gi0/1 (.2) | 10.23.0.0/30 | SP backbone P<->PE2, OSPF + LDP |
| L3 | R1 Gi0/2 (.1) | R4 Gi0/0 (.2) | 10.14.0.0/30 | PE1-CE1 in VRF CUST-A (lab-01+) |
| L4 | R3 Gi0/2 (.1) | R5 Gi0/0 (.2) | 10.35.0.0/30 | PE2-CE2 in VRF CUST-A (lab-01+) |

Loopback0: R1 10.0.0.1/32, R2 10.0.0.2/32, R3 10.0.0.3/32, R4 192.168.4.4/32, R5 192.168.5.5/32.

### Routing plan

- **SP IGP:** OSPF process 1, area 0 on all SP backbone interfaces and Loopback0. OSPF advertises PE/P loopbacks so LDP and MP-BGP can reach each other via `update-source Loopback0`.
- **MPLS:** `mpls ip` on every SP backbone interface; LDP router-id sourced from Loopback0.
- **VRF CUST-A:** RD `65000:100`, RT import/export `65000:100` on both PEs. A single VRF (not one per CE) is mandatory for end-to-end reachability between CE1 and CE2 — mismatched import/export is one of the faults reserved for Capstone II.
- **MP-BGP:** Full-mesh iBGP between R1 and R3 (AS 65000), `address-family vpnv4 unicast`, `send-community extended`, `update-source Loopback0`. No route reflector needed at 2 PEs.
- **PE-CE:** eBGP inside VRF CUST-A. R1<->R4 uses AS 65000<->65001; R3<->R5 uses AS 65000<->65002. Different customer ASNs avoid the need for `as-override` or `allowas-in` and keep the configuration minimal for a describe-only topic.

## Lab Progression

| # | Folder | Title | Difficulty | Time | Type | Blueprint Refs | Devices |
|---|--------|-------|-----------|------|------|----------------|---------|
| 00 | lab-00-mpls-forwarding | MPLS Forwarding + L3VPN Fundamentals | Foundation | 90m | progressive | 2.1, 2.2 | R1, R2, R3 |
| 01 | lab-01-capstone-config | MPLS L3VPN Full Mastery — Capstone I | Advanced | 120m | capstone_i | 2.1, 2.2 | R1, R2, R3, R4, R5 |
| 02 | lab-02-capstone-troubleshooting | MPLS L3VPN Comprehensive Troubleshooting — Capstone II | Advanced | 120m | capstone_ii | 2.1, 2.2 | R1, R2, R3, R4, R5 |

### lab-00 — MPLS Forwarding + L3VPN Fundamentals (90 min)

Progressive build on the three-router core. No CEs attached. The purpose is to see every MPLS/L3VPN moving part in isolation before adding customer complexity.

Milestones:
1. OSPF area 0 between R1-R2-R3, loopbacks reachable, `show ip ospf neighbor` clean.
2. `mpls ip` + LDP on backbone interfaces; `show mpls ldp neighbor` shows operational sessions and `show mpls forwarding-table` shows labelled entries for remote loopbacks.
3. Create VRF `CUST-A` on R1 and R3 with RD/RT values from the addressing plan.
4. Bring up MP-BGP VPNv4 between R1 and R3; confirm `show bgp vpnv4 all summary` reaches Established.
5. Without any CE, inject a test prefix in each PE VRF using `ip route vrf CUST-A 203.0.113.X/32 Null0` and redistribute static into BGP VPNv4. This proves VPNv4 advertisement, RD stamping, RT import filtering, and VPN label assignment with no customer equipment in the loop.
6. Read and explain `show bgp vpnv4 all labels`, `show ip route vrf CUST-A`, `show ip cef vrf CUST-A <prefix>`, and `show mpls forwarding-table vrf CUST-A` — tying the control plane (BGP) to the data plane (LFIB).

### lab-01 — Capstone I: Full L3VPN build (120 min)

Clean slate. Student builds the whole stack from scratch with CEs attached.

Success criteria: `R4# ping 192.168.5.5 source Lo0` succeeds, and `R4# traceroute 192.168.5.5 source Lo0` shows MPLS labels on the hop between the PEs. Learners should be able to show, for one packet, the outer transport label (LDP) and inner VPN label (MP-BGP) and identify where each is pushed/swapped/popped.

### lab-02 — Capstone II: Layered troubleshooting (120 min)

Clean working config is pre-loaded, then faults are injected by the `fault-injector` skill in Phase 3. The student troubleshoots from bottom to top.

#### Planned fault categories for Capstone II

The fault-injector will select ~5 faults (one per layer where possible) from the candidate list below. The final set is chosen at build time — this spec fixes the *categories* so the learning coverage is predictable.

| Layer | Candidate faults |
|-------|------------------|
| IGP (OSPF) | Mismatched OSPF network type; wrong area on one backbone link; missing `network` statement for Loopback0. |
| MPLS / LDP | `no mpls ip` on one backbone interface (LSP incomplete); LDP router-id sourced from a flapping interface instead of Loopback0; MTU mismatch causing LDP session flap. |
| MP-BGP VPNv4 | `address-family vpnv4` not activated for the neighbor; `update-source Loopback0` missing; `send-community extended` missing so RTs are not propagated. |
| VRF / RT | Mismatched RT import on one PE (prefix advertised but not installed); RD typo producing duplicate-RD behaviour; VRF missing from the CE-facing interface. |
| PE-CE | Wrong eBGP AS on one PE-CE neighbor; PE-CE subnet mis-mask; `redistribute bgp` missing between VRF BGP and VPNv4 (or vice versa). |

Each fault is chosen so the symptom at `R4#` (ping/traceroute to R5 Lo0) is visible but the root cause sits at a specific layer, forcing students to use layer-appropriate show commands instead of guessing.

## Blueprint Coverage Matrix

| Blueprint Bullet | Description | Covered In |
|-----------------|-------------|------------|
| 2.1 | MPLS operations: LSR roles, LDP neighbors, label switching, LSP end-to-end | lab-00 (primary), lab-01 (applied), lab-02 (troubleshoot) |
| 2.2 | MPLS Layer 3 VPN: VRF, RD, RT, VPNv4, MP-BGP, PE-CE | lab-00 (primary), lab-01 (applied), lab-02 (troubleshoot) |

## Control Plane vs Data Plane — the mental model this series teaches

L3VPN is where students first have to hold two planes in their head simultaneously. The series is built around these pairings:

| Plane | Identity | Filtering | Transport |
|-------|----------|-----------|-----------|
| Control | **RD** stamps the VPNv4 prefix so overlapping customer addresses stay unique in BGP | **RT** import/export decides which VRF installs the prefix | **MP-BGP** carries the VPNv4 NLRI plus the VPN label |
| Data | **Inner VPN label** (assigned by egress PE) identifies the VRF / next-hop CE | — | **Outer LDP label** (assigned per-hop) carries the packet across the MPLS core |

Every lab exercise, show command, and fault in this series maps back to one cell in that table. That is how a learner who "understands MPLS L3VPN" actually thinks about it.

## Design Decisions

- **Minimum-sized topic (3 labs).** Both blueprint bullets are describe-only, so the series is 1 foundation + 2 capstones. Adding more would repeat concepts without new coverage.
- **Single customer VRF (`CUST-A`) across both CEs.** The whole point of L3VPN is end-to-end reachability through the core. Two different VRFs (CUST-A and CUST-B) with non-overlapping RTs would advertise but never install each other's prefixes, and ping would silently fail — a trap for the learner, not a lesson. A single VRF with matching RT import/export is the canonical demonstration.
- **Different customer ASNs (65001 vs 65002).** With the same ASN on both CEs, the remote CE's AS would appear in the AS-path and be dropped by eBGP loop prevention, requiring `as-override` or `allowas-in`. Those are valid tools but out of scope for a describe-only topic; different ASNs keep the PE-CE config minimal and the focus on VPNv4.
- **OSPF as SP IGP, not IS-IS.** ENARSI (300-410) does not cover IS-IS. OSPF is already in the exam, and the MPLS LDP/LSP behaviour the student must describe is identical.
- **eBGP PE-CE, not OSPF/static.** eBGP is the most common real-world PE-CE protocol and the one that forces the student to see the VPNv4 label being allocated when a VRF BGP route is redistributed. Static or OSPF PE-CE would hide that step. Note: when OSPF *is* used as the PE-CE protocol, the **DN-bit** (downward bit, RFC 4577) prevents re-advertisement of VPN-received prefixes back into the customer OSPF domain — it is an L3VPN-specific loop-prevention mechanism that cannot be demonstrated on an IGP-only topology and is therefore deferred here rather than in the `route-control` topic.
- **Lab-00 uses null-route static injection instead of CEs.** Adding CEs early would conflate PE-CE routing problems with MPLS/VPNv4 mechanics. A `Null0` static inside the VRF generates a VPNv4 advertisement with a real label and RT, so the VPNv4 control plane is fully visible with three routers.
- **No RR in the core.** Two PEs do not require a route reflector. Introducing one would add moving parts without teaching anything the blueprint asks for.
- **Out of scope (deliberately).** Segment Routing, MPLS-TE, inter-AS options (A/B/C), 6PE/6VPE, MVPN, L2VPN. The blueprint bullets are describe-only and do not require these; adding them would dilute the foundation.
- **Dependency on BGP topic.** The series assumes the learner has completed the `bgp` topic. MP-BGP is introduced here only as a new address family, not from scratch.
