# Policy Routing, VRF-Lite, and BFD — Lab Specification

## Exam Reference

- **Exam:** Implementing Cisco Enterprise Advanced Routing and Services (300-410)
- **Blueprint Bullets:**
  - 1.6 — Configure and verify policy-based routing
  - 1.7 — Configure and verify VRF-Lite
  - 1.8 — Describe Bidirectional Forwarding Detection (BFD)

Blueprint 1.8 is describe-only — BFD is demonstrated here through its operational role in PBR next-hop tracking, not as a standalone feature.

## Topology Summary

A 5-router diamond. R2 is the policy router and PE1 at the centre; R3 and R4 are the two alternate paths; R1 and R5 are the CE endpoints. The diamond serves double duty: PBR uses R3 and R4 as competing next-hops, while VRF-Lite uses the R2–R4 trunk as a multi-VRF PE–PE link.

- **All labs (R1, R2, R3, R4, R5):** R1 source/CE1, R2 policy-router/PE1, R3 Path-A backbone, R4 Path-B backbone/PE2, R5 destination/CE2.
- **lab-01 (VRF-Lite):** R3 is idle. Active devices: R1, R2, R4, R5.
- **Platforms:** iosv (all five routers).

### Physical layout

```
                         ┌──────────────────┐
                         │        R3        │   Path-A (upper)
                         │   Lo0 10.3.3.3   │
                         └───────┬──────┬───┘
               Gi0/1 (L2)        │      │        Gi0/2 (L4)
           10.23.0.0/30          │      │        10.35.0.0/30
                                 │      │
┌──────────┐  Gi0/1 (L1)  ┌─────┴──────┴─────┐        ┌──────────┐
│    R1    ├───────────────┤       R2          │        │    R5    │
│  Source  │  10.12.0.0/30 │   Policy Rtr      │        │   Dest.  │
│CE1/Lo0   │               │   PE1  Lo0        │        │CE2/Lo0   │
│10.1.1.1  │               │   10.2.2.2        │        │10.5.5.5  │
└──────────┘               └─────────┬─────────┘        └──┬───┬───┘
                           Gi0/3(L3) │                      │   │
                       10.24.0.0/30  │              (L4)    │   │ (L5)
                                     │         10.35.0.0/30 │   │ 10.45.0.0/30
                               ┌─────┴─────────┐            │   │
                               │      R4        ├───────────┘   │
                               │   Path-B/PE2   │  Gi0/2 (L5)   │
                               │   Lo0 10.4.4.4 ├───────────────┘
                               └────────────────┘
```

### Interface-level IP plan

| Link | Interface (A) | Interface (B) | Subnet | Purpose |
|------|---------------|---------------|--------|---------|
| L1 | R1 Gi0/1 (.1) | R2 Gi0/1 (.2) | 10.12.0.0/30 | Source to policy-router; VRF CUST-A PE-CE (lab-01) |
| L2 | R2 Gi0/2 (.1) | R3 Gi0/1 (.2) | 10.23.0.0/30 | PBR Path-A (upper). BFD session tracks R3 next-hop |
| L3 | R2 Gi0/3 (.1) | R4 Gi0/1 (.2) | 10.24.0.0/30 | PBR Path-B (flat, lab-00); 802.1Q PE–PE trunk (lab-01) |
| L4 | R3 Gi0/2 (.1) | R5 Gi0/1 (.2) | 10.35.0.0/30 | Path-A continuation R3 → R5 |
| L5 | R4 Gi0/2 (.1) | R5 Gi0/2 (.2) | 10.45.0.0/30 | Path-B continuation R4 → R5; VRF CUST-B PE-CE (lab-01) |

Loopback0: R1 10.1.1.1/32, R2 10.2.2.2/32, R3 10.3.3.3/32, R4 10.4.4.4/32, R5 10.5.5.5/32.

### VRF-Lite sub-interface plan (lab-01 only)

L3 (R2.Gi0/3 — R4.Gi0/1) carries both VRFs on 802.1Q sub-interfaces:

| Sub-intf | 802.1Q | VRF | R2 address | R4 address | Subnet | OSPF process |
|---------|--------|-----|-----------|-----------|--------|-------------|
| Gi0/3.100 / Gi0/1.100 | 100 | CUST-A | 10.24.10.1 | 10.24.10.2 | /30 | 10 |
| Gi0/3.200 / Gi0/1.200 | 200 | CUST-B | 10.24.20.1 | 10.24.20.2 | /30 | 20 |

### Routing plan

**lab-00 (PBR + BFD):**
- OSPF process 1, area 0 on all links (L1–L5) and all loopbacks — global routing table only.
- PBR on R2 Gi0/1 (inbound): ACL matches R1 Lo0 → R5 Lo0 traffic; route-map sets Path-A (R3 next-hop) as preferred via `set ip next-hop verify-availability 10.23.0.2 10 track 10`. Track 10 monitors BFD to R3.
- Fallback entry in the same route-map: `set ip next-hop verify-availability 10.24.0.2 20 track 20`. Track 20 monitors BFD to R4.
- BFD on R2 Gi0/2 and R2 Gi0/3 with timers 300ms/900ms multiplier 3. When BFD detects R3 down, track 10 goes Down and PBR silently fails over to R4 within the hold timer — no OSPF dead-timer wait.

**lab-01 (VRF-Lite):**
- No global routing beyond management. VRFs CUST-A (RD 65000:10) and CUST-B (RD 65000:20) on R2 and R4.
- OSPF process 10 inside VRF CUST-A: R2 (Gi0/1 + Gi0/3.100) and R4 (Gi0/1.100). Advertises R1 Lo0 into CUST-A.
- OSPF process 20 inside VRF CUST-B: R2 (Gi0/3.200) and R4 (Gi0/1.200 + Gi0/2). Advertises R5 Lo0 into CUST-B.
- Inter-VRF leak: `ip route vrf CUST-B 10.1.1.1/32 <nh> vrf CUST-A` on R4 — allows R5 to reach R1 Lo0 only; all other CUST-A prefixes remain isolated.

## Lab Progression

| # | Folder | Title | Difficulty | Time | Type | Blueprint Refs | Devices |
|---|--------|-------|-----------|------|------|----------------|---------|
| 00 | lab-00-pbr-bfd | PBR and BFD acceleration (paired: BFD for next-hop tracking in PBR) | Foundation | 90m | progressive | 1.6, 1.8 | R1–R5 |
| 01 | lab-01-vrf-lite-leaking | VRF-Lite design with inter-VRF route leaking | Intermediate | 90m | progressive | 1.7 | R1, R2, R4, R5 |
| 02 | lab-02-capstone-config | Capstone I: Full PBR/VRF/BFD configuration challenge | Advanced | 120m | capstone_i | 1.6, 1.7, 1.8 | R1–R5 |
| 03 | lab-03-capstone-troubleshooting | Capstone II: Comprehensive PBR/VRF/BFD troubleshooting | Advanced | 120m | capstone_ii | 1.6, 1.7, 1.8 | R1–R5 |

### lab-00 — PBR and BFD (90 min)

Foundation lab. Students build OSPF area 0 on all five routers, then layer PBR onto R2 without disturbing global routing for other traffic.

Milestones:
1. OSPF area 0 on all links. `show ip ospf neighbor` shows 4 sessions on R2 (R1, R3, R4, and through R3/R4 to R5).
2. Write ACL 100 matching `10.1.1.1 0.0.0.0` source, `10.5.5.5 0.0.0.0` destination.
3. Create route-map RM-PBR: seq 10 match ACL 100, `set ip next-hop verify-availability 10.23.0.2 10 track 10` (Path-A); seq 20 same ACL, `set ip next-hop verify-availability 10.24.0.2 20 track 20` (Path-B). Apply `ip policy route-map RM-PBR` on R2 Gi0/1.
4. Enable BFD on R2 Gi0/2 and Gi0/3. Create track 10 bound to BFD peer 10.23.0.2; track 20 bound to BFD peer 10.24.0.2.
5. Confirm `traceroute 10.5.5.5 source Lo0` from R1 shows R3 as next-hop (Path-A preferred).
6. Shut R3 Gi0/1. Observe track 10 go Down within 900ms (BFD hold time). Re-trace from R1 — Path-B (R4) now appears. Measure elapsed time vs the 40s OSPF dead timer. That gap is the value of BFD.
7. Study `show ip policy`, `show route-map RM-PBR`, `show bfd neighbors detail`, `show track 10`.

### lab-01 — VRF-Lite with inter-VRF leaking (90 min)

Start from a clean slate (no OSPF global table; VRFs are the only routing domains). R3 is not used.

Milestones:
1. Create VRFs CUST-A and CUST-B on R2 and R4. Confirm `show vrf` lists both with distinct RDs.
2. Assign R2 Gi0/1 to VRF CUST-A (PE1-CE1 to R1). Assign R4 Gi0/2 to VRF CUST-B (PE2-CE2 to R5). Note: the moment an interface joins a VRF its IP address is wiped — re-enter it.
3. Configure 802.1Q sub-interfaces on L3: Gi0/3.100 (CUST-A, 10.24.10.0/30) and Gi0/3.200 (CUST-B, 10.24.20.0/30) on R2; matching sub-interfaces on R4 Gi0/1.
4. Start OSPF process 10 in VRF CUST-A on R2 and R4. Start OSPF process 20 in VRF CUST-B on R2 and R4. `show ip ospf neighbor` inside each VRF should show one adjacency per process.
5. Verify VRF isolation: `ping vrf CUST-A 10.5.5.5` from R2 should fail (CUST-B prefix not visible in CUST-A table).
6. Add cross-VRF static: `ip route vrf CUST-B 10.1.1.1 255.255.255.255 10.24.20.1 vrf CUST-A` on R4 — making R1 Lo0 reachable inside CUST-B. Confirm R5 can now reach 10.1.1.1 but no other CUST-A prefix.
7. Identify what the DN-bit would prevent here if OSPF were the PE-CE protocol inside a real MPLS VPN — conceptual note, not a lab step (OSPF PE-CE + DN-bit is a full MPLS L3VPN construct covered in `mpls-l3vpn`).

### lab-02 — Capstone I: Full PBR/VRF/BFD build (120 min)

Clean slate. Students build both features simultaneously on the same topology and verify they operate independently (PBR on the global table, VRF-Lite on the VRF table — no interaction unless explicitly leaked).

Success criteria:
- `traceroute 10.5.5.5 source 10.1.1.1` from R1 shows Path-A (R3) hops.
- Shut R2 Gi0/2 → traceroute shifts to Path-B (R4) within 3 seconds (BFD hold timer).
- `show ip route vrf CUST-A` and `show ip route vrf CUST-B` show correct prefixes with VRF isolation intact.
- The one authorized cross-VRF prefix (10.1.1.1/32 in CUST-B) is reachable from R5; all others are not.

### lab-03 — Capstone II: Layered troubleshooting (120 min)

Clean working config is pre-loaded, then faults are injected by the `fault-injector` skill in Phase 3. Students troubleshoot from the PBR match clause downward.

#### Planned fault categories for Capstone II

The fault-injector will select ~5 faults (one per layer where possible) from the candidate list below.

| Layer | Candidate faults |
|-------|------------------|
| PBR match (1.6) | ACL references wrong source/destination — route-map matches nothing, all traffic falls through to normal routing; `ip policy` applied on wrong interface (Gi0/2 instead of Gi0/1 — policy fires on Path-A traffic, not on ingress from R1). |
| PBR next-hop (1.6) | `verify-availability` missing — traffic black-holes when Path-A goes down instead of failing over; wrong sequence numbers so fallback seq fires before preferred seq. |
| BFD session (1.8) | BFD not enabled on the peer interface (R3 Gi0/1) — session stays Down; timer mismatch (tx/rx asymmetry) causes session flap; track object not bound to the BFD session (track monitors wrong IP). |
| VRF assignment (1.7) | Interface placed in wrong VRF — OSPF adjacency never forms; sub-interface encapsulation dot1q VLAN ID wrong on one side (802.1Q mismatch breaks L2 on trunk). |
| Inter-VRF leak (1.7) | Cross-VRF static points to wrong next-hop VRF; leaked prefix has wrong mask — /24 instead of /32 covers too much; static is on wrong router (R2 instead of R4 — the PE adjacent to the CE that needs the leak). |

Each fault is designed so the symptom (unexpected traceroute hop, unreachable prefix, VRF prefix absent from RIB) is observable from R1 or R5, but the root cause sits at a specific layer — forcing students to use layer-appropriate show commands rather than guessing.

## Blueprint Coverage Matrix

| Blueprint Bullet | Description | Covered In |
|-----------------|-------------|------------|
| 1.6 | Configure and verify policy-based routing | lab-00 (primary), lab-02 (applied), lab-03 (troubleshoot) |
| 1.7 | Configure and verify VRF-Lite | lab-01 (primary), lab-02 (applied), lab-03 (troubleshoot) |
| 1.8 | Describe BFD | lab-00 (applied via PBR track), lab-02 (applied), lab-03 (troubleshoot) |

## Design Decisions

- **Diamond topology serves both topics.** PBR needs two competing next-hops (R3 and R4) to make path selection and failover observable. VRF-Lite needs a PE–PE trunk (R2–R4) and two CEs. The same 5-router diamond covers both without adding routers — R3 is simply idle in the VRF-Lite lab.
- **`verify-availability` is mandatory in PBR.** Without it, a route-map `set ip next-hop` sends traffic to a down next-hop and silently black-holes it. With `verify-availability`, IOS checks the track object before applying the set — if the track is Down, the set is skipped and the next route-map sequence is evaluated. This is the mechanism that makes BFD useful in PBR.
- **BFD is paired with PBR, not standalone.** Blueprint 1.8 is describe-only. Rather than a dry vocabulary exercise, BFD is introduced through its operational purpose: it delivers sub-second next-hop failure detection (300ms × 3 = 900ms hold) where OSPF dead timer would take 40s. Students see and measure the difference. Every BFD concept — session, echo mode, timer, discriminator — is observable via `show bfd neighbors detail` during the lab.
- **VRF-Lite uses 802.1Q sub-interfaces for the PE–PE trunk.** A single physical link between R2 and R4 carries both VRFs on separate sub-interfaces. This is the canonical IOS VRF-Lite pattern; it keeps the interface count within iosv limits and shows how VRF-Lite achieves traffic separation without MPLS label switching.
- **Cross-VRF static leaking, not RD/RT import.** iosv without MPLS has no MP-BGP or VPN label mechanism. The correct IOS mechanism for controlled inter-VRF reachability without MPLS is `ip route vrf B <prefix> <nh> vrf A`. This is explicitly within scope for VRF-Lite (it is how real-world VRF-Lite shared services are implemented); it is not a workaround.
- **OSPF inside each VRF (not eBGP PE-CE).** Blueprint 1.7 covers VRF-Lite, not MPLS L3VPN. The PE-CE protocol choice is unrestricted; OSPF keeps the lab focused on VRF mechanics (VRF creation, interface assignment, per-VRF routing process, sub-interface trunk) rather than on BGP attribute manipulation, which belongs in the `bgp` and `mpls-l3vpn` topics.
- **DN-bit is a conceptual note only.** The OSPF downward bit (RFC 4577) is a loop-prevention mechanism that exists specifically when OSPF is the PE-CE protocol inside a full MPLS L3VPN. Lab-01 includes a one-sentence conceptual note about it at the VRF-Lite boundary — enough for the learner to know the concept exists and where it lives — but it cannot be authentically demonstrated without MPLS PE infrastructure. The `mpls-l3vpn` topic owns DN-bit demonstration.
- **Dependency on `ospf`.** OSPF is used in both labs (global area 0 in lab-00; per-VRF in lab-01). The learner is assumed able to configure OSPF already. This topic teaches what happens when OSPF runs inside a VRF context, not how to configure OSPF from scratch.
- **Out of scope (deliberately).** MPLS L3VPN, MP-BGP, Route Distinguisher/Route Target (`mpls-l3vpn`); DMVPN tunnels (`dmvpn`); IPsec (`dmvpn`); full OSPF PE-CE + DN-bit (`mpls-l3vpn`); BFD as a standalone IGP fast-convergence trigger (covered by describing BFD timer mechanics during lab-00, not a separate lab).
