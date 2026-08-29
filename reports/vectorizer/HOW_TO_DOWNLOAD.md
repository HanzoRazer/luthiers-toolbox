# How to get the pipeline files onto your PC

Do not copy-paste from GitHub. Use the zip.

## What this bundle is, and is not

It is a **point-in-time convenience snapshot**, made so the canonical pipeline files can be
read and worked on locally without copy-pasting forty-odd files out of the GitHub UI.

It is **not** a release artifact, not a distribution channel, and **not a source of truth**.
The source of truth is the repository itself, at the commit named in
[`CANONICAL_PIPELINE.md`](CANONICAL_PIPELINE.md). The zip is a copy of source files that will
keep changing; the moment they do, the zip is stale and nothing will tell you. Check it
against the repo before relying on it for anything that matters.

Reuse it freely inside the project. Do not hand it to anyone as "the vectorizer," because in
three weeks it will not be.

## Download

**Use this link once the PR is merged** — it follows `main` and survives branch deletion:

https://github.com/HanzoRazer/luthiers-toolbox/raw/main/reports/vectorizer/canonical_vectorizer_pipeline.zip

**Before the PR is merged**, that link 404s because the file is not on `main` yet. Use the
branch link instead:

https://github.com/HanzoRazer/luthiers-toolbox/raw/cursor/vec-canonical-pipeline-files-5bd1/reports/vectorizer/canonical_vectorizer_pipeline.zip

> **The branch link is temporary.** It stops working as soon as
> `cursor/vec-canonical-pipeline-files-5bd1` is deleted, which normally happens on merge. It
> is here for reviewing this PR, and for nothing else. If you are bookmarking or pasting a
> link anywhere that outlives this review, use the `main` link above.

Then in Downloads: right-click → **Extract All**.

## If the link opens a page instead of downloading

1. Open the file page — after merge:
   https://github.com/HanzoRazer/luthiers-toolbox/blob/main/reports/vectorizer/canonical_vectorizer_pipeline.zip
2. Click **Download raw file** (down-arrow, top right).

## Where to start after extracting

`CANONICAL_PIPELINE.md`, at the top of the extracted folder. It is the index: it explains
that there is **not** one Python file but two production intakes, and it names the commit the
snapshot was verified against.

The source files keep their repo paths inside the zip
(`services/photo-vectorizer/edge_to_dxf.py`, and so on), so a path in `CANONICAL_PIPELINE.md`
is also the path in the repository.
