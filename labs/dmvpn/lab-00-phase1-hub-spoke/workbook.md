# DMVPN Lab 00 — Phase 1: Hub-and-Spoke with mGRE and NHRP

## Table of Contents

1. [Concepts & Skills Covered](#1-concepts--skills-covered)
2. [Topology & Scenario](#2-topology--scenario)
3. [Hardware & Environment Specifications](#3-hardware--environment-specifications)
4. [Base Configuration](#4-base-configuration)
5. [Lab Challenge: Core Implementation](#5-lab-challenge-core-implementation)
6. [Verification & Analysis](#6-verification--analysis)
7. [Verification Cheatsheet](#7-verification-cheatsheet)
8. [Solutions (Spoiler Alert!)](#8-solutions-spoiler-alert)
9. [Troubleshooting Scenarios](#9-troubleshooting-scenarios)
10. [Lab Completion Checklist](#10-lab-completion-checklist)
11. [Appendix: Script Exit Codes](#11-appendix-script-exit-codes)

---

## 1. Concepts & Skills Covered

**Exam Objective:** 2.3 — Configure and verify DMVPN (single hub): 2.3.a GRE/mGRE, 2.3.b NHRP, 2.3.d Dynamic neighbor

### DMVPN Architecture and the Two-Layer Model

DMVPN solves a fundamental hub-and-spoke WAN problem: how do you allow branch sites to communicate without pre-configuring a static tunnel to every possible peer? The answer is to split connectivity into two layers that operate independently:

- **Underlay** — the public IP network (in this lab, simulated by R4). Each DMVPN member has one physical/public-side IP address. The underlay carries encrypted GRE packets between NBMA addresses. DMVPN members do not run a routing protocol in the underlay; they use a single static default route pointing at their ISP next-hop.
- **Overlay** — the logical tunnel network (10.100.0.0/24 in this lab). OSPF runs here. Loopback LANs are advertised here. Show commands about routing, reachability, and adjacency all refer to the overlay.

Keeping these two layers mentally separate is the foundation skill for every DMVPN lab. When troubleshooting, the first question is always: "Is the problem in the underlay or the overlay?"

### mGRE — Multipoint GRE

Standard GRE (Generic Routing Encapsulation) requires a static destination: `tunnel destination <ip>`. This means for N spokes, the hub needs N GRE tunnel interfaces — one per spoke.

**Multipoint GRE (mGRE)** removes the static destination. The `tunnel mode gre multipoint` command allows a single tunnel interface to send and receive encapsulated packets to/from any NBMA address. The destination is resolved dynamically by NHRP at forwarding time.

Key distinction for this lab series: **both the hub and the spokes use mGRE**. This is the modern baseline. The Phase 1 vs Phase 3 distinction is purely about NHRP behavior (whether shortcuts are enabled), not about tunnel mode.

```
! Hub and ALL spokes use the same tunnel mode:
interface Tunnel0
 tunnel mode gre multipoint
```

Why not `tunnel mode gre ip` (standard point-to-point GRE) on spokes? Because spoke-to-spoke shortcuts in Phase 3 require each spoke to send packets directly to another spoke's NBMA address. A point-to-point tunnel can only reach one destination — the hub. mGRE enables any-to-any resolution.

### NHRP — Next Hop Resolution Protocol

NHRP is a client-server protocol (RFC 2332). The hub is the **Next-Hop Server (NHS)**; spokes are **Next-Hop Clients (NHC)**.

**Registration sequence (Phase 1):**
1. Spoke boots, creates its mGRE tunnel, and sends an NHRP Registration Request to the hub NHS. The request travels over the underlay using the hub's NBMA (public) IP.
2. Hub receives the registration, records the spoke's tunnel IP → NBMA IP mapping in its NHRP table, and sends a Registration Reply.
3. Spoke is now registered. Hub's `show ip nhrp` shows the spoke as a dynamic entry.

This is what blueprint bullet **2.3.d ("dynamic neighbor")** refers to: spokes register dynamically, without any hub reconfiguration. Add a new spoke, point it at the hub's NHS IP, and it appears in the hub's NHRP table automatically.

**Key NHRP parameters (must match across all members):**

| Parameter | Hub config | Spoke config | Must match? |
|-----------|-----------|--------------|------------|
| `ip nhrp network-id` | 100 | 100 | Yes — same value on all members |
| `ip nhrp authentication` | ENARSI | ENARSI | Yes — mismatch = silent registration failure |
| `ip nhrp map multicast dynamic` | Hub only | n/a | Hub caches spoke NBMA for multicast |
| `ip nhrp map multicast <hub-nbma>` | n/a | Spoke only | Tells spoke where to send OSPF hellos |
| `ip nhrp nhs <hub-tunnel-ip>` | n/a | Spoke only | Points spoke at the NHS |
| `ip nhrp map <hub-tunnel-ip> <hub-nbma>` | n/a | Spoke only | Static mapping so spoke can reach NHS |

### OSPF Point-to-Multipoint on the Overlay

OSPF runs on the tunnel interface (overlay). The network type `ip ospf network point-to-multipoint` is the correct choice for DMVPN because:

1. **No DR/BDR election** — broadcast and non-broadcast network types elect a DR. On a mGRE mesh where any device could be hub or spoke, DR election produces unpredictable results. Point-to-multipoint treats each adjacency as a collection of point-to-point links.
2. **Works identically in Phase 1 and Phase 3** — no reconfiguration needed when enabling shortcuts in lab-01.
3. **Hosts routes in the routing table** — OSPF installs next-hop IPs as /32 host routes for each adjacency, which is exactly what NHRP and CEF need.

OSPF hellos reach spokes via the hub's `ip nhrp map multicast dynamic` — when a spoke registers, the hub adds it to its multicast replication list. Spoke-to-hub OSPF hellos use `ip nhrp map multicast <hub-nbma>` to know where to send multicast.

### Skills this lab develops

| Skill | Description |
|-------|-------------|
| Underlay verification | Confirm NBMA reachability before touching tunnel config |
| mGRE tunnel creation | Configure Tunnel0 with multipoint mode, MTU, source interface |
| NHRP hub config | NHS, dynamic multicast map, authentication, hold-time |
| NHRP spoke config | Static hub mapping, NHS pointer, multicast map to hub |
| OSPF overlay | Point-to-multipoint network type, passive-interface, area 0 |
| Phase 1 behavior analysis | Read traceroute to confirm spoke-to-spoke traffic transits hub |
| DMVPN show commands | show dmvpn, show ip nhrp, show ip ospf neighbor, show dmvpn detail |

---

## 2. Topology & Scenario

**Scenario:** You are a network engineer at GlobalLogix, a company with a headquarters site (HQ) and two branch offices (Branch A and Branch B). The WAN team has recently moved to an internet-based connectivity model and wants to deploy DMVPN Phase 1 as the overlay network. Your task is to bring up the hub-and-spoke DMVPN using mGRE tunnels and NHRP dynamic registration, then verify that all sites can reach each other and that OSPF is distributing LAN reachability across the overlay.

```
                    ┌──────────────────────────────┐
                    │             R4               │
                    │      Simulated ISP/Transit   │
                    │      Lo0: 4.4.4.4/32         │
                    └────────┬────────┬────────────┘
             Gi0/0           │        │           Gi0/2
      203.0.113.2/30         │        │       192.0.2.2/30
                             │Gi0/1   │
                    198.51.100.2/30   │
                             │        │
         203.0.113.1/30      │        │       192.0.2.1/30
              Gi0/0          │        │            Gi0/0
    ┌──────────────────┐     │        │     ┌──────────────────┐
    │       R1         │     │        │     │       R3         │
    │   HUB / NHS      │     │        │     │  Spoke 2         │
    │   HQ Site        │     │        │     │  Branch B        │
    │ Lo0: 10.1.1.1/24 │     │        │     │ Lo0: 10.3.3.3/24 │
    │ Tu0: 10.100.0.1  │     │        │     │ Tu0: 10.100.0.3  │
    └──────────────────┘     │        │     └──────────────────┘
                       198.51.100.1/30│
                             Gi0/0    │
                    ┌─────────────────┘
                    │       R2
                    │   Spoke 1
                    │   Branch A
                    │ Lo0: 10.2.2.2/24
                    │ Tu0: 10.100.0.2
                    └─────────────────

  Overlay tunnel network: 10.100.0.0/24
  Underlay: RFC 5737 documentation ranges (203.0.113/198.51.100/192.0.2)
```

**Phase 1 traffic path (this lab):** Spoke-to-spoke traffic (R2 → R3) transits the hub R1. Traceroute from R2 Loopback0 to R3 Loopback0 will show R1 in the path. This is expected Phase 1 behavior — direct spoke-to-spoke shortcuts are not enabled until lab-01.

---

## 3. Hardware & Environment Specifications

### Device Inventory

| Device | Role | Platform | Image |
|--------|------|----------|-------|
| R1 | DMVPN Hub / NHS (HQ) | IOSv | vios-adventerprisek9-m.SPA.156-2.T |
| R2 | DMVPN Spoke 1 (Branch A) | IOSv | vios-adventerprisek9-m.SPA.156-2.T |
| R3 | DMVPN Spoke 2 (Branch B) | IOSv | vios-adventerprisek9-m.SPA.156-2.T |
| R4 | Simulated ISP/Transit | IOSv | vios-adventerprisek9-m.SPA.156-2.T |

### Cabling

| Link | Device A | Interface A | Device B | Interface B | Subnet | Purpose |
|------|----------|-------------|----------|-------------|--------|---------|
| L1 | R1 | Gi0/0 | R4 | Gi0/0 | 203.0.113.0/30 | Hub underlay uplink |
| L2 | R2 | Gi0/0 | R4 | Gi0/1 | 198.51.100.0/30 | Spoke1 underlay uplink |
| L3 | R3 | Gi0/0 | R4 | Gi0/2 | 192.0.2.0/30 | Spoke2 underlay uplink |

### Console Access

| Device | Port | Connection Command |
|--------|------|--------------------|
| R1 | (see EVE-NG UI) | `telnet <eve-ng-ip> <port>` |
| R2 | (see EVE-NG UI) | `telnet <eve-ng-ip> <port>` |
| R3 | (see EVE-NG UI) | `telnet <eve-ng-ip> <port>` |
| R4 | (see EVE-NG UI) | `telnet <eve-ng-ip> <port>` |

---

## 4. Base Configuration

The following is **pre-loaded** via `setup_lab.py`:

**IS pre-loaded:**
- Hostnames on all devices
- `no ip domain-lookup` on all devices
- Underlay interface IP addresses (Gi0/0 on R1/R2/R3; Gi0/0-2 on R4)
- Loopback0 IP addresses on all devices
- All interfaces set to `no shutdown`

**IS NOT pre-loaded** (student configures this):
- Static default routes on R1, R2, and R3 (underlay reachability toward R4)
- Tunnel0 interface on R1, R2, and R3 (mGRE, MTU, source)
- NHRP configuration on R1 (NHS role), R2, and R3 (NHC role)
- OSPF process 100 overlay routing on R1, R2, and R3
- R4 requires no additional configuration

---

## 5. Lab Challenge: Core Implementation

> Work through these tasks in order. Each task builds on the previous one. Verify the stated condition before moving to the next task.

### Task 1: Verify Underlay Connectivity

Before configuring any tunnel, confirm the public-side underlay is working end-to-end.

- Add a static default route on R1 pointing toward R4 (next-hop: the R4 Gi0/0 address on the 203.0.113.0/30 subnet)
- Add a static default route on R2 pointing toward R4 (next-hop: the R4 Gi0/1 address on the 198.51.100.0/30 subnet)
- Add a static default route on R3 pointing toward R4 (next-hop: the R4 Gi0/2 address on the 192.0.2.0/30 subnet)
- From R2, ping R1's public (Gi0/0) IP address
- From R3, ping R1's public (Gi0/0) IP address
- From R2, ping R3's public (Gi0/0) IP address

**Verification:** All six pings must succeed (5/5 packets) before proceeding. R4 provides transit; no routing config is needed on R4.

---

### Task 2: Configure the Hub mGRE Tunnel Interface

On R1, create a tunnel interface using multipoint GRE mode. This is the DMVPN hub / NHS interface.

- Assign the hub tunnel IP address (10.100.0.1/24)
- Set the tunnel MTU to 1400 and TCP MSS adjust to 1360
- Set the tunnel source to the physical underlay interface (Gi0/0)
- Enable multipoint GRE tunnel mode
- Set the tunnel key to 100
- Disable IP redirects on the tunnel interface
- Configure NHRP: network-id 100, authentication string "ENARSI", hold-time 300
- Configure NHRP to accept dynamic multicast registrations from spokes
- Configure OSPF network type point-to-multipoint on the tunnel
- Configure OSPF area 0 directly on the tunnel interface

**Verification:** `show interface Tunnel0` must show the tunnel is up/up and the tunnel source is Gi0/0 with mode set to GRE multipoint.

---

### Task 3: Configure Spoke mGRE Tunnels and NHRP

On R2 and R3, create matching tunnel interfaces and configure them as NHRP Next-Hop Clients pointing at the hub NHS.

- Assign spoke tunnel IPs: R2 = 10.100.0.2/24, R3 = 10.100.0.3/24
- Set the same MTU (1400) and MSS adjust (1360) as the hub
- Set each spoke's tunnel source to its Gi0/0 underlay interface
- Enable multipoint GRE tunnel mode with tunnel key 100
- Configure NHRP on each spoke:
  - network-id 100 and authentication string "ENARSI" (must match the hub)
  - Static mapping from the hub tunnel IP (10.100.0.1) to the hub NBMA (public) IP (203.0.113.1)
  - Static multicast map to the hub NBMA IP (so OSPF hellos reach the hub)
  - NHS pointer to the hub tunnel IP (10.100.0.1)
- Configure OSPF network type point-to-multipoint and area 0 on each spoke's tunnel

**Verification:** `show ip nhrp` on R1 must show dynamic entries for both R2 and R3 within 30 seconds of the spokes coming up. `show dmvpn` on R1 must show both spokes in state `UP`.

---

### Task 4: Bring Up OSPF Overlay Routing

On R1, R2, and R3, configure OSPF process 100 to advertise the overlay tunnel subnet and each router's Loopback0 LAN network into area 0.

- Configure OSPF with router-IDs matching each Loopback0 address (R1 = 10.1.1.1, R2 = 10.2.2.2, R3 = 10.3.3.3)
- Use `passive-interface default` and then selectively enable OSPF only on Tunnel0
- Advertise the tunnel subnet (10.100.0.0/24) and each Loopback0 network (/24 prefix) into area 0

**Verification:** `show ip ospf neighbor` on R1 must show two FULL adjacencies (one for R2, one for R3). `show ip route ospf` on R2 must show R3's Loopback0 network (10.3.3.0/24) via the hub tunnel IP (10.100.0.1).

---

### Task 5: Verify Phase 1 Behavior (Hub Transit)

Confirm that DMVPN is operating in Phase 1 mode: all spoke-to-spoke traffic transits the hub.

- From R2, ping R3's Loopback0 IP (10.3.3.3) sourced from R2's Loopback0 (10.2.2.2)
- Run a traceroute from R2 Loopback0 to R3 Loopback0 and confirm R1's tunnel IP appears in the path
- Examine `show dmvpn detail` on R1 to confirm both spoke entries are present and UP
- Read `show ip nhrp` on R1 and identify the NBMA-to-tunnel-IP mappings for each spoke

**Verification:** Traceroute from R2 to R3 must show R1's tunnel IP (10.100.0.1) as an intermediate hop. No direct spoke-to-spoke shortcut should form — that is Phase 3 behavior.

---

## 6. Verification & Analysis

### Task 1 — Underlay reachability

```
R2# ping 203.0.113.1
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 203.0.113.1, timeout is 2 seconds:
!!!!!                                                              ! ← 5/5 — underlay R2→R1 working
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms

R3# ping 198.51.100.1
!!!!!                                                              ! ← 5/5 — underlay R3→R2 via R4 working
```

### Task 2 — Hub tunnel interface

```
R1# show interface Tunnel0
Tunnel0 is up, line protocol is up                                 ! ← must be up/up
  Hardware is Tunnel
  Internet address is 10.100.0.1/24                               ! ← correct tunnel IP
  MTU 1400 bytes, BW 1000 Kbit/sec                                ! ← MTU 1400
  Tunnel source 203.0.113.1 (GigabitEthernet0/0),                 ! ← source = Gi0/0 NBMA IP
        destination UNKNOWN, fastswitch TTL 255
  Tunnel protocol/transport multi-GRE/IP                          ! ← mGRE confirmed
  Tunnel key 0x64                                                  ! ← hex 64 = decimal 100
```

### Task 3 — NHRP dynamic registration

```
R1# show ip nhrp
10.100.0.2/32 via 10.100.0.2                                      ! ← R2 spoke entry
   Tunnel0 created 00:01:12, expire 00:04:47
   Type: dynamic, Flags: registered used nhop                     ! ← "dynamic" = auto-registered
   NBMA address: 198.51.100.1                                     ! ← R2's public IP
10.100.0.3/32 via 10.100.0.3                                      ! ← R3 spoke entry
   Tunnel0 created 00:01:08, expire 00:04:51
   Type: dynamic, Flags: registered used nhop                     ! ← "dynamic" = auto-registered
   NBMA address: 192.0.2.1                                        ! ← R3's public IP

R1# show dmvpn
Legend: Attrb --> S - Static, D - Dynamic, I - Incomplete
        N - NATed, L - Local, X - No Socket, T1 - Route Installed, T3 - Not Installed
        # Ent --> Number of NHRP entries with same NBMA peer

                         ----------- DMVPN Sessions -----------
Interface: Tunnel0, IPv4 NHRP Details
Type:Hub, NHRP Peers:2,

 # Ent  Peer NBMA Addr Peer Tunnel Add State  UpDn Tm Attrb
 ----- --------------- --------------- ----- -------- -----
     1 198.51.100.1       10.100.0.2    UP    00:01:12   D    ! ← R2 up, dynamic
     1 192.0.2.1          10.100.0.3    UP    00:01:08   D    ! ← R3 up, dynamic
```

### Task 4 — OSPF overlay adjacencies

```
R1# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
10.2.2.2          1   FULL/  -        00:01:34    10.100.0.2      Tunnel0   ! ← R2 FULL, no DR (p2mp)
10.3.3.3          1   FULL/  -        00:01:31    10.100.0.3      Tunnel0   ! ← R3 FULL, no DR (p2mp)

R2# show ip route ospf
      10.0.0.0/8 is variably subnetted
O     10.1.1.0/24 [110/1001] via 10.100.0.1, 00:01:20, Tunnel0   ! ← R1 LAN via hub
O     10.3.3.0/24 [110/2001] via 10.100.0.1, 00:01:17, Tunnel0   ! ← R3 LAN via hub (Phase 1!)
O     10.100.0.1/32 [110/1000] via 10.100.0.1, 00:01:20, Tunnel0 ! ← hub host route (p2mp behavior)
O     10.100.0.3/32 [110/2000] via 10.100.0.1, 00:01:17, Tunnel0 ! ← R3 host route via hub
```

Note: OSPF installs /32 host routes for each p2mp peer — this is expected and correct.

### Task 5 — Phase 1 spoke-to-spoke transit

```
R2# traceroute 10.3.3.3 source Loopback0
Type escape sequence to abort.
Tracing the route to 10.3.3.3
VRF info: (vrf in name/id, vrf out name/id)
  1 10.100.0.1 4 msec 4 msec 4 msec                              ! ← R1 hub tunnel IP = transit hop
  2 10.100.0.3 8 msec 8 msec 8 msec                              ! ← R3 reached

R1# show dmvpn detail
Interface: Tunnel0, IPv4 NHRP Details
Type:Hub, NHRP Peers:2, NHS:    0,
   Tunnel Interface Address  : 10.100.0.1
   NHRP group                : (none)
   NHS Identifier            : (none configured — this IS the hub)
 # Ent  Peer NBMA Addr  Peer Tunnel Add  State UpDn Tm  Attrb
 ----- --------------- ---------------  ----- -------- ------
     1 198.51.100.1        10.100.0.2    UP    00:02:15    D     ! ← R2 spoke
     1 192.0.2.1           10.100.0.3    UP    00:02:11    D     ! ← R3 spoke
```

---

## 7. Verification Cheatsheet

### Underlay Verification

```
ping <remote-public-ip> source <local-public-int>
show ip route 0.0.0.0
```

| Command | Purpose |
|---------|---------|
| `ping 203.0.113.1` from R2 | Confirm underlay R2→R1 reachable before tunnels |
| `show ip route 0.0.0.0` | Confirm default route toward R4 is installed |

> **Exam tip:** Always verify underlay NBMA reachability before adding tunnel commands. A missing default route causes every subsequent symptom to look like an NHRP or tunnel problem.

### mGRE Tunnel Configuration

```
interface Tunnel0
 ip address <tunnel-ip> <mask>
 ip mtu 1400
 ip tcp adjust-mss 1360
 tunnel source <underlay-int>
 tunnel mode gre multipoint
 tunnel key <key>
 no ip redirects     ! hub only
```

| Command | Purpose |
|---------|---------|
| `tunnel mode gre multipoint` | Enables mGRE (no static tunnel destination needed) |
| `tunnel key 100` | Optional but prevents mismatched tunnels from forming |
| `ip mtu 1400` | Prevents fragmentation of GRE-encapsulated packets |
| `ip tcp adjust-mss 1360` | Clamps TCP MSS to avoid black-holing large flows |
| `no ip redirects` | Required on hub to prevent ICMP redirects on the overlay |

> **Exam tip:** `tunnel mode gre multipoint` must be on ALL members — hub AND spokes. A common misconception is that only the hub uses multipoint GRE.

### NHRP Configuration

```
! Hub:
 ip nhrp network-id 100
 ip nhrp authentication ENARSI
 ip nhrp map multicast dynamic
 ip nhrp hold-time 300

! Spoke:
 ip nhrp network-id 100
 ip nhrp authentication ENARSI
 ip nhrp map <hub-tunnel-ip> <hub-nbma-ip>
 ip nhrp map multicast <hub-nbma-ip>
 ip nhrp nhs <hub-tunnel-ip>
```

| Command | Purpose |
|---------|---------|
| `ip nhrp network-id 100` | Must match on all members — mismatch = silent failure |
| `ip nhrp authentication ENARSI` | Optional auth string — mismatch = no registration |
| `ip nhrp map multicast dynamic` | Hub: OSPF hellos relayed to registered spokes automatically |
| `ip nhrp map multicast <hub-nbma>` | Spoke: tells the spoke where to send multicast (OSPF hellos) |
| `ip nhrp nhs <hub-tunnel-ip>` | Spoke: points the NHC at the NHS to register |
| `ip nhrp hold-time 300` | How long the hub keeps a dynamic entry without refresh |

> **Exam tip:** `ip nhrp map multicast dynamic` on the hub and `ip nhrp map multicast <hub-nbma>` on spokes are OSPF's mechanism for sending hellos across the DMVPN overlay. Forgetting either one means OSPF neighbors never form — even if NHRP registration works fine.

### OSPF Overlay Verification

```
show ip ospf neighbor
show ip route ospf
show ip ospf interface Tunnel0
```

| Command | What to Look For |
|---------|-----------------|
| `show ip ospf neighbor` | State must be FULL, no DR/BDR role (p2mp shows `-`) |
| `show ip route ospf` | Remote LANs with `O` prefix, metric > 1000 (tunnel cost) |
| `show ip ospf interface Tunnel0` | Network type: POINT_TO_MULTIPOINT, state: POINT_TO_MULTIPOINT |

### DMVPN-Specific Verification

```
show dmvpn
show dmvpn detail
show ip nhrp
show ip nhrp detail
```

| Command | What to Look For |
|---------|-----------------|
| `show dmvpn` | Both spokes show `UP`, Attrb = `D` (dynamic) |
| `show dmvpn detail` | NBMA-to-tunnel IP mappings; UpDn Tm shows stability |
| `show ip nhrp` | Type: dynamic; NBMA address matches spoke's public IP |
| `show ip nhrp detail` | Registration timestamps, NHS state, flags |

### Wildcard Mask Quick Reference

| Subnet Mask | Wildcard Mask | Common Use |
|-------------|---------------|------------|
| /24 (255.255.255.0) | 0.0.0.255 | LAN loopbacks in this lab |
| /30 (255.255.255.252) | 0.0.0.3 | Underlay point-to-point links |
| /32 (255.255.255.255) | 0.0.0.0 | Host route / exact match |

### Common DMVPN Phase 1 Failure Causes

| Symptom | Likely Cause |
|---------|-------------|
| Spokes not appearing in `show ip nhrp` | Missing default route (underlay), NHRP network-id mismatch, or auth mismatch |
| OSPF neighbors not forming | Missing `ip nhrp map multicast` (hub or spoke), passive-interface on Tunnel0 |
| Tunnel0 line protocol down | Tunnel source interface is down or wrong interface specified |
| Ping to spoke LAN fails despite NHRP UP | OSPF not advertising Loopback0 (wrong network statement or passive) |
| Traceroute shows no hub hop | NHRP shortcut accidentally enabled (Phase 3 behavior) |

---

## 8. Solutions (Spoiler Alert!)

> Try to complete the lab challenge without looking at these steps first!

### Task 1: Static Default Routes (Underlay)

<details>
<summary>Click to view R1 configuration</summary>

```bash
! R1
ip route 0.0.0.0 0.0.0.0 203.0.113.2
```
</details>

<details>
<summary>Click to view R2 configuration</summary>

```bash
! R2
ip route 0.0.0.0 0.0.0.0 198.51.100.2
```
</details>

<details>
<summary>Click to view R3 configuration</summary>

```bash
! R3
ip route 0.0.0.0 0.0.0.0 192.0.2.2
```
</details>

<details>
<summary>Click to view Verification Commands</summary>

```bash
ping 203.0.113.1           ! from R2 — underlay to hub
ping 198.51.100.1          ! from R3 — underlay to R2
show ip route 0.0.0.0      ! confirm default route installed
```
</details>

---

### Task 2: Hub mGRE Tunnel Interface

<details>
<summary>Click to view R1 configuration</summary>

```bash
! R1 — Hub / NHS
interface Tunnel0
 description DMVPN-Hub-NHS
 bandwidth 1000
 ip address 10.100.0.1 255.255.255.0
 no ip redirects
 ip mtu 1400
 ip tcp adjust-mss 1360
 ip nhrp authentication ENARSI
 ip nhrp map multicast dynamic
 ip nhrp network-id 100
 ip nhrp hold-time 300
 ip ospf network point-to-multipoint
 ip ospf 100 area 0
 tunnel source GigabitEthernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 no shutdown
```
</details>

<details>
<summary>Click to view Verification Commands</summary>

```bash
show interface Tunnel0
show ip interface Tunnel0
```
</details>

---

### Task 3: Spoke mGRE Tunnels and NHRP

<details>
<summary>Click to view R2 configuration</summary>

```bash
! R2 — Spoke 1 (Branch A)
interface Tunnel0
 description DMVPN-Spoke1-BranchA
 bandwidth 1000
 ip address 10.100.0.2 255.255.255.0
 ip mtu 1400
 ip tcp adjust-mss 1360
 ip nhrp authentication ENARSI
 ip nhrp map 10.100.0.1 203.0.113.1
 ip nhrp map multicast 203.0.113.1
 ip nhrp network-id 100
 ip nhrp nhs 10.100.0.1
 ip ospf network point-to-multipoint
 ip ospf 100 area 0
 tunnel source GigabitEthernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 no shutdown
```
</details>

<details>
<summary>Click to view R3 configuration</summary>

```bash
! R3 — Spoke 2 (Branch B)
interface Tunnel0
 description DMVPN-Spoke2-BranchB
 bandwidth 1000
 ip address 10.100.0.3 255.255.255.0
 ip mtu 1400
 ip tcp adjust-mss 1360
 ip nhrp authentication ENARSI
 ip nhrp map 10.100.0.1 203.0.113.1
 ip nhrp map multicast 203.0.113.1
 ip nhrp network-id 100
 ip nhrp nhs 10.100.0.1
 ip ospf network point-to-multipoint
 ip ospf 100 area 0
 tunnel source GigabitEthernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 no shutdown
```
</details>

<details>
<summary>Click to view Verification Commands</summary>

```bash
show ip nhrp               ! on R1 — should show dynamic entries for R2 and R3
show dmvpn                 ! on R1 — both spokes UP
```
</details>

---

### Task 4: OSPF Overlay Routing

<details>
<summary>Click to view R1 configuration</summary>

```bash
! R1
router ospf 100
 router-id 10.1.1.1
 passive-interface default
 no passive-interface Tunnel0
 network 10.1.1.0 0.0.0.255 area 0
 network 10.100.0.0 0.0.0.255 area 0
```
</details>

<details>
<summary>Click to view R2 configuration</summary>

```bash
! R2
router ospf 100
 router-id 10.2.2.2
 passive-interface default
 no passive-interface Tunnel0
 network 10.2.2.0 0.0.0.255 area 0
 network 10.100.0.0 0.0.0.255 area 0
```
</details>

<details>
<summary>Click to view R3 configuration</summary>

```bash
! R3
router ospf 100
 router-id 10.3.3.3
 passive-interface default
 no passive-interface Tunnel0
 network 10.3.3.0 0.0.0.255 area 0
 network 10.100.0.0 0.0.0.255 area 0
```
</details>

<details>
<summary>Click to view Verification Commands</summary>

```bash
show ip ospf neighbor      ! on R1 — R2 and R3 must be FULL
show ip route ospf         ! on R2 — must see R1 and R3 LAN prefixes
```
</details>

---

### Task 5: Phase 1 Behavior Analysis

<details>
<summary>Click to view Verification Commands</summary>

```bash
! From R2:
traceroute 10.3.3.3 source Loopback0

! From R1:
show dmvpn detail
show ip nhrp
show ip ospf neighbor
```
</details>

---

## 9. Troubleshooting Scenarios

Each ticket simulates a real-world fault. Inject the fault first, then diagnose and fix using only show commands.

### Workflow

```bash
python3 setup_lab.py --host <eve-ng-ip>                           # reset to known-good
python3 scripts/fault-injection/inject_scenario_01.py --host <eve-ng-ip>  # Ticket 1
python3 scripts/fault-injection/apply_solution.py --host <eve-ng-ip>      # restore
```

---

### Ticket 1 — R2 Cannot Reach Any Remote Site

The Branch A team reports total loss of connectivity. R2 cannot ping anything outside its local subnet, including the hub.

**Inject:** `python3 scripts/fault-injection/inject_scenario_01.py --host <eve-ng-ip>`

**Success criteria:** R2 can ping R1's tunnel IP (10.100.0.1) and R3's Loopback0 (10.3.3.3) after fix. `show dmvpn` on R1 shows R2 as UP.

<details>
<summary>Click to view Diagnosis Steps</summary>

```bash
! Start at the underlay — check if R2 can reach its ISP next-hop
R2# ping 198.51.100.2

! Check the routing table for a default route
R2# show ip route 0.0.0.0

! If no default route, check for any static routes
R2# show running-config | include ip route
```

**Root cause:** R2's static default route (`ip route 0.0.0.0 0.0.0.0 198.51.100.2`) has been removed. Without a default route, R2 cannot reach R4 (the ISP/transit), so no GRE packet can exit R2's Gi0/0 toward the hub. NHRP registration fails silently; OSPF never forms.

</details>

<details>
<summary>Click to view Fix</summary>

```bash
R2# configure terminal
R2(config)# ip route 0.0.0.0 0.0.0.0 198.51.100.2
R2(config)# end

! Verify
R2# ping 198.51.100.2
R2# show dmvpn           ! R2 entry should reappear on R1 within 60 seconds
R1# show ip nhrp         ! Should show R2's dynamic entry
```
</details>

---

### Ticket 2 — Hub Shows Only One Spoke; Branch B Cannot Communicate

The Branch B team (R3) reports they can reach HQ (R1) but cannot reach Branch A (R2). On the hub, `show dmvpn` shows only one spoke entry.

**Inject:** `python3 scripts/fault-injection/inject_scenario_02.py --host <eve-ng-ip>`

**Success criteria:** Both R2 and R3 appear in `show dmvpn` on R1. R3 can ping R2's Loopback0 (10.2.2.2).

<details>
<summary>Click to view Diagnosis Steps</summary>

```bash
! On R1 — confirm which spoke is missing
R1# show dmvpn
R1# show ip nhrp

! On R3 — check NHRP registration state
R3# show ip nhrp
R3# show dmvpn

! Check NHRP parameters — network-id must match
R3# show running-config | section Tunnel0
R1# show running-config | section Tunnel0
```

**Root cause:** R3's NHRP network-id has been changed to a non-matching value. The hub ignores NHRP Registration Requests from a spoke with a different network-id — no error message, the registration simply doesn't appear.

</details>

<details>
<summary>Click to view Fix</summary>

```bash
R3# configure terminal
R3(config)# interface Tunnel0
R3(config-if)# ip nhrp network-id 100
R3(config-if)# end

! Verify — R3 entry should appear within the hold-time
R1# show ip nhrp
R1# show dmvpn
R3# show dmvpn
```
</details>

---

### Ticket 3 — OSPF Adjacency Not Forming on the Hub

The network team confirms NHRP is working (`show dmvpn` shows both spokes UP), but none of the branch LANs are reachable. The hub shows no OSPF neighbors.

**Inject:** `python3 scripts/fault-injection/inject_scenario_03.py --host <eve-ng-ip>`

**Success criteria:** `show ip ospf neighbor` on R1 shows FULL adjacencies with both R2 and R3. Branch LAN routes appear in `show ip route ospf`.

<details>
<summary>Click to view Diagnosis Steps</summary>

```bash
! Check NHRP first — confirm the transport layer is working
R1# show dmvpn

! Check OSPF neighbor state
R1# show ip ospf neighbor

! Check OSPF interface state on Tunnel0
R1# show ip ospf interface Tunnel0

! Check if Tunnel0 is passive
R1# show running-config | section ospf
```

**Root cause:** `passive-interface Tunnel0` has been added to R1's OSPF configuration. A passive interface suppresses both sending and receiving OSPF hellos on that interface. NHRP operates independently of OSPF, so DMVPN sessions stay UP but no routing information is exchanged.

</details>

<details>
<summary>Click to view Fix</summary>

```bash
R1# configure terminal
R1(config)# router ospf 100
R1(config-router)# no passive-interface Tunnel0
R1(config-router)# end

! Verify
R1# show ip ospf neighbor
R2# show ip route ospf    ! Branch LAN prefixes should return
```
</details>

---

## 10. Lab Completion Checklist

### Core Implementation

- [ ] Static default route installed on R1, R2, and R3 toward R4
- [ ] Underlay pings succeed: R2→R1, R3→R1, R2→R3 (via R4)
- [ ] Tunnel0 is up/up on R1, R2, and R3 with tunnel mode gre multipoint
- [ ] `show ip nhrp` on R1 shows dynamic entries for both R2 and R3
- [ ] `show dmvpn` on R1 shows both spokes in UP state with Attrb = D
- [ ] `show ip ospf neighbor` on R1 shows two FULL adjacencies (no DR role)
- [ ] `show ip route ospf` on R2 shows R1 LAN (10.1.1.0/24) and R3 LAN (10.3.3.0/24)
- [ ] Traceroute from R2 Loopback0 to R3 Loopback0 shows R1 hub IP as intermediate hop

### Troubleshooting

- [ ] Ticket 1 injected, diagnosed (missing underlay default route), and fixed
- [ ] Ticket 2 injected, diagnosed (NHRP network-id mismatch on R3), and fixed
- [ ] Ticket 3 injected, diagnosed (passive-interface on hub Tunnel0), and fixed
- [ ] `apply_solution.py` run after each ticket to restore clean state

---

## 11. Appendix: Script Exit Codes

| Code | Meaning | Applies to |
|------|---------|------------|
| 0 | Success | All scripts |
| 1 | Partial failure (one or more devices failed) | `setup_lab.py`, `apply_solution.py` |
| 2 | `--host` not provided | All scripts |
| 3 | EVE-NG connectivity error | All scripts |
| 4 | Pre-flight check failed (lab not in expected state) | Inject scripts only |
