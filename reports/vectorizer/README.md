# Vectorizer — canonical pipeline bundle

Start here.

## What is in this folder

| File | What it is |
|---|---|
| [`CANONICAL_PIPELINE.md`](CANONICAL_PIPELINE.md) | **The index.** Which files actually constitute the vectorizer pipeline, split by intake, verified against a named commit |
| [`HOW_TO_DOWNLOAD.md`](HOW_TO_DOWNLOAD.md) | How to get the zip onto a PC, and which link to use |
| `PATHS.txt` | The same file list, plain text, for scripting |
| `canonical_vectorizer_pipeline.zip` | A snapshot of those source files, with repo paths preserved |

## The canonical source of truth is the repository

Everything in this folder is **derived**. The zip is a copy of source files taken at one
moment; `CANONICAL_PIPELINE.md` names that moment. The repository at that commit is
authoritative, and this folder is not.

That matters more than it sounds. A bundle of source files carries no signal when it goes
stale — it keeps opening, keeps looking complete, and quietly describes a pipeline that has
moved. Treat any disagreement between this folder and the repository as the folder being
wrong.

## What this bundle is for

Reading and working on the pipeline locally, without copy-pasting dozens of files out of the
GitHub UI. It is fine to reuse inside the project.

It is **not** a release artifact and not a distribution channel. It is not versioned, it is
not rebuilt when the sources change, and nothing watches it for drift. Do not hand it to
someone as "the vectorizer."

## The two-intake point

The single most useful thing in `CANONICAL_PIPELINE.md` is that there is **not one Python
file**. There are **two production intakes** — the blueprint path (default mode `refined`)
and the photo path, which is a separate endpoint. Anyone looking for "the vectorizer file"
is looking for something that does not exist, and that is the misconception this bundle was
assembled to correct.

`vectorizer-sandbox` is deliberately out of scope here. This is `luthiers-toolbox` only.
