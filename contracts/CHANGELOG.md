# Contracts Changelog

All notable changes to contract schemas are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `smart_guitar_toolbox_telemetry_v1` - Smart Guitar telemetry contract for cross-repo validation
- `toolbox_smart_guitar_safe_export_v1` - Safe export format for Smart Guitar data
- `viewer_pack_v1` - Viewer pack schema for instrument geometry visualization
- `cam_policy` - CAM policy schema (non-versioned, internal) + SHA256 hash
- `qa_core` - QA core schema (non-versioned, internal) + SHA256 hash
- `CONTRACTS_VERSION.json` - Sentinel file for governance (Scenario B)
- `CHANGELOG.md` - This file

### Changed
- None

### Deprecated
- None

### Removed
- None

---

## Governance Notes

- **Immutability**: Once `CONTRACTS_VERSION.json` has `public_released: true`, all `*_v1.schema.json` and `*_v1.schema.sha256` files become immutable.
- **Changelog requirement**: Any schema or hash change requires updating this CHANGELOG.md with a mention of the contract stem.
- **SHA256 format**: All `.schema.sha256` files must contain exactly one line of 64 lowercase hex characters.
