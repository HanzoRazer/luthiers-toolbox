# IBG — Instrument Body Generator bundle

Start here.

## What is in this folder

| File | What it is |
|---|---|
| [`CANONICAL_PIPELINE.md`](CANONICAL_PIPELINE.md) | **The index.** Which files constitute the IBG pipeline, verified against a named commit |
| [`HOW_TO_DOWNLOAD.md`](HOW_TO_DOWNLOAD.md) | How to get the zip onto a PC, and which link to use |
| `PATHS.txt` | The same file list, plain text, for scripting |
| `canonical_ibg_pipeline.zip` | A snapshot of those source files, with repo paths preserved |

## Two boundaries this bundle exists to draw

**IBG is the Instrument Body Generator** — a parametric body completor. It consumes DXF and
landmarks. **It does not process images.** That is a governed boundary, not a description of
current capability.

**`services/api/app/ibg_repository/` is not this.** It is a repository-proposal package that
shares the initials, and it is deliberately excluded from the zip. Sharing three letters with
a governed pipeline is exactly how two unrelated things get discussed as one.

## The canonical source of truth is the repository

Everything in this folder is **derived**. The zip is a copy of source files taken at one
moment; `CANONICAL_PIPELINE.md` names that moment. The repository at that commit is
authoritative, and this folder is not.

For anything about what IBG is *permitted* to do — as opposed to which files it currently
occupies — `docs/governance/IBG_ROLE_DEFINITION.md` outranks this folder entirely.

That distinction matters here more than it would for an ordinary bundle. A snapshot of
governed code carries no signal when it goes stale: it keeps opening, keeps looking complete,
and quietly describes a pipeline whose governance may have moved underneath it. Treat any
disagreement between this folder and either the repository or the role definition as this
folder being wrong.

## What this bundle is for

Reading and working on the IBG pipeline locally, without copy-pasting dozens of files out of
the GitHub UI. Fine to reuse inside the project.

It is **not** a release artifact and not a distribution channel. It is not versioned, not
rebuilt when the sources change, and nothing watches it for drift.
