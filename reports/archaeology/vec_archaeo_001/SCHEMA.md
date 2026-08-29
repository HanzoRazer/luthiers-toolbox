# VEC-ARCHAEO-001 Stage 1 schemas

Companion for Stage 2 consumers. The JSONL files are one JSON object per line
with no comment header (a `#` or `//` block would break a strict JSONL parser).
`sessions.json` is a single JSON object.

Encoding is UTF-8. Dates are ISO-8601 strings as emitted by git (offset included;
timezone is not normalized). Null is JSON `null`.

Scope of this scan: `HanzoRazer/luthiers-toolbox` parent mirror only.
`vectorizer-sandbox` was not scanned.

---

## `commits.jsonl`

One record per SHA from:

`git rev-list --all --since=2026-01-01 --until=2026-04-01`

Git default for `--since`/`--until` is **committer** date. Count in this
delivery: **4254**.

| Field | Type | Notes |
| --- | --- | --- |
| `sha` | string | Full 40-char object name. |
| `short_sha` | string | First 8 characters of `sha`. |
| `author_date` | string | Author timestamp (ISO-8601 with offset). |
| `commit_date` | string | Committer timestamp (ISO-8601 with offset). |
| `author` | string | Author name (not email). |
| `subject` | string | First line of the commit message, unmodified. |
| `body` | string | Remainder of the message after the subject. May be empty. |
| `parents` | string[] | Parent SHAs. Length 1 for ordinary commits; 2 for the 16 merges in this window. |
| `is_merge` | boolean | `true` when `len(parents) > 1`. |
| `refs` | string[] | Refs from `git log --all --source` that pointed at this commit in the mirror. |
| `tags` | string[] | Tags whose peeled object **is** this commit (direct). Ancestry containment was not computed. |
| `pr_number` | int \| null | GitHub PR number when one could be parsed from the message or ref; otherwise `null`. |
| `trailers` | object | Git trailers as `name → string`. Observed keys in this delivery: `Co-authored-by`, `Fixes`. Empty object when none. |
| `files` | object[] | Paths touched by this commit. See below. |
| `surface` | string[] | Coarse path-bucket labels for files on this commit. A commit may belong to more than one surface. Values observed: `other`, `docs`, `tests`, `blueprint_import`, `photo_vectorizer`, `archive`, `api_routing`, `phase4_annotations`, `calibration`, `classifiers`. |
| `notes` | string | Reserved. Empty string throughout this Stage 1 delivery. |

### `files[]` on a commit record

| Field | Type | Notes |
| --- | --- | --- |
| `status` | string | git status letter: `A` add, `M` modify, `D` delete, `R` rename, `C` copy. |
| `path` | string | Path after the change. |
| `old_path` | string \| null | Path before a rename/copy; `null` otherwise. |
| `added` | int | Lines added. **Always `0` in this Stage 1 delivery** (numstat was not populated). |
| `deleted` | int | Lines deleted. **Always `0` in this Stage 1 delivery**. |

---

## `files.jsonl`

One record per distinct path touched in the window. Count in this delivery: **6061**.

| Field | Type | Notes |
| --- | --- | --- |
| `path` | string | Path as recorded by git. Unusual names may be shell-quoted (leading/trailing `"`). |
| `first_seen_sha` | string | First in-window commit that introduced or first touched the path. |
| `first_seen_date` | string | Committer date of `first_seen_sha`. |
| `last_touched_sha` | string | Last in-window commit that touched the path. |
| `last_touched_date` | string | Committer date of `last_touched_sha`. |
| `deleted_in_window` | boolean | `true` if the path was deleted by some in-window commit. |
| `deleted_sha` | string \| null | SHA of that delete commit when `deleted_in_window` is true; otherwise `null`. |
| `rename_chain` | string[] | Observed names of this path in the window, oldest first. Length 1 when never renamed. |
| `touch_count` | int | In-window commits that touched the path. |
| `authors` | string[] | Distinct author names who touched the path. |
| `kind` | string | Coarse file class. Values observed: `code`, `document`, `artifact`, `config`, `fixture`. |
| `surface` | string | Single path-bucket label. Same vocabulary as `commits.jsonl` `surface` (one value, not a list). |

---

## `sessions.json`

A single JSON object. Sessions are a **navigation index**, not hours worked.

| Field | Type | Notes |
| --- | --- | --- |
| `session_definition` | string | Prose definition used to cut the stream. |
| `gap_hours_primary` | number | Gap used for the `sessions` array. This delivery: `4.0`. |
| `gap_hours_sensitivity` | object | Session counts at alternate gaps. This delivery: `{"2": 216, "4": 125, "8": 47}`. |
| `known_distortion` | string | Why session counts are not effort. Parallel worktrees and duplicate-subject SHAs inflate the index. |
| `sessions` | object[] | Sessions at `gap_hours_primary`, ordered by author date. |

### `sessions[]`

A session is a maximal run of window commits ordered by **author** date where the
gap between consecutive commits is `<= gap_hours_primary`. A larger gap starts a
new session.

| Field | Type | Notes |
| --- | --- | --- |
| `session_id` | string | `S001` … `S125` in this delivery. |
| `start` | string | Author date of the first commit. |
| `end` | string | Author date of the last commit. |
| `duration_hours` | number | `end - start` in hours (not working time). |
| `commit_count` | int | Number of SHAs in `commits`. |
| `commits` | string[] | Full SHAs, author-date order. |
| `branches_touched` | string[] | Union of `refs` from those commits. |
| `files_created` | string[] | Paths with status `A` in the session. |
| `files_modified` | string[] | Paths with status `M`. |
| `files_deleted` | string[] | Paths with status `D`. |
| `documents_produced` | string[] | Subset of created/modified paths classified `document`. |
| `subjects` | string[] | Commit subjects, same order as `commits`. |
| `annotations` | any[] | Reserved. Empty throughout this Stage 1 delivery. |

---

## What Stage 1 does not contain

- No disposition labels (`effective`, `failed`, `superseded`, and similar).
- No AGE / IBG / three-loop evaluation.
- No `vectorizer-sandbox` objects.
- No line-level numstat (`added` / `deleted` are present but unused).
