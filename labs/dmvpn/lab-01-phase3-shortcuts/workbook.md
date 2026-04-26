# DMVPN Lab 01 — Phase 3: Spoke-to-Spoke Shortcuts with IPsec Protection

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

**Exam Objective:** 2.3 — Configure and verify DMVPN (single hub): 2.3.a GRE/mGRE, 2.3.b NHRP, 2.3.c IPsec, 2.3.e Spoke-to-spoke

### Phase 3 vs Phase 1 — What Actually Changes

Phase 1 and Phase 3 are often described as different tunnel modes, but that is a misconception. In this lab series, both phases use mGRE (`tunnel mode gre multipoint`) on hub and spokes — the tunnel mode does not change.

The Phase 1 to Phase 3 transition is controlled entirely by **two NHRP commands**:

| Command | Placed on | Phase 1 | Phase 3 |
|---------|-----------|---------|---------|
| `ip nhrp redirect` | Hub Tunnel0 | Absent | Present |
| `ip nhrp shortcut` | Spoke Tunnel0 | Absent | Present |

**Without these commands (Phase 1):** When R2 sends traffic destined for R3, the hub R1 forwards every packet. The hub never sends an NHRP redirect — R2 has no way to learn R3's NBMA address.

**With these commands (Phase 3):** When R2 sends the first packet toward R3, the hub forwards it *and* sends an NHRP Redirect message back to R2, telling it to resolve R3 directly. R2 sends an NHRP Resolution Request to the hub; the hub responds with R3's NBMA address. R2 installs an NHRP-resolved next-hop in CEF (a "shortcut"). Subsequent packets go directly from R2 to R3 — bypassing the hub entirely.

This shortcut is dynamic and temporary. If R2 and R3 stop sending spoke-to-spoke traffic, the NHRP entry ages out and the shortcut is removed.

### IPsec in DMVPN — Transport Mode and the Wildcard PSK

DMVPN uses **IPsec transport mode**, not tunnel mode. GRE is already encapsulating the inner IP packet — adding IPsec tunnel mode would add a second IP header unnecessarily. Transport mode encrypts only the GRE payload, keeping the outer GRE header intact for routing.

The encryption stack for each DMVPN packet in lab-01:

```
[ Outer IP (NBMA src→dst) ][ GRE header ][ ESP (encrypted) [ Inner IP ][ Data ] ]
```

**The wildcard PSK problem:** In a standard IKEv1 PSK deployment, each peer has a specific IP address. In DMVPN, spoke NBMA addresses are dynamic — the hub cannot pre-configure a PSK entry for every possible spoke IP. The solution:

```
crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0
```

This wildcard entry matches any peer IP. When IKE negotiates with a new spoke, it finds the wildcard entry and uses `cisco123` as the shared secret. All three devices (R1, R2, R3) configure the same wildcard key — spoke-to-spoke IKE negotiation (after shortcut resolution) also uses this key.

**IKEv1 Phase 1 and Phase 2 for DMVPN:**
- **Phase 1 (ISAKMP SA):** Peers negotiate encryption (AES-256), hash (SHA-256), DH group (14), and authenticate using the PSK. Result: an ISAKMP SA protecting the management channel.
- **Phase 2 (IPsec SA / Quick Mode):** Peers negotiate the IPsec transform-set (`esp-aes 256 esp-sha256-hmac`, transport mode). Result: a pair of IPsec SAs (one per direction) protecting GRE traffic.

Both SAs are created on demand — IKE does not start until the first packet needs to be encrypted. This is why the first ping after IPsec configuration may be slow or fail: IKE negotiation takes a few hundred milliseconds.

### The Spoke-to-Spoke Shortcut Resolution Sequence

Understanding this sequence is what separates someone who configured DMVPN from someone who understands it:

1. R2 sends a packet to 10.3.3.3 (R3's LAN). OSPF installed the next-hop as 10.100.0.3 (R3's tunnel IP), but the ARP/NHRP cache does not have R3's NBMA address.
2. R2 sends the packet to the hub (10.100.0.1) as a default — hub forwards it to R3.
3. Hub sees traffic from R2 destined for R3 **and** has `ip nhrp redirect` configured. It sends an NHRP Redirect to R2: "you should resolve R3 directly."
4. R2 receives the redirect and sends an NHRP Resolution Request to the hub: "what is R3's NBMA address?"
5. Hub responds with an NHRP Resolution Reply: "R3's NBMA is 192.0.2.1."
6. R2 installs a CEF shortcut: next-hop for 10.100.0.3 (or 10.3.3.0/24) = NBMA 192.0.2.1. This is the "shortcut."
7. R2 can now send subsequent packets directly to 192.0.2.1 (R3's underlay IP), bypassing the hub.
8. IKE negotiates an IPsec SA between R2 (198.51.100.1) and R3 (192.0.2.1) for this direct path.

**Observable in the lab:** The first traceroute from R2 to R3 shows R1 in the path. After the shortcut forms (~1-2 seconds), subsequent traceroutes show R3 directly.

### Skills this lab develops

| Skill | Description |
|-------|-------------|
| Phase 3 activation | Add redirect/shortcut without changing tunnel mode |
| IKEv1 ISAKMP policy | AES-256 / SHA-256 / DH 14 / lifetime configuration |
| Wildcard PSK | Configure a single key matching all DMVPN peers |
| IPsec transform-set | esp-aes 256 esp-sha256-hmac in transport mode |
| Tunnel protection | Apply IPsec profile to mGRE tunnel interface |
| Shortcut verification | Trace the NHRP resolution sequence in real time |
| IPsec SA verification | Read show crypto isakmp sa and show crypto ipsec sa |

---

## 2. Topology & Scenario

**Scenario:** GlobalLogix's DMVPN Phase 1 deployment (lab-00) is working, but the security team requires all WAN traffic to be encrypted. The network team also wants to reduce hub bandwidth consumption by enabling spoke-to-spoke direct tunnels for branch-to-branch traffic. Your task is to upgrade the existing Phase 1 deployment to Phase 3 with IPsec protection — without changing the tunnel mode or any existing NHRP registration parameters.

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
    │   Phase 3 + IPsec│     │        │     │  Phase 3 + IPsec │
    │ Tu0: 10.100.0.1  │     │        │     │ Tu0: 10.100.0.3  │
    │ ip nhrp redirect │     │        │     │ ip nhrp shortcut │
    └──────────────────┘     │        │     └──────────────────┘
                       198.51.100.1/30│
                             Gi0/0    │
                    ┌─────────────────┘
                    │       R2
                    │   Spoke 1
                    │   Phase 3 + IPsec
                    │ Tu0: 10.100.0.2
                    │ ip nhrp shortcut
                    └─────────────────

  Phase 3: spoke-to-spoke traffic bypasses hub after first packet
  IPsec: all GRE traffic encrypted (transport mode, AES-256/SHA-256/DH14)
```

---

## 3. Hardware & Environment Specifications

### Device Inventory

| Device | Role | Platform | Image |
|--------|------|----------|-------|
| R1 | DMVPN Hub / NHS (HQ) — Phase 3 + IPsec | IOSv | vios-adventerprisek9-m.SPA.156-2.T |
| R2 | DMVPN Spoke 1 (Branch A) — Phase 3 + IPsec | IOSv | vios-adventerprisek9-m.SPA.156-2.T |
| R3 | DMVPN Spoke 2 (Branch B) — Phase 3 + IPsec | IOSv | vios-adventerprisek9-m.SPA.156-2.T |
| R4 | Simulated ISP/Transit (unchanged) | IOSv | vios-adventerprisek9-m.SPA.156-2.T |

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
- Everything from lab-00 solutions: hostnames, interface IPs, static default routes on R1/R2/R3
- Tunnel0 on R1, R2, R3 with mGRE mode, NHRP parameters, OSPF point-to-multipoint
- OSPF process 100 on R1, R2, R3 with Loopback0 and tunnel subnet advertised
- OSPF adjacencies established; NHRP dynamic registration working; Phase 1 behavior active

**IS NOT pre-loaded** (student configures this):
- IKEv1 ISAKMP policy on R1, R2, R3
- Pre-shared key (wildcard) on R1, R2, R3
- IPsec transform-set on R1, R2, R3
- IPsec profile on R1, R2, R3
- Tunnel protection (IPsec profile applied to Tunnel0) on R1, R2, R3
- Phase 3 NHRP redirect on R1 hub Tunnel0
- Phase 3 NHRP shortcut on R2 and R3 spoke Tunnel0 interfaces

---

## 5. Lab Challenge: Core Implementation

> This lab extends lab-00. All Phase 1 config is pre-loaded. Add Phase 3 and IPsec without modifying any existing NHRP or tunnel-mode commands.

### Task 1: Configure IKEv1 ISAKMP Policy

On R1, R2, and R3, define an ISAKMP (IKE Phase 1) policy. The policy must specify the encryption algorithm, integrity hash, authentication method, Diffie-Hellman group, and SA lifetime.

- Use policy priority 10
- Encryption: AES with 256-bit key
- Hash/integrity: SHA-256
- Authentication: pre-shared key
- DH group: 14 (2048-bit)
- Lifetime: 86400 seconds (24 hours)

**Verification:** `show crypto isakmp policy` must display the policy with the configured parameters on all three routers.

---

### Task 2: Configure the Wildcard Pre-Shared Key

On R1, R2, and R3, configure a pre-shared key that matches any peer IP address. The key string is `cisco123`.

- Configure the key to apply to any peer address (wildcard match — not a specific IP)
- The same command must appear identically on all three DMVPN members

**Verification:** `show crypto isakmp key` must show the key configured with a wildcard address pattern on all three routers.

---

### Task 3: Configure IPsec Transform-Set and Profile

On R1, R2, and R3, define the IPsec Phase 2 parameters and package them into an IPsec profile.

- Create a transform-set named `DMVPN-TS` using AES-256 for encryption and SHA-256 HMAC for integrity
- Set the transform mode to transport (not tunnel) — GRE provides the outer encapsulation
- Create an IPsec profile named `DMVPN-PROFILE` that references `DMVPN-TS`

**Verification:** `show crypto ipsec transform-set` must show `DMVPN-TS` with transport mode. `show crypto ipsec profile` must show `DMVPN-PROFILE` referencing `DMVPN-TS`.

---

### Task 4: Apply IPsec Tunnel Protection

On R1, R2, and R3, apply the IPsec profile to the existing Tunnel0 interface. This binds IPsec encryption to all GRE traffic on the tunnel.

- Apply `DMVPN-PROFILE` as tunnel protection on Tunnel0 on all three devices
- Do not change any other tunnel parameters (mGRE mode, NHRP config, OSPF config)

**Verification:** `show interface Tunnel0` must show `Tunnel protection via IPsec` on all three routers. Confirm OSPF adjacencies recover after a brief flap (the tunnel restarts when protection is applied).

---

### Task 5: Enable Phase 3 NHRP Behavior

Add Phase 3 NHRP commands to activate spoke-to-spoke shortcut resolution.

- On R1 (hub): add `ip nhrp redirect` to Tunnel0 — this causes the hub to send redirect messages when forwarding spoke-to-spoke traffic
- On R2 (spoke 1): add `ip nhrp shortcut` to Tunnel0 — this allows R2 to install NHRP-resolved CEF shortcuts
- On R3 (spoke 2): add `ip nhrp shortcut` to Tunnel0 — same as R2

**Verification:** `show ip nhrp` on R1 must show the redirect flag is active. After triggering a spoke-to-spoke flow (next task), `show ip nhrp` on R2 should show a dynamic shortcut entry for R3's tunnel IP.

---

### Task 6: Trigger and Verify Spoke-to-Spoke Shortcut and IPsec

Trigger spoke-to-spoke traffic and observe the full Phase 3 + IPsec resolution sequence.

- From R2, ping R3's Loopback0 (10.3.3.3) sourced from R2's Loopback0 (10.2.2.2) — the first ping may lose 1-2 packets during shortcut resolution and IKE negotiation
- Immediately run a traceroute from R2 Loopback0 to R3 Loopback0 — subsequent probes should show R3 directly (no hub hop)
- On R2, examine the NHRP table for a shortcut entry to R3's tunnel IP
- On R2, examine the IPsec SAs and confirm an encrypted SA exists to R3's NBMA address (192.0.2.1)

**Verification:** Traceroute from R2 to R3 must show R3 directly (no R1 hub hop) after the first packet. `show crypto ipsec sa peer 192.0.2.1` on R2 must show encrypted/decrypted packet counters incrementing.

---

## 6. Verification & Analysis

### Task 1 — ISAKMP policy

```
R1# show crypto isakmp policy
Global IKE policy
Protection suite of priority 10
        encryption algorithm:   AES - Advanced Encryption Standard (256 bit keys). ! ← AES-256
        hash algorithm:         Secure Hash Standard 2 (256 bit)                    ! ← SHA-256
        authentication method:  Pre-Shared Key                                      ! ← PSK
        Diffie-Hellman group:   #14 (2048 bit)                                     ! ← group 14
        lifetime:               86400 seconds, no volume limit                     ! ← 24h
```

### Task 2 — Wildcard PSK

```
R1# show crypto isakmp key
Keyring      Hostname/Address                            Preshared Key
default      0.0.0.0/0.0.0.0                             cisco123   ! ← wildcard — matches any peer
```

### Task 3 — Transform-set and profile

```
R1# show crypto ipsec transform-set
Transform set default: { esp-256-aes esp-sha256-hmac  }
   will negotiate = { Transport,  },                               ! ← transport mode confirmed

R1# show crypto ipsec profile
IPSEC PROFILE DMVPN-PROFILE
        IKE Security Association lifetime: 86400 seconds (no kilobytes)
        Responder-Only (Y/N): N
        PFS (Y/N): N
        Mixed-mode : Disabled
        Transform sets={
                DMVPN-TS:  { esp-256-aes esp-sha256-hmac  },       ! ← references correct TS
        }
```

### Task 4 — Tunnel protection applied

```
R1# show interface Tunnel0
Tunnel0 is up, line protocol is up
  ...
  Tunnel protocol/transport multi-GRE/IP
  Tunnel protection via IPsec (profile "DMVPN-PROFILE" shared)    ! ← protection applied
```

### Task 5 — Phase 3 redirect/shortcut active

```
R1# show ip nhrp detail
10.100.0.2/32 via 10.100.0.2
   Tunnel0 created 00:05:22, expire 00:04:37
   Type: dynamic, Flags: registered used nhop                     ! ← R2 registration intact
   NBMA address: 198.51.100.1
10.100.0.3/32 via 10.100.0.3
   Type: dynamic, Flags: registered used nhop
   NBMA address: 192.0.2.1

R2# show ip nhrp (after spoke-to-spoke traffic triggered)
10.100.0.1/32 via 10.100.0.1
   Type: static, Flags: used                                      ! ← static NHS mapping
   NBMA address: 203.0.113.1
10.100.0.3/32 via 10.100.0.3
   Tunnel0 created 00:00:08, expire 00:01:51
   Type: dynamic, Flags: router rib nho shortcut                  ! ← shortcut entry for R3
   NBMA address: 192.0.2.1                                        ! ← R3's NBMA resolved
```

### Task 6 — Spoke-to-spoke shortcut and IPsec SAs

```
R2# traceroute 10.3.3.3 source Loopback0
  1 10.3.3.3 8 msec 6 msec 6 msec                                ! ← R3 directly — no hub hop!

R2# show crypto isakmp sa
dst             src             state          conn-id status
192.0.2.1       198.51.100.1    QM_IDLE           1001 ACTIVE    ! ← IKE SA to R3's NBMA
203.0.113.1     198.51.100.1    QM_IDLE           1000 ACTIVE    ! ← IKE SA to R1's NBMA

R2# show crypto ipsec sa peer 192.0.2.1
interface: Tunnel0
    Crypto map tag: Tunnel0-head-0, local addr 198.51.100.1
   protected vrf: (none)
   local  ident (addr/mask/prot/port): (198.51.100.1/255.255.255.255/47/0)
   remote ident (addr/mask/prot/port): (192.0.2.1/255.255.255.255/47/0)
   current_peer 192.0.2.1 port 500
    #pkts encaps: 10, #pkts encrypt: 10, #pkts digest: 10        ! ← packets encrypted (R2→R3)
    #pkts decaps: 8, #pkts decrypt: 8, #pkts verify: 8           ! ← packets decrypted (R3→R2)
```

---

## 7. Verification Cheatsheet

### IKEv1 ISAKMP Configuration

```
crypto isakmp policy 10
 encr aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400
!
crypto isakmp key <psk> address 0.0.0.0 0.0.0.0
```

| Command | Purpose |
|---------|---------|
| `crypto isakmp policy 10` | Define IKE Phase 1 parameters (lower number = higher priority) |
| `encr aes 256` | AES-256 encryption for the ISAKMP SA |
| `hash sha256` | SHA-256 HMAC for integrity |
| `group 14` | DH group 14 (2048-bit) — stronger than group 2 or 5 |
| `authentication pre-share` | Use PSK for peer authentication |
| `crypto isakmp key X address 0.0.0.0 0.0.0.0` | Wildcard PSK — matches any NBMA peer |

> **Exam tip:** `group 14` is the minimum DH group Cisco recommends for modern deployments. Groups 1, 2, and 5 are considered weak. The lab uses 14 rather than 5 to align with current best practice.

### IPsec Transform-Set and Profile

```
crypto ipsec transform-set DMVPN-TS esp-aes 256 esp-sha256-hmac
 mode transport
!
crypto ipsec profile DMVPN-PROFILE
 set transform-set DMVPN-TS
```

| Command | Purpose |
|---------|---------|
| `esp-aes 256` | AES-256 encryption for data |
| `esp-sha256-hmac` | SHA-256 HMAC for data integrity |
| `mode transport` | Encrypt GRE payload only — outer IP header stays intact |
| `set transform-set DMVPN-TS` | Bind the transform-set to this profile |

> **Exam tip:** DMVPN always uses `mode transport`, not `mode tunnel`. GRE provides the outer encapsulation — adding an IPsec tunnel-mode header would create an unnecessary third layer of encapsulation.

### Tunnel Protection

```
interface Tunnel0
 tunnel protection ipsec profile DMVPN-PROFILE
```

| Command | Purpose |
|---------|---------|
| `tunnel protection ipsec profile DMVPN-PROFILE` | Bind the IPsec profile to the mGRE tunnel |

> **Exam tip:** Applying `tunnel protection` to an mGRE tunnel causes the tunnel line protocol to briefly go down/up as the protection is installed. OSPF adjacencies will flap once — this is expected.

### Phase 3 NHRP Commands

```
! Hub only:
interface Tunnel0
 ip nhrp redirect

! Spokes only:
interface Tunnel0
 ip nhrp shortcut
```

| Command | Device | Purpose |
|---------|--------|---------|
| `ip nhrp redirect` | Hub | Sends NHRP redirect when forwarding spoke-to-spoke traffic |
| `ip nhrp shortcut` | Spokes | Allows spoke to install NHRP-resolved CEF shortcuts |

> **Exam tip:** Neither command changes the mGRE tunnel mode or the NHRP registration behavior. Spokes still register with the hub exactly as in Phase 1.

### Verification Commands

| Command | What to Look For |
|---------|-----------------|
| `show crypto isakmp policy` | Policy 10 with AES-256, SHA-256, group 14 |
| `show crypto isakmp sa` | State = QM_IDLE (established), one SA per NBMA peer |
| `show crypto isakmp key` | Wildcard entry (0.0.0.0/0.0.0.0) with preshared key |
| `show crypto ipsec transform-set` | `esp-256-aes esp-sha256-hmac`, mode = Transport |
| `show crypto ipsec sa` | Encaps/decaps counters incrementing for each active peer |
| `show crypto ipsec sa peer <nbma-ip>` | SA stats for one specific NBMA peer |
| `show interface Tunnel0` | `Tunnel protection via IPsec (profile "DMVPN-PROFILE")` |
| `show ip nhrp` | Shortcut entry (Flags: shortcut) on spokes after traffic trigger |
| `traceroute <spoke-lan> source Loopback0` | No hub hop after shortcut resolves |

### Common Phase 3 / IPsec Failure Causes

| Symptom | Likely Cause |
|---------|-------------|
| IKE SA stuck in MM_NO_STATE | ISAKMP policy mismatch (encryption/hash/group differ) |
| IKE SA stuck in MM_KEY_EXCH | PSK mismatch between peers |
| IPsec SA not forming after IKE | Transform-set mismatch; `mode transport` missing |
| Tunnel0 line protocol down after `tunnel protection` | Normal — waits for first IKE negotiation |
| Shortcut never forms despite Phase 3 commands | `ip nhrp redirect` missing on hub, or `ip nhrp shortcut` missing on spoke |
| Spoke-to-spoke still going via hub | Shortcut aged out; retrigger with spoke-to-spoke traffic |
| `show crypto ipsec sa` shows 0 encaps | Traffic not reaching the tunnel; check routing/CEF |

---

## 8. Solutions (Spoiler Alert!)

> Try to complete the lab challenge without looking at these steps first!

### Task 1: ISAKMP Policy

<details>
<summary>Click to view R1, R2, R3 configuration (identical on all three)</summary>

```bash
crypto isakmp policy 10
 encr aes 256
 hash sha256
 authentication pre-share
 group 14
 lifetime 86400
```
</details>

<details>
<summary>Click to view Verification Commands</summary>

```bash
show crypto isakmp policy
```
</details>

---

### Task 2: Wildcard Pre-Shared Key

<details>
<summary>Click to view R1, R2, R3 configuration (identical on all three)</summary>

```bash
crypto isakmp key cisco123 address 0.0.0.0 0.0.0.0
```
</details>

<details>
<summary>Click to view Verification Commands</summary>

```bash
show crypto isakmp key
```
</details>

---

### Task 3: IPsec Transform-Set and Profile

<details>
<summary>Click to view R1, R2, R3 configuration (identical on all three)</summary>

```bash
crypto ipsec transform-set DMVPN-TS esp-aes 256 esp-sha256-hmac
 mode transport
!
crypto ipsec profile DMVPN-PROFILE
 set transform-set DMVPN-TS
```
</details>

<details>
<summary>Click to view Verification Commands</summary>

```bash
show crypto ipsec transform-set
show crypto ipsec profile
```
</details>

---

### Task 4: Apply Tunnel Protection

<details>
<summary>Click to view R1 configuration</summary>

```bash
interface Tunnel0
 tunnel protection ipsec profile DMVPN-PROFILE
```
</details>

<details>
<summary>Click to view R2 configuration</summary>

```bash
interface Tunnel0
 tunnel protection ipsec profile DMVPN-PROFILE
```
</details>

<details>
<summary>Click to view R3 configuration</summary>

```bash
interface Tunnel0
 tunnel protection ipsec profile DMVPN-PROFILE
```
</details>

<details>
<summary>Click to view Verification Commands</summary>

```bash
show interface Tunnel0           ! look for "Tunnel protection via IPsec"
show ip ospf neighbor            ! OSPF should recover to FULL after brief flap
```
</details>

---

### Task 5: Enable Phase 3 NHRP

<details>
<summary>Click to view R1 (hub) configuration</summary>

```bash
interface Tunnel0
 ip nhrp redirect
```
</details>

<details>
<summary>Click to view R2 (spoke) configuration</summary>

```bash
interface Tunnel0
 ip nhrp shortcut
```
</details>

<details>
<summary>Click to view R3 (spoke) configuration</summary>

```bash
interface Tunnel0
 ip nhrp shortcut
```
</details>

---

### Task 6: Trigger and Verify

<details>
<summary>Click to view Commands</summary>

```bash
! From R2 — trigger spoke-to-spoke traffic
ping 10.3.3.3 source Loopback0 repeat 10
traceroute 10.3.3.3 source Loopback0

! On R2 — verify shortcut and IPsec
show ip nhrp
show crypto isakmp sa
show crypto ipsec sa peer 192.0.2.1

! On R1 — confirm hub is NOT forwarding subsequent spoke-to-spoke packets
show ip traffic  ! GRE forwarding counter should not increase during direct spoke-to-spoke
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

### Ticket 1 — All Encrypted Tunnels Go Down After a Config Change

The team applied a DMVPN configuration change and now no spoke can communicate with the hub. DMVPN sessions show as DOWN. OSPF adjacencies are lost.

**Inject:** `python3 scripts/fault-injection/inject_scenario_01.py --host <eve-ng-ip>`

**Success criteria:** DMVPN sessions return to UP state. OSPF adjacencies re-establish. Encrypted traffic resumes between all peers.

<details>
<summary>Click to view Diagnosis Steps</summary>

```bash
! Check DMVPN session state
R1# show dmvpn

! Check IKE SA state
R1# show crypto isakmp sa
R2# show crypto isakmp sa

! Debug IKE negotiation (brief)
R1# debug crypto isakmp
! Look for: "ISAKMP:(0): atts are not acceptable" — policy mismatch
! Or: "ISAKMP:(0): construct_proposal failed" — no matching policy

! Compare ISAKMP policies
R1# show crypto isakmp policy
R2# show crypto isakmp policy
```

**Root cause:** R2's ISAKMP policy DH group has been changed from 14 to 2. IKE Phase 1 fails because R1 proposes group 14 and R2 only accepts group 2 — no matching policy. DMVPN sessions drop because IKE cannot establish the ISAKMP SA needed to protect NHRP registration.

</details>

<details>
<summary>Click to view Fix</summary>

```bash
R2# configure terminal
R2(config)# crypto isakmp policy 10
R2(config-isakmp)# group 14
R2(config-isakmp)# end

! Verify IKE re-establishes
R2# show crypto isakmp sa     ! state should move to QM_IDLE
R1# show dmvpn               ! R2 entry should return to UP
R1# show ip ospf neighbor    ! FULL adjacency should recover
```
</details>

---

### Ticket 2 — Spoke-to-Spoke Traffic Still Routes Through the Hub

Both spokes are connected and OSPF is working. However, traceroute from R2 to R3 always shows R1 in the path — even after multiple pings to trigger shortcut resolution.

**Inject:** `python3 scripts/fault-injection/inject_scenario_02.py --host <eve-ng-ip>`

**Success criteria:** Traceroute from R2 Loopback0 to R3 Loopback0 shows R3 directly (no R1 hop). `show ip nhrp` on R2 shows a shortcut entry for R3.

<details>
<summary>Click to view Diagnosis Steps</summary>

```bash
! Trigger spoke-to-spoke traffic
R2# ping 10.3.3.3 source Loopback0 repeat 20

! Check if shortcuts are forming on the spoke
R2# show ip nhrp      ! no shortcut entry = Phase 3 not working

! Check hub for redirect configuration
R1# show running-config | section Tunnel0 | include nhrp
! Missing "ip nhrp redirect" = hub will never send redirects

! Check spoke for shortcut configuration
R2# show running-config | section Tunnel0 | include nhrp
! Missing "ip nhrp shortcut" = spoke will ignore redirect messages
```

**Root cause:** `ip nhrp redirect` has been removed from R1's Tunnel0. The hub forwards spoke-to-spoke traffic but never sends NHRP redirect messages. R2 has no way to learn R3's NBMA address, so shortcuts never form.

</details>

<details>
<summary>Click to view Fix</summary>

```bash
R1# configure terminal
R1(config)# interface Tunnel0
R1(config-if)# ip nhrp redirect
R1(config-if)# end

! Retrigger spoke-to-spoke traffic
R2# ping 10.3.3.3 source Loopback0 repeat 10
R2# show ip nhrp      ! shortcut entry for 10.100.0.3 should appear
R2# traceroute 10.3.3.3 source Loopback0   ! R1 should no longer appear
```
</details>

---

### Ticket 3 — IPsec Not Encrypting Spoke-to-Spoke Packets

Spoke-to-spoke shortcuts are forming and traffic reaches R3, but a packet capture on the underlay shows GRE packets are not encrypted. The security team flags this as a compliance failure.

**Inject:** `python3 scripts/fault-injection/inject_scenario_03.py --host <eve-ng-ip>`

**Success criteria:** `show crypto ipsec sa peer 192.0.2.1` on R2 shows incrementing encaps/decaps counters. Spoke-to-spoke traffic is encrypted.

<details>
<summary>Click to view Diagnosis Steps</summary>

```bash
! Check if IPsec SAs exist for the spoke-to-spoke path
R2# show crypto ipsec sa peer 192.0.2.1
! If no SA or 0 encaps — IPsec not protecting that path

! Check if tunnel protection is applied on R2
R2# show interface Tunnel0
! Missing "Tunnel protection via IPsec" = profile not applied

! Check if protection is applied on R3
R3# show interface Tunnel0

! Compare — if R1 has protection but R3 does not, the direct R2→R3 path is unprotected
R3# show running-config | section Tunnel0 | include protection
```

**Root cause:** `tunnel protection ipsec profile DMVPN-PROFILE` has been removed from R3's Tunnel0. R3 sends unencrypted GRE; R2 receives unencrypted GRE but expects encrypted — the mismatch means the spoke-to-spoke direct path works at the IP level but without IPsec protection.

</details>

<details>
<summary>Click to view Fix</summary>

```bash
R3# configure terminal
R3(config)# interface Tunnel0
R3(config-if)# tunnel protection ipsec profile DMVPN-PROFILE
R3(config-if)# end

! Re-trigger spoke-to-spoke traffic
R2# ping 10.3.3.3 source Loopback0
R2# show crypto ipsec sa peer 192.0.2.1   ! encaps/decaps should increment
R3# show crypto ipsec sa peer 198.51.100.1 ! mirrored SA on R3
```
</details>

---

## 10. Lab Completion Checklist

### Core Implementation

- [ ] ISAKMP policy 10 (AES-256 / SHA-256 / group 14 / 86400s) configured on R1, R2, R3
- [ ] Wildcard PSK `cisco123` (address 0.0.0.0 0.0.0.0) configured on R1, R2, R3
- [ ] Transform-set `DMVPN-TS` (esp-aes 256, esp-sha256-hmac, transport mode) on R1, R2, R3
- [ ] IPsec profile `DMVPN-PROFILE` referencing `DMVPN-TS` on R1, R2, R3
- [ ] `tunnel protection ipsec profile DMVPN-PROFILE` applied on Tunnel0 of R1, R2, R3
- [ ] `show interface Tunnel0` shows `Tunnel protection via IPsec` on all three members
- [ ] `ip nhrp redirect` added to R1 Tunnel0
- [ ] `ip nhrp shortcut` added to R2 and R3 Tunnel0
- [ ] Spoke-to-spoke traffic triggered; `show ip nhrp` on R2 shows shortcut entry for R3
- [ ] Traceroute from R2 to R3 shows no R1 hub hop
- [ ] `show crypto ipsec sa peer 192.0.2.1` on R2 shows non-zero encaps/decaps

### Troubleshooting

- [ ] Ticket 1 injected, diagnosed (ISAKMP DH group mismatch), and fixed
- [ ] Ticket 2 injected, diagnosed (ip nhrp redirect missing on hub), and fixed
- [ ] Ticket 3 injected, diagnosed (tunnel protection missing on R3), and fixed
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
