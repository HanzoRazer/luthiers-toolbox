# Codespace Configuration

This directory contains the GitHub Codespaces / VS Code devcontainer configuration for Luthier's Toolbox.

## What Gets Configured

### Environment
- **Python 3.11** with all backend dependencies
- **Node.js 20** for Vue 3 frontend
- **Git** and **GitHub CLI** for repository management

### VS Code Extensions
- Python (Pylance, Black formatter)
- Vue (Volar)
- GitHub Copilot & Copilot Chat
- ESLint, Prettier

### Ports
- **8000**: FastAPI backend
- **5173**: Vite frontend dev server

### Environment Variables
```bash
CODESPACES=true
PYTHONPATH=/workspaces/luthiers-toolbox/services/api
RMOS_RUNS_V2_ENABLED=true
ART_STUDIO_DB_PATH=/tmp/art_studio.db
```

## First-Time Setup

When you open the repository in a Codespace:

1. **Wait for setup** - The `postCreateCommand` will run `setup.sh` automatically
2. **Check output** - Review the setup log for any errors
3. **Verify fence system** - Run `make check-boundaries` to confirm all CI gates work

## Quick Start

```bash
# Terminal 1: Start backend
make start-api

# Terminal 2: Start frontend
make start-client

# Terminal 3: Run fence checks
make check-boundaries
```

## Fence System Validation

The setup script automatically:
- Validates `FENCE_REGISTRY.json` JSON syntax
- Makes CI scripts executable
- Tests the fence runner

To manually verify:
```bash
cd services/api
python -m app.ci.fence_runner --list    # List all 8 fence profiles
python -m app.ci.fence_runner --dry-run # Preview checks
python -m app.ci.fence_runner           # Run all enabled fences
```

## Troubleshooting

### Setup script failed
```bash
# Re-run setup manually
bash .devcontainer/setup.sh
```

### Python imports not working
```bash
# Verify PYTHONPATH
echo $PYTHONPATH
# Should include: /workspaces/luthiers-toolbox/services/api
```

### Port forwarding issues
- Check VS Code Ports panel (bottom)
- Ensure ports 8000 and 5173 are forwarded
- Try stopping/restarting the services

### Fence runner errors
```bash
# Test from correct directory
cd services/api
python -m app.ci.fence_runner --list

# Check registry exists
ls ../../FENCE_REGISTRY.json
```

## File Structure

```
.devcontainer/
├── devcontainer.json  # Main configuration
├── setup.sh          # Post-create setup script
└── README.md         # This file
```

## Differences from Local Environment

| Aspect | Codespace | Local (Windows) |
|--------|-----------|-----------------|
| Shell | bash | PowerShell |
| Line endings | LF | CRLF (controlled by .gitattributes) |
| Python env | System python 3.11 | .venv virtual env |
| Database path | /tmp/art_studio.db | services/api/app/data/art_studio.db |
| `$CODESPACES` | `true` | empty/not set |

## Syncing Between Environments

When working across Codespace and local desktop:

1. **Commit in Codespace**:
   ```bash
   git add .devcontainer/
   git commit -m "feat(ci): add Codespace configuration"
   git push
   ```

2. **Pull on Desktop**:
   ```powershell
   git pull --rebase
   ```

3. **Line Endings**: `.gitattributes` ensures consistent LF in repo, CRLF on Windows checkout

## Environment Detection

Scripts can detect the environment:
```bash
if [ "$CODESPACES" = "true" ]; then
  echo "Running in Codespace"
else
  echo "Running locally"
fi
```

```powershell
if ($env:CODESPACES -eq "true") {
  Write-Host "Running in Codespace"
} else {
  Write-Host "Running locally"
}
```

## See Also

- [FENCE_REGISTRY.json](../FENCE_REGISTRY.json) - Boundary enforcement registry
- [docs/governance/FENCE_ARCHITECTURE.md](../docs/governance/FENCE_ARCHITECTURE.md) - Fence system docs
- [Makefile](../Makefile) - Build and CI targets
