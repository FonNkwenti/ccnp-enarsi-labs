# Topology — DMVPN Lab 01: Phase 3 with IPsec

## Topology Summary

Same four-router topology as lab-00. No physical topology changes between Phase 1 and Phase 3 — the upgrade is entirely software (NHRP + IPsec config additions on the existing mGRE tunnel interfaces).

- R1 (DMVPN hub / NHS) connected to R4 (ISP/transit)
- R2 (Spoke 1 / Branch A) connected to R4
- R3 (Spoke 2 / Branch B) connected to R4
- R4 provides underlay transit only — unchanged from lab-00

## EVE-NG Import Instructions

Use the same EVE-NG lab topology imported for lab-00. No new .unl file is needed — the topology is identical. Simply run `setup_lab.py` to push the lab-01 initial configs (lab-00 solutions) over the existing nodes.

If you need to import fresh:
1. Log in to the EVE-NG web interface.
2. Navigate to **File > Import**.
3. Select the `.unl` file for this lab.
4. Start all nodes before running `setup_lab.py`.

## Node Configuration Reference

| Device | Role | EVE-NG Template | RAM | Image |
|--------|------|----------------|-----|-------|
| R1 | DMVPN Hub / NHS | Cisco IOSv | 512 MB | vios-adventerprisek9-m.SPA.156-2.T |
| R2 | Spoke 1 — Branch A | Cisco IOSv | 512 MB | vios-adventerprisek9-m.SPA.156-2.T |
| R3 | Spoke 2 — Branch B | Cisco IOSv | 512 MB | vios-adventerprisek9-m.SPA.156-2.T |
| R4 | Simulated ISP/Transit | Cisco IOSv | 512 MB | vios-adventerprisek9-m.SPA.156-2.T |

## Starting the Lab

1. Start all four nodes from the EVE-NG UI.
2. Wait ~60–90 seconds for IOSv to boot.
3. Run `python3 setup_lab.py --host <eve-ng-ip>` to load the Phase 1 initial state.
4. Follow workbook.md starting from Task 1.

## Exporting the Lab

If you modify the topology, export the updated `.unl` via **File > Export** in EVE-NG and save it alongside this `topology/` directory.
