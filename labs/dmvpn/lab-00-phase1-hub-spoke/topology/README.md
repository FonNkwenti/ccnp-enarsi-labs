# Topology — DMVPN Lab 00: Phase 1 Hub-and-Spoke

## Topology Summary

Four IOSv routers in a hub-and-spoke arrangement:
- R1 (DMVPN hub / NHS) connected to R4 (ISP/transit)
- R2 (Spoke 1 / Branch A) connected to R4
- R3 (Spoke 2 / Branch B) connected to R4
- R4 provides underlay transit only — no DMVPN membership

## EVE-NG Import Instructions

1. Log in to the EVE-NG web interface.
2. Navigate to **File > Import** (or use the Management > Labs menu).
3. Select the `.unl` file for this lab when it is available.
4. The lab will appear in your lab list under the `dmvpn` folder.
5. Open the lab and start all nodes before running `setup_lab.py`.

## Node Configuration Reference

| Device | Role | EVE-NG Template | RAM | Image |
|--------|------|----------------|-----|-------|
| R1 | DMVPN Hub / NHS | Cisco IOSv | 512 MB | vios-adventerprisek9-m.SPA.156-2.T |
| R2 | Spoke 1 — Branch A | Cisco IOSv | 512 MB | vios-adventerprisek9-m.SPA.156-2.T |
| R3 | Spoke 2 — Branch B | Cisco IOSv | 512 MB | vios-adventerprisek9-m.SPA.156-2.T |
| R4 | Simulated ISP/Transit | Cisco IOSv | 512 MB | vios-adventerprisek9-m.SPA.156-2.T |

## Starting the Lab

1. Start all four nodes from the EVE-NG UI.
2. Wait approximately 60–90 seconds for IOSv to boot fully.
3. Note the console port numbers assigned to each node in the EVE-NG UI.
4. Run `python3 setup_lab.py --host <eve-ng-ip>` — the script discovers ports automatically via the REST API.

## Exporting the Lab

If you make topology changes (add/remove nodes or links) in the EVE-NG canvas:
1. Navigate to **File > Export** in the EVE-NG UI.
2. Save the `.unl` file alongside this `topology/` directory if you want to track changes.
3. The `topology.drawio` file documents the intended layout — update it to reflect any topology changes.
