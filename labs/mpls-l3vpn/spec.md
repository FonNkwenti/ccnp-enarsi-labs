# MPLS and Layer 3 VPN — Lab Specification

## Exam Reference

- **Exam:** Implementing Cisco Enterprise Advanced Routing and Services (300-410)
- **Blueprint Bullets:**
  - 2.1: Describe MPLS operations (LSR, LDP, label switching, LSP)
  - 2.2: Describe MPLS Layer 3 VPN

## Topology Summary

A 3-router Service Provider MPLS core with optional customer edge devices:

- **Core (always active):** R1 (PE), R2 (P core router), R3 (PE) — forms the MPLS backbone with LDP-advertised LSPs
- **Optional (lab-01+):** R4 (CE for VRF-A), R5 (CE for VRF-B) — customer endpoints
- **Addressing:** IPv4 loopback and link subnets pre-planned for all devices; VPN RDs/RTs assigned per VRF
- **Platforms:** iosv (all routers)

## Lab Progression

| # | Folder | Title | Difficulty | Time | Type | Blueprint Refs | Devices |
|---|--------|-------|-----------|------|------|----------------|---------|
| 00 | lab-00-mpls-forwarding | MPLS Forwarding + L3VPN Fundamentals | Foundation | 90m | progressive | 2.1, 2.2 | R1, R2, R3 |
| 01 | lab-01-capstone-config | MPLS L3VPN Full Mastery — Capstone I | Advanced | 120m | capstone_i | 2.1, 2.2 | R1, R2, R3, R4, R5 |
| 02 | lab-02-capstone-troubleshooting | MPLS L3VPN Comprehensive Troubleshooting — Capstone II | Advanced | 120m | capstone_ii | 2.1, 2.2 | R1, R2, R3, R4, R5 |

## Blueprint Coverage Matrix

| Blueprint Bullet | Description | Covered In |
|-----------------|-------------|------------|
| 2.1 | MPLS operations (LSR, LDP, label switching, LSP) | lab-00, lab-01, lab-02 |
| 2.2 | MPLS Layer 3 VPN (VRF, RD, RT, VPNv4, PE-CE) | lab-00, lab-01, lab-02 |

## Design Decisions

- **Minimum-sized topic:** Only 2 describe-only bullets; 3-lab series is sufficient (1 foundation + 2 capstones)
- **Progressive design:** Lab-00 introduces MPLS forwarding plane (LSR/P/PE roles, LDP, LSP) and L3VPN concepts (VRF/RD/RT/VPNv4) in a controlled 3-router topology
- **Capstone integration:** Both capstones include customer edge devices (R4, R5) to demonstrate PE-CE relationships and VRF separation
- **PE/P separation:** R1 and R3 act as PEs (attach customers), R2 acts as core P router; lab-00 focuses on SP-internal MPLS, capstones add customer perspective
- **Dependency:** Assumes BGP topic (for MP-BGP VPNv4) is completed before building these labs

