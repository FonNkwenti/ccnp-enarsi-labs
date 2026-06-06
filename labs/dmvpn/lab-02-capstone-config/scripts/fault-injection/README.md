# Fault Injection — DMVPN Lab 02: Capstone I

Each script injects one fault. Work through the corresponding ticket in
`workbook.md` Section 9 before looking at the solution.

## Prerequisites

- The lab `.unl` file must already be **imported** into EVE-NG (one-time manual step via EVE-NG web UI)
- All nodes must be **started** in EVE-NG
- Python 3.x and `netmiko` installed (`pip install netmiko`)
- The lab must be in the **solution state** before injecting any fault — run `apply_solution.py` first if unsure

## Scenarios

### Scenario 01 — Missing NHRP Multicast Map (R2 and R3)

Removes `ip nhrp map multicast 203.0.113.1` from Tunnel0 on both R2 and R3.

NHRP unicast registrations continue to work, so the tunnels stay up, but
OSPF hello delivery fails because multicast is no longer mapped to the hub's
NBMA address. OSPF adjacencies drop and routing tables go stale.

### Scenario 02 — NHRP Network-ID Mismatch (R3)

Changes R3's NHRP network-id on Tunnel0 from 100 to 200.

R3 can no longer register with the hub. R3's tunnel remains up but NHRP
mappings are never established, so traffic to and from R3 is black-holed.
R1 and R2 are unaffected.

### Scenario 03 — ISAKMP DH Group Mismatch (R3)

Changes R3's ISAKMP policy 10 DH group from 14 to 5.

Spoke-to-spoke IKE Phase 1 fails when R2 tries to build a direct shortcut
tunnel to R3 — R2 proposes DH group 14, R3 only accepts group 5. Hub-to-spoke
sessions between R1 and R3 are unaffected. Traceroute from R2 to R3 continues
to traverse R1 indefinitely.

## Inject a Fault

```bash
python3 inject_scenario_01.py --host <eve-ng-ip>   # Ticket 1
python3 inject_scenario_02.py --host <eve-ng-ip>   # Ticket 2
python3 inject_scenario_03.py --host <eve-ng-ip>   # Ticket 3
```

## Restore

```bash
python3 apply_solution.py --host <eve-ng-ip>
python3 apply_solution.py --host <eve-ng-ip> --reset   # full write-erase + restore
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Partial restore failure (`apply_solution.py` only) |
| 2 | `--host` not provided (placeholder value detected) |
| 3 | EVE-NG connectivity or port discovery error |
| 4 | Pre-flight check failed — lab not in expected state (inject scripts only) |
