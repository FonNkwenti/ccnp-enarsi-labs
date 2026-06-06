# DMVPN Lab 02 — Capstone I: Full Configuration Mastery

## Table of Contents

1. [Concepts & Skills Covered](#1-concepts--skills-covered)
2. [Topology & Scenario](#2-topology--scenario)
3. [Hardware & Environment Specifications](#3-hardware--environment-specifications)
4. [Base Configuration](#4-base-configuration)
5. [Lab Challenge: Full Protocol Mastery](#5-lab-challenge-full-protocol-mastery)
6. [Verification & Analysis](#6-verification--analysis)
7. [Verification Cheatsheet](#7-verification-cheatsheet)
8. [Solutions (Spoiler Alert!)](#8-solutions-spoiler-alert)
9. [Troubleshooting Scenarios](#9-troubleshooting-scenarios)
10. [Lab Completion Checklist](#10-lab-completion-checklist)
11. [Appendix: Script Exit Codes](#11-appendix-script-exit-codes)

---

## 1. Concepts & Skills Covered

**Exam Objectives:** 2.3 — Configure and verify DMVPN (single hub): 2.3.a GRE/mGRE, 2.3.b NHRP, 2.3.c IPsec, 2.3.d Dynamic neighbor, 2.3.e Spoke-to-spoke

This lab tests end-to-end mastery of the full DMVPN Phase 3 + IPsec stack. You receive IP addressing only — every protocol layer must be configured from scratch.

### DMVPN Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Underlay | Static default route | Reachability between NBMA endpoints |
| Encapsulation | mGRE (`tunnel mode gre multipoint`) | Logical overlay on all members |
| Discovery | NHRP network-id + authentication | Spoke registration and NHS lookup |
| Hub functions | `ip nhrp map multicast dynamic`, `ip nhrp redirect` | Multicast forwarding + Phase 3 redirects |
| Spoke functions | `ip nhrp nhs`, `ip nhrp map`, `ip nhrp shortcut` | NHS pointer + Phase 3 shortcut installation |
| Overlay routing | OSPF process 100, area 0, `network point-to-multipoint` | LAN prefix advertisement over the tunnel |
| Security | IKEv1 PSK + IPsec transform-set (transport mode) | GRE payload encryption |
| Binding | `tunnel protection ipsec profile DMVPN-PROFILE` | Apply IPsec to the mGRE interface |

### Skills this lab develops

| Skill | Description |
|-------|-------------|
| Full-stack DMVPN build | Configure underlay → overlay → routing → security without scaffolding |
| NHRP hub/spoke asymmetry | Hub uses dynamic multicast map; spokes use static NHS mapping |
| IPsec transport mode | Choose correct IPsec mode for GRE-encapsulated DMVPN traffic |
| Phase 3 activation | Add redirect/shortcut to an already-running DMVPN |
| Layer-by-layer verification | Confirm each protocol layer before moving to the next |

---

## 2. Topology & Scenario

**Scenario:** GlobalLogix has opened two new branch offices (Branch A and Branch B) and requires a secure WAN overlay connecting both branches to HQ. The network team has selected DMVPN Phase 3 with IPsec as the architecture. R4 is a transit ISP router managed externally — it has connected routes only and must not be modified. Your task: build the complete DMVPN solution from the IP-addressed base state.

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
    │   HUB / NHS (HQ) │     │        │     │  Spoke 2         │
    │ Tu0: 10.100.0.1  │     │        │     │ Tu0: 10.100.0.3  │
    │ Lo0: 10.1.1.1/24 │     │        │     │ Lo0: 10.3.3.3/24 │
    └──────────────────┘     │        │     └──────────────────┘
                       198.51.100.1/30│
                             Gi0/0    │
                    ┌─────────────────┘
                    │       R2
                    │   Spoke 1 (Branch A)
                    │ Tu0: 10.100.0.2
                    │ Lo0: 10.2.2.2/24
                    └─────────────────

  Overlay: 10.100.0.0/24 (mGRE tunnel subnet)
  IPsec: all GRE traffic encrypted — transport mode, AES-256/SHA-256/DH14
  Phase 3: spoke-to-spoke shortcuts form on demand via NHRP redirect/shortcut
```

---

## 3. Hardware & Environment Specifications

### Device Inventory

| Device | Role | Platform | Image |
|--------|------|----------|-------|
| R1 | DMVPN Hub / NHS (HQ) | IOSv | vios-adventerprisek9-m.SPA.156-2.T |
| R2 | DMVPN Spoke 1 (Branch A) | IOSv | vios-adventerprisek9-m.SPA.156-2.T |
| R3 | DMVPN Spoke 2 (Branch B) | IOSv | vios-adventerprisek9-m.SPA.156-2.T |
| R4 | Simulated ISP/Transit (do not modify) | IOSv | vios-adventerprisek9-m.SPA.156-2.T |

### Cabling

| Link | Device A | Interface A | Device B | Interface B | Subnet | Purpose |
|------|----------|-------------|----------|-------------|--------|---------|
| L1 | R1 | Gi0/0 | R4 | Gi0/0 | 203.0.113.0/30 | Hub underlay uplink |
| L2 | R2 | Gi0/0 | R4 | Gi0/1 | 198.51.100.0/30 | Spoke1 underlay uplink |
| L3 | R3 | Gi0/0 | R4 | Gi0/2 | 192.0.2.0/30 | Spoke2 underlay uplink |

### Address Reference

| Device | Gi0/0 (NBMA) | Loopback0 (LAN) | Tunnel0 (Overlay) |
|--------|-------------|-----------------|-------------------|
| R1 | 203.0.113.1 | 10.1.1.1/24 | 10.100.0.1/24 |
| R2 | 198.51.100.1 | 10.2.2.2/24 | 10.100.0.2/24 |
| R3 | 192.0.2.1 | 10.3.3.3/24 | 10.100.0.3/24 |
| R4 | (multiple — ISP only) | 4.4.4.4/32 | — |

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
- Interface IP addresses on all physical interfaces (Gi0/0, Gi0/1, Gi0/2 as applicable)
- Loopback0 addresses on R1, R2, R3, R4
- `no ip domain-lookup` on all devices
- R4 ISP interfaces are configured and ready — do not modify R4

**IS NOT pre-loaded** (student configures all of this):
- Default routes on R1, R2, R3
- Tunnel0 interface on R1, R2, R3 (mGRE mode, NHRP, OSPF binding)
- NHRP hub configuration on R1 (dynamic multicast map, hold-time, redirect)
- NHRP spoke configuration on R2, R3 (static hub mapping, nhs, shortcut)
- OSPF process 100 on R1, R2, R3 (point-to-multipoint, passive-interface default)
- IKEv1 ISAKMP policy (AES-256 / SHA-256 / group 14 / 86400s) on R1, R2, R3
- Pre-shared key (`cisco123`, wildcard) on R1, R2, R3
- IPsec transform-set (`DMVPN-TS`, transport mode) on R1, R2, R3
- IPsec profile (`DMVPN-PROFILE`) on R1, R2, R3
- Tunnel protection applied to Tunnel0 on R1, R2, R3

---

## 5. Lab Challenge: Full Protocol Mastery

> This is a capstone lab. No step-by-step guidance is provided.
> Configure the complete DMVPN solution from scratch — IP addressing is pre-configured; everything else is yours to build.
> All blueprint bullets for this chapter must be addressed.

### Success Criteria

When complete, the following must be true:

| Check | Command | Expected Result |
|-------|---------|----------------|
| Underlay reachability | `ping 203.0.113.2` from R1 | 5/5 success |
| NHRP registration | `show ip nhrp` on R1 | Dynamic entries for R2 and R3 |
| OSPF adjacencies | `show ip ospf neighbor` on R1 | FULL state with R2 and R3 |
| Full mesh routing | `show ip route ospf` on R2 | Routes to 10.1.1.0/24 and 10.3.3.0/24 |
| IPsec applied | `show interface Tunnel0` | `Tunnel protection via IPsec` on all three |
| Phase 3 shortcut | `show ip nhrp` on R2 after spoke-to-spoke ping | Shortcut entry with `Flags: shortcut` |
| Direct spoke-to-spoke | `traceroute 10.3.3.3 source Loopback0` from R2 | R3 direct — no R1 hop |
| Encrypted spoke-to-spoke | `show crypto ipsec sa peer 192.0.2.1` on R2 | Non-zero `#pkts encaps` and `#pkts decaps` |

### NHRP Parameters

- Network-ID: `100`
- Authentication key: `ENARSI`
- Hub NBMA: `203.0.113.1`
- Hub tunnel IP: `10.100.0.1`
- Hold-time (hub): `300`
- Tunnel key: `100`

### IPsec Parameters

- IKE version: IKEv1
- Policy priority: `10`
- Encryption: AES-256
- Hash: SHA-256
- DH group: 14
- Lifetime: 86400 seconds
- PSK: `cisco123` (wildcard — all peers)
- Transform-set name: `DMVPN-TS`
- Transform: `esp-aes 256 esp-sha256-hmac`
- Mode: **transport** (not tunnel)
- Profile name: `DMVPN-PROFILE`

---

## 6. Verification & Analysis

### Underlay Layer

```
R1# ping 203.0.113.2       ! R4 — confirms Gi0/0 is up
R2# ping 198.51.100.2      ! R4 — confirms Gi0/0 is up
R3# ping 192.0.2.2         ! R4 — confirms Gi0/0 is up

R2# ping 203.0.113.1       ! R1 hub NBMA — requires default route + ISP transit
```

### mGRE Tunnel Layer

```
R1# show interface Tunnel0
  Tunnel0 is up, line protocol is up
  ...
  Tunnel protocol/transport multi-GRE/IP          ! ← mGRE confirmed
  Tunnel protection via IPsec (profile "DMVPN-PROFILE" shared)  ! ← IPsec applied
```

### NHRP Registration

```
R1# show ip nhrp
10.100.0.2/32 via 10.100.0.2
   Tunnel0 created 00:03:41, expire 00:04:18
   Type: dynamic, Flags: registered used nhop        ! ← R2 dynamic registration
   NBMA address: 198.51.100.1
10.100.0.3/32 via 10.100.0.3
   Type: dynamic, Flags: registered used nhop        ! ← R3 dynamic registration
   NBMA address: 192.0.2.1
```

### OSPF Overlay

```
R1# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
10.2.2.2          1   FULL/  -        00:01:39    10.100.0.2      Tunnel0
10.3.3.3          1   FULL/  -        00:01:39    10.100.0.3      Tunnel0

R2# show ip route ospf
      10.0.0.0/8 is variably subnetted
O        10.1.1.0/24 [110/1001] via 10.100.0.1, 00:05:10, Tunnel0  ! ← hub LAN
O        10.3.3.0/24 [110/1002] via 10.100.0.1, 00:04:55, Tunnel0  ! ← spoke2 via hub (pre-shortcut)
```

### DMVPN Summary

```
R1# show dmvpn
Legend: Attrb --> S - Static, D - Dynamic, I - Incomplete
        N - NATed, L - Local, X - No Socket
        # Ent --> Number of NHRP Entries with Same Tunnel Policy

Intf     Type Tunnel     NBMA Addr         Tunnel Addr       State  UpDn Tm Attrb
Tu0      Hub  198.51.100.1    10.100.0.2    NHRP    00:10:32 D    ! ← R2 up
Tu0      Hub  192.0.2.1       10.100.0.3    NHRP    00:08:47 D    ! ← R3 up
```

### Phase 3 Shortcut

```
! Trigger spoke-to-spoke traffic
R2# ping 10.3.3.3 source Loopback0 repeat 20

! Observe shortcut formation (allow 2-3 seconds)
R2# show ip nhrp
10.100.0.1/32 via 10.100.0.1
   Type: static, Flags: used                           ! ← NHS static mapping
   NBMA address: 203.0.113.1
10.100.0.3/32 via 10.100.0.3
   Type: dynamic, Flags: router rib nho shortcut       ! ← shortcut entry!
   NBMA address: 192.0.2.1                             ! ← R3 NBMA resolved

R2# traceroute 10.3.3.3 source Loopback0
  1 10.3.3.3 8 msec 6 msec 5 msec                     ! ← R3 directly — no hub hop
```

### IPsec SA Verification

```
R2# show crypto isakmp sa
dst             src             state          conn-id status
192.0.2.1       198.51.100.1    QM_IDLE           1001 ACTIVE  ! ← SA to R3 NBMA
203.0.113.1     198.51.100.1    QM_IDLE           1000 ACTIVE  ! ← SA to R1 NBMA

R2# show crypto ipsec sa peer 192.0.2.1
    #pkts encaps: 15, #pkts encrypt: 15, #pkts digest: 15      ! ← R2→R3 encrypted
    #pkts decaps: 13, #pkts decrypt: 13, #pkts verify: 13      ! ← R3→R2 decrypted
```

---

## 7. Verification Cheatsheet

### Underlay (all DMVPN members)

```
ip route 0.0.0.0 0.0.0.0 <next-hop-toward-R4>
```

| Device | Next-hop |
|--------|---------|
| R1 | 203.0.113.2 |
| R2 | 198.51.100.2 |
| R3 | 192.0.2.2 |

### Hub Tunnel0 (R1)

```
interface Tunnel0
 ip address 10.100.0.1 255.255.255.0
 no ip redirects
 ip mtu 1400
 ip tcp adjust-mss 1360
 ip nhrp authentication ENARSI
 ip nhrp map multicast dynamic
 ip nhrp network-id 100
 ip nhrp hold-time 300
 ip nhrp redirect
 ip ospf network point-to-multipoint
 ip ospf 100 area 0
 tunnel source GigabitEthernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile DMVPN-PROFILE
```

### Spoke Tunnel0 (R2 — replace addresses for R3)

```
interface Tunnel0
 ip address 10.100.0.2 255.255.255.0        ! R3: 10.100.0.3
 ip mtu 1400
 ip tcp adjust-mss 1360
 ip nhrp authentication ENARSI
 ip nhrp map 10.100.0.1 203.0.113.1         ! static mapping to hub
 ip nhrp map multicast 203.0.113.1          ! OSPF hellos via hub
 ip nhrp network-id 100
 ip nhrp nhs 10.100.0.1                     ! NHS = hub tunnel IP
 ip nhrp shortcut
 ip ospf network point-to-multipoint
 ip ospf 100 area 0
 tunnel source GigabitEthernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile DMVPN-PROFILE
```

### IKEv1 + IPsec (identical on R1, R2, R3)

```
crypto isakmp policy 10
 encr aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400
!
crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0
!
crypto ipsec transform-set DMVPN-TS esp-aes 256 esp-sha256-hmac
 mode transport
!
crypto ipsec profile DMVPN-PROFILE
 set transform-set DMVPN-TS
```

### OSPF (identical structure on R1, R2, R3)

```
router ospf 100
 router-id <loopback0-ip>
 passive-interface default
 no passive-interface Tunnel0
 network 10.<x>.<x>.0 0.0.0.255 area 0     ! LAN subnet
 network 10.100.0.0 0.0.0.255 area 0        ! overlay subnet
```

### Key Verification Commands

| Command | What to Look For |
|---------|-----------------|
| `show interface Tunnel0` | `multi-GRE/IP`, `Tunnel protection via IPsec` |
| `show ip nhrp` | Dynamic registrations on hub; shortcut flag on spokes |
| `show dmvpn` | All spokes in NHRP UP state |
| `show ip ospf neighbor` | FULL state with all DMVPN members |
| `show ip route ospf` | Spoke LAN routes visible on all members |
| `show crypto isakmp sa` | QM_IDLE state per NBMA peer |
| `show crypto ipsec sa` | Non-zero encaps/decaps per peer |
| `traceroute <spoke-lan> source Loopback0` | No hub hop after shortcut resolves |

### Common Build Mistakes

| Symptom | Likely Cause |
|---------|-------------|
| Spokes not registering with hub | NHRP network-id mismatch, wrong NHS IP, or missing default route |
| OSPF adjacency stuck at INIT/2WAY | `network point-to-multipoint` not set, or `passive-interface Tunnel0` still set |
| IPsec never negotiates | ISAKMP policy mismatch, PSK mismatch, or tunnel protection not applied |
| Shortcuts never form | `ip nhrp redirect` missing on hub, or `ip nhrp shortcut` missing on spoke |
| OSPF adjacency flaps when tunnel protection added | Expected — tunnel restarts once; adjacency recovers within 40-60 seconds |

---

## 8. Solutions (Spoiler Alert!)

> Attempt the full configuration without looking at these. Use them only to verify a specific section after you have tried.

### R1 (Hub)

<details>
<summary>Click to view R1 complete configuration</summary>

```bash
ip route 0.0.0.0 0.0.0.0 203.0.113.2
!
crypto isakmp policy 10
 encr aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400
!
crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0
!
crypto ipsec transform-set DMVPN-TS esp-aes 256 esp-sha256-hmac
 mode transport
!
crypto ipsec profile DMVPN-PROFILE
 set transform-set DMVPN-TS
!
interface Tunnel0
 description DMVPN-Hub-NHS-Phase3
 bandwidth 1000
 ip address 10.100.0.1 255.255.255.0
 no ip redirects
 ip mtu 1400
 ip tcp adjust-mss 1360
 ip nhrp authentication ENARSI
 ip nhrp map multicast dynamic
 ip nhrp network-id 100
 ip nhrp hold-time 300
 ip nhrp redirect
 ip ospf network point-to-multipoint
 ip ospf 100 area 0
 tunnel source GigabitEthernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile DMVPN-PROFILE
 no shutdown
!
router ospf 100
 router-id 10.1.1.1
 passive-interface default
 no passive-interface Tunnel0
 network 10.1.1.0 0.0.0.255 area 0
 network 10.100.0.0 0.0.0.255 area 0
```
</details>

### R2 (Spoke 1)

<details>
<summary>Click to view R2 complete configuration</summary>

```bash
ip route 0.0.0.0 0.0.0.0 198.51.100.2
!
crypto isakmp policy 10
 encr aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400
!
crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0
!
crypto ipsec transform-set DMVPN-TS esp-aes 256 esp-sha256-hmac
 mode transport
!
crypto ipsec profile DMVPN-PROFILE
 set transform-set DMVPN-TS
!
interface Tunnel0
 description DMVPN-Spoke1-BranchA-Phase3
 bandwidth 1000
 ip address 10.100.0.2 255.255.255.0
 ip mtu 1400
 ip tcp adjust-mss 1360
 ip nhrp authentication ENARSI
 ip nhrp map 10.100.0.1 203.0.113.1
 ip nhrp map multicast 203.0.113.1
 ip nhrp network-id 100
 ip nhrp nhs 10.100.0.1
 ip nhrp shortcut
 ip ospf network point-to-multipoint
 ip ospf 100 area 0
 tunnel source GigabitEthernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile DMVPN-PROFILE
 no shutdown
!
router ospf 100
 router-id 10.2.2.2
 passive-interface default
 no passive-interface Tunnel0
 network 10.2.2.0 0.0.0.255 area 0
 network 10.100.0.0 0.0.0.255 area 0
```
</details>

### R3 (Spoke 2)

<details>
<summary>Click to view R3 complete configuration</summary>

```bash
ip route 0.0.0.0 0.0.0.0 192.0.2.2
!
crypto isakmp policy 10
 encr aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400
!
crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0
!
crypto ipsec transform-set DMVPN-TS esp-aes 256 esp-sha256-hmac
 mode transport
!
crypto ipsec profile DMVPN-PROFILE
 set transform-set DMVPN-TS
!
interface Tunnel0
 description DMVPN-Spoke2-BranchB-Phase3
 bandwidth 1000
 ip address 10.100.0.3 255.255.255.0
 ip mtu 1400
 ip tcp adjust-mss 1360
 ip nhrp authentication ENARSI
 ip nhrp map 10.100.0.1 203.0.113.1
 ip nhrp map multicast 203.0.113.1
 ip nhrp network-id 100
 ip nhrp nhs 10.100.0.1
 ip nhrp shortcut
 ip ospf network point-to-multipoint
 ip ospf 100 area 0
 tunnel source GigabitEthernet0/0
 tunnel mode gre multipoint
 tunnel key 100
 tunnel protection ipsec profile DMVPN-PROFILE
 no shutdown
!
router ospf 100
 router-id 10.3.3.3
 passive-interface default
 no passive-interface Tunnel0
 network 10.3.3.0 0.0.0.255 area 0
 network 10.100.0.0 0.0.0.255 area 0
```
</details>

---

## 9. Troubleshooting Scenarios

Each ticket injects a single fault into your working configuration. Diagnose and fix without looking at the hints first.

### Workflow

```bash
python3 setup_lab.py --host <eve-ng-ip>                                    # reset to solutions
python3 scripts/fault-injection/inject_scenario_01.py --host <eve-ng-ip>   # inject fault
# diagnose and fix
python3 scripts/fault-injection/apply_solution.py --host <eve-ng-ip>       # restore
```

---

### Ticket 1 — Both Spokes Register but OSPF Never Forms

R1 shows both spokes in the NHRP table as dynamic registrations. However, `show ip ospf neighbor` on R1 shows no neighbors. Pings between LAN subnets fail.

**Inject:** `python3 scripts/fault-injection/inject_scenario_01.py --host <eve-ng-ip>`

**Success criteria:** OSPF adjacency reaches FULL between R1↔R2 and R1↔R3. All LAN routes visible in routing tables.

<details>
<summary>Click to view Diagnosis Steps</summary>

```bash
! Check NHRP registrations — are spokes registered?
R1# show ip nhrp
! Dynamic entries for R2 and R3 should exist

! Check OSPF neighbors — none expected with the fault present
R1# show ip ospf neighbor

! Check if OSPF hellos reach the hub
R1# debug ip ospf hello
! If no hellos received — multicast path broken

! Check spoke NHRP multicast map
R2# show running-config | section Tunnel0 | include nhrp
! Look for "ip nhrp map multicast 203.0.113.1" — its absence prevents OSPF hello delivery

! Compare R1's multicast map config
R1# show running-config | section Tunnel0 | include nhrp
! Hub should show "ip nhrp map multicast dynamic" — spokes need the static multicast map
```

**Root cause:** `ip nhrp map multicast 203.0.113.1` has been removed from R2 and R3's Tunnel0. OSPF hellos from the spokes cannot reach the hub (no multicast path), so adjacencies never form. NHRP registration itself uses unicast to the NHS — that is why NHRP still works.

</details>

<details>
<summary>Click to view Fix</summary>

```bash
R2(config)# interface Tunnel0
R2(config-if)# ip nhrp map multicast 203.0.113.1
R2(config-if)# end

R3(config)# interface Tunnel0
R3(config-if)# ip nhrp map multicast 203.0.113.1
R3(config-if)# end

! Verify OSPF adjacency recovers
R1# show ip ospf neighbor     ! FULL state should appear for R2 and R3
R2# show ip route ospf        ! Routes to 10.1.1.0 and 10.3.3.0 should install
```
</details>

---

### Ticket 2 — Spoke R3 Cannot Register with the Hub

R1 shows R2 registered in the NHRP table, but no entry exists for R3. R3 can ping R4 (underlay works), but cannot reach R1's tunnel or LAN.

**Inject:** `python3 scripts/fault-injection/inject_scenario_02.py --host <eve-ng-ip>`

**Success criteria:** R1's NHRP table shows a dynamic entry for R3 (10.100.0.3 → 192.0.2.1). OSPF adjacency between R1 and R3 reaches FULL.

<details>
<summary>Click to view Diagnosis Steps</summary>

```bash
! Check hub NHRP — is R3 missing?
R1# show ip nhrp
! R2 entry exists; R3 entry absent

! Check DMVPN tunnel state on R3
R3# show dmvpn
! State may show INTF UP but NHRP not established

! Check NHRP debug on R3
R3# debug ip nhrp
! Look for "NHRP: Receive Registration Reply" failure
! Or: "NHRP: Sending Registration Request" repeatedly

! Compare NHRP network-id on R3 vs R1
R3# show running-config | section Tunnel0 | include nhrp
R1# show running-config | section Tunnel0 | include nhrp
! If network-id differs — registration will silently fail
```

**Root cause:** R3's NHRP network-id has been changed to `200` (from `100`). NHRP registration requests from R3 carry network-id 200; R1 expects 100 and discards them. No error message appears on R1 — the mismatch is silent.

</details>

<details>
<summary>Click to view Fix</summary>

```bash
R3(config)# interface Tunnel0
R3(config-if)# no ip nhrp network-id 200
R3(config-if)# ip nhrp network-id 100
R3(config-if)# end

! Verify registration
R3# clear ip nhrp               ! force re-registration
R1# show ip nhrp                ! R3 entry should appear within 30 seconds
R1# show ip ospf neighbor       ! FULL state should recover for R3
```
</details>

---

### Ticket 3 — IPsec SAs Form Between Hub and Spokes but Not Between Spokes

Spoke-to-spoke shortcuts form and traffic reaches both spokes, but `show crypto ipsec sa` on R2 shows no SA to R3's NBMA address (192.0.2.1). A packet capture shows unencrypted GRE on the spoke-to-spoke path.

**Inject:** `python3 scripts/fault-injection/inject_scenario_03.py --host <eve-ng-ip>`

**Success criteria:** `show crypto ipsec sa peer 192.0.2.1` on R2 shows non-zero encaps/decaps. All spoke-to-spoke traffic is encrypted.

<details>
<summary>Click to view Diagnosis Steps</summary>

```bash
! Trigger spoke-to-spoke traffic
R2# ping 10.3.3.3 source Loopback0 repeat 10

! Check IKE SA — SA to R3?
R2# show crypto isakmp sa
! If no entry for 192.0.2.1 — IKE failed between R2 and R3

! Check IPsec SA explicitly
R2# show crypto ipsec sa peer 192.0.2.1
! No output = no SA established

! Initiate IKE debug briefly
R2# debug crypto isakmp
R2# ping 10.3.3.3 source Loopback0
! Look for: "ISAKMP: atts are not acceptable" — policy mismatch
! Or: "ISAKMP: Failed to find matching policy" — R3 has different policy number

! Compare ISAKMP policy on R2 and R3
R2# show crypto isakmp policy
R3# show crypto isakmp policy
! DH group, encryption, or hash algorithm likely differs between peers
```

**Root cause:** R3's ISAKMP policy 10 has been modified — DH group changed from 14 to 5. When R2 initiates IKE with R3 for the spoke-to-spoke SA, it proposes group 14. R3 only has group 5 — the proposals do not match and IKE fails. Hub-to-spoke SAs are not affected because R2↔R1 both still have group 14.

</details>

<details>
<summary>Click to view Fix</summary>

```bash
R3(config)# crypto isakmp policy 10
R3(config-isakmp)# group 14
R3(config-isakmp)# end

! Retrigger spoke-to-spoke traffic
R2# ping 10.3.3.3 source Loopback0 repeat 10

! Verify IKE and IPsec SAs
R2# show crypto isakmp sa              ! QM_IDLE entry for 192.0.2.1 should appear
R2# show crypto ipsec sa peer 192.0.2.1  ! encaps/decaps should increment
```
</details>

---

## 10. Lab Completion Checklist

### Full Configuration

- [ ] Default route on R1 (toward 203.0.113.2), R2 (toward 198.51.100.2), R3 (toward 192.0.2.2)
- [ ] Tunnel0 on R1 with mGRE mode, NHRP hub config, `ip nhrp redirect`, OSPF p2mp, IPsec protection
- [ ] Tunnel0 on R2 with mGRE mode, NHRP spoke config, `ip nhrp shortcut`, OSPF p2mp, IPsec protection
- [ ] Tunnel0 on R3 with mGRE mode, NHRP spoke config, `ip nhrp shortcut`, OSPF p2mp, IPsec protection
- [ ] NHRP network-id 100 and auth ENARSI consistent on all three members
- [ ] IKEv1 policy (AES-256 / SHA-256 / group 14 / 86400s) on R1, R2, R3
- [ ] Wildcard PSK `cisco123` (address 0.0.0.0 0.0.0.0) on R1, R2, R3
- [ ] Transform-set `DMVPN-TS` (esp-aes 256 / esp-sha256-hmac / transport) on R1, R2, R3
- [ ] IPsec profile `DMVPN-PROFILE` on R1, R2, R3
- [ ] `tunnel protection ipsec profile DMVPN-PROFILE` applied on Tunnel0 of all three

### Verification

- [ ] `show ip nhrp` on R1 — dynamic entries for R2 (198.51.100.1) and R3 (192.0.2.1)
- [ ] `show ip ospf neighbor` on R1 — FULL state with R2 (10.2.2.2) and R3 (10.3.3.3)
- [ ] `show ip route ospf` on R2 — routes to 10.1.1.0/24 and 10.3.3.0/24 installed
- [ ] `show interface Tunnel0` — `Tunnel protection via IPsec` on all three
- [ ] `show crypto isakmp sa` on R2 — QM_IDLE entries for 203.0.113.1 (R1) and 192.0.2.1 (R3)
- [ ] `show ip nhrp` on R2 after spoke-to-spoke ping — shortcut entry with `Flags: shortcut`
- [ ] `traceroute 10.3.3.3 source Loopback0` from R2 — R3 directly (no R1 hop)
- [ ] `show crypto ipsec sa peer 192.0.2.1` on R2 — non-zero `#pkts encaps` and `#pkts decaps`

### Troubleshooting

- [ ] Ticket 1 diagnosed (NHRP multicast map missing) and fixed — OSPF adjacency recovered
- [ ] Ticket 2 diagnosed (NHRP network-id mismatch on R3) and fixed — R3 registered
- [ ] Ticket 3 diagnosed (ISAKMP DH group mismatch on R3) and fixed — spoke-to-spoke IPsec working
- [ ] `apply_solution.py` run after each ticket to restore known-good state

---

## 11. Appendix: Script Exit Codes

| Code | Meaning | Applies to |
|------|---------|------------|
| 0 | Success | All scripts |
| 1 | Partial failure (one or more devices failed) | `setup_lab.py`, `apply_solution.py` |
| 2 | `--host` not provided | All scripts |
| 3 | EVE-NG connectivity error | All scripts |
| 4 | Pre-flight check failed (lab not in expected state) | Inject scripts only |
