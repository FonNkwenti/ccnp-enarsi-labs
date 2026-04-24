# DMVPN (single hub) — Lab Specification

## Exam Reference

- **Exam:** Implementing Cisco Enterprise Advanced Routing and Services (300-410)
- **Blueprint Bullets:**
  - 2.3 — Configure and verify DMVPN (single hub)
    - 2.3.a — GRE/mGRE
    - 2.3.b — NHRP
    - 2.3.c — IPsec
    - 2.3.d — Dynamic neighbor
    - 2.3.e — Spoke-to-spoke

Single-hub, IPv4-only DMVPN. The series walks from Phase 1 (hub-and-spoke only) to Phase 3 (spoke-to-spoke shortcuts with IPsec) in two learning labs, then exercises the full stack in a build capstone and a troubleshoot capstone.

## Topology Summary

Four iosv routers:

- **R1 — DMVPN hub / NHRP Next-Hop Server (NHS).** Represents HQ.
- **R2, R3 — DMVPN spokes.** Represent Branch A and Branch B.
- **R4 — simulated ISP / transit.** Provides underlay connectivity only; R4 is never a DMVPN member and knows nothing about tunnels, NHRP, or OSPF.

All four are `iosv` (IPsec is confirmed-working on this image per `eve-ng/SKILL.md`). No optional devices — every lab uses the same 4-router topology, so every `show` command lands on the same place every time.

### Physical layout (underlay) and overlay (tunnel)

```
                       ┌──────────────────────┐
                       │         R4           │
                       │  "ISP" / transit     │
                       │  Lo0 4.4.4.4/32      │
                       └──┬────────┬────────┬─┘
                Gi0/0 (L1)│  Gi0/1 │(L2)    │Gi0/2 (L3)
            203.0.113.0/30│  198.51│.100.0/30│  192.0.2.0/30
                          │        │        │
                 ┌────────┴──┐ ┌───┴───┐ ┌──┴────────┐
                 │    R1     │ │  R2   │ │    R3     │
                 │ HUB / NHS │ │ Spoke1│ │ Spoke2    │
                 │ Lo0       │ │ Lo0   │ │ Lo0       │
                 │ 10.1.1.1  │ │10.2.2.│ │ 10.3.3.3  │
                 │ Tu0       │ │ Tu0   │ │ Tu0       │
                 │ 10.100.0.1│ │.0.2   │ │ .0.3      │
                 └───────────┘ └───────┘ └───────────┘

    Overlay (mGRE + NHRP, 10.100.0.0/24) runs on top of the underlay above
```

Key relationships (what the diagram can't show):
- `tunnel source` on each member = its Gi0/0 (underlay)
- `tunnel destination` is **absent** on mGRE — NHRP resolves next-hop NBMA on demand
- NHRP `nbma` addresses used in the hub's dynamic table are the members' public IPs (203.0.113.1, 198.51.100.1, 192.0.2.1) — not their Tu0 addresses
- OSPF neighbors form over Tu0 (overlay), never over Gi0/0 (underlay)

### Interface-level IP plan

| Link | Endpoint A | Endpoint B | Subnet | Purpose |
|------|------------|------------|--------|---------|
| L1 | R1 Gi0/0 (.1) | R4 Gi0/0 (.2) | 203.0.113.0/30 | Hub underlay uplink |
| L2 | R2 Gi0/0 (.1) | R4 Gi0/1 (.2) | 198.51.100.0/30 | Spoke1 underlay uplink |
| L3 | R3 Gi0/0 (.1) | R4 Gi0/2 (.2) | 192.0.2.0/30 | Spoke2 underlay uplink |

Tunnel overlay (all members): `10.100.0.0/24`, with R1=`10.100.0.1/24`, R2=`10.100.0.2/24`, R3=`10.100.0.3/24`.

Loopback LANs: R1 `10.1.1.1/24`, R2 `10.2.2.2/24`, R3 `10.3.3.3/24`. These represent the site LANs behind each router and are what end-to-end ping tests target.

Why TEST-NET for underlay: the 203.0.113/198.51.100/192.0.2 prefixes are RFC 5737 documentation ranges. Using them for the underlay makes the underlay-vs-overlay split obvious at a glance in every show command.

### Underlay routing

Static. Each DMVPN member has a single `ip route 0.0.0.0 0.0.0.0 <R4 neighbor IP>`. R4 has nothing but connected routes. This is deliberate — running an IGP in the underlay would entangle with the overlay OSPF and teach the wrong lesson.

### Overlay routing (on the tunnel)

OSPF process 100, area 0, `ip ospf network point-to-multipoint` on every Tu0. This is the only network type that works cleanly for both Phase 1 and Phase 3 without DR election drama, and it does not require `ip ospf priority 0` gymnastics on spokes.

### NHRP baseline parameters

- `ip nhrp network-id 100` (identical on all members; must match)
- `ip nhrp authentication ENARSI` (optional but trains the student on the command)
- Hub: `ip nhrp map multicast dynamic`, `ip nhrp hold time 300`
- Spoke: `ip nhrp nhs <hub tunnel IP>`, `ip nhrp map <hub tunnel IP> <hub NBMA>`, `ip nhrp map multicast <hub NBMA>`

### IPsec baseline (applied from lab-01 onward)

- IKEv1 with pre-shared key `cisco123` (iosv is known-good for IKEv1; IKEv2 on this image is not a requirement of the blueprint)
- ISAKMP: AES-256 / SHA-256 / DH group 14 / lifetime 86400
- IPsec transform-set: `esp-aes 256 esp-sha256-hmac`, transport mode (tunnel mode would double-encapsulate)
- Applied via `tunnel protection ipsec profile DMVPN-PROFILE` — same profile on hub and spokes

## Lab Progression

| # | Folder | Title | Difficulty | Time | Type | Blueprint Refs | Devices |
|---|--------|-------|-----------|------|------|----------------|---------|
| 00 | lab-00-phase1-hub-spoke | DMVPN Phase 1 — Hub-and-Spoke with mGRE and NHRP | Foundation | 90m | progressive | 2.3, 2.3.a, 2.3.b, 2.3.d | R1, R2, R3, R4 |
| 01 | lab-01-phase3-shortcuts | DMVPN Phase 3 — Spoke-to-Spoke Shortcuts with IPsec Protection | Intermediate | 90m | progressive | 2.3, 2.3.a, 2.3.b, 2.3.c, 2.3.e | R1, R2, R3, R4 |
| 02 | lab-02-capstone-config | DMVPN Full Configuration Mastery — Capstone I | Advanced | 120m | capstone_i | all 2.3.* | R1, R2, R3, R4 |
| 03 | lab-03-capstone-troubleshooting | DMVPN Comprehensive Troubleshooting — Capstone II | Advanced | 120m | capstone_ii | all 2.3.* | R1, R2, R3, R4 |

### lab-00 — Phase 1 Hub-and-Spoke (90 min)

Progressive build. End state: all three DMVPN members have a working mGRE tunnel, NHRP is registered, OSPF adjacencies are up over the tunnel, and end-to-end ping between any two loopbacks works. Spoke-to-spoke traffic traverses the hub — traceroute from R2 Lo0 to R3 Lo0 shows R1 in the middle.

Key teaching points:
1. **Underlay first, overlay second.** Verify R1-R2-R3 can ping each other's public IPs via R4 *before* configuring a single tunnel command. Without this, every later symptom looks like an NHRP problem.
2. **mGRE on everything.** Both hub and spokes use `tunnel mode gre multipoint`. This is the modern baseline and means lab-01 only needs to *add* NHRP redirect/shortcut — not change tunnel mode. The Phase 1 vs Phase 3 distinction is an NHRP-behavior distinction, not a tunnel-mode distinction.
3. **"Dynamic neighbor" (2.3.d) means dynamic NHRP registration.** Spokes come and go without any reconfiguration on the hub — this is the whole point of NHRP's `map multicast dynamic`. `show ip nhrp` on the hub shows spoke entries appearing automatically.
4. **OSPF network type point-to-multipoint.** Treat the tunnel as a collection of point-to-point adjacencies. No DR/BDR. Works identically in Phase 1 and Phase 3.

### lab-01 — Phase 3 Shortcuts + IPsec (90 min)

Progressive extension of lab-00. Two changes, both purely additive per the skill's config-chaining rule:

1. **Enable Phase 3 shortcuts.** Add `ip nhrp redirect` on the hub tunnel, and `ip nhrp shortcut` on each spoke tunnel. When a spoke sends traffic destined for another spoke, the hub forwards the first packet *and* sends an NHRP redirect; the ingress spoke then resolves the egress spoke's NBMA directly and installs a shortcut in CEF. Traceroute from R2 Lo0 to R3 Lo0 goes from "via R1" to "direct" after the first packet.
2. **Add IPsec protection.** Configure ISAKMP policy + PSK (keyring/crypto keyring if using `isakmp profile`), IPsec transform-set, IPsec profile, then `tunnel protection ipsec profile DMVPN-PROFILE` on each tunnel interface. All tunnels — hub-to-spoke and spoke-to-spoke — are now encrypted.

Key teaching point: **Phase 3 doesn't require changing the tunnel mode.** Students who believe Phase 1 = p2p GRE and Phase 3 = mGRE will be confused — the real line is NHRP behavior.

### lab-02 — Capstone I (120 min)

Clean slate (addressing + default routes only). Build the whole Phase 3 + IPsec stack from scratch, including every 2.3.* bullet in one deployment.

Success criteria:
- `R2# traceroute 10.3.3.3 source Lo0` — first attempt shows R1 in the path, subsequent attempts go directly spoke-to-spoke
- `R1# show dmvpn detail` — dynamic spoke entries for both spokes
- `R2# show crypto ipsec sa peer 192.0.2.1` — encrypted SA to R3's NBMA address after shortcut resolution
- `R1# show ip ospf neighbor` — two adjacencies, one per spoke, on Tu0

### lab-03 — Capstone II: Layered Troubleshooting (120 min)

Clean slate. Pre-loaded working configuration then broken by the `fault-injector` skill in Phase 3. Faults are chosen at build time from the candidate list below; this spec fixes the *layers* so the learning coverage is predictable.

#### Planned fault categories for Capstone II

| Layer | Candidate faults |
|-------|------------------|
| Underlay (L3 transport) | Missing default route on a spoke; wrong public IP on a spoke; R4 interface shutdown; MTU misconfig on an underlay interface. |
| mGRE | `tunnel source` pointing at the wrong interface; `tunnel key` mismatch between hub and one spoke; tunnel interface `shutdown`; missing `tunnel mode gre multipoint` on one node. |
| NHRP | Mismatched `network-id` on one spoke; missing `ip nhrp nhs` on a spoke; missing `ip nhrp map multicast` to the hub NBMA (OSPF hellos die silently); `ip nhrp authentication` mismatch. |
| IPsec | ISAKMP PSK mismatch (phase 1 never completes); transform-set mismatch (phase 2 fails); IPsec profile not applied to one tunnel interface; ISAKMP policy DH group mismatch. |
| OSPF overlay | `ip ospf network broadcast` on a spoke (DR election fails on p2mp); OSPF hello-interval mismatch; OSPF `passive-interface tunnel0` on a spoke. |
| Phase 3 behavior | `ip nhrp redirect` removed from hub (shortcuts never get triggered); `ip nhrp shortcut` removed from a spoke (the spoke never installs CEF shortcuts even when the hub redirects). |

Each fault is chosen so the user-visible symptom at the spoke CLI (ping/traceroute failure or unexpected path) is clear, while the root cause sits at exactly one layer — forcing layer-appropriate show commands instead of guessing.

## Blueprint Coverage Matrix

| Blueprint Bullet | Description | Covered In |
|-----------------|-------------|------------|
| 2.3 | Configure and verify DMVPN (single hub) | lab-00, lab-01, lab-02, lab-03 |
| 2.3.a | GRE / mGRE | lab-00 (primary), lab-01, lab-02, lab-03 |
| 2.3.b | NHRP (registration, mapping, redirect, shortcut) | lab-00 (registration/mapping), lab-01 (redirect/shortcut), lab-02, lab-03 |
| 2.3.c | IPsec (ISAKMP, IPsec profile, tunnel protection) | lab-01 (primary), lab-02, lab-03 |
| 2.3.d | Dynamic neighbor (NHRP dynamic spoke registration at hub) | lab-00 (primary), lab-02, lab-03 |
| 2.3.e | Spoke-to-spoke (NHRP-resolved direct tunnels) | lab-01 (primary), lab-02, lab-03 |

## Control Plane vs Data Plane — the mental model this series teaches

DMVPN packs several protocols into one interface. The student needs to keep them straight.

| Plane | Protocol | Role |
|-------|----------|------|
| Control | **NHRP** | Registers spoke NBMA -> tunnel mappings at the hub, redirects first packet, resolves spoke-to-spoke shortcuts |
| Control | **OSPF (overlay)** | Advertises LAN loopbacks across the tunnel; learns that R3's 10.3.3.0/24 is reachable via 10.100.0.3 |
| Control | **IKE / ISAKMP** | Negotiates IPsec SAs between NBMA peers before data can flow encrypted |
| Data | **mGRE** | Encapsulates inner IP packets inside GRE with a dynamically-resolved NBMA destination |
| Data | **IPsec (ESP, transport mode)** | Encrypts the GRE payload between NBMA peers |
| Data | **CEF shortcut (Phase 3 only)** | Installs the NHRP-resolved next-hop so subsequent spoke-to-spoke packets skip the hub |

Every lab milestone and every Capstone II fault maps to exactly one cell in this table. That mapping is what "understanding DMVPN" looks like in practice.

## Design Decisions

- **4-device topology (R1 hub, R2/R3 spokes, R4 transit).** Minimum needed to show all 2.3.* bullets — you need at least two spokes to demonstrate spoke-to-spoke, and you need a distinct transit node so the underlay is visibly separate from the overlay. No optional devices; every lab uses all four.
- **iosv on all four.** `eve-ng/SKILL.md` confirms iosv supports GRE and IPsec. csr1000v would work too but costs ~6x the RAM for no pedagogical gain on this blueprint.
- **mGRE everywhere from lab-00.** Students sometimes learn "Phase 1 = p2p GRE spokes, Phase 3 = mGRE spokes." That's historically true but not how modern DMVPN is built, and it would force lab-01 to *remove* `tunnel mode gre` commands — a violation of the skill's "only add config between labs" rule. Treating Phase 1 vs Phase 3 as an NHRP-behavior distinction (no redirect/shortcut vs redirect+shortcut) keeps the progression clean and matches current practice.
- **OSPF point-to-multipoint on the tunnel.** Works identically for Phase 1 and Phase 3, avoids DR/BDR election over a mGRE mesh (where election behavior depends on who booted first), and does not require `ip ospf priority 0` tricks on spokes. The blueprint does not dictate a network type; this is the simplest correct choice.
- **Static underlay routing, no IGP.** Running an IGP in the underlay would make every troubleshooting exercise ambiguous ("is OSPF failing in the underlay or the overlay?"). A single static default per member keeps the layers separate.
- **Single IGP in the overlay (OSPF).** The topic depends on the OSPF topic; reusing OSPF here gives the student one fewer moving part to learn.
- **IKEv1 PSK, not IKEv2 or certificates.** iosv is rock-solid for IKEv1; IKEv2 on this image varies by sub-version. The blueprint says "IPsec" — not "IKEv2" — so IKEv1 is in-scope. Certificates would add PKI setup without teaching anything new about DMVPN.
- **IPsec transport mode, not tunnel mode.** GRE is already doing the outer encapsulation. Wrapping it again in IPsec tunnel mode would add a pointless second IP header. Transport mode is the canonical DMVPN choice.
- **Out of scope (deliberately).**
  - **Dual-hub DMVPN** — the blueprint explicitly says "single hub."
  - **Phase 2** — deprecated; the industry moved to Phase 3. The blueprint does not reference Phase 2.
  - **Front-door VRF (FVRF)** — valuable but out of scope for the describe-plus-configure bullet set here.
  - **EIGRP or BGP overlay** — OSPF covers the blueprint requirement; alternative IGPs would add scope without changing what DMVPN is doing.
  - **DMVPN over IPv6** — not listed in 2.3.*.
  - **Per-tunnel QoS / NHRP group features** — advanced design, beyond 300-410.
- **Dependency on OSPF topic.** The student has already configured OSPF in the `ospf` topic; this series reuses OSPF only as the overlay IGP and does not re-teach it from scratch.
