# Local development — sibling repositories

This folder documents **local workspace layout** for repos related to
`luthiers-toolbox`. The cognition-layer clone lives as a **sibling directory**
next to this repo (not inside `services/` and not inside `local/`).

## Two-repo semantic incubation

| Path (sibling clone) | Remote | Role |
|----------------------|--------|------|
| `../vectorizer-sandbox/` | https://github.com/HanzoRazer/vectorizer-sandbox | Semantic cognition layer (Tier A archaeology, incubation R&D) |

When both repos live under `Downloads/`:

```text
Downloads/
├── luthiers-toolbox/          ← runtime spine (this repo)
└── vectorizer-sandbox/        ← cognition layer (git clone)
```

**Runtime spine (this repo):** production extraction, Blueprint Reader, IBG gates.  
**Cognition layer (sandbox):** experiments and relocated semantic lineage — graduate via
`docs/governance/SEMANTIC_INCUBATION_ARCHITECTURE.md`, never bulk-import into `services/`.

## First-time setup

From repo root (PowerShell):

```powershell
.\local\clone-vectorizer-sandbox.ps1
```

Or manually (sibling next to this repo):

```powershell
git clone https://github.com/HanzoRazer/vectorizer-sandbox.git ..\vectorizer-sandbox
```

If you already cloned as `vectorizer-sandbox-review`, promote it to the canonical name:

```powershell
Move-Item "c:\Users\thepr\Downloads\vectorizer-sandbox-review" "c:\Users\thepr\Downloads\vectorizer-sandbox"
```

(Remove or rename an older `vectorizer-sandbox` folder first if one already exists.)

## Not the same as `sandbox/` at repo root

| Directory | Purpose |
|-----------|---------|
| **`../vectorizer-sandbox/`** | External cognition git repo (sibling) |
| **`sandbox/`** (repo root, gitignored) | In-repo experiments (e.g. `arc_reconstructor/`) |

Do not copy sandbox code into `services/`.

## Governance

- Main repo must not import sandbox modules under `services/` — enforced by
  `scripts/governance/check_semantic_sandbox_imports.py`.
- Relocation pointers: `services/photo-vectorizer/ARCHAEOLOGY_RELOCATION.md`,
  `services/blueprint-import/PHASE2_RELOCATION.md`.
