# DMVPN Lab 03 — Capstone II: Comprehensive Troubleshooting

## Table of Contents

1. [Concepts & Skills Covered](#1-concepts--skills-covered)
2. [Topology & Scenario](#2-topology--scenario)
3. [Hardware & Environment Specifications](#3-hardware--environment-specifications)
4. [Fault Environment](#4-fault-environment)
5. [Lab Challenge: Full Stack Troubleshooting](#5-lab-challenge-full-stack-troubleshooting)
6. [Verification: Expected Final State](#6-verification-expected-final-state)
7. [Troubleshooting Reference](#7-troubleshooting-reference)
8. [Solutions (Spoiler Alert!)](#8-solutions-spoiler-alert)
9. [Lab Completion Checklist](#9-lab-completion-checklist)
10. [Appendix: Script Exit Codes](#10-appendix-script-exit-codes)

---

## 1. Concepts & Skills Covered

**Exam Objectives:** 2.3 — Configure and verify DMVPN (single hub): 2.3.a GRE/mGRE, 2.3.b NHRP, 2.3.c IPsec, 2.3.d Dynamic neighbor, 2.3.e Spoke-to-spoke

This lab tests the ability to diagnose a broken but mostly-complete DMVPN Phase 3 + IPsec deployment. No configuration is built from scratch — instead, a production-like broken environment is loaded and the student must work through it layer by layer.

### Troubleshooting Methodology

DMVPN troubleshooting follows a strict layer order. Each layer depends on the one below it:

```
Layer 5 — Phase 3 behavior         show ip nhrp, traceroute spoke-to-spoke
     ↑
Layer 4 — OSPF overlay             show ip ospf neighbor, show ip route ospf
     ↑
Layer 3 — IPsec / IKEv1            show crypto isakmp sa, show crypto ipsec sa
     ↑
Layer 2 — NHRP (registration)      show ip nhrp, show dmvpn
     ↑
Layer 1 — mGRE tunnel              show interface Tunnel0, show dmvpn
     ↑
Layer 0 — Underlay (routing)       ping <nbma>, show ip route, traceroute
```

Never skip a layer. Verify each is working before advancing. A fault at Layer 0 can produce misleading symptoms at Layer 3 — fixing at the wrong layer wastes time.

### Key Commands by Layer

| Layer | Primary Commands | What to Look For |
|-------|-----------------|-----------------|
| Underlay | `ping <nbma-ip>`, `show ip route` | Reachability between NBMA addresses |
| Tunnel | `show interface Tunnel0`, `show dmvpn` | Line protocol up, mGRE mode confirmed |
| NHRP | `show ip nhrp`, `show dmvpn` | Dynamic spoke registrations on hub |
| IPsec | `show crypto isakmp sa`, `show crypto ipsec sa` | QM_IDLE state, non-zero counters |
| OSPF | `show ip ospf neighbor`, `show ip route ospf` | FULL state, spoke LANs in routing table |
| Phase 3 | `show ip nhrp` on spoke, `traceroute` | Shortcut flag, no hub hop in traceroute |

### Skills this lab develops

| Skill | Description |
|-------|-------------|
| Systematic layer isolation | Prove each protocol layer is working before moving up |
| Silent failure recognition | Identify faults that produce no error messages |
| IKE failure diagnosis | Read `debug crypto isakmp` output for Phase 1 failure modes |
| NHRP registration analysis | Distinguish underlay, auth, and network-id failures |
| Phase 3 shortcut verification | Confirm shortcut via NHRP table and traceroute |

---

## 2. Topology & Scenario

**Scenario:** GlobalLogix's DMVPN deployment was configured by an engineer who has since left the company. Before leaving, the engineer committed several errors. You have been asked to troubleshoot the deployment and restore full Phase 3 + IPsec functionality. The expected end state: both branch spokes (R2 and R3) fully registered with the hub (R1), OSPF adjacencies established, all LAN routes reachable, IPsec protecting all GRE traffic, and Phase 3 spoke-to-spoke shortcuts working.

R4 (ISP) is managed externally — do not modify R4.

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

  Overlay: 10.100.0.0/24
  Protocol stack: underlay static route → mGRE → NHRP → IKEv1/IPsec → OSPF → Phase 3
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

| Link | Device A | Interface A | Device B | Interface B | Subnet |
|------|----------|-------------|----------|-------------|--------|
| L1 | R1 | Gi0/0 | R4 | Gi0/0 | 203.0.113.0/30 |
| L2 | R2 | Gi0/0 | R4 | Gi0/1 | 198.51.100.0/30 |
| L3 | R3 | Gi0/0 | R4 | Gi0/2 | 192.0.2.0/30 |

### Address Reference

| Device | Gi0/0 (NBMA) | Loopback0 (LAN) | Tunnel0 (Overlay) |
|--------|-------------|-----------------|-------------------|
| R1 | 203.0.113.1 | 10.1.1.1/24 | 10.100.0.1/24 |
| R2 | 198.51.100.1 | 10.2.2.2/24 | 10.100.0.2/24 |
| R3 | 192.0.2.1 | 10.3.3.3/24 | 10.100.0.3/24 |
| R4 | (multiple — ISP only) | 4.4.4.4/32 | — |

---

## 4. Fault Environment

The broken configuration is loaded by running `setup_lab.py`. The DMVPN deployment is fully configured — interfaces, IPs, tunnel parameters, NHRP, IPsec, and OSPF are all present — but there are **four deliberate errors** embedded across the devices. Your job is to find and fix all four.

**What IS configured (do not change):**
- All interface IP addresses and physical link configurations
- mGRE tunnel mode on all devices (Tunnel0 is configured)
- NHRP parameters structure (nhs, map, multicast) — some values may be wrong
- IPsec policy, transform-set, and profile structure — some values may be wrong
- OSPF process 100 with network statements and passive-interface settings

**The symptoms when the lab starts:**
1. Neither spoke appears in R1's NHRP table
2. `show dmvpn` on R1 shows no entries
3. `show ip ospf neighbor` on all devices shows no neighbors
4. Ping between any LAN subnet pair fails

**Your task:** Find all four faults, fix them with minimum changes, and verify each protocol layer from bottom to top after each fix.

---

## 5. Lab Challenge: Full Stack Troubleshooting

> This is a capstone lab. No guided steps are provided.
> Diagnose the broken deployment layer by layer using show and debug commands.
> Apply the minimum configuration change to fix each fault.
> Document: what layer failed, what command revealed the fault, and what change fixed it.

### Success Criteria

| Check | Command | Expected Result |
|-------|---------|----------------|
| R2 underlay reachability | `ping 203.0.113.1` from R2 | 5/5 success |
| R3 underlay reachability | `ping 203.0.113.1` from R3 | 5/5 success |
| NHRP registrations | `show ip nhrp` on R1 | Dynamic entries for R2 and R3 |
| DMVPN sessions | `show dmvpn` on R1 | Both spokes in UP state |
| OSPF adjacencies | `show ip ospf neighbor` on R1 | FULL state with R2 and R3 |
| LAN reachability | `ping 10.3.3.3 source Lo0` from R2 | 5/5 success |
| IPsec hub-spoke | `show crypto ipsec sa` on R1 | Active SAs to R2 and R3 NBMA |
| Phase 3 shortcut | `traceroute 10.3.3.3 source Lo0` from R2 | R3 directly — no R1 hop |
| Spoke-to-spoke IPsec | `show crypto ipsec sa peer 192.0.2.1` on R2 | Non-zero encaps/decaps |

### Reference: Expected NHRP Parameters

| Parameter | Correct Value |
|-----------|--------------|
| Network-ID | 100 |
| Authentication key | ENARSI |
| Hub NBMA | 203.0.113.1 |
| Hub tunnel IP | 10.100.0.1 |
| Hold-time (hub) | 300 |
| Tunnel key | 100 |

### Reference: Expected IPsec Parameters

| Parameter | Correct Value |
|-----------|--------------|
| PSK | cisco123 (wildcard — all peers) |
| IKE policy | AES-256, SHA-256, DH group 14, 86400s |
| Transform-set | esp-aes 256 esp-sha256-hmac, transport mode |
| Profile | DMVPN-PROFILE |

---

## 6. Verification: Expected Final State

### After all faults fixed

```
! ── Underlay ──────────────────────────────────────────────────────────
R2# ping 203.0.113.1 source Gi0/0
!!!!!                                                    ! ← 5/5

R2# show ip route | include 0.0.0.0
S*   0.0.0.0/0 [1/0] via 198.51.100.2                   ! ← correct gateway

! ── NHRP / DMVPN ──────────────────────────────────────────────────────
R1# show ip nhrp
10.100.0.2/32 via 10.100.0.2
   Type: dynamic, Flags: registered used nhop             ! ← R2 registered
   NBMA address: 198.51.100.1
10.100.0.3/32 via 10.100.0.3
   Type: dynamic, Flags: registered used nhop             ! ← R3 registered
   NBMA address: 192.0.2.1

R1# show dmvpn
Interface: Tunnel0, IPv4 NHRP Details
Type:Hub, NHRP Peers:2,
 # Ent  Peer NBMA Addr Peer Tunnel Add State  UpDn Tm Attrb
 ----- --------------- --------------- ----- -------- -----
     1 198.51.100.1       10.100.0.2    UP    00:05:12     D   ! ← R2 UP
     1 192.0.2.1          10.100.0.3    UP    00:04:48     D   ! ← R3 UP

! ── OSPF ──────────────────────────────────────────────────────────────
R1# show ip ospf neighbor
Neighbor ID     Pri   State           Dead Time   Address         Interface
10.2.2.2          1   FULL/  -        00:01:36    10.100.0.2      Tunnel0
10.3.3.3          1   FULL/  -        00:01:33    10.100.0.3      Tunnel0

R2# show ip route ospf
O    10.1.1.0/24 [110/1001] via 10.100.0.1, Tunnel0      ! ← hub LAN
O    10.3.3.0/24 [110/1002] via 10.100.0.1, Tunnel0      ! ← spoke2 via hub (pre-shortcut)

! ── IPsec ─────────────────────────────────────────────────────────────
R1# show crypto isakmp sa
dst             src             state          conn-id status
198.51.100.1    203.0.113.1     QM_IDLE           1000 ACTIVE   ! ← SA to R2
192.0.2.1       203.0.113.1     QM_IDLE           1001 ACTIVE   ! ← SA to R3

! ── Phase 3 Shortcuts ─────────────────────────────────────────────────
R2# ping 10.3.3.3 source Loopback0 repeat 10
!!!!!.!!!!

R2# show ip nhrp
10.100.0.3/32 via 10.100.0.3
   Type: dynamic, Flags: router rib nho shortcut          ! ← shortcut formed
   NBMA address: 192.0.2.1

R2# traceroute 10.3.3.3 source Loopback0
  1  10.3.3.3  8 msec  6 msec  6 msec                    ! ← R3 directly, no hub hop

R2# show crypto ipsec sa peer 192.0.2.1
    #pkts encaps: 12, #pkts encrypt: 12                   ! ← spoke-to-spoke encrypted
    #pkts decaps: 10, #pkts decrypt: 10
```

---

## 7. Troubleshooting Reference

### Underlay Verification

| Command | Reveals |
|---------|---------|
| `ping <nbma-ip>` | Basic L3 reachability between NBMA addresses |
| `show ip route` | Default route presence and correct gateway |
| `traceroute <nbma-ip>` | Path to hub; confirms transit through R4 |

### NHRP / mGRE Verification

| Command | Reveals |
|---------|---------|
| `show ip nhrp` | Registration entries on hub; NHS mapping on spokes |
| `show dmvpn` | Spoke state (UP/NHRP/IKE) and NBMA-to-tunnel mapping |
| `debug ip nhrp` | Registration request/reply sequence; auth failures |
| `show interface Tunnel0` | mGRE mode, IPsec protection applied, tunnel source |

### IKEv1 / IPsec Verification

| Command | Reveals |
|---------|---------|
| `show crypto isakmp sa` | IKE Phase 1 state — QM_IDLE = established, MM_ = failed |
| `show crypto isakmp policy` | Configured parameters; compare across peers for mismatches |
| `show crypto isakmp key` | PSK and peer address — check for wildcard vs specific entries |
| `debug crypto isakmp` | MM_NO_STATE = policy mismatch, MM_KEY_EXCH = PSK mismatch |
| `show crypto ipsec sa` | Phase 2 SAs; encaps/decaps counters |

### OSPF Verification

| Command | Reveals |
|---------|---------|
| `show ip ospf neighbor` | Neighbor state; absence = hello not reaching peer |
| `show ip ospf interface Tunnel0` | Network type, hello/dead timers, passive status |
| `debug ip ospf hello` | Hello packets sent/received on tunnel interface |
| `show ip route ospf` | Spoke LAN prefixes in routing table |

### Phase 3 Shortcut Verification

| Command | Reveals |
|---------|---------|
| `show ip nhrp` on spoke | Shortcut entry with `Flags: shortcut` after traffic trigger |
| `traceroute <spoke-lan> source Lo0` | Hub bypass — R3 appears directly in output |
| `show running-config \| section Tunnel0` | Confirm `ip nhrp redirect` on hub, `ip nhrp shortcut` on spokes |

### IKE Failure State Decoding

| ISAKMP State | Root Cause |
|-------------|-----------|
| `MM_NO_STATE` | ISAKMP policy mismatch — encryption, hash, or DH group differ |
| `MM_KEY_EXCH` | PSK mismatch — DH exchange succeeds but authentication fails |
| No SA at all | Peers cannot reach each other (underlay or tunnel-protection issue) |
| `QM_IDLE` | IKE Phase 1 established successfully |

---

## 8. Solutions (Spoiler Alert!)

> Do not read this section before attempting the troubleshooting. Use it only after you have tried each layer independently.

### The Four Faults

The faults were injected in dependency order. Fixing them in the same order is the most efficient path.

---

### Fault 1 — Underlay (R2): Missing Default Route

**Layer:** Underlay (Layer 0)

**Symptom:** R2 cannot ping R4 (198.51.100.2) or R1 (203.0.113.1). NHRP registration from R2 never reaches the hub. R1's NHRP table shows no R2 entry.

**Discovery:**
```bash
R2# show ip route
! No default route entry — S* 0.0.0.0/0 is absent

R2# ping 203.0.113.1
...... (all fail)
```

**Fix:**
```bash
R2(config)# ip route 0.0.0.0 0.0.0.0 198.51.100.2

! Verify
R2# show ip route | include 0.0.0.0
S*   0.0.0.0/0 [1/0] via 198.51.100.2
R2# ping 203.0.113.1
!!!!!
```

---

### Fault 2 — IPsec (R1): Wrong Pre-Shared Key

**Layer:** IKEv1 (Layer 3)

**Symptom:** After fixing the R2 default route, R2 attempts NHRP registration but the tunnel-protected GRE packets cannot be encrypted because IKE fails. `show crypto isakmp sa` on R2 shows a stuck state — no QM_IDLE entry. `show dmvpn` on R1 still shows no entries.

**Discovery:**
```bash
R2# show crypto isakmp sa
dst             src             state          conn-id status
203.0.113.1     198.51.100.1    MM_KEY_EXCH       0 ACTIVE
! MM_KEY_EXCH = DH exchange succeeded, authentication (PSK) failed

R1# show crypto isakmp key
Keyring      Hostname/Address                            Preshared Key
default      0.0.0.0/0.0.0.0                             badkey123
! PSK on R1 does not match R2 and R3 which have cisco123
```

**Fix:**
```bash
R1(config)# no crypto isakmp key badkey123 address 0.0.0.0 0.0.0.0
R1(config)# crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0

! Verify IKE re-establishes
R1# clear crypto isakmp
R2# show crypto isakmp sa
! QM_IDLE should appear for 203.0.113.1 after a few seconds
```

---

### Fault 3 — NHRP (R3): Wrong Network-ID

**Layer:** NHRP (Layer 2)

**Symptom:** After fixing faults 1 and 2, R2 fully registers with R1 and an OSPF adjacency forms. However, R3 never appears in R1's NHRP table. R3 can ping R4 (underlay OK). IKE on R3 also fails to establish.

**Discovery:**
```bash
R1# show ip nhrp
! Only R2's entry is present — R3 is absent

! Check R3's tunnel config
R3# show running-config | section Tunnel0
 ip nhrp network-id 200   ! ← should be 100

! R1 expects network-id 100 — packets from R3 with network-id 200 are discarded silently
! IKE also cannot establish because tunnel-protected GRE is blocked
```

**Fix:**
```bash
R3(config)# interface Tunnel0
R3(config-if)# no ip nhrp network-id 200
R3(config-if)# ip nhrp network-id 100
R3(config-if)# end

R3# clear ip nhrp

! Verify registration
R1# show ip nhrp
! R3 entry (NBMA: 192.0.2.1) should appear within 30 seconds
R1# show ip ospf neighbor
! FULL state should appear for both R2 and R3
```

---

### Fault 4 — Phase 3 (R1): Missing NHRP Redirect

**Layer:** Phase 3 / NHRP (Layer 5)

**Symptom:** After fixing faults 1-3, both spokes are registered, OSPF is FULL, all LAN routes are reachable. However, traceroute from R2 to R3 always shows R1 in the path — even after multiple spoke-to-spoke pings. `show ip nhrp` on R2 never shows a shortcut entry for R3.

**Discovery:**
```bash
! Trigger spoke-to-spoke traffic
R2# ping 10.3.3.3 source Loopback0 repeat 30

! Check for shortcuts on R2
R2# show ip nhrp
! No shortcut entry for 10.100.0.3 — R2 never received a redirect

! Check hub for redirect
R1# show running-config | section Tunnel0
! "ip nhrp redirect" is absent from Tunnel0 config
! Without redirect, R1 forwards spoke-to-spoke traffic silently — never notifies R2
```

**Fix:**
```bash
R1(config)# interface Tunnel0
R1(config-if)# ip nhrp redirect
R1(config-if)# end

! Retrigger spoke-to-spoke traffic
R2# ping 10.3.3.3 source Loopback0 repeat 10

! Verify shortcut forms
R2# show ip nhrp
! Shortcut entry with Flags: shortcut should appear for 10.100.0.3

R2# traceroute 10.3.3.3 source Loopback0
  1  10.3.3.3  8 msec  7 msec  6 msec   ! ← R1 no longer in path

R2# show crypto ipsec sa peer 192.0.2.1
    #pkts encaps: ...                    ! ← spoke-to-spoke traffic encrypted
```

---

## 9. Lab Completion Checklist

### Fault Resolution

- [ ] Fault 1 found: R2 missing default route — command that revealed it: _______________
- [ ] Fault 1 fixed: `ip route 0.0.0.0 0.0.0.0 198.51.100.2` added to R2
- [ ] Fault 2 found: R1 wrong PSK (`badkey123`) — command that revealed it: _______________
- [ ] Fault 2 fixed: Correct PSK (`cisco123`) configured on R1, IKE re-established
- [ ] Fault 3 found: R3 NHRP network-id 200 — command that revealed it: _______________
- [ ] Fault 3 fixed: network-id 100 restored on R3, R3 registered with hub
- [ ] Fault 4 found: R1 missing `ip nhrp redirect` — command that revealed it: _______________
- [ ] Fault 4 fixed: `ip nhrp redirect` added to R1 Tunnel0, Phase 3 shortcuts working

### Final Verification

- [ ] `show ip nhrp` on R1 — dynamic entries for R2 (198.51.100.1) and R3 (192.0.2.1)
- [ ] `show dmvpn` on R1 — both spokes in UP state
- [ ] `show ip ospf neighbor` on R1 — FULL state with R2 and R3
- [ ] `show ip route ospf` on R2 — routes to 10.1.1.0/24 and 10.3.3.0/24 installed
- [ ] `show crypto isakmp sa` on R1 — QM_IDLE state for both spokes
- [ ] `show interface Tunnel0` on R1 — `Tunnel protection via IPsec`
- [ ] `traceroute 10.3.3.3 source Loopback0` from R2 — R3 directly (no R1 hop)
- [ ] `show crypto ipsec sa peer 192.0.2.1` on R2 — non-zero `#pkts encaps`/`#pkts decaps`

---

## 10. Appendix: Script Exit Codes

| Code | Meaning | Applies to |
|------|---------|------------|
| 0 | Success | All scripts |
| 1 | Partial failure (one or more devices failed) | `setup_lab.py`, `apply_solution.py` |
| 2 | `--host` not provided | All scripts |
| 3 | EVE-NG connectivity error | All scripts |
