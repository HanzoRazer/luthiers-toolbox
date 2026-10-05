# Detector runs

Normal mode and full-repository mode are the same command: `python -m code_audit <repository> --json`. There is no second official full-repository switch. The direct command is `python -m code_audit <file> --json`, and the implementation scans that file's parent directory.

`HOLLOW_GUARANTEE_001` does not use the discovered file list. It reads only the immediate `*.yml` / `*.yaml` children of `<scan-root>/.github/workflows`.

| Fixture | Normal scan | Direct scan | Full-repo scan | Classification |
|---|---|---|---|---|
| F-2 | 8,111 findings; 2 `hollow_guarantee`, both `client_lint_build.yml`; F-2 not reported | Parent `services/api/tests/`: 1,714 findings; 0 `hollow_guarantee`; F-2 not reported | Same run as the normal scan | `SIGNATURE_GAP` |
| F-3 | Same repository scan; F-3 not reported | `edge_to_dxf.py` parent: 211 findings, 0 hollow. Orchestrator parent: 161 findings, 0 hollow. F-3 not reported | Same run as the normal scan | `SIGNATURE_GAP` |

## Commands

| Id | Command | Exit | stdout SHA-256 | stderr SHA-256 |
|---|---|---:|---|---|
| CTD-001 self-test | `python -m pytest tests/test_hollow_guarantee_analyzer.py -q --tb=line` in the detector checkout | 0 | `11a0325b6060b3447fd362169f65fd99c3a188fa6dfd7ec5bc03dd76fc5d3cb6` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty) |
| CTD-002 / CTD-006 default repository scan | `python -m code_audit <repository> --json` | 2 | `c04612ecf8254d03f2b6531125e2c9073495760600bff2f9f00300de81886a48` | `014b50247769a130c6ce8fbfe3c401048c131f8fe4e4ebb92da7a9c38fcb8d8d` |
| CTD-004 direct F-2 file | `python -m code_audit services/api/tests/test_text_masking_regression.py --json` | 2 | `96fcb22f88089fd848ef68fbe386235ced2700232d0800ae0e24c5eab304b019` | `df99e1fc84064a0944d4180e93608756b8c7439560bd5747b62866f0af23c3b1` |
| CTD-005 direct OCR file | `python -m code_audit services/photo-vectorizer/edge_to_dxf.py --json` | 2 | `2cf3370d463f8fdc0fc9cba6be84006b6d7dc7236d113d9664eb7e7978dea19b` | `e78772a7f0c326505c18c620a3ae509930fd3b488eb1f47319c0b44d9e09f3b8` |
| CTD-005 direct result type | `python -m code_audit services/api/app/services/blueprint_orchestrator.py --json` | 2 | `e1464cb22e23be405403e84880c57de514317d70ab43f604f148e24524887fab` | `de146ba1b4fcce24ee338c472fc56313626648f96b12f738dcf3bebe36498ad2` |
| CI-flag probe | `python -m code_audit <repository> --ci --json` with `CI` unset | 2 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty) | `bafb3c9663f2db7ed3b90dac412e871910b32ba3be9ef9d8031bdfdff4990698` |
| Protocol check | `HollowGuaranteeAnalyzer.run(repository, [F-2 file, F-3 files])` | 0 | `c7f90dcfd058935b978f8ce102e6eda0e323d2a7190aaee821d46c205063dd8c` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty) |

Exit 2 on a completed scan is the tool's red confidence score (`0/100`), not a crash. Exit 2 on the `--ci` probe is a usage refusal: `--ci` requires `CI=true`. That flag is not the local default.

Changed-file, staged-file, and merge-base selection are not part of the default command. None was invented. The `scan` subcommand calls the same `scan_project` entry and was not a separate mode.

Raw logs were not committed. Several tool messages contain machine paths. The digests above identify those logs.
