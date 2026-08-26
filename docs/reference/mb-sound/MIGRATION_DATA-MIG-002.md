# DATA-MIG-002 — MB Sound corpus: parity proof and custody transfer

**Increment:** DATA-MIG-002 · **Date:** 2026-08-25
**Toolbox base:** `b5e082794c9102b0133a9c25bbc17c8992bd959c` (`origin/main`)
**Outcome:** Toolbox ceases to be an MB Sound data authority and becomes a pinned consumer.

This record exists so the deletion it authorises remains auditable after the deleted
files are gone. It is written and committed **before** the deletion commit.

---

## 1. What this migration is

Toolbox held a complete second copy of the MB Sound corpus. The canonical copy now
lives in `HanzoRazer/luthier-acoustics-data` at the immutable release `mb-sound/v1.0.0`.

This increment removes the duplicate and replaces it with a verifiable pin.

**It is not a deletion of evidence.** It is the removal of a duplicate custody copy
after byte-level parity with the immutable canonical release was proven. Every file
removed here is present, byte-identical, in a tagged release of the canonical
repository, and its hash was verified before removal. The evidence did not become
less available; it stopped having two owners.

---

## 2. Canonical target

| Field | Value |
|---|---|
| Repository | `HanzoRazer/luthier-acoustics-data` (private) |
| Release tag | `mb-sound/v1.0.0` (annotated) |
| Tag object | `ee824083c87f6e7e3b1db59c4a67dcff570c7a34` |
| Release commit | `081601ecf25703acfe8ba3b64d21fff0c07cfa2e` |
| Content commit | `21d36fbdbcf8d66f5618b88cef2312c42ed9d792` |
| Cohort path | `cohorts/external/mb_sound/` |
| Record count | 114 specimens / 114 envelopes |
| Dataset digest | `ea77ca6397c2e4b34d92133a59a55f07ff14a8ec3bec7f33e0f59590df653717` |
| Manifest digest | `03abe6509ae4e0ad530d85a9d6ff04d43418260380854c72b6b50dc5d2f86689` |
| Schema | `mb_sound_lab_procedure_v1` |
| Source dataset version | `0.5.0-draft` (unchanged — custody matured, the data did not) |

The tag is annotated: the tag object `ee824083...` dereferences to commit `081601ec...`.
Both are recorded so a future reader does not mistake the tag object for tag drift.

---

## 3. Method

Local bytes were read from **git blobs** (`git cat-file blob`), not from the working
tree, so a Windows CRLF checkout could not corrupt the comparison. The canonical
dataset digest is line-ending sensitive; a CRLF checkout yields `0ee9adc2...` instead.

Canonical bytes came from the release tarball for `mb-sound/v1.0.0`.

**Fidelity control:** the release manifest extracted from that tarball hashes to
`03abe650...`, exactly the value the Lab pin was written against. The tarball is
therefore a byte-faithful rendering of the release, and comparisons against it are
comparisons against the release.

---

## 4. Results

### TC-001 / TC-002 / TC-003 — corpus parity

| Group | Files | Match | Mismatch | Missing canonically |
|---|---:|---:|---:|---:|
| `specimens/` | 114 | 114 | 0 | 0 |
| `species/` | 6 | 6 | 0 | 0 |
| `validation/` | 3 | 3 | 0 | 0 |
| `source_artifacts/` (incl. 4 `.xlsx` workbooks) | 6 | 6 | 0 | 0 |
| cohort root (`manifest.json`, `README.md`, `MB_SOUND_SOURCES.md`) | 3 | 3 | 0 | 0 |
| `docs/reference/mb-sound/` to canonical `process/` | 13 | 13 | 0 | 0 |
| **Total** | **145** | **145** | **0** | **0** |

All 114 identifiers are `mb-*` and unchanged. No identifier was created, renamed or aliased.

### TC-009 — dataset digest reproduces from the Toolbox copy

Recomputed over the 114 **Toolbox-local** specimen blobs using the canonical algorithm
(sorted by filename; `name + NUL + raw bytes + NUL` per record):

```
recomputed from Toolbox blobs : ea77ca6397c2e4b34d92133a59a55f07ff14a8ec3bec7f33e0f59590df653717
canonical release value       : ea77ca6397c2e4b34d92133a59a55f07ff14a8ec3bec7f33e0f59590df653717
MATCH
```

This is the strongest available parity statement: the copy being deleted independently
reproduces the digest the canonical release publishes.

### Corroboration from the release's own parity gate

`mb-sound/v1.0.0` records `preserved_at_revision: df3b3581` with
`132/132 corpus blobs identical to luthiers-toolbox`. This migration re-proves parity at
`b5e08279`, confirming the Toolbox copy did not drift between `df3b3581` and today.

---

## 5. Consumer census — why the consumer-migration phases are vacuous

The handoff anticipated material adapters, `TonewoodEntry` mappings, API routes and UI
views reading this corpus. **None exist.** Searched at `b5e08279`:

```
git grep -n -I -E "empirical_tonewood|mb_sound" -- "*.py" "*.ts" "*.vue" "*.js" ":!scripts/"
  -> no matches
```

The only code touching the dataset is `scripts/mb_sound_*.py` (offline extraction and
validation tooling). `scripts/knowledge_packs/build_cohort_catalog.py` matches on the
string `nicoletti_mb_sound_acoustic_study_set` but reads only
`docs/calculators/acoustics/`, never a payload. No test referenced the corpus.

Consequently these are recorded **vacuous-by-inventory**, not implemented:

| Item | Disposition |
|---|---|
| Handoff 5.4 material adapters | No such adapter exists |
| Handoff 5.6 validator reuse | Canonical repo owns the validator; none added here |
| Phase 5 consumer migration | No consumer to migrate |
| Phase 6 application parity | No application path to compare |
| TC-004 field-value parity | Subsumed by byte parity — no consumer transforms values |
| TC-017 adapter parity | No adapter |
| TC-018 public API parity | Corpus is not exposed by any endpoint |
| TC-019 UI/consumer parity | Corpus is not rendered by any view |

No adapter or runtime consumer was invented to satisfy these. Doing so would have added
the application coupling this increment does not authorise.

---

## 6. Disposition of every MB Sound file

| Classification | Paths | Action |
|---|---|---|
| `CANONICAL_DATA_DUPLICATE` | `services/api/app/data_registry/system/materials/empirical_tonewood/mb_sound/` (132 files) | **REMOVED** |
| `CANONICAL_DATA_DUPLICATE` | `docs/reference/mb-sound/` process docs (13 files) | **REMOVED** |
| Pin | `docs/reference/mb-sound/CORPUS_DEPENDENCY.json`, `README.md` | **ADDED** |
| `TOOLBOX_TOOLING` | `scripts/mb_sound_{extract_frames,ocr_frames,merge_rows,validate_corpus}.py` | **RETAINED**, non-authoritative |
| `TOOLBOX_PROVENANCE` | `docs/calculators/acoustics/mb_sound_panel_laboratory_records/`, `.../nicoletti_mb_sound_acoustic_study_set/` | **RETAINED** |
| Redirect stubs | `materials/panel_acoustic/{README.md,MB_SOUND_SOURCES.md,mb_sound_panels.json}` | **REPOINTED** to canonical |
| Authority language | `materials/SOURCES.md` | **UPDATED** |
| Ignore rule | `.gitignore` workbook negation | **REMOVED** (target gone) |

The four `.xlsx` laboratory workbooks are removed under the framing in section 1: each is
byte-identical to `cohorts/external/mb_sound/source_artifacts/workbooks/` in the
immutable release, and each hash was verified before removal (see Appendix A).

The four extraction scripts are duplicated canonically under `tools/mb_sound/` but are
retained pending a later audit, since they are process tooling rather than evidence.

---

## 7. Terminal authority

```
luthier-acoustics-data - mb-sound/v1.0.0     <- canonical evidence
        |
        +-- luthier-acoustics-lab            VERIFIED PINNED CONSUMER
        +-- luthiers-toolbox                 VERIFIED PINNED CONSUMER (this increment)
        +-- tap_tone_pi                      not yet a consumer
```

No change was made to the canonical data repository, the Laboratory, or Tap Tone Pi.
No specimen identifier, schema, vocabulary or measured value was altered.

---

## Appendix A — full hash table (145 files)

Both sides hash identically; a single column is shown.

| # | Toolbox path (removed) | Canonical path @ `mb-sound/v1.0.0` | sha256 (both sides) | Result |
|---:|---|---|---|:---:|
| 1 | `mb_sound/specimens/mb-adt-000001.json` | `mb_sound/specimens/mb-adt-000001.json` | `17a36bbf35ea85171ab6b816177ad2a9944f4115cbb0a874a043ccb2a403064b` | MATCH |
| 2 | `mb_sound/specimens/mb-adt-000003.json` | `mb_sound/specimens/mb-adt-000003.json` | `40604748dc913e9b0625549ad19ebbe521f2f0793b8060d750018a41bd0b40ce` | MATCH |
| 3 | `mb_sound/specimens/mb-adt-000004.json` | `mb_sound/specimens/mb-adt-000004.json` | `8085d4e3752f1e41b500c0f062b4e4bf93e26244ef1be37049d3cee936b126f4` | MATCH |
| 4 | `mb_sound/specimens/mb-adt-000005.json` | `mb_sound/specimens/mb-adt-000005.json` | `243b6b32dbfe9c74a374ec291d13eb19c67471283bc2601da680c4e1b04ccb91` | MATCH |
| 5 | `mb_sound/specimens/mb-adt-000006.json` | `mb_sound/specimens/mb-adt-000006.json` | `82a7e56e59658b41ad628434b7c69bf14ee1562049ec90ecde8367f197adc860` | MATCH |
| 6 | `mb_sound/specimens/mb-adt-000007.json` | `mb_sound/specimens/mb-adt-000007.json` | `f66c17dde7ddbb2373e873d95c8e5aeeb189559226d6bf9f5fe5a37698a1e7c2` | MATCH |
| 7 | `mb_sound/specimens/mb-adt-000008.json` | `mb_sound/specimens/mb-adt-000008.json` | `d9d42b9bdfde0d58d522d4066776aad72461af8de1f9e30091c2803dfbed869d` | MATCH |
| 8 | `mb_sound/specimens/mb-adt-000009.json` | `mb_sound/specimens/mb-adt-000009.json` | `47662191d4f7e90aa9925c4e0c86252c2036e7b859369aed30a11235135eb80b` | MATCH |
| 9 | `mb_sound/specimens/mb-adt-000010.json` | `mb_sound/specimens/mb-adt-000010.json` | `9bfa39667012b92c75c95cc556d9b7d7a65b537f07bf74ecbf88ddc9f37c6d2b` | MATCH |
| 10 | `mb_sound/specimens/mb-adt-000011.json` | `mb_sound/specimens/mb-adt-000011.json` | `c85efd96e81456bd3f3c739166f1395424bc50020a4604e0bc9e7e75fb4c521a` | MATCH |
| 11 | `mb_sound/specimens/mb-adt-000012.json` | `mb_sound/specimens/mb-adt-000012.json` | `9b984f04ec3a68e2dec540dc0d3c4b6963f27f61ec79814dfd3513a8d3364307` | MATCH |
| 12 | `mb_sound/specimens/mb-adt-000013.json` | `mb_sound/specimens/mb-adt-000013.json` | `aa06b36e2e668ac98b4f6b953c96e4e93578346f4337e11ab4a71876fcf3e397` | MATCH |
| 13 | `mb_sound/specimens/mb-adt-000014.json` | `mb_sound/specimens/mb-adt-000014.json` | `6e61dae95f7ce17fdf4db5d223613814150e3f81bd0eae5e8bf47817595897a0` | MATCH |
| 14 | `mb_sound/specimens/mb-adt-000015.json` | `mb_sound/specimens/mb-adt-000015.json` | `51dbd0068bfc340f2203cfd3a71ca942ea047bf0a47c27d90c978c278d702f8e` | MATCH |
| 15 | `mb_sound/specimens/mb-adt-000016.json` | `mb_sound/specimens/mb-adt-000016.json` | `0728e19b0cbf5d0bfb48ffe44b15d0f3e5debdf995a8bb58df2b2e05c442c0dd` | MATCH |
| 16 | `mb_sound/specimens/mb-adt-000017.json` | `mb_sound/specimens/mb-adt-000017.json` | `ff5b232adb1c9dfc18775eaadf1996144d355400ede3d6514da86ec62a7665de` | MATCH |
| 17 | `mb_sound/specimens/mb-adt-000018.json` | `mb_sound/specimens/mb-adt-000018.json` | `227787966aa923bd23ec52da79cdb2dc30ce698b7626ebb81dc12eee043c5e9a` | MATCH |
| 18 | `mb_sound/specimens/mb-adt-000019.json` | `mb_sound/specimens/mb-adt-000019.json` | `63d857029a23be6a55744a254bcf960076426356558d44cd1dfea8ba2e6b9496` | MATCH |
| 19 | `mb_sound/specimens/mb-adt-000020.json` | `mb_sound/specimens/mb-adt-000020.json` | `8d2a6e2b9947d2c00491cfcc2144096940da29347da07207410d1018f1e8405a` | MATCH |
| 20 | `mb_sound/specimens/mb-adt-000021.json` | `mb_sound/specimens/mb-adt-000021.json` | `18aa66bc8ed5207289919b4a9fe42b28286d2d00aeaac8b228e17d4d424c27a5` | MATCH |
| 21 | `mb_sound/specimens/mb-adt-000022.json` | `mb_sound/specimens/mb-adt-000022.json` | `39ce117e72760a7f53dadba7d72570f1eae2cd2cb99a293bfbfb85bdfab1b13d` | MATCH |
| 22 | `mb_sound/specimens/mb-as-000001.json` | `mb_sound/specimens/mb-as-000001.json` | `5301dd18645badade73959079c8fa28ca54fdab4487c30b32dfe3ddd2add18e8` | MATCH |
| 23 | `mb_sound/specimens/mb-as-000002.json` | `mb_sound/specimens/mb-as-000002.json` | `cecb116215232951e8c535c4e0f08aadd190987d8910cf2cf63c9ec4e92117e9` | MATCH |
| 24 | `mb_sound/specimens/mb-as-000003.json` | `mb_sound/specimens/mb-as-000003.json` | `d0c08c48999e44bb3ea1d9f5ae95237c840119870ff6b5288560ec7988587406` | MATCH |
| 25 | `mb_sound/specimens/mb-as-000004.json` | `mb_sound/specimens/mb-as-000004.json` | `5b785cb4e9a83aa558b123730f6b4726a703b10b448ab1639cbb9b73fc8156a5` | MATCH |
| 26 | `mb_sound/specimens/mb-as-000005.json` | `mb_sound/specimens/mb-as-000005.json` | `1b28d959eb7b72a9bbdb92078c293f0ce5d0d9bb7bab1c93b9303771cc46e6dc` | MATCH |
| 27 | `mb_sound/specimens/mb-as-000006.json` | `mb_sound/specimens/mb-as-000006.json` | `df1d227112f7ff5c78977b5e9774645bf29c76f8210d2813fa2fd03b5c228c53` | MATCH |
| 28 | `mb_sound/specimens/mb-as-000007.json` | `mb_sound/specimens/mb-as-000007.json` | `472ea0fab073c9f07ebf2154936866deb4eecb30b377ff8ef67cfceb3d69d813` | MATCH |
| 29 | `mb_sound/specimens/mb-as-000008.json` | `mb_sound/specimens/mb-as-000008.json` | `6915ac0400900e578e00533db18722c9eb6b186f182c8067f2a48dcc4589f802` | MATCH |
| 30 | `mb_sound/specimens/mb-as-000009.json` | `mb_sound/specimens/mb-as-000009.json` | `223d0a55b1a51f178f39bb62cb740a75b5818a60bb314c52d33d5c07f404c61f` | MATCH |
| 31 | `mb_sound/specimens/mb-as-000010.json` | `mb_sound/specimens/mb-as-000010.json` | `be055ae6810d10351ef7af207c5f13d12403dddc640479c46c9c0ec8033b149d` | MATCH |
| 32 | `mb_sound/specimens/mb-as-000011.json` | `mb_sound/specimens/mb-as-000011.json` | `30b60034f894224251fbb04c40b5ad55ee2f53fdcf63da448aef873ff1cd2ce3` | MATCH |
| 33 | `mb_sound/specimens/mb-as-000012.json` | `mb_sound/specimens/mb-as-000012.json` | `ac37872658030e8b58020f0eb60d2991316df10bdfc556cf9d45bb50f2adbda9` | MATCH |
| 34 | `mb_sound/specimens/mb-as-000013.json` | `mb_sound/specimens/mb-as-000013.json` | `e77412a85e87a1eb2a39691f20a88202bb7ce1704d3e8d7b3226a44feef418a2` | MATCH |
| 35 | `mb_sound/specimens/mb-as-000014.json` | `mb_sound/specimens/mb-as-000014.json` | `4ec864ea9f433624c9aad943527a4a4738398f9ada209dc98da1ffb73056d91d` | MATCH |
| 36 | `mb_sound/specimens/mb-as-000015.json` | `mb_sound/specimens/mb-as-000015.json` | `8755b6a8b97ddaca559828224170a49402c95cb0bcc977ed8f76fee367fa81b4` | MATCH |
| 37 | `mb_sound/specimens/mb-as-000016.json` | `mb_sound/specimens/mb-as-000016.json` | `1da7631e37dcb9389871a619506ad7e71cdf486454bc21b45b18f856ec1de96b` | MATCH |
| 38 | `mb_sound/specimens/mb-as-000017.json` | `mb_sound/specimens/mb-as-000017.json` | `3edda59efafd7ac659fbaff6ce87271a7badc44a880eeaf4df5043673d8d1b1a` | MATCH |
| 39 | `mb_sound/specimens/mb-as-000018.json` | `mb_sound/specimens/mb-as-000018.json` | `9817a04ed7818404979c6ee26e323175eb69244c4d42ea98a7dd6c6642304c4b` | MATCH |
| 40 | `mb_sound/specimens/mb-as-000019.json` | `mb_sound/specimens/mb-as-000019.json` | `3c32d812ed22e549949603b3179b77de5c27418dcc58df6d9ca120736a694eb9` | MATCH |
| 41 | `mb_sound/specimens/mb-as-000020.json` | `mb_sound/specimens/mb-as-000020.json` | `8d364bd531135ee104989bd7b823a656dd08d7c39ac09bcd2e717ed2c13fdec4` | MATCH |
| 42 | `mb_sound/specimens/mb-as-000021.json` | `mb_sound/specimens/mb-as-000021.json` | `a177ee535d277a83ed6ea6f25dd5fc41994a352ccf749ca574ad7efed5dd599c` | MATCH |
| 43 | `mb_sound/specimens/mb-as-000022.json` | `mb_sound/specimens/mb-as-000022.json` | `ff95eb0c4b3ec30998dc28fd07d3087ff40ceaea13633ebabe9af52b2f29c920` | MATCH |
| 44 | `mb_sound/specimens/mb-rc-000001.json` | `mb_sound/specimens/mb-rc-000001.json` | `22b9247df040b5134a1c4bc7864d57f7a723c1b8772370619e3afaad356f2ad6` | MATCH |
| 45 | `mb_sound/specimens/mb-rc-000002.json` | `mb_sound/specimens/mb-rc-000002.json` | `b95ecd90013933f5653ac1e51af7d4a40c2bd71478b54b496e5986e6ba54238f` | MATCH |
| 46 | `mb_sound/specimens/mb-rc-000003.json` | `mb_sound/specimens/mb-rc-000003.json` | `106eac38d10929abe5fca16fe6592a16b7abd935687932042ae09a5ade4fd4a8` | MATCH |
| 47 | `mb_sound/specimens/mb-rc-000004.json` | `mb_sound/specimens/mb-rc-000004.json` | `bea06173cf5a505dfd4a21ac95e4e478365894d9df987242eb51cdd0f9029aca` | MATCH |
| 48 | `mb_sound/specimens/mb-rc-000005.json` | `mb_sound/specimens/mb-rc-000005.json` | `726abfd253f1f04bb21df0c6cb5de8dfdc1e4258a7a01630071ed66a53e4c09c` | MATCH |
| 49 | `mb_sound/specimens/mb-rc-000006.json` | `mb_sound/specimens/mb-rc-000006.json` | `b09c2c9b2a0a84ace2cb33791b1b4e4e050c3ded88b6a1dcd993d358850f6eb4` | MATCH |
| 50 | `mb_sound/specimens/mb-rc-000007.json` | `mb_sound/specimens/mb-rc-000007.json` | `949987fb1d853e409bc470236d7d40a462de908f569082457036fc7dccc28594` | MATCH |
| 51 | `mb_sound/specimens/mb-rc-000008.json` | `mb_sound/specimens/mb-rc-000008.json` | `c392d55d79ab65351dbdc8410ceced2a83db3d7023e236d16bd64be30430b918` | MATCH |
| 52 | `mb_sound/specimens/mb-rc-000009.json` | `mb_sound/specimens/mb-rc-000009.json` | `bbedc95ce45fa5f1ea19b5330616ea7c8ac5cc11b343b36dc3e60179885a9bd6` | MATCH |
| 53 | `mb_sound/specimens/mb-rc-000010.json` | `mb_sound/specimens/mb-rc-000010.json` | `8acb75acbb0df5b3a1a64fbbe65c1460ab8acbd42ab09aba7e3de13ba22ec8d7` | MATCH |
| 54 | `mb_sound/specimens/mb-rc-000011.json` | `mb_sound/specimens/mb-rc-000011.json` | `2de5e39db7de30224d025524f15e0df4a70dcd11109459dd92d70d109a3b28bc` | MATCH |
| 55 | `mb_sound/specimens/mb-rc-000012.json` | `mb_sound/specimens/mb-rc-000012.json` | `1890d6bfa245e704607916d8f6eff696e3a0a09e853527c9864be97e935d0efd` | MATCH |
| 56 | `mb_sound/specimens/mb-rc-000013.json` | `mb_sound/specimens/mb-rc-000013.json` | `206da774869cd2b59e38a8c786c22691494b2b84f5e8694f4c6d68ccb8a7eb51` | MATCH |
| 57 | `mb_sound/specimens/mb-rc-000014.json` | `mb_sound/specimens/mb-rc-000014.json` | `3c6963025d8f9eab689512c5a3758dc5ee009c56e08934b2f7869fb364aacc5b` | MATCH |
| 58 | `mb_sound/specimens/mb-rc-000015.json` | `mb_sound/specimens/mb-rc-000015.json` | `c11c9a6c8064182a98aa892ccdc87764e9f724c2b8b3160666824eda3268049b` | MATCH |
| 59 | `mb_sound/specimens/mb-rc-000016.json` | `mb_sound/specimens/mb-rc-000016.json` | `761a76e3b61d3e801744bd0e14bbd3f4b82f9b8e200c3f931c1dfb4fec7f44ef` | MATCH |
| 60 | `mb_sound/specimens/mb-rc-000017.json` | `mb_sound/specimens/mb-rc-000017.json` | `323fbcbadbc6c2b145283030e23cbdea42b3a26ae7e4e5b0439ba111ce41dd7c` | MATCH |
| 61 | `mb_sound/specimens/mb-rc-000018.json` | `mb_sound/specimens/mb-rc-000018.json` | `0c76caa1552f859f3d103a6a21a5c7e59b05acefd34bd33a69611fcad9a46586` | MATCH |
| 62 | `mb_sound/specimens/mb-rc-000019.json` | `mb_sound/specimens/mb-rc-000019.json` | `ca4835b1e4aac3be433305850685c62efe5c0ea79bb1ebaf5de491eb9c8bdba4` | MATCH |
| 63 | `mb_sound/specimens/mb-rc-000020.json` | `mb_sound/specimens/mb-rc-000020.json` | `2e1296461f6043551a8ca0cffcc3be6a3b0b8e487534bd133ee063858735fdb5` | MATCH |
| 64 | `mb_sound/specimens/mb-rc-000021.json` | `mb_sound/specimens/mb-rc-000021.json` | `8d6e0f8d9ca558c2e37dc6d44deee842082556bd19b888c31d4c521f0c2b282a` | MATCH |
| 65 | `mb_sound/specimens/mb-rc-000022.json` | `mb_sound/specimens/mb-rc-000022.json` | `bd9c2349fe72bc2157b74b767deb6e413f9953aae95202f3363b7033ef1d680c` | MATCH |
| 66 | `mb_sound/specimens/mb-rc30-000024.json` | `mb_sound/specimens/mb-rc30-000024.json` | `1a47e2520ef75742dbf1a96d4af472ec3e58c453f60ea3d64e6b91236d174964` | MATCH |
| 67 | `mb_sound/specimens/mb-rc30-000025.json` | `mb_sound/specimens/mb-rc30-000025.json` | `b8dbdd84f638314c52ea258135e2509f5c52a181ccf9f03edfab43ce5c852a46` | MATCH |
| 68 | `mb_sound/specimens/mb-rc30-000026.json` | `mb_sound/specimens/mb-rc30-000026.json` | `b5b458b8f6aca9bf91e0f632d5f4eb2a0c9e436c83e4a3c44728747eda868178` | MATCH |
| 69 | `mb_sound/specimens/mb-rc30-000027.json` | `mb_sound/specimens/mb-rc30-000027.json` | `4726e7d54be29af87568563cb4ae8d069f6afc7ce4f18490409b32a46a80cc89` | MATCH |
| 70 | `mb_sound/specimens/mb-rc30-000028.json` | `mb_sound/specimens/mb-rc30-000028.json` | `2c5b5e1fcbb18956c88a0a1c6e723ee20043b41177564dcab10bb28a72f86cfa` | MATCH |
| 71 | `mb_sound/specimens/mb-rc30-000029.json` | `mb_sound/specimens/mb-rc30-000029.json` | `429cd26b332e28d09889277c52e833259a4e3fa6533034f1621943b07e84d058` | MATCH |
| 72 | `mb_sound/specimens/mb-rc30-000030.json` | `mb_sound/specimens/mb-rc30-000030.json` | `ecb0e20edd6db6ac6e42b9b1f462cd59f5692957b8f8cac7bc4fdeca362db87c` | MATCH |
| 73 | `mb_sound/specimens/mb-rc30-000031.json` | `mb_sound/specimens/mb-rc30-000031.json` | `1a28073f1fe5a6e5f47af1790ee7d45d960aa9a5ae329e629bc1199298a50cc0` | MATCH |
| 74 | `mb_sound/specimens/mb-rc30-000032.json` | `mb_sound/specimens/mb-rc30-000032.json` | `48795aea2b6f2c64b6620217fb30a90de70144d671ac5e5637205db32936c2d3` | MATCH |
| 75 | `mb_sound/specimens/mb-rc30-000033.json` | `mb_sound/specimens/mb-rc30-000033.json` | `de86c7ad902253e39742f40cd4b24286fc36e713c320aab3a039fbf456ce3a0d` | MATCH |
| 76 | `mb_sound/specimens/mb-rc30-000034.json` | `mb_sound/specimens/mb-rc30-000034.json` | `2a065af2ee49e143034aa9cfa461438ce3b5ea2ddb8bdfe686ad94b984d1481a` | MATCH |
| 77 | `mb_sound/specimens/mb-rc30-000035.json` | `mb_sound/specimens/mb-rc30-000035.json` | `407e397a05a3e35ed3b5717433141e9921b8642136d6ddb61fb886d7c8eae064` | MATCH |
| 78 | `mb_sound/specimens/mb-rc30-000036.json` | `mb_sound/specimens/mb-rc30-000036.json` | `1663a878eb2ae91d019839b0c96c5fb1dcb43e176d8941a949e0371790d2f953` | MATCH |
| 79 | `mb_sound/specimens/mb-rc30-000037.json` | `mb_sound/specimens/mb-rc30-000037.json` | `7a62296fbbc0e7489055a2eceafc967a2f753ee015e971ecadcc2497a3391a18` | MATCH |
| 80 | `mb_sound/specimens/mb-rc30-000038.json` | `mb_sound/specimens/mb-rc30-000038.json` | `9957ebc75029a665d7eaacc2e350c115b2028273d90b7bdc487c5a4d5dfcced8` | MATCH |
| 81 | `mb_sound/specimens/mb-rc30-000039.json` | `mb_sound/specimens/mb-rc30-000039.json` | `a1dd31c5348e83f2903890cd048d30a79a7677d330a4dec3520660ca021c92a6` | MATCH |
| 82 | `mb_sound/specimens/mb-rc30-000040.json` | `mb_sound/specimens/mb-rc30-000040.json` | `a78d6c17af1e534826d264729c26fcd08370e19b9536b32a3e877b517dcfc71a` | MATCH |
| 83 | `mb_sound/specimens/mb-rc30-000041.json` | `mb_sound/specimens/mb-rc30-000041.json` | `579a5c3267971c0b793f4f858b38c54fe7190594e73a4b58f4efd6965a5b68fb` | MATCH |
| 84 | `mb_sound/specimens/mb-rc30-000042.json` | `mb_sound/specimens/mb-rc30-000042.json` | `9af39db2b46bdd2ac093c749954cdff6d649a2665d1c16dfcd5dcfbc5f7d7fa1` | MATCH |
| 85 | `mb_sound/specimens/mb-rc30-000043.json` | `mb_sound/specimens/mb-rc30-000043.json` | `b06343db8c0e9c2d4330103d05102724fc77e7b16d8a05ea725a32e338032b7e` | MATCH |
| 86 | `mb_sound/specimens/mb-rc30-000044.json` | `mb_sound/specimens/mb-rc30-000044.json` | `d1b5b34ca143479cb979935fc84292cb03518d85176bd1827b33374b277e51b2` | MATCH |
| 87 | `mb_sound/specimens/mb-rc30-000045.json` | `mb_sound/specimens/mb-rc30-000045.json` | `82669b596279dc27fa3cce5be5be0d173fe5c81a059602b9fc865d1c52f52490` | MATCH |
| 88 | `mb_sound/specimens/mb-rc30-000046.json` | `mb_sound/specimens/mb-rc30-000046.json` | `96ebbbcb61f860350fc0e075995144639a77920696d362316d0b6e963f668305` | MATCH |
| 89 | `mb_sound/specimens/mb-rc30-000047.json` | `mb_sound/specimens/mb-rc30-000047.json` | `d90f6c4a4d704191f8390767c515cbe02d17d13cc8bcb9d488da1c2d80869a65` | MATCH |
| 90 | `mb_sound/specimens/mb-rc30-000048.json` | `mb_sound/specimens/mb-rc30-000048.json` | `0239310452ef2c11a8927d65a4a454854d02acfeb91021f7184ce954e67fe433` | MATCH |
| 91 | `mb_sound/specimens/mb-rc30-000049.json` | `mb_sound/specimens/mb-rc30-000049.json` | `92912839ac8066d7725afaad6ca458c751280bdb8207cc09996142e801d81685` | MATCH |
| 92 | `mb_sound/specimens/mb-rc30-000050.json` | `mb_sound/specimens/mb-rc30-000050.json` | `356fcc4bb72d0c05b14148c35d91e6fe59c3aadcf1c9b47ff88e0aff8c77a1c3` | MATCH |
| 93 | `mb_sound/specimens/mb-rc30-000051.json` | `mb_sound/specimens/mb-rc30-000051.json` | `3533107751cd356b184b954633e789094343c5979ff407ef952c947e7d98523f` | MATCH |
| 94 | `mb_sound/specimens/mb-rc30-000052.json` | `mb_sound/specimens/mb-rc30-000052.json` | `75fd9840bd7d20dac3eeaec01c633a351fc0e4a61bb7d11d7083f21680685a06` | MATCH |
| 95 | `mb_sound/specimens/mb-rc30-000053.json` | `mb_sound/specimens/mb-rc30-000053.json` | `645bc5ed59f1114a0f794d89975a810a023c525910dee8195caa406b51e81d42` | MATCH |
| 96 | `mb_sound/specimens/mb-rc30-000054.json` | `mb_sound/specimens/mb-rc30-000054.json` | `ebeabb35bdaa1e7b993962607526fbc00befc4adba4c8fd73e5b23df8fdfce64` | MATCH |
| 97 | `mb_sound/specimens/mb-rc30-000055.json` | `mb_sound/specimens/mb-rc30-000055.json` | `b2838feaabd017846f894a30c578986c083a1917b24ed584e1198598b01940af` | MATCH |
| 98 | `mb_sound/specimens/mb-rc30-000056.json` | `mb_sound/specimens/mb-rc30-000056.json` | `eea4bf6d26e28b44bef292e6e7344731bc4bae649acb7373f95304725f69729c` | MATCH |
| 99 | `mb_sound/specimens/mb-rc30-000057.json` | `mb_sound/specimens/mb-rc30-000057.json` | `55c921c2e4201b690d9cd93ad56aea63e5376c1cf2fa95c243615385134a9a85` | MATCH |
| 100 | `mb_sound/specimens/mb-rc30-000058.json` | `mb_sound/specimens/mb-rc30-000058.json` | `68acd964534c44a38424bf9e119b9f3770efc2984afff367c0368d34c603960b` | MATCH |
| 101 | `mb_sound/specimens/mb-rc30-000059.json` | `mb_sound/specimens/mb-rc30-000059.json` | `d1ff761b98aadaa06737411177cd4e842a08d614b05d799d8934967efb39cab0` | MATCH |
| 102 | `mb_sound/specimens/mb-rc30-000060.json` | `mb_sound/specimens/mb-rc30-000060.json` | `47bbf9491a12ef59f93764ed16d45752cd7cd43b7426b596261643ef508c6b78` | MATCH |
| 103 | `mb_sound/specimens/mb-rc30-000061.json` | `mb_sound/specimens/mb-rc30-000061.json` | `f726c8ed2779f490a8998150e19aa724541f35bfe96afa798f59e6e59d1d9eee` | MATCH |
| 104 | `mb_sound/specimens/mb-rc30-000062.json` | `mb_sound/specimens/mb-rc30-000062.json` | `3d10619b2b1f9b43f9d2e8d5d4745bab248af3841aa17d311d0ca91bd7bc8cd7` | MATCH |
| 105 | `mb_sound/specimens/mb-rc30-000063.json` | `mb_sound/specimens/mb-rc30-000063.json` | `baf64b4e0050718048e0d0c203b41199050bec31f01629fa5f611db9f158382c` | MATCH |
| 106 | `mb_sound/specimens/mb-rc30-000064.json` | `mb_sound/specimens/mb-rc30-000064.json` | `0a5ac57d9b12c6e68452600fee63ab3eddcc67438818dd0142e1093634f8b392` | MATCH |
| 107 | `mb_sound/specimens/mb-rc30-000065.json` | `mb_sound/specimens/mb-rc30-000065.json` | `a6205b40853b2ddaec5e29544e491313c0554e64183344ecdab7059bda7b83ec` | MATCH |
| 108 | `mb_sound/specimens/mb-rc30-000066.json` | `mb_sound/specimens/mb-rc30-000066.json` | `a16a613631a834ad990c9668d3da452dc175392ed4b6623d1ac975bdaddda830` | MATCH |
| 109 | `mb_sound/specimens/mb-rc30-000067.json` | `mb_sound/specimens/mb-rc30-000067.json` | `2a37ab3b0df714bf1fe1f23ba1090557c9ebf798f55aea4b8183e85e29b4da23` | MATCH |
| 110 | `mb_sound/specimens/mb-rc30-000068.json` | `mb_sound/specimens/mb-rc30-000068.json` | `fc07a3039ab3f388d08e6910d7a638daa996921f84441e20eb9e6d1023866973` | MATCH |
| 111 | `mb_sound/specimens/mb-rc30-000069.json` | `mb_sound/specimens/mb-rc30-000069.json` | `ee46df861474f03825bf1856e8a3b4023436e6712d8a3804d162e144bff56f0a` | MATCH |
| 112 | `mb_sound/specimens/mb-rc30-000070.json` | `mb_sound/specimens/mb-rc30-000070.json` | `1f9a5a1f560f5fc624fc0c86d76969ec75499dda03e9b3176164d96ff8dbe3dd` | MATCH |
| 113 | `mb_sound/specimens/mb-rc30-000071.json` | `mb_sound/specimens/mb-rc30-000071.json` | `4d876c4ffcdf8d97356deddeecdb11244f11f704e34706d184142679a4163b1a` | MATCH |
| 114 | `mb_sound/specimens/mb-rc30-000072.json` | `mb_sound/specimens/mb-rc30-000072.json` | `c355208d1995ecad6af2663f4cd35ba9a0d7feaa4ba2bb59d189c79fa798ed7e` | MATCH |
| 115 | `mb_sound/species/adirondack/cohort.json` | `mb_sound/species/adirondack/cohort.json` | `bd4fffa70030e5db1fb5785f4e8e86b462df1a48f6c1d945650551ca9ff15765` | MATCH |
| 116 | `mb_sound/species/adirondack_torrefied/cohort.json` | `mb_sound/species/adirondack_torrefied/cohort.json` | `aadb403985ea1c8f1749ae7601c189ab3b413fb46421d50690741a5233115a3a` | MATCH |
| 117 | `mb_sound/species/alpine_spruce/cohort.json` | `mb_sound/species/alpine_spruce/cohort.json` | `256ac105b1439dea8cab9f0a988ce01d90807e1694d842448d5d12b335af9d91` | MATCH |
| 118 | `mb_sound/species/european_spruce/cohort.json` | `mb_sound/species/european_spruce/cohort.json` | `23251162210bfe425164237ef47f257f4e856b245c584ee08a770586fe543f16` | MATCH |
| 119 | `mb_sound/species/red_cedar/cohort.json` | `mb_sound/species/red_cedar/cohort.json` | `fb9500a1421bb22f83fbb393ac7869ccaaeda9cc7c5cb422e747adefe8cd5579` | MATCH |
| 120 | `mb_sound/species/red_cedar_30yr_naturally_dried/cohort.json` | `mb_sound/species/red_cedar_30yr_naturally_dried/cohort.json` | `6a4659203da312cbe62f3c1451293b5c5778f76bb6594c01f4ebbf32b697d90d` | MATCH |
| 121 | `mb_sound/validation/consistency_results.json` | `mb_sound/validation/consistency_results.json` | `93d60bd660221b3d04a764a3464a2db6a1da0c82b8bc388a3d487332bb641557` | MATCH |
| 122 | `mb_sound/validation/corpus_laboratory_statistics.json` | `mb_sound/validation/corpus_laboratory_statistics.json` | `eaf74bf4226f077dda6262bb516cc89cc7ecf6a22893477450bc29bcf9580d3d` | MATCH |
| 123 | `mb_sound/validation/unresolved_fields.json` | `mb_sound/validation/unresolved_fields.json` | `37ccf167e1158e2bc8bcdf36a8ef8f7ea3e0546bdee777d75f57a62c35a281eb` | MATCH |
| 124 | `mb_sound/source_artifacts/.gitignore` | `mb_sound/source_artifacts/.gitignore` | `2ee74f221926754add8416d7d5fbbbf244f82835ffe10a66046cef4b1792d69a` | MATCH |
| 125 | `mb_sound/source_artifacts/artifact_manifest.json` | `mb_sound/source_artifacts/artifact_manifest.json` | `7faf86615ccc77eb509914dadb7335c993cd78c64d7f5b05cfa4ec1f4cc8fbc8` | MATCH |
| 126 | `mb_sound/source_artifacts/workbooks/Alpine_Spruce_Complete_Laboratory_Record.xlsx` | `mb_sound/source_artifacts/workbooks/Alpine_Spruce_Complete_Laboratory_Record.xlsx` | `fabf9e694b559bee439e0bd239ae0c55ff8748d3e8aa2e2e8c8be43594e4c481` | MATCH |
| 127 | `mb_sound/source_artifacts/workbooks/Red_Cedar_30_Year_Drying_Complete_Laboratory_Record.xlsx` | `mb_sound/source_artifacts/workbooks/Red_Cedar_30_Year_Drying_Complete_Laboratory_Record.xlsx` | `da9aeee4998405c52418c5619717a45d751db465ddf3b4759621039004c6078a` | MATCH |
| 128 | `mb_sound/source_artifacts/workbooks/Red_Cedar_Complete_Laboratory_Record.xlsx` | `mb_sound/source_artifacts/workbooks/Red_Cedar_Complete_Laboratory_Record.xlsx` | `6bb5355da5a4402d3ddec7bdf9f428bb1e0d54a584a536aa6be5f8cfb795c291` | MATCH |
| 129 | `mb_sound/source_artifacts/workbooks/Torrefied_Adirondack_Complete_Laboratory_Record.xlsx` | `mb_sound/source_artifacts/workbooks/Torrefied_Adirondack_Complete_Laboratory_Record.xlsx` | `5e293e5c0bae685fc4d0b230e5bc0aaa899c7377918dad710e4f1975065b3289` | MATCH |
| 130 | `mb_sound/MB_SOUND_SOURCES.md` | `mb_sound/MB_SOUND_SOURCES.md` | `b00d8c5535d97fd453412cebd34f7644dc14c9f3092afd4ce58348613e05a5f9` | MATCH |
| 131 | `mb_sound/README.md` | `mb_sound/README.md` | `a2546801a7c76446a8b3ad8cad5a168f119a30af63475e94631d7a893fcff92c` | MATCH |
| 132 | `mb_sound/manifest.json` | `mb_sound/manifest.json` | `61dae87fbeaae5dac9ee83b0b3e3fa8b3ee8c184eadd385843f74dd2a772d42b` | MATCH |
| 133 | `docs/reference/mb-sound/DO_SIP_PROGRAM.md` | `mb_sound/process/DO_SIP_PROGRAM.md` | `913a1f4f085f312f71b2f3747bbc6472d2cabb4447cc7113e8c277abccc0e8af` | MATCH |
| 134 | `docs/reference/mb-sound/EXTRACTION_PLAYBOOK.md` | `mb_sound/process/EXTRACTION_PLAYBOOK.md` | `dc36cfff1c5940c708e22401c88ab88a09f7fffa6be67ca71ebcdc3a03b18ec8` | MATCH |
| 135 | `docs/reference/mb-sound/FIELD_GLOSSARY_ES_EN.md` | `mb_sound/process/FIELD_GLOSSARY_ES_EN.md` | `bb30ea383062a54a0ed015208a4aa4b988042c9674ec9f25af6e9b9b1e3a4c3b` | MATCH |
| 136 | `docs/reference/mb-sound/LABORATORY_RECORD.md` | `mb_sound/process/LABORATORY_RECORD.md` | `4d20544b22af5088c1f253087151dd559d75208edf4be434f54c496b8be0bcf1` | MATCH |
| 137 | `docs/reference/mb-sound/LINKAGE.md` | `mb_sound/process/LINKAGE.md` | `fa5641cae9c47c94d8821fbad81fcffccd9d6b46e2dfafa7afc66c1d1d72dd1a` | MATCH |
| 138 | `docs/reference/mb-sound/NAMESPACE.md` | `mb_sound/process/NAMESPACE.md` | `41c50cfee0ed5e1b4d1c59105cc3599c3def6bc087e036f58912708a3e9d369d` | MATCH |
| 139 | `docs/reference/mb-sound/README.md` | `mb_sound/process/README.md` | `96d1a676f5e3096b3b6dc38501795669798a541f6f40bfccac397a96caf50db5` | MATCH |
| 140 | `docs/reference/mb-sound/TREATMENT_COHORTS.md` | `mb_sound/process/TREATMENT_COHORTS.md` | `c6df9b6b103e82e2d1f1ff4708473431948c3cb2496a6fe0c1b6ebb8f4141b47` | MATCH |
| 141 | `docs/reference/mb-sound/schema/lab_procedure.example.json` | `mb_sound/process/schema/lab_procedure.example.json` | `451abe22ad224aaead0506a07de422ff3bef99d04cc77ad3658aaac5881f34d7` | MATCH |
| 142 | `docs/reference/mb-sound/schema/panel.example.json` | `mb_sound/process/schema/panel.example.json` | `93ff83140193175ab16e73ba1d7d32b4efa4d3348bcfd591272e5cc9b0dc6c24` | MATCH |
| 143 | `docs/reference/mb-sound/staging/.gitignore` | `mb_sound/process/staging/.gitignore` | `5cf2f8a09910e16e5fca65a4ed016eb87022b1279d5893de9a8fab5b1d6bb5ce` | MATCH |
| 144 | `docs/reference/mb-sound/staging/ocr/.gitkeep` | `mb_sound/process/staging/ocr/.gitkeep` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | MATCH |
| 145 | `docs/reference/mb-sound/staging/rows.jsonl` | `mb_sound/process/staging/rows.jsonl` | `59dc50d00730d2bf8c335ca995017af3698f90bd1192f5c83079593d8bc66c2f` | MATCH |
