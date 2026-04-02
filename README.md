# KubePathAudit

**Graph-Based Security Analysis for Cloud-Native Infrastructure**

KubePathAudit models a Kubernetes cluster as a directed graph and applies classical graph algorithms to detect exploitable multi-hop attack paths — chains of permissions that appear harmless in isolation but enable lateral movement to crown-jewel resources.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   KubePathAudit                          │
├──────────────┬──────────────────┬────────────────────────┤
│   CLI Tool   │   FastAPI REST   │  React Dashboard       │
│  (cli.py)    │   (main.py)      │  (frontend/)           │
├──────────────┴──────────────────┴────────────────────────┤
│              Graph Engine (graph_engine.py)               │
│   BFS Blast Radius · Dijkstra Shortest Path              │
│   DFS Cycle Detection · Critical Node Analysis           │
├──────────────────────────────────────────────────────────┤
│  Data Ingestion   │  CVE Scorer   │  Temporal Analysis   │
│  (ingest.py)      │  (cve_scorer) │  (temporal.py)       │
├──────────────────────────────────────────────────────────┤
│            NetworkX · kubectl · mock data                 │
└──────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the web dashboard)
- `kubectl` (optional — for live cluster ingestion)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### Run the CLI

```bash
# Full analysis with all 4 algorithms
python cli.py analyze --input mock-cluster-graph.json

# Generate a PDF Kill Chain Report
python cli.py analyze --input mock-cluster-graph.json --pdf report.pdf

# Machine-readable JSON output
python cli.py analyze --input mock-cluster-graph.json --json
```

### Run the Web Dashboard

```bash
# Terminal 1 — Backend API
cd backend
uvicorn main:app --reload

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

---

## CLI Reference

### `analyze` — Full Security Analysis

Runs all 4 algorithms (BFS, Dijkstra, DFS, Critical Node) and outputs a complete Kill Chain Report.

```bash
python cli.py analyze --input mock-cluster-graph.json
python cli.py analyze -i mock-cluster-graph.json --pdf report.pdf
python cli.py analyze -i mock-cluster-graph.json --json
python cli.py analyze -i mock-cluster-graph.json --diff --snapshot
```

| Flag | Description |
|---|---|
| `--input`, `-i` | Path to cluster graph JSON (default: `mock-cluster-graph.json`) |
| `--pdf FILE` | Export the report as a PDF file |
| `--json` | Output all results as a JSON object |
| `--hops N` | Max hops for blast radius (default: 3) |
| `--blast-source ID` | Override source node for blast radius |
| `--path-source ID` | Override source for shortest path |
| `--path-target ID` | Override target for shortest path |
| `--diff` | Compare against the latest stored snapshot |
| `--snapshot` | Save current scan as a timestamped snapshot |
| `--snapshot-label TEXT` | Label for the snapshot |

### `blast-radius` — BFS Blast Radius

```bash
python cli.py blast-radius --source internet --hops 3 --input mock-cluster-graph.json
```

### `shortest-path` — Dijkstra's Shortest Attack Path

```bash
python cli.py shortest-path --source internet --target prod-database --input mock-cluster-graph.json
```

### `detect-cycles` — DFS Circular Permission Detection

```bash
python cli.py detect-cycles --input mock-cluster-graph.json
```

### `critical-node` — Critical Chokepoint Identification

```bash
python cli.py critical-node --input mock-cluster-graph.json
```

### `ingest` — Live Cluster Ingestion

```bash
python cli.py ingest -o cluster-graph.json
python cli.py ingest -o cluster-graph.json --live-cve --snapshot
```

| Flag | Description |
|---|---|
| `--output`, `-o` | Output JSON file path (default: `cluster-graph.json`) |
| `--live-cve` | Enable live NVD API lookups for CVE scoring |
| `--snapshot` | Save the ingested data as a snapshot |

### `snapshots` — List Stored Snapshots

```bash
python cli.py snapshots
```

### `diff` — Temporal Graph Comparison

```bash
python cli.py diff --input cluster-graph.json
python cli.py diff --old snapshots/snap_old.json --new snapshots/snap_new.json
```

### Global Flags

| Flag | Description |
|---|---|
| `--no-color` | Disable ANSI colored output |

---

## JSON Schema

The cluster graph JSON conforms to the following schema:

```json
{
  "metadata": {
    "cluster_name": "string",
    "scan_timestamp": "ISO 8601 datetime",
    "scenario": "string (optional)",
    "description": "string (optional)"
  },
  "nodes": [
    {
      "id": "unique-string-id",
      "label": "Human-readable name",
      "type": "pod | serviceaccount | role | clusterrole | rolebinding | secret | configmap | database | internet | ingress | service",
      "namespace": "kubernetes-namespace",
      "risk_level": "low | medium | high | critical | crown-jewel | entry-point | info",
      "metadata": {
        "description": "string",
        "cves": ["CVE-YYYY-NNNNN"],
        "cvss_scores": [0.0],
        "ports": [80],
        "labels": {},
        "icon": "string"
      }
    }
  ],
  "edges": [
    {
      "source": "node-id",
      "target": "node-id",
      "relationship": "uses_service_account | bound_by | grants | can_access | authenticates_to | routes_to | forwards_to | ...",
      "weight": 1.0,
      "metadata": {
        "description": "string"
      }
    }
  ]
}
```

### Edge Weight Convention

Edge weights represent **exploitability** — lower values mean easier to exploit:

| Weight | Meaning |
|---|---|
| 0.5 | Trivial (auto-mounted token, `cluster-admin` binding) |
| 1.0 | Easy (standard credential access) |
| 1.5–2.0 | Moderate (requires some access or authentication) |
| 2.5–3.0 | Hard (requires specific conditions or multiple steps) |

---

## Algorithms

### 1. Blast Radius (BFS)

**Purpose:** If a node is compromised, how far can the attacker reach?

Runs breadth-first search from the source up to N hops, returning the "Danger Zone" — all reachable nodes and whether crown jewels are within reach.

### 2. Shortest Attack Path (Dijkstra)

**Purpose:** What is the easiest route from entry point to crown jewel?

Uses Dijkstra's algorithm with edge weights (exploitability scores) to find the lowest-cost attack path, then formats it as a Kill Chain with per-step CVE annotations.

### 3. Circular Permission Detection (DFS)

**Purpose:** Detect misconfigured mutual admin grants.

Uses DFS-based cycle detection to find circular permission loops (e.g., `Service-A ↔ Service-B` mutual admin grants) that amplify attack paths.

### 4. Critical Node Analysis

**Purpose:** Which single node's removal breaks the most attack paths?

For each intermediate node, temporarily removes it and recounts the number of valid source-to-crown-jewel paths. Reports the node whose removal causes the greatest reduction.

---

## Project Structure

```
kuber attack path visualizer/
├── backend/
│   ├── cli.py                  # CLI entry point
│   ├── main.py                 # FastAPI REST API
│   ├── graph_engine.py         # Core graph analysis (NetworkX)
│   ├── ingest.py               # kubectl data ingestion
│   ├── cve_scorer.py           # CVE scoring (static DB + NVD API)
│   ├── temporal.py             # Snapshot storage & graph diffing
│   ├── mock-cluster-graph.json # Sample cluster data
│   ├── requirements.txt        # Python dependencies
│   └── snapshots/              # Timestamped graph snapshots
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # Main dashboard
│   │   ├── components/         # React components
│   │   │   ├── GraphCanvas.tsx      # Force-directed graph
│   │   │   ├── ControlPanel.tsx     # Algorithm controls
│   │   │   ├── KillChainReport.tsx  # Kill Chain modal + PDF export
│   │   │   └── SecuritySidebar.tsx  # Node detail sidebar
│   │   └── lib/                # API client, types, utilities
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## License

MIT
