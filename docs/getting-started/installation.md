# Installation

## Prerequisites

- **Python 3.11+** - For the API backend
- **Node.js 18+** - For the Vue frontend
- **Git** - For cloning the repository

---

## Clone the Repository

```bash
git clone https://github.com/HanzoRazer/luthiers-toolbox.git
cd luthiers-toolbox
```

---

## Backend Setup

### 1. Create Virtual Environment

```bash
cd services/api
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file:

```env
# Optional: AI features
OPENAI_API_KEY=your-key-here

# Optional: Data directory
RMOS_RUNS_DIR=./data/runs
```

### 4. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

API available at: [http://localhost:8000](http://localhost:8000)

API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd packages/client
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

UI available at: [http://localhost:5173](http://localhost:5173)

---

## Verify Installation

### Check API Health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "version": "0.33.x"
}
```

### Check UI

Open [http://localhost:5173](http://localhost:5173) in your browser. You should see the ToolBox dashboard.

---

## Docker (Alternative)

```bash
docker-compose up -d
```

This starts both API and UI in containers.

---

## Next Steps

- [Quick Start Guide](quickstart.md) - Build your first project
- [Configuration](configuration.md) - Customize settings
