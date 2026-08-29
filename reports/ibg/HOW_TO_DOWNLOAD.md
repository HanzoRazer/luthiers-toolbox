# How to get the IBG files onto your PC

Do not copy-paste from GitHub. Use the zip.

## This is a snapshot, and it will drift

The zip is a **point-in-time copy** of the IBG source files, taken at the commit named in
[`CANONICAL_PIPELINE.md`](CANONICAL_PIPELINE.md). It is not rebuilt when those files change,
and nothing watches it for drift.

If you are extracting this weeks after it was made, assume it has moved. Check any file that
matters against the repository before relying on it. **Where the zip and the repository
disagree, the repository is right.**

That warning is worth reading twice for IBG specifically, because the pipeline is under
active governance and its role definition has been amended more than once. A snapshot of
governed code is exactly the artifact most likely to be quoted after it stopped being true.

## Download

**Use this link once the PR is merged** — it follows `main` and survives branch deletion:

https://github.com/HanzoRazer/luthiers-toolbox/raw/main/reports/ibg/canonical_ibg_pipeline.zip

**Before the PR is merged**, that link 404s because the file is not on `main` yet. Use the
branch link instead:

https://github.com/HanzoRazer/luthiers-toolbox/raw/cursor/ibg-canonical-pipeline-files-5bd1/reports/ibg/canonical_ibg_pipeline.zip

> **The branch link is temporary.** It stops working as soon as
> `cursor/ibg-canonical-pipeline-files-5bd1` is deleted, which normally happens on merge. It
> exists for reviewing this PR. If you are bookmarking or pasting a link anywhere that
> outlives this review, use the `main` link above.

Then in Downloads: right-click → **Extract All**.

## If the link opens a page instead of downloading

1. Open the file page — after merge:
   https://github.com/HanzoRazer/luthiers-toolbox/blob/main/reports/ibg/canonical_ibg_pipeline.zip
2. Click **Download raw file** (down-arrow, top right).

## Where to start after extracting

`CANONICAL_PIPELINE.md`, at the top of the extracted folder. It is the index, and it also
draws the two boundaries that make this bundle worth having:

- **IBG is the Instrument Body Generator** — a parametric body completor. It consumes DXF and
  landmarks. **It does not process images.**
- `services/api/app/ibg_repository/` is a **repository-proposal package**, a different thing
  that shares the initials. It is deliberately **not** in the zip.

Source files keep their repo paths inside the zip
(`services/api/app/instrument_geometry/body/ibg/instrument_body_generator.py`, and so on), so
a path in `CANONICAL_PIPELINE.md` is also a path in the repository.
