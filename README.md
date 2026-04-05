# KubeInsights — Kubernetes Attack Path Visualizer

# demo link

https://cyberpaglus-hnt9.onrender.com/

> Graph-Based Security Analysis for Cloud-Native Infrastructure

KubeInsights is a security analysis tool that models Kubernetes cluster permissions as a directed graph and discovers attack paths from entry points (internet, users) to crown jewels (databases, secrets, persistent volumes).

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/TheCodeNotTakenT-T/kuber-attack-path-project.git
cd kuber-attack-path-project

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Run full analysis
python cli.py analyze --input mock-cluster-graph.json
```

### Requirements

- Python 3.10+
- Dependencies: `networkx`, `fastapi`, `uvicorn`, `pydantic`, `python-multipart`, `reportlab`

---

## CLI Usage

### Full Security Report

Runs all 4 algorithms and generates a comprehensive Kill Chain report:

```bash
python cli.py analyze --input mock-cluster-graph.json
```

**Expected output** (abbreviated):

```
══════════════════════════════════════════════════════════════════
  KILL CHAIN REPORT  —  2026-04-03 02:25:35
  Cluster : mock-prod-cluster
  Nodes   : 41  |  Edges: 48
══════════════════════════════════════════════════════════════════

[ SECTION 1 — ATTACK PATH DETECTION (Dijkstra) ]
  ⚠  18 attack path(s) detected
  Path #1  |  3 hops  |  Risk Score: 9.5  [MEDIUM]
  ...

[ SECTION 2 — BLAST RADIUS ANALYSIS (BFS, depth=3) ]
  Source: internet  →  13 reachable resource(s) within 3 hops
  ...

[ SECTION 3 — CIRCULAR PERMISSION DETECTION (DFS) ]
  ⚠  1 cycle(s) detected
  Cycle #1: service-a ↔ service-b ↔ service-a

[ SECTION 4 — CRITICAL NODE ANALYSIS ]
  Baseline attack paths : 46
  ★  RECOMMENDATION:
     Remove permission binding 'web-frontend' (Pod) to eliminate 32 of 46 attack paths.
```

### Individual Algorithm Commands

```bash
# BFS Blast Radius — find all nodes reachable within N hops
python cli.py blast-radius --source pod-webfront --hops 3 --input mock-cluster-graph.json

# Dijkstra Shortest Path — find cheapest attack path between two nodes
python cli.py shortest-path --source user-dev1 --target db-production --input mock-cluster-graph.json

# DFS Cycle Detection — find circular permission loops
python cli.py detect-cycles --input mock-cluster-graph.json

# Critical Node Analysis — identify the most impactful node to remove
python cli.py critical-node --input mock-cluster-graph.json
```

### Additional Options

```bash
# JSON output (for scripting/integration)
python cli.py analyze --input mock-cluster-graph.json --json

# PDF export
python cli.py analyze --input mock-cluster-graph.json --pdf report.pdf

# Live cluster ingestion (requires kubectl)
python cli.py ingest -o cluster-graph.json

# Temporal diff (compare snapshots)
python cli.py analyze --input mock-cluster-graph.json --snapshot --diff
```

---

## Algorithms

### 1. BFS — Blast Radius Analysis

Performs a **Breadth-First Search** from a source node to discover all reachable resources within N hops. Results are grouped by hop layer to show the "danger zone" — everything an attacker could reach from a compromised entry point.

- **Input:** Source node ID, max hops (default: 3)
- **Output:** Nodes grouped by hop distance, total count, risk summary

### 2. Dijkstra — Shortest Attack Path

Uses **Dijkstra's algorithm** with edge weights (attack difficulty scores) to find the lowest-cost path from an attacker's entry point to a high-value target. Lower total weight = easier attack.

- **Input:** Source and target node IDs
- **Output:** Ordered node sequence, total cost, hop count, CVE annotations on edges
- **Severity Labels:** `CRITICAL` (≥20), `HIGH` (10–19.9), `MEDIUM` (5–9.9), `LOW` (<5)

### 3. DFS — Cycle Detection

Detects **circular permission loops** using DFS-based cycle finding (via `nx.simple_cycles` with length bound). These represent mutual admin grants or privilege escalation loops.

- **Input:** Full graph
- **Output:** List of cycles as ordered node sequences, deduplicated

### 4. Critical Node Analysis — Graph Surgery

Identifies the **single non-source, non-sink node** whose removal eliminates the greatest number of source-to-sink attack paths. Uses brute-force removal-and-recount methodology:

1. Count baseline paths using `nx.all_simple_paths` with cutoff depth
2. For each candidate, **copy** the graph (original never mutated), remove the node, recount paths
3. Rank by paths eliminated

- **Input:** Full graph with source/sink annotations
- **Output:** Critical node, paths eliminated count, top-5 ranking

---

## Schema Documentation

### `cluster-graph.json` Format

The input JSON file follows this schema:

```json
{
  "metadata": {
    "cluster": "cluster-name",
    "generated": "2026-04-03",
    "node_count": 40,
    "edge_count": 48,
    "description": "Cluster description"
  },
  "nodes": [ ... ],
  "edges": [ ... ]
}
```

### Node Schema

Each node represents a Kubernetes resource:

| Field        | Type       | Description                                          |
|-------------|------------|------------------------------------------------------|
| `id`        | `string`   | Unique internal identifier (e.g., `pod-webfront`)    |
| `type`      | `string`   | Resource type: `Pod`, `ServiceAccount`, `Role`, `ClusterRole`, `Secret`, `ConfigMap`, `Service`, `Database`, `Node`, `Namespace`, `PersistentVolume`, `User`, `ExternalActor` |
| `name`      | `string`   | Human-readable display name (e.g., `web-frontend`)   |
| `namespace` | `string`   | Kubernetes namespace                                  |
| `risk_score`| `float`    | Numeric risk score (0.0–10.0)                        |
| `is_source` | `boolean`  | `true` if this is an attacker entry point            |
| `is_sink`   | `boolean`  | `true` if this is a high-value target (crown jewel)  |
| `cves`      | `string[]` | List of CVE identifiers (e.g., `["CVE-2024-1234"]`)  |

**Example node:**
```json
{
  "id": "pod-webfront",
  "type": "Pod",
  "name": "web-frontend",
  "namespace": "default",
  "risk_score": 7.5,
  "is_source": false,
  "is_sink": false,
  "cves": ["CVE-2024-1234"]
}
```

### Edge Schema

Each edge represents a relationship between two resources:

| Field          | Type           | Description                                      |
|---------------|----------------|--------------------------------------------------|
| `source`      | `string`       | Source node ID                                    |
| `target`      | `string`       | Target node ID                                    |
| `relationship`| `string`       | Relationship type (see below)                     |
| `weight`      | `float`        | Attack difficulty score (lower = easier)          |
| `cve`         | `string\|null` | CVE exploited on this edge (if any)               |
| `cvss`        | `float\|null`  | CVSS score of the exploited CVE                   |

**Relationship types:**
- `can-exec` — User can execute commands in a pod
- `uses` — Pod uses a ServiceAccount
- `bound-to` — ServiceAccount is bound to a Role via RoleBinding
- `can-read` — Role can read a Secret/ConfigMap
- `grants-access-to` — Secret grants access to a database/system
- `reaches` — External actor reaches a service
- `routes-to` — Service routes traffic to a pod
- `calls` — Pod calls a service endpoint
- `falls-back-to` — Pod falls back to default ServiceAccount
- `admin-grant` — Mutual admin permission (cycle indicator)
- `mounts` — Node mounts a PersistentVolume
- `reads` — Pod reads a ConfigMap
- `exposes-endpoint` — ConfigMap exposes a database endpoint
- `impersonates` — User impersonates a ServiceAccount
- `can-exec-on` — Role can execute on a Node

**Weight semantics:** Edge weights represent attack difficulty on a 0–10 scale. Lower weights indicate easier exploitation. The sum of edge weights along a path gives the total attack difficulty score.

**Example edge:**
```json
{
  "source": "user-dev1",
  "target": "pod-webfront",
  "relationship": "can-exec",
  "weight": 5.0,
  "cve": "CVE-2024-1234",
  "cvss": 8.1
}
```

---

## Project Structure

```
kuber-attack-path-project/
├── backend/
│   ├── cli.py                    # CLI tool (main entry point)
│   ├── graph_engine.py           # Core graph analytics engine (NetworkX)
│   ├── main.py                   # FastAPI REST API server
│   ├── ingest.py                 # Live cluster ingestion via kubectl
│   ├── cve_scorer.py             # CVE/CVSS scoring (NVD API + static DB)
│   ├── advanced_weight_scorer.py # Multi-factor edge weight calculation
│   ├── temporal.py               # Snapshot storage & temporal diffing
│   ├── mock-cluster-graph.json   # Mock cluster data for testing
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # Main React component
│   │   ├── components/           # UI components (graph viz, sidebar, etc.)
│   │   └── lib/                  # Utilities and type definitions
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## Bonus Features

### B1: Interactive Graph Visualization (+5)

A React + D3.js frontend renders the attack graph in the browser with:
- Color-coded nodes by risk level (red = critical, green = safe)
- Attack path highlighting
- Zoom/pan navigation
- Node tooltips showing name, type, risk score, CVEs

**Run the frontend:**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### B2: Live CVE Scoring (+5)

Integration with NIST NVD API for real-time CVSS score lookups:
- Automatic CVE scoring based on container image vulnerabilities
- Fallback to static CVE database when API is unavailable
- Rate limiting handled gracefully

### B3: Temporal Analysis (+5)

Snapshot-based temporal diffing:
- Store graph snapshots over time
- Detect new nodes, edges, and attack paths between scans
- Alert output describes changes and risk delta

```bash
# Save a snapshot
python cli.py analyze --input cluster-graph.json --snapshot

# Compare with latest snapshot
python cli.py diff --input cluster-graph.json
```
