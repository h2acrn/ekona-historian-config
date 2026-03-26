# Historian Configuration Repository

## Purpose

This repository stores controlled exports of the AVEVA Historian configuration so changes can be tracked over time, reviewed, and compared when troubleshooting or onboarding new points.

The repository is intended to capture the current known state of:

1. Full Historian configuration export
2. OI Gateway browse/export lists
3. Historian tag acquisition/export lists

This is a configuration snapshot repository, not a software development repository.

---

## Repository Structure

### `exports/full/`
Contains the latest full configuration export generated from the Historian Configuration Export and Import tool.

Example:
- `Historian_Full_Configuration_Export.txt`

### `exports/oi-gateway/`
Contains exports of the points visible through OI Gateway / OPC UA browse structure for the main source groups.

Examples:
- `DeltaV_Gen2_BMS_FARC.csv`
- `Gen2_PCS_LabVIEW.csv`
- `SFR_PCS_LabVIEW.csv`

### `exports/tags/`
Contains exports of the Historian tags currently configured for acquisition from the gateway/source groups.

Examples:
- `DeltaV_Gen2_BMS_FARC.csv`
- `Gen2_PCS_LabVIEW.csv`
- `SFR_PCS_LabVIEW.csv`

### `notes/`
Contains markdown notes describing important snapshots, changes, baselines, or troubleshooting context.

### `scripts/`
Helper scripts for cleaning, normalizing, and comparing exports.

---

## Export Meaning

### Full Export
Use this to capture the broad Historian configuration state.
Useful for:
- major milestones
- before/after significant config changes
- before upgrades
- before vendor troubleshooting
- known-good baselines

### OI Gateway Export
Use this to capture what points are available upstream through the gateway / OPC UA browse layer.
Useful for:
- confirming whether a point was exposed at all
- tracking browse structure changes
- tracking newly available points

### Tags Export
Use this to capture what points are actually configured for Historian acquisition.
Useful for:
- confirming whether an available point was historized
- tracking added/removed/renamed tags
- reviewing historian onboarding progress

---

## Working Approach

This repository stores the latest exported files in-place.
History is tracked using:
- Git commit history for normal changes
- Git tags for important milestone baselines

The repo should remain simple and readable.

---

## When to Commit Changes

Commit new exports when there is a meaningful change, such as:

- new points exposed in OI Gateway
- new points added to Historian
- points renamed or removed
- major historian configuration changes
- before/after significant troubleshooting
- before/after upgrades
- creation of a known-good baseline

Do not commit trivial or accidental export churn without a reason.

---

## Commit Message Convention

Recommended format:

`<area>: <summary>`

Examples:
- `full: baseline export before Gen2 changes`
- `oi-gateway: add new Gen2 LabVIEW browse points`
- `tags: add SFR historian tags`
- `full: export after OI Gateway reconfiguration`
- `notes: document stable commissioning baseline`

If more than one area changed:

- `snapshot: update full, oi-gateway, and tags after Gen2 onboarding`

---

## Git Tag Convention

Use Git tags only for important baselines or milestone states.

Examples:
- `baseline-initial`
- `pre-gen2-onboarding`
- `post-gen2-tag-addition`
- `stable-historian-baseline`
- `before-upgrade-2026-04`

Tags should represent states that may need to be referenced later.

---

## Recommended Workflow

1. Make the required configuration change
2. Export the relevant files
3. Replace the corresponding files in `exports/`
4. Add or update a note in `notes/`
5. Commit with a clear message
6. Add a tag if the state is an important milestone
7. Push

---

## Ownership

Suggested owner:
- Ali for Historian configuration snapshots

Related but separate upstream configuration repositories may be maintained independently.