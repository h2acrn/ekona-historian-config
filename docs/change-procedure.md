# Historian / OI Gateway Change Procedure

## Purpose

This procedure defines the minimum workflow for keeping AVEVA Historian aligned with upstream tag/configuration changes while formal LabVIEW-side configuration control is still being established.

This repository is the official Historian-side configuration snapshot and comparison record.

It is intended to:
- maintain a recoverable snapshot of Historian configuration
- track what points are visible through OI Gateway
- track what points are currently configured for Historian acquisition
- identify mismatches between OI Gateway availability and Historian tag configuration
- support troubleshooting, onboarding, and configuration review

---

## Scope

This procedure applies to:
- Full Historian configuration exports
- OI Gateway exported point lists
- Historian tag acquisition exported tag lists
- Comparison summaries generated from those exports

This procedure does not replace upstream LabVIEW/controller-side configuration management.
It provides downstream Historian-side traceability and drift detection.

---

## Roles

### Historian-side owner
Suggested owner:
- Ali

Responsibilities:
- maintain this repository
- capture exports when required
- run comparison tools
- document notable changes and mismatches
- commit and push updated snapshots

### Upstream configuration owners
Examples:
- Matt
- others maintaining LabVIEW/controller-side configuration

Responsibilities:
- communicate additions/removals/renames that affect exposed tags
- eventually maintain the official upstream configuration repository/process

---

## Trigger Events

A new snapshot/update should be taken when any of the following occurs:

### Upstream exposure changes
- a point is added on the LabVIEW/controller side
- a point is removed
- a point is renamed
- browse structure changes
- OPC UA / OI Gateway item exposure changes

### Historian changes
- a Historian tag is added
- a Historian tag is removed
- a Historian tag is renamed
- engineering units / descriptions / ranges are updated
- acquisition configuration changes

### System events
- before major Historian changes
- after major Historian changes
- before upgrades
- after upgrades
- before vendor troubleshooting
- after vendor troubleshooting
- after commissioning milestones
- when establishing a known-good baseline

---

## Minimum Workflow

### 1. Detect or receive notification of change
A change may originate from:
- LabVIEW/controller configuration update
- OI Gateway reconfiguration
- Historian onboarding/removal/update
- troubleshooting or maintenance activity

### 2. Refresh exports
Capture the relevant current-state exports:
- Full Historian configuration export
- OI Gateway export(s)
- Historian tag export(s)

### 3. Update repository files
Replace the current files in:
- `exports/full/raw/`
- `exports/oi-gateway/`
- `exports/tags/`

Then run:
- `scripts/normalize_exports.ps1`
- `scripts/compare_exports.py`

### 4. Review compare summary
Review:
- `notes/latest-compare-summary.md`

Classify mismatches as one of:
- real missing Historian onboarding
- naming alias / formatting issue
- intentional non-historized item
- export/parsing issue requiring script improvement

### 5. Action as needed
If required:
- add missing Historian tags
- correct misnamed tags
- document accepted aliases
- record intentional exclusions

### 6. Record notes
Update:
- `notes/snapshot-notes.md`
- `docs/open-items.md` as needed

### 7. Commit and push
Commit with a clear message and push changes.

Tag only when the state is an important milestone/baseline.

---

## Repository Meaning

### `exports/full/raw/`
Raw import-capable full Historian export.
This file should remain untouched after export.

### `exports/full/normalized/`
Normalized copy of the full export for Git diff/review purposes.

### `exports/oi-gateway/`
Current exported list of points/items available through OI Gateway.

### `exports/tags/`
Current exported list of Historian tags configured for acquisition.

### `notes/latest-compare-summary.md`
Machine-generated current mismatch summary.

### `notes/snapshot-notes.md`
Human-authored notes about what changed and why.

### `docs/open-items.md`
Running list of unresolved mismatches, accepted aliases, and follow-up items.

---

## Decision Rules for Mismatches

### Case 1 — Available in OI Gateway but missing from Tags
Interpretation:
- the point may have been added upstream but not yet onboarded into Historian
- or it may be intentionally excluded

Action:
- verify whether Historian should monitor it
- if yes, add to Historian and refresh snapshot
- if no, record as intentional in `docs/open-items.md`

### Case 2 — Present in Tags but missing from OI Gateway
Interpretation:
- the point may have been removed upstream
- the OI Gateway export may have changed format/path
- the tag may be stale/orphaned in Historian

Action:
- verify whether the source still exists
- determine whether the Historian tag should remain
- record outcome in `docs/open-items.md`

### Case 3 — Apparent mismatch caused by naming differences
Examples:
- `calc_` prefix
- `_1` suffix
- `time` vs `systemtime`

Action:
- add alias rule if appropriate
- document accepted naming equivalence

---

## Current Governance Limitation

This repository is currently the official Historian-side control point, but it is not yet the official upstream source of truth for LabVIEW/controller tag configuration.

Until an upstream configuration repository/procedure is in place:
- this repo should be used to detect drift
- compare summaries should be reviewed after known upstream changes
- significant mismatches should be documented and resolved deliberately

---

## Recommended Commit Message Format

Use:

`<area>: <summary>`

Examples:
- `baseline: add initial historian configuration snapshot`
- `snapshot: refresh exports after Gen2 tag additions`
- `compare: add alias handling for calc and system time tags`
- `process: add historian change procedure and open items tracker`

---

## Tagging Guidance

Use Git tags only for milestone states, for example:
- `baseline-initial`
- `stable-historian-baseline`
- `post-gen2-onboarding`
- `before-upgrade-2026-04`

Do not tag every routine snapshot.