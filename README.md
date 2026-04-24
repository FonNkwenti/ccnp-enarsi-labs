# CCNP ENARSI (300-410) Lab Series

A comprehensive set of hands-on labs for the CCNP ENARSI (300-410) exam. **47 labs** across **9 topics**.

## Getting Started

1. Clone with submodules: git clone --recurse-submodules <repo-url>
2. Install Python dependencies: pip install -r requirements.txt
3. Set up EVE-NG (see .agent/skills/eve-ng/SKILL.md for constraints)
4. Navigate to a lab and follow the workbook

## Lab Topics

<!-- lab-index-start -->

### eigrp

EIGRP Routing (classic and named mode, dual-stack, VRF and global, DUAL, stubs, load balancing, metrics). **6 labs.**

- [ ] lab-00-classic-adjacency — Foundation (classic mode, neighbor relationships, authentication)
- [ ] lab-01-named-mode-dual-stack — Named mode with IPv4/IPv6 dual-stack
- [ ] lab-02-dual-and-stubs — DUAL algorithm, feasible successors, stub routers
- [ ] lab-03-load-balancing-vrf — Equal/unequal-cost load balancing, VRF instances
- [ ] lab-04-capstone-config — Capstone I: Full EIGRP configuration challenge
- [ ] lab-05-capstone-troubleshooting — Capstone II: Comprehensive EIGRP troubleshooting

### ospf

OSPF Routing v2 and v3 (dual-stack, neighbors, network types, area types, router roles, virtual links, path preference). **7 labs.**

- [ ] lab-00-single-area-foundation — Foundation (single area, neighbor relationships, authentication)
- [ ] lab-01-multi-area-path-preference — Multi-area design, ABR/ASBR roles, path selection
- [ ] lab-02-network-types — Broadcast, P2P, NBMA, point-to-multipoint networks
- [ ] lab-03-area-types-virtual-link — Stub/totally-stub/NSSA areas, virtual links
- [ ] lab-04-ospfv3-dual-stack — OSPFv3 with IPv4/IPv6 dual-stack
- [ ] lab-05-capstone-config — Capstone I: Full OSPF configuration challenge
- [ ] lab-06-capstone-troubleshooting — Capstone II: Comprehensive OSPF troubleshooting

### bgp

BGP Routing iBGP and eBGP (unicast and VRF-Lite, dual-stack, neighbor relationships, best-path attributes, route reflectors, policies). **6 labs.**

- [ ] lab-00-ebgp-ibgp-foundation — Foundation (eBGP and iBGP neighbors, 4-byte AS, authentication)
- [ ] lab-01-neighbor-features-dual-stack — Advanced neighbor features, dual-stack, route refresh
- [ ] lab-02-path-preference — Best-path attributes, local preference, AS-path manipulation
- [ ] lab-03-rr-policies-vrf — Route reflectors, inbound/outbound policies, VRF-Lite BGP
- [ ] lab-04-capstone-config — Capstone I: Full BGP configuration challenge
- [ ] lab-05-capstone-troubleshooting — Capstone II: Comprehensive BGP troubleshooting

### route-control

Route Control and Redistribution (administrative distance, route maps, loop prevention, redistribution, summarization). **6 labs.** *Requires: eigrp, ospf, bgp*

- [ ] lab-00-admin-distance — Foundation (AD troubleshooting across protocols)
- [ ] lab-01-route-maps — Route maps, attributes, tagging, filtering
- [ ] lab-02-loop-prevention — Filtering, tagging, split horizon, route poisoning, downward bit
- [ ] lab-03-redistribution-summarization — Redistribution and auto/manual summarization (paired)
- [ ] lab-04-capstone-config — Capstone I: Full route control configuration challenge
- [ ] lab-05-capstone-troubleshooting — Capstone II: Comprehensive route control troubleshooting

### pbr-vrf-bfd

Policy Routing, VRF-Lite, and BFD (policy-based routing, VRF-Lite inter-VRF leaking, BFD convergence). **4 labs.** *Requires: ospf, bgp*

- [ ] lab-00-pbr-bfd — PBR and BFD acceleration (paired: BFD for next-hop tracking in PBR)
- [ ] lab-01-vrf-lite-leaking — VRF-Lite design with inter-VRF route leaking
- [ ] lab-02-capstone-config — Capstone I: Full PBR/VRF/BFD configuration challenge
- [ ] lab-03-capstone-troubleshooting — Capstone II: Comprehensive PBR/VRF/BFD troubleshooting

### mpls-l3vpn

MPLS and Layer 3 VPN (MPLS forwarding, LDP, LSP, MP-BGP, VRF, route distinguisher, route target, VPNv4). **3 labs.** *Requires: bgp*

- [ ] lab-00-mpls-forwarding — MPLS Forwarding + L3VPN Fundamentals
- [ ] lab-01-capstone-config — MPLS L3VPN Full Mastery — Capstone I
- [ ] lab-02-capstone-troubleshooting — MPLS L3VPN Comprehensive Troubleshooting — Capstone II

### dmvpn

DMVPN (Dynamic Multipoint VPN) — single-hub topology (GRE, mGRE, NHRP, IPsec, spoke-to-spoke shortcut). **4 labs.** *Requires: ospf*

- [ ] `lab-00-phase1-hub-spoke` — DMVPN Phase 1 — Hub-and-Spoke with mGRE and NHRP
- [ ] `lab-01-phase3-shortcuts` — DMVPN Phase 3 — Spoke-to-Spoke Shortcuts with IPsec Protection
- [ ] `lab-02-capstone-config` — DMVPN Full Configuration Mastery — Capstone I
- [ ] `lab-03-capstone-troubleshooting` — DMVPN Comprehensive Troubleshooting — Capstone II

### infrastructure-security

Infrastructure Security (AAA/TACACS+/RADIUS, ACLs, CoPP, IPv6 First Hop Security). **5 labs.**

- [ ] lab-00-aaa — IOS AAA (TACACS+, RADIUS, local authentication)
- [ ] lab-01-acls-urpf — ACLs (IPv4/IPv6, time-based), uRPF (unicast RPF)
- [ ] lab-02-copp-ipv6-fhs — CoPP, IPv6 First Hop Security (RA guard, DHCP guard, binding table, ND inspection/snooping)
- [ ] lab-03-capstone-config — Capstone I: Full infrastructure security configuration challenge
- [ ] lab-04-capstone-troubleshooting — Capstone II: Comprehensive infrastructure security troubleshooting

### infrastructure-services

Infrastructure Services (device management planes, SNMP, syslog, DHCP, IP SLA, NetFlow, CCI Assurance). **6 labs.**

- [ ] lab-00-device-management — Management planes (console/VTY, Telnet/HTTP(S)/SSH/SCP/(T)FTP)
- [ ] lab-01-snmp-syslog — SNMP v2c/v3 and syslog/logging/timestamps/telemetry (observability pair)
- [ ] lab-02-dhcp — DHCP client/server/relay for IPv4/IPv6 with options
- [ ] lab-03-ip-sla-netflow — IP SLA, object tracking, NetFlow v9/Flexible NetFlow/IPFIX (monitoring pair)
- [ ] lab-04-capstone-config — Capstone I: Full infrastructure services configuration challenge
- [ ] lab-05-capstone-troubleshooting — Capstone II: Comprehensive infrastructure services troubleshooting

<!-- lab-index-end -->

## Development

Lab creation uses skills in .agent/skills/. See CLAUDE.md for context.
