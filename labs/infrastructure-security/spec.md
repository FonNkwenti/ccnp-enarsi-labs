# Infrastructure Security — Lab Specification

## Exam Reference

- **Exam:** Implementing Cisco Enterprise Advanced Routing and Services (300-410)
- **Blueprint Bullets:**
  - 3.1 — Configure and verify device access control
    - (AAA using TACACS+, RADIUS, local; method lists; line application)
  - 3.2 — Configure and verify infrastructure security features
    - 3.2.a — ACLs (standard, extended, time-based)
    - 3.2.b — IPv6 traffic filter
    - 3.2.c — Unicast Reverse Path Forwarding (uRPF)
  - 3.3 — Configure and verify Control Plane Policing (CoPP)
  - 3.4 — Describe IPv6 First Hop Security (RA guard, DHCP guard, binding table, ND inspection/snooping, IPv6 source guard)

Blueprint bullet 3.4 is describe-only. The remaining bullets (3.1, 3.2, 3.3) are configure-and-verify and are fully buildable on iosv. The series is sized accordingly: two progressive learning labs, then two capstones.

## Topology Summary

Four devices on a hub-and-spoke management topology. R1 is the target router (the device under policy). R2 and R3 generate live routing protocol traffic (hellos, LSAs, keepalives) that exercises CoPP classes without any simulation. Linux-Srv provides both TACACS+ and RADIUS AAA services.

- **R1** — AAA client, ACL enforcer, CoPP enforcer. All three labs configure policy here.
- **R2** — OSPF area 0 + EIGRP named-mode neighbor (generates real control-plane traffic for CoPP); source of test traffic for ACL lab.
- **R3** — eBGP peer (AS 65001); generates real BGP keepalives for the CoPP routing class.
- **Linux-Srv** — Ubuntu 20.04. Runs FreeRADIUS (RADIUS) and tacacs+ daemon (TACACS+). Both are pre-configured as a lab prerequisite — the lab exercises IOS AAA configuration, not Linux server administration.

### Physical layout

```
    ┌──────────────┐           ┌──────────────────────────────────────┐
    │     R2       │           │                R1                    │
    │ Lo0 10.2.2.2 │           │ Lo0 10.1.1.1                        │
    │ OSPF + EIGRP │           │ AAA client, ACL+uRPF, CoPP target   │
    └──────┬───────┘           └──────┬───────┬───────────┬──────────┘
           │ Gi0/1 (L1)               │ Gi0/1 │ Gi0/2     │ Gi0/3
    10.12.0.0/30                      │       │           │
    OSPF area 0 + EIGRP AS 100        │       │  10.13.0  │   192.168.100.0/30
                                      │       │  .0/30    │
                               ────────        │           │
                                               │           └──────────────┐
                                     ┌─────────┴──────┐    ┌─────────────┴────┐
                                     │      R3        │    │    Linux-Srv     │
                                     │ Lo0 10.3.3.3   │    │ eth0             │
                                     │ eBGP AS 65001  │    │ FreeRADIUS +     │
                                     └────────────────┘    │ TACACS+ daemon   │
                                                           └──────────────────┘
```

Key relationships:
- L1 runs both OSPF and EIGRP simultaneously — this gives CoPP two routing-protocol classes to police from one link, avoiding extra topology complexity
- L2 (R1-R3) carries only eBGP — a single keepalive/open exchange is enough to exercise the CoPP BGP class-map
- L3 is an out-of-band management link — no routing protocol runs on it; it exists only so R1 can reach the AAA server
- IPv6 dual-stack on L1 and L2 (lab-01 onward) using `2001:db8:12::/64` and `2001:db8:13::/64`

### Interface-level IP plan

| Link | Endpoint A | Endpoint B | Subnet | Purpose |
|------|------------|------------|--------|---------|
| L1 | R1 Gi0/1 (.1) | R2 Gi0/1 (.2) | 10.12.0.0/30 | OSPF area 0 + EIGRP AS 100 |
| L2 | R1 Gi0/2 (.1) | R3 Gi0/1 (.2) | 10.13.0.0/30 | eBGP AS 65000 (R1) <-> AS 65001 (R3) |
| L3 | R1 Gi0/3 (.1) | Linux-Srv eth0 (.2) | 192.168.100.0/30 | AAA management — out-of-band only |

Loopback0: R1 `10.1.1.1/32`, R2 `10.2.2.2/32`, R3 `10.3.3.3/32`. Linux-Srv has no loopback; it is reachable only via L3.

IPv6 loopbacks (lab-01 onward): R1 `2001:db8::1/128`, R2 `2001:db8::2/128`, R3 `2001:db8::3/128`.

### Routing plan

- **OSPF process 1, area 0:** R1 Gi0/1, R1 Lo0, R2 Gi0/1, R2 Lo0. Adjacency established in lab-01 as a pre-requisite; used primarily to generate real hello/LSA traffic for CoPP.
- **EIGRP named-mode, instance SECURITY, ASN 100:** R1 Gi0/1, R2 Gi0/1. Dual-protocol on L1 gives the CoPP COPP-ROUTING class two distinct hello sources.
- **eBGP:** R1 (AS 65000) <-> R3 (AS 65001) over L2. BGP keepalives provide the third routing protocol stream for CoPP verification.
- **No routing on L3:** Linux-Srv is statically reachable via R1 Gi0/3; it is not an OSPF/EIGRP/BGP participant.

### AAA plan

| Parameter | Value |
|-----------|-------|
| AAA server IP | 192.168.100.2 (Linux-Srv eth0) |
| TACACS+ shared key | TACACS-KEY |
| RADIUS shared key | RADIUS-KEY |
| Local fallback user | admin / Cisco123! (privilege 15) |
| Method order | TACACS+ → RADIUS → local |
| Pre-requisite | FreeRADIUS and tacacs+ daemons pre-configured on Linux-Srv before lab-00 starts |

### CoPP class-map plan

| Class | Match | Police rate |
|-------|-------|-------------|
| COPP-ROUTING | ACL matching OSPF + EIGRP + BGP | 1 000 000 bps |
| COPP-SSH-TELNET | ACL matching TCP 22 and TCP 23 | 128 000 bps |
| COPP-HTTP | ACL matching TCP 80 and TCP 443 | 32 000 bps |
| COPP-SNMP | ACL matching UDP 161/162 | 32 000 bps |
| class-default | any remaining | 8 000 bps |

The routing class police rate (1 Mbps) is set well above the actual hello rate so routing adjacencies remain up throughout the lab. Students verify conforming counters — not drops — on the routing class. Drops on COPP-SSH-TELNET are demonstrated deliberately by scripting rapid SSH attempts from R2.

## Lab Progression

| # | Folder | Title | Difficulty | Time | Type | Blueprint Refs | Devices |
|---|--------|-------|-----------|------|------|----------------|---------|
| 00 | lab-00-aaa | IOS AAA (TACACS+, RADIUS, local authentication) | Foundation | 75m | progressive | 3.1 | R1, Linux-Srv |
| 01 | lab-01-acls-urpf | ACLs (IPv4/IPv6, time-based) and uRPF | Intermediate | 90m | progressive | 3.2, 3.2.a, 3.2.b, 3.2.c | R1, R2, R3 |
| 02 | lab-02-copp-ipv6-fhs | CoPP and IPv6 First Hop Security | Intermediate | 105m | progressive | 3.3, 3.4 | R1, R2, R3 |
| 03 | lab-03-capstone-config | Infrastructure Security Full Configuration — Capstone I | Advanced | 120m | capstone_i | 3.1, 3.2, 3.2.a, 3.2.b, 3.2.c, 3.3, 3.4 | R1, R2, R3, Linux-Srv |
| 04 | lab-04-capstone-troubleshooting | Infrastructure Security Comprehensive Troubleshooting — Capstone II | Advanced | 120m | capstone_ii | 3.1, 3.2, 3.2.a, 3.2.b, 3.2.c, 3.3, 3.4 | R1, R2, R3, Linux-Srv |

### lab-00 — IOS AAA (75 min)

Progressive build on R1 + Linux-Srv only. No routing protocols in scope yet — this lab is purely about authentication configuration.

Milestones:
1. Enable `aaa new-model` and create local user `admin privilege 15 secret Cisco123!`. Confirm local login works on console before touching server config.
2. Configure TACACS+ server group pointing to 192.168.100.2, key `TACACS-KEY`. Confirm `show aaa servers` shows the server.
3. Configure RADIUS server group pointing to 192.168.100.2, key `RADIUS-KEY`. Confirm `show aaa servers` shows both servers.
4. Build method list: `aaa authentication login default group tacacs+ group radius local`. Apply to console and VTY lines.
5. Test successful TACACS+ login. Simulate TACACS+ daemon failure (stop the daemon on Linux-Srv) — confirm login falls through to RADIUS, then to local.
6. Verify with `show aaa servers`, `show aaa sessions`, `debug aaa authentication`.

Key teaching point: **TACACS+ encrypts the entire packet body (including the username); RADIUS encrypts only the password field.** Both deliver authentication, authorization, and accounting, but their security models differ in what is visible to a packet capture. This distinction is directly examinable.

### lab-01 — ACLs and uRPF (90 min)

Progressive extension of lab-00. Brings up routing protocols, then layers ACLs and uRPF on top.

Milestones:
1. Bring up OSPF area 0 on L1 and eBGP on L2. Confirm loopback reachability as a baseline before applying any filters.
2. **Extended IPv4 ACL:** permit selected source/destination/port combinations; deny Telnet (TCP 23); apply inbound on R1 Gi0/1. Verify with `show ip access-lists` hit counts.
3. **Standard IPv4 ACL (VTY access-class):** permit only R2 Lo0 (10.2.2.2) to reach R1 VTY lines. Apply with `access-class` on the VTY. Confirm R3 cannot Telnet/SSH to R1 management.
4. **Time-based ACL (3.2.a):** define a time-range `BUSINESS-HOURS` Mon-Fri 08:00-18:00; permit HTTP (TCP 80) only within that window; apply inbound. Test with `show clock` to confirm time-range is active or inactive.
5. **IPv6 traffic filter (3.2.b):** configure dual-stack on L1 (using `2001:db8:12::/64`); write an `ipv6 access-list` blocking ICMPv6 echo-requests from `2001:db8:12::/64`; apply inbound on R1 Gi0/1. Verify with `show ipv6 access-list`.
6. **uRPF strict mode (3.2.c):** `ip verify unicast source reachable-via rx` on R1 Gi0/1. Generate traffic from R2 with a spoofed source address not in R1's routing table — confirm uRPF drops it. Switch to loose mode and observe the behavioral difference.
7. Verify end-state: `show ip access-lists`, `show ipv6 access-list`, `show ip verify unicast source`, `show clock`.

### lab-02 — CoPP and IPv6 FHS (105 min)

Progressive extension of lab-01. Adds EIGRP on L1 (so CoPP has OSPF + EIGRP simultaneously), then applies CoPP using MQC.

Milestones:
1. Enable EIGRP named-mode (instance SECURITY, ASN 100) on R1 and R2 Gi0/1. Confirm both OSPF and EIGRP adjacencies are up — this gives the COPP-ROUTING class two live hello streams.
2. **Define CoPP class-maps using MQC:** one extended ACL per traffic class; `match ip address <acl>` in each class-map.
3. **Build policy-map COPP-POLICY:** police each class at the rates from the plan. Use `conform-action transmit exceed-action drop` on management classes, `conform-action transmit exceed-action transmit` on the routing class (so policing doesn't kill adjacencies).
4. **Apply:** `service-policy input COPP-POLICY` under `control-plane`.
5. Verify R2's OSPF/EIGRP hellos and R3's BGP keepalives are conforming via `show policy-map control-plane`. Confirm no routing neighbor drops.
6. Simulate a rapid SSH burst from R2 toward R1 (e.g., `for` loop of connections). Observe the drop counter increment on COPP-SSH-TELNET.
7. **IPv6 FHS (describe-only, blueprint 3.4):** work through the binding table concept (SISF — Source IP / MAC / VLAN / interface tuple), RA guard (drop RAs arriving on access ports), DHCP guard (drop DHCPv6 server replies on access ports), ND inspection, and IPv6 source guard. Present the reference CLI for each feature and explain the `show ipv6 neighbors binding` output. Note clearly that a buildable FHS demo requires an L2 switch plus a rogue-host VM not present in this topology.

### lab-03 — Capstone I: Full Configuration (120 min)

Clean slate. Student builds every layer from scratch.

Success criteria:
- `show ip ospf neighbor` and `show ip eigrp neighbors` and `show bgp summary` — all adjacencies established
- `show aaa servers` — both TACACS+ and RADIUS servers reachable and counting auth requests
- `show ip access-lists` — ACLs applied in correct direction with hit counts on expected traffic
- `show ip verify unicast source` — uRPF strict mode active on Gi0/1
- `show policy-map control-plane` — all five classes present; routing class shows conforming traffic, no drops; COPP-SSH-TELNET shows drops after a burst test

### lab-04 — Capstone II: Layered Troubleshooting (120 min)

Clean slate. Working configuration pre-loaded then broken by the `fault-injector` skill at build time. Student diagnoses layer by layer.

#### Planned fault categories for Capstone II

| Layer | Candidate faults |
|-------|------------------|
| AAA | TACACS+ server key mismatch (auth silently fails, no fallback unless local is reachable); RADIUS UDP port wrong (1812 vs 1645); `aaa authentication login` method list not applied to VTY; `aaa new-model` disabled. |
| ACL | ACL applied outbound instead of inbound; extended ACL with `deny any` before the permit entries; access-class blocking management traffic from the right host; IPv6 ACL bound to wrong interface; time-range name mismatch. |
| uRPF | uRPF mode set to `loose` when `strict` is required (spoofed traffic passes); uRPF applied on wrong interface; uRPF enabled on an asymmetric-path interface causing legitimate traffic drops. |
| CoPP | COPP-ROUTING police rate set too low (5 Kbps) — OSPF/EIGRP adjacencies flap; wrong class-map match ACL misses the protocol; policy-map applied under global config instead of `control-plane`; `conform-action drop` on routing class. |
| IPv6 filter | IPv6 ACL permits instead of denies; ACL applied in wrong direction; wrong prefix length in the match condition. |

Each fault produces a visible symptom (adjacency flap, management lockout, ACL pass-through, wrong CoPP drops) while the root cause sits at exactly one layer — forcing layer-appropriate verification commands rather than guessing.

## Blueprint Coverage Matrix

| Blueprint Bullet | Description | Covered In |
|-----------------|-------------|------------|
| 3.1 | AAA: TACACS+, RADIUS, local; method lists; line application | lab-00 (primary), lab-03, lab-04 |
| 3.2 | Infrastructure security features | lab-01 (primary), lab-03, lab-04 |
| 3.2.a | Standard and extended IPv4 ACLs, time-based ACLs | lab-01 (primary), lab-03, lab-04 |
| 3.2.b | IPv6 traffic filter | lab-01 (primary), lab-03, lab-04 |
| 3.2.c | Unicast Reverse Path Forwarding (uRPF strict and loose) | lab-01 (primary), lab-03, lab-04 |
| 3.3 | Control Plane Policing (MQC: class-maps, policy-map, control-plane application) | lab-02 (primary), lab-03, lab-04 |
| 3.4 | IPv6 First Hop Security (describe-only): RA guard, DHCP guard, binding table, ND inspection/snooping, IPv6 source guard | lab-02 (describe section) |

## Control Plane vs Data Plane — the mental model this series teaches

Infrastructure Security spans three distinct feature areas. A student who "understands" this blueprint section can place every command and show output in exactly one row of this table:

| Area | Mechanism | What it controls | Key verification |
|------|-----------|-----------------|-----------------|
| Authentication | **AAA method list** (TACACS+ → RADIUS → local) | Who can log in and in what order the servers are tried | `show aaa servers`, `debug aaa authentication` |
| Traffic filtering (data plane) | **ACL / IPv6 traffic filter / uRPF** | Which packets are forwarded or dropped based on headers | `show ip access-lists`, `show ipv6 access-list`, `show ip verify unicast source` |
| Traffic filtering (control plane) | **CoPP** | Which packets reach the router CPU and at what rate | `show policy-map control-plane` |
| L2 host protection (describe-only) | **IPv6 FHS** (SISF binding table + guard policies) | Which L2 hosts are trusted to source RAs / DHCPv6 offers / NDP traffic | `show ipv6 neighbors binding`, `show ipv6 dhcp guard policy` |

The critical insight for exam performance: ACLs filter the **data plane** (transit traffic); CoPP filters the **control plane** (traffic destined for the router CPU). Both use ACL syntax for matching, but they apply at different processing stages and use different verification commands. Students who conflate them will mis-diagnose CoPP drops as ACL issues and vice versa.

## Design Decisions

- **R2 runs both OSPF and EIGRP on L1.** Dual-protocol on a single link gives CoPP two real hello streams to police without adding a fourth router. The EIGRP named-mode instance (`SECURITY`) also reinforces named-mode syntax from the EIGRP topic.
- **R3 is eBGP-only.** A single eBGP session to a separate AS produces real BGP keepalives without complicating the topology. R3 never participates in OSPF or EIGRP, which keeps the CoPP class-map matching clean and unambiguous.
- **Linux-Srv hosts both TACACS+ and RADIUS.** ISE is not available on this EVE-NG host. Ubuntu 20.04 with `apt install tacacs+` and `apt install freeradius` provides both daemon types at zero additional license cost. Both daemons are pre-configured as a prerequisite (outside the lab timer) so the lab focuses entirely on IOS-side configuration, not Linux server administration.
- **AAA lab uses only R1 + Linux-Srv.** Bringing up routing protocols before the AAA lab would let a mis-configured method list accidentally lock the student out of the router with no recovery path. Isolating AAA to two devices means recovery is straightforward: console access is always available.
- **lab-01 starts with routing pre-built.** The ACL lab builds on lab-00's AAA config and adds routing protocols as step 1. This ensures that ACL misconfigurations do not block console access (AAA is already working) and gives the student a clean baseline ping before applying filters.
- **uRPF strict mode on Gi0/1 (toward R2).** The OSPF/EIGRP topology ensures R2's real source addresses are always in R1's routing table, so uRPF strict mode passes legitimate traffic. The spoofed-source test uses an address not in the table — students see exactly one drop counter increment per spoofed packet, making the feature behavior unambiguous.
- **CoPP routing class uses conform-action transmit exceed-action transmit.** The police rate (1 Mbps) is far above the actual hello rate, so both actions effectively transmit. This is intentional: students observe conforming counters climbing without seeing adjacency drops, which lets them focus on the CoPP mechanics rather than fire-fighting flapping neighbors. The SSH burst test (rapid connections to R1) deliberately triggers exceed/violating counters on COPP-SSH-TELNET — that is the designed observable outcome.
- **IPv6 FHS is describe-only (blueprint 3.4).** `IOSvL2` FHS commands (`ipv6 nd raguard`, `ipv6 dhcp guard`, `ipv6 snooping policy`) cannot be meaningfully validated without: (a) an L2 switch node generating rogue RAs or DHCPv6 server replies, and (b) a host VM generating rogue traffic. Neither is available in this topology. lab-02 covers the feature conceptually with reference CLI and documented show-command output drawn from Cisco documentation. This is consistent with the blueprint's "describe" verb for 3.4.
- **Five labs, not three.** Unlike MPLS (two describe-only bullets, 3 labs), the infrastructure-security bullets are configure-and-verify at 3.1, 3.2, and 3.3. Three distinct feature areas that each need their own progressive build, plus two capstones, yields the minimum number of labs needed to build and exercise every configurable bullet exactly once before the capstones re-test them from a clean slate.
- **Out of scope (deliberately).**
  - **Zone-Based Firewall (ZBF)** — not in 3.1–3.4.
  - **IOS-XE AAA with YANG/NETCONF** — out of scope for this exam.
  - **RADIUS attribute manipulation / TACACS+ authorization (exec privilege)** — the blueprint covers authentication; advanced authorization profiles and CoA are not listed.
  - **SNMPv3 auth/priv** — covered in the `infrastructure-services` topic.
  - **DAI (Dynamic ARP Inspection)** — an IPv4 FHS feature; not listed in 3.4 (which is IPv6 FHS only).
  - **DHCP snooping** — also infrastructure-services scope, not infrastructure-security per the blueprint breakdown.
- **Dependency note.** This topic has no hard prerequisite, but the ACL and CoPP labs assume the student understands OSPF adjacencies (used as the live traffic generator). Running the `ospf` topic first is strongly recommended.
