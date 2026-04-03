# Full Codebase

## CODEBASE.md

```markdown

```

## README.md

```markdown
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
#   k u b e r - a t t a c k - p a t h - p r o j e c t 
 
 # kuber-attack-path-project
```

## backend\attack_report.pdf

*(Could not read file: 'utf-8' codec can't decode byte 0x93 in position 10: invalid start byte)*

## backend\cli.py

```python
#!/usr/bin/env python3
"""
KubePathAudit CLI — Command-line security analysis tool for Kubernetes clusters.

Usage:
    python cli.py analyze --input mock-cluster-graph.json
    python cli.py blast-radius --source internet --hops 3
    python cli.py shortest-path --source internet --target prod-database
    python cli.py detect-cycles
    python cli.py critical-node
    python cli.py ingest -o cluster-graph.json
    python cli.py analyze --pdf report.pdf
    python cli.py analyze --diff
    python cli.py snapshots
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

from graph_engine import K8sGraphEngine
from cve_scorer import score_cve, score_image_cves, STATIC_CVE_DB
from temporal import (
    save_snapshot, list_snapshots, get_latest_snapshot,
    diff_graphs, format_diff_report,
)


# ── ANSI Colors ────────────────────────────────────────────────

class C:
    """ANSI color codes for terminal output."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"

    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"

    BG_RED    = "\033[41m"
    BG_YELLOW = "\033[43m"
    BG_BLUE   = "\033[44m"

    @staticmethod
    def disable():
        for attr in dir(C):
            if attr.isupper() and not attr.startswith("_"):
                setattr(C, attr, "")


# ── Helpers ────────────────────────────────────────────────────

def _severity_color(severity: str) -> str:
    colors = {
        "CRITICAL": C.RED + C.BOLD,
        "HIGH": C.RED,
        "MEDIUM": C.YELLOW,
        "LOW": C.GREEN,
        "NONE": C.GREEN,
        "TRIVIAL": C.RED + C.BOLD,
        "EASY": C.RED,
        "MODERATE": C.YELLOW,
        "HARD": C.GREEN,
    }
    return colors.get(severity.upper(), C.WHITE)


def _risk_color(risk: str) -> str:
    colors = {
        "crown-jewel": C.YELLOW + C.BOLD,
        "critical": C.RED + C.BOLD,
        "high": C.RED,
        "medium": C.YELLOW,
        "low": C.GREEN,
        "entry-point": C.CYAN,
        "info": C.DIM,
    }
    return colors.get(risk, C.WHITE)


def _load_engine(input_path: str) -> K8sGraphEngine:
    """Load the graph engine from a JSON file."""
    path = Path(input_path)
    if not path.exists():
        print(f"{C.RED}✗ File not found: {input_path}{C.RESET}")
        sys.exit(1)
    engine = K8sGraphEngine(str(path))
    return engine


def _print_banner():
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗  █████╗ ████████╗║
║   ██║ ██╔╝██║   ██║██╔══██╗██╔════╝██╔══██╗██╔══██╗╚══██╔══╝║
║   █████╔╝ ██║   ██║██████╔╝█████╗  ██████╔╝███████║   ██║   ║
║   ██╔═██╗ ██║   ██║██╔══██╗██╔══╝  ██╔═══╝ ██╔══██║   ██║   ║
║   ██║  ██╗╚██████╔╝██████╔╝███████╗██║     ██║  ██║   ██║   ║
║   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝  ╚═╝   ╚═╝   ║
║                                                              ║
║         {C.WHITE}K u b e P a t h A u d i t   C L I   v1.0{C.CYAN}            ║
║     {C.DIM}Graph-Based Security Analysis for Cloud-Native Infra{C.CYAN}     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{C.RESET}
""")


# ── Report Formatting ─────────────────────────────────────────

def _print_graph_summary(engine: K8sGraphEngine):
    """Print a summary of the loaded graph."""
    data = engine.get_graph_data()
    stats = data["stats"]
    meta = data.get("metadata", {})

    print(f"\n{C.BOLD}📊 Graph Summary{C.RESET}")
    print(f"{'─' * 50}")
    if meta.get("cluster_name"):
        print(f"  Cluster:      {C.CYAN}{meta['cluster_name']}{C.RESET}")
    if meta.get("scenario"):
        print(f"  Scenario:     {C.YELLOW}{meta['scenario']}{C.RESET}")
    print(f"  Total Nodes:  {C.WHITE}{stats['total_nodes']}{C.RESET}")
    print(f"  Total Edges:  {C.WHITE}{stats['total_edges']}{C.RESET}")
    print(f"  Crown Jewels: {C.YELLOW}{stats['crown_jewels']}{C.RESET}")
    print(f"  Critical:     {C.RED}{stats['critical_nodes']}{C.RESET}")
    print()


def _print_blast_radius(result: dict):
    """Print blast radius results."""
    if "error" in result and not result.get("affected_nodes"):
        print(f"\n{C.RED}✗ {result['error']}{C.RESET}")
        return

    risk = result["risk_summary"]
    color = _severity_color(risk)

    print(f"\n{C.BOLD}💥 Blast Radius Analysis{C.RESET}")
    print(f"{'─' * 50}")
    print(f"  Source:          {C.CYAN}{result['source']}{C.RESET}")
    print(f"  Max Hops:        {result['max_hops']}")
    print(f"  Nodes Affected:  {C.WHITE}{C.BOLD}{result['total_affected']}{C.RESET}")
    print(f"  Risk Level:      {color}{risk}{C.RESET}")
    if result.get("crown_jewels_reached"):
        print(f"  {C.RED}{C.BOLD}⚠ Crown Jewels Reached: {result['crown_jewels_reached']}{C.RESET}")
        for name in result.get("crown_jewel_names", []):
            print(f"    • {C.YELLOW}{name}{C.RESET}")

    print(f"\n  {C.DIM}Affected Nodes (Danger Zone):{C.RESET}")
    for node in sorted(result["affected_nodes"], key=lambda n: n["hop_distance"]):
        rc = _risk_color(node.get("risk_level", "low"))
        hop_bar = "█" * (node["hop_distance"] + 1)
        print(f"    {C.DIM}Hop {node['hop_distance']}:{C.RESET} {hop_bar} "
              f"{rc}{node.get('label', node['id'])}{C.RESET} "
              f"[{node.get('type', '?')}] "
              f"({node.get('risk_level', '?')})")
    print()


def _print_shortest_path(result: dict):
    """Print shortest path / kill chain results."""
    if "error" in result:
        if not result.get("path_exists", True):
            print(f"\n{C.GREEN}✓ No attack path exists from '{result.get('source', '?')}' "
                  f"to '{result.get('target', '?')}'{C.RESET}\n")
        else:
            print(f"\n{C.RED}✗ {result['error']}{C.RESET}")
        return

    diff = result["difficulty"]
    color = _severity_color(diff)

    print(f"\n{C.BOLD}⚠  ATTACK PATH DETECTED{C.RESET}")
    print(f"{'═' * 50}")
    print(f"  Source → Target:  {C.CYAN}{result['source']}{C.RESET} → {C.YELLOW}{result['target']}{C.RESET}")
    print(f"  Total Hops:       {C.WHITE}{C.BOLD}{result['hop_count']}{C.RESET}")
    print(f"  Path Risk Score:  {color}{result['total_weight']}{C.RESET}")
    print(f"  Difficulty:       {color}{diff}{C.RESET}")
    print(f"{'─' * 50}")

    # Kill chain
    chain = result.get("kill_chain_summary", [])
    print(f"\n  {C.BOLD}Kill Chain:{C.RESET}")
    for step in chain:
        rc = _risk_color(step.get("risk_level", "low"))
        cves = step.get("cves_exploited", [])
        cve_str = f" {C.RED}({', '.join(cves)}){C.RESET}" if cves else ""
        edge_str = f" {C.DIM}→ {step['edge_info']}{C.RESET}" if step.get("edge_info") and step["edge_info"] != "—" else ""

        print(f"    {C.BOLD}Step {step['step']}.{C.RESET} "
              f"{rc}{step['node']}{C.RESET} "
              f"[{step['node_type']}]{cve_str}")
        print(f"           {C.DIM}{step['action']}{edge_str}{C.RESET}")

    # Path summary line
    path_str = f" → ".join(result.get("path", []))
    print(f"\n  {C.DIM}Path: {path_str}{C.RESET}")
    print()


def _print_cycles(result: dict):
    """Print cycle detection results."""
    if not result["has_cycles"]:
        print(f"\n{C.GREEN}✓ No circular permission loops detected.{C.RESET}\n")
        return

    risk = result["risk_summary"]
    color = _severity_color(risk)

    print(f"\n{C.BOLD}🔄 Circular Permission Detection{C.RESET}")
    print(f"{'─' * 50}")
    print(f"  Cycles Found:  {color}{result['total_cycles']}{C.RESET}")
    print(f"  Risk Level:    {color}{risk}{C.RESET}")

    for i, cycle in enumerate(result["cycles"], 1):
        cr = _severity_color(cycle["risk"])
        print(f"\n  {C.BOLD}Cycle #{i}{C.RESET} ({cr}{cycle['risk']}{C.RESET}, "
              f"weight: {cycle['total_weight']}, "
              f"length: {cycle['length']}):")
        print(f"    {C.YELLOW}{cycle['description']}{C.RESET}")
    print()


def _print_critical_node(result: dict):
    """Print critical node analysis results."""
    if "error" in result:
        print(f"\n{C.RED}✗ {result['error']}{C.RESET}\n")
        return

    cn = result.get("critical_node")
    if not cn:
        print(f"\n{C.GREEN}✓ No critical chokepoint node identified.{C.RESET}\n")
        return

    print(f"\n{C.BOLD}🎯 Critical Node Analysis{C.RESET}")
    print(f"{'─' * 50}")
    print(f"  Baseline Attack Paths:  {C.WHITE}{result['baseline_paths']}{C.RESET}")
    print(f"  Entry Points:           {', '.join(result['entry_points'])}")
    print(f"  Crown Jewels:           {', '.join(result['crown_jewels'])}")

    print(f"\n  {C.RED}{C.BOLD}► Critical Node: {cn['label']}{C.RESET}")
    print(f"    Type:         {cn['type']}")
    print(f"    Namespace:    {cn['namespace']}")
    print(f"    Paths Broken: {C.RED}{cn['paths_broken']}{C.RESET} / {result['baseline_paths']}")
    print(f"    Impact:       {C.RED}{C.BOLD}{cn['impact_percentage']}%{C.RESET}")

    print(f"\n  {C.BOLD}💡 Recommendation:{C.RESET}")
    print(f"    {C.CYAN}{result['recommendation']}{C.RESET}")

    top5 = result.get("top_5_nodes", [])
    if len(top5) > 1:
        print(f"\n  {C.DIM}Top 5 Chokepoints:{C.RESET}")
        for i, node in enumerate(top5, 1):
            bar_len = int(node["impact_percentage"] / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"    {i}. {node['label']:<25} "
                  f"{_risk_color(node.get('risk_level', 'low'))}{bar} {node['impact_percentage']}%{C.RESET} "
                  f"({node['paths_broken']} paths)")
    print()


# ── PDF Report Generation ─────────────────────────────────────

def _generate_pdf(engine: K8sGraphEngine, output_path: str, blast_result=None, path_result=None, cycle_result=None, critical_result=None):
    """Generate a PDF Kill Chain Report using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import HexColor
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        print(f"{C.RED}✗ reportlab is required for PDF generation.{C.RESET}")
        print(f"  Install it with: pip install reportlab")
        return

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "KPATitle", parent=styles["Title"],
        fontSize=24, textColor=HexColor("#0ea5e9"),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "KPASubtitle", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#64748b"),
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "KPAHeading", parent=styles["Heading2"],
        fontSize=14, textColor=HexColor("#1e293b"),
        spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "KPABody", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#334155"),
        leading=14,
    ))
    styles.add(ParagraphStyle(
        "KPAWarning", parent=styles["Normal"],
        fontSize=11, textColor=HexColor("#dc2626"),
        leading=14, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "KPAMono", parent=styles["Normal"],
        fontSize=9, textColor=HexColor("#475569"),
        fontName="Courier", leading=12,
    ))

    elements = []

    # Title
    elements.append(Paragraph("KubePathAudit — Kill Chain Report", styles["KPATitle"]))
    graph_data = engine.get_graph_data()
    meta = graph_data.get("metadata", {})
    elements.append(Paragraph(
        f"Cluster: {meta.get('cluster_name', 'Unknown')} | "
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Nodes: {graph_data['stats']['total_nodes']} | "
        f"Edges: {graph_data['stats']['total_edges']}",
        styles["KPASubtitle"],
    ))
    elements.append(Spacer(1, 8 * mm))

    # ── Graph Summary Section
    elements.append(Paragraph("1. Graph Summary", styles["KPAHeading"]))
    stats = graph_data["stats"]
    summary_data = [
        ["Metric", "Value"],
        ["Total Nodes", str(stats["total_nodes"])],
        ["Total Edges", str(stats["total_edges"])],
        ["Crown Jewels", str(stats["crown_jewels"])],
        ["Critical Nodes", str(stats["critical_nodes"])],
    ]
    if meta.get("scenario"):
        summary_data.append(["Scenario", meta["scenario"]])

    t = Table(summary_data, colWidths=[70 * mm, 100 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0ea5e9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8fafc"), HexColor("#ffffff")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6 * mm))

    # ── Shortest Path / Kill Chain
    if path_result and path_result.get("path_exists"):
        elements.append(Paragraph("2. Attack Path — Kill Chain", styles["KPAHeading"]))
        elements.append(Paragraph(
            f"⚠ {path_result['difficulty']} attack path detected: "
            f"{path_result['source']} → {path_result['target']}",
            styles["KPAWarning"],
        ))
        elements.append(Spacer(1, 3 * mm))

        path_summary = [
            ["Metric", "Value"],
            ["Source", path_result["source"]],
            ["Target", path_result["target"]],
            ["Total Hops", str(path_result["hop_count"])],
            ["Path Risk Score", str(path_result["total_weight"])],
            ["Difficulty", path_result["difficulty"]],
        ]
        t2 = Table(path_summary, colWidths=[70 * mm, 100 * mm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#dc2626")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#fef2f2"), HexColor("#ffffff")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 4 * mm))

        # Kill chain steps
        chain = path_result.get("kill_chain_summary", [])
        if chain:
            elements.append(Paragraph("Detailed Kill Chain Steps:", styles["KPABody"]))
            elements.append(Spacer(1, 2 * mm))
            chain_data = [["Step", "Node", "Type", "Action", "CVEs"]]
            for step in chain:
                cves = ", ".join(step.get("cves_exploited", [])) or "—"
                chain_data.append([
                    str(step["step"]),
                    step["node"],
                    step["node_type"],
                    step["action"][:40],
                    cves,
                ])

            t3 = Table(chain_data, colWidths=[12 * mm, 35 * mm, 25 * mm, 55 * mm, 40 * mm])
            t3.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8fafc"), HexColor("#ffffff")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(t3)
        elements.append(Spacer(1, 6 * mm))

    # ── Blast Radius
    if blast_result and blast_result.get("affected_nodes"):
        elements.append(Paragraph("3. Blast Radius Analysis", styles["KPAHeading"]))
        elements.append(Paragraph(
            f"Source: {blast_result['source']} | "
            f"Max Hops: {blast_result['max_hops']} | "
            f"Affected: {blast_result['total_affected']} nodes | "
            f"Risk: {blast_result['risk_summary']}",
            styles["KPABody"],
        ))
        if blast_result.get("crown_jewels_reached"):
            elements.append(Paragraph(
                f"⚠ Crown Jewels Reached: {', '.join(blast_result.get('crown_jewel_names', []))}",
                styles["KPAWarning"],
            ))
        elements.append(Spacer(1, 6 * mm))

    # ── Cycle Detection
    if cycle_result:
        elements.append(Paragraph("4. Circular Permission Detection", styles["KPAHeading"]))
        if cycle_result["has_cycles"]:
            elements.append(Paragraph(
                f"⚠ {cycle_result['total_cycles']} circular permission loop(s) detected! "
                f"Risk: {cycle_result['risk_summary']}",
                styles["KPAWarning"],
            ))
            for cycle in cycle_result["cycles"]:
                elements.append(Paragraph(f"  • {cycle['description']}", styles["KPAMono"]))
        else:
            elements.append(Paragraph("✓ No circular permission loops detected.", styles["KPABody"]))
        elements.append(Spacer(1, 6 * mm))

    # ── Critical Node
    if critical_result and critical_result.get("critical_node"):
        cn = critical_result["critical_node"]
        elements.append(Paragraph("5. Critical Node Analysis", styles["KPAHeading"]))
        elements.append(Paragraph(
            f"Recommendation: Remove or restrict '{cn['label']}' "
            f"to break {cn['paths_broken']}/{critical_result['baseline_paths']} attack paths "
            f"({cn['impact_percentage']}% impact).",
            styles["KPAWarning"],
        ))

        top5 = critical_result.get("top_5_nodes", [])
        if top5:
            elements.append(Spacer(1, 3 * mm))
            cn_data = [["Rank", "Node", "Type", "Paths Broken", "Impact %"]]
            for i, node in enumerate(top5, 1):
                cn_data.append([
                    str(i),
                    node["label"],
                    node["type"],
                    str(node["paths_broken"]),
                    f"{node['impact_percentage']}%",
                ])
            t4 = Table(cn_data, colWidths=[15 * mm, 45 * mm, 30 * mm, 35 * mm, 25 * mm])
            t4.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#7c3aed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#faf5ff"), HexColor("#ffffff")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(t4)
        elements.append(Spacer(1, 6 * mm))

    # ── Footer
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(
        f"Generated by KubePathAudit CLI v1.0 • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Confidential",
        styles["KPASubtitle"],
    ))

    doc.build(elements)
    print(f"\n{C.GREEN}✓ PDF report saved to: {output_path}{C.RESET}")


# ── Subcommand Handlers ───────────────────────────────────────

def cmd_analyze(args):
    """Run all 4 algorithms and produce a full Kill Chain Report."""
    is_json = getattr(args, 'json', False)
    if not is_json:
        _print_banner()
    engine = _load_engine(args.input)
    if not is_json:
        _print_graph_summary(engine)

    # Run all algorithms
    if not is_json:
        print(f"{C.BOLD}Running security analysis...{C.RESET}\n")

    # 1. Find entry points
    entry_points = [
        n for n, d in engine.graph.nodes(data=True)
        if d.get("type") == "internet" or d.get("risk_level") == "entry-point"
    ]
    crown_jewels = [
        n for n, d in engine.graph.nodes(data=True)
        if d.get("risk_level") == "crown-jewel"
    ]

    # 2. Blast radius from first entry point
    blast_result = None
    if entry_points:
        source = args.blast_source or entry_points[0]
        blast_result = engine.bfs_blast_radius(source, args.hops)
        if not is_json:
            _print_blast_radius(blast_result)

    # 3. Shortest path from entry → each crown jewel
    path_result = None
    if entry_points and crown_jewels:
        source = args.path_source or entry_points[0]
        target = args.path_target or crown_jewels[0]
        path_result = engine.dijkstra_shortest_path(source, target)
        if not is_json:
            _print_shortest_path(path_result)

    # 4. Cycle detection
    cycle_result = engine.dfs_cycle_detection()
    if not is_json:
        _print_cycles(cycle_result)

    # 5. Critical node
    critical_result = engine.critical_node_analysis()
    if not is_json:
        _print_critical_node(critical_result)

    # ── Temporal diff (if --diff flag)
    if args.diff:
        prev_snapshot = get_latest_snapshot()
        if prev_snapshot:
            current_data = engine.get_graph_data()
            current_data["nodes"] = [
                {"id": n, **dict(d)} for n, d in engine.graph.nodes(data=True)
            ]
            current_data["edges"] = [
                {"source": s, "target": t, **dict(d)} for s, t, d in engine.graph.edges(data=True)
            ]
            diff = diff_graphs(prev_snapshot, current_data)
            if not is_json:
                print(format_diff_report(diff))
        else:
            if not is_json:
                print(f"\n{C.YELLOW}⚠ No previous snapshot found for diff. Saving current state as first snapshot.{C.RESET}")

    # Save snapshot
    if args.snapshot:
        graph_data = engine.get_graph_data()
        raw_data = {"nodes": engine.raw_data.get("nodes", []), "edges": engine.raw_data.get("edges", []),
                     "metadata": engine.raw_data.get("metadata", {})}
        snapshot_path = save_snapshot(raw_data, label=args.snapshot_label or "")
        if not is_json:
            print(f"{C.GREEN}✓ Snapshot saved: {snapshot_path}{C.RESET}")

    # ── PDF Export
    if args.pdf:
        _generate_pdf(engine, args.pdf, blast_result, path_result, cycle_result, critical_result)

    # ── JSON output
    if args.json:
        output = {
            "graph_summary": engine.get_graph_data()["stats"],
            "blast_radius": blast_result,
            "shortest_path": path_result,
            "cycles": cycle_result,
            "critical_node": critical_result,
        }
        # Convert sets to lists for JSON serialization
        print(json.dumps(output, indent=2, default=str))


def cmd_blast_radius(args):
    """Run BFS blast radius from a source node."""
    engine = _load_engine(args.input)
    result = engine.bfs_blast_radius(args.source, args.hops)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_graph_summary(engine)
        _print_blast_radius(result)


def cmd_shortest_path(args):
    """Run Dijkstra's shortest path between two nodes."""
    engine = _load_engine(args.input)
    result = engine.dijkstra_shortest_path(args.source, args.target)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_graph_summary(engine)
        _print_shortest_path(result)


def cmd_detect_cycles(args):
    """Run DFS cycle detection."""
    engine = _load_engine(args.input)
    result = engine.dfs_cycle_detection()

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_graph_summary(engine)
        _print_cycles(result)


def cmd_critical_node(args):
    """Run critical node analysis."""
    engine = _load_engine(args.input)
    result = engine.critical_node_analysis()

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_graph_summary(engine)
        _print_critical_node(result)


def cmd_ingest(args):
    """Ingest live cluster state via kubectl."""
    _print_banner()
    from ingest import ingest_cluster
    data = ingest_cluster(output_path=args.output, live_cve=args.live_cve)

    if args.snapshot:
        snapshot_path = save_snapshot(data, label="ingest")
        print(f"{C.GREEN}✓ Snapshot saved: {snapshot_path}{C.RESET}")

    print(f"\n{C.GREEN}✓ Ingestion complete. Run analysis with:{C.RESET}")
    print(f"  {C.CYAN}python cli.py analyze --input {args.output}{C.RESET}\n")


def cmd_snapshots(args):
    """List all stored snapshots."""
    snapshots = list_snapshots()
    if not snapshots:
        print(f"\n{C.YELLOW}No snapshots found. Run an analysis with --snapshot to create one.{C.RESET}\n")
        return

    print(f"\n{C.BOLD}📸 Stored Snapshots{C.RESET}")
    print(f"{'─' * 70}")
    for i, s in enumerate(snapshots, 1):
        label = f" [{s['label']}]" if s.get("label") else ""
        print(f"  {i}. {C.CYAN}{s['filename']}{C.RESET}{label}")
        print(f"     {C.DIM}Timestamp: {s['timestamp']} | "
              f"Nodes: {s['node_count']} | Edges: {s['edge_count']}{C.RESET}")
    print()


def cmd_diff(args):
    """Diff two snapshots or current state vs latest snapshot."""
    if args.old and args.new:
        from temporal import load_snapshot
        old_data = load_snapshot(args.old)
        new_data = load_snapshot(args.new)
        if not old_data or not new_data:
            print(f"{C.RED}✗ Could not load one or both snapshot files.{C.RESET}")
            return
    elif args.input:
        old_data = get_latest_snapshot()
        if not old_data:
            print(f"{C.RED}✗ No previous snapshot found. Cannot diff.{C.RESET}")
            return
        engine = _load_engine(args.input)
        new_data = {
            "nodes": engine.raw_data.get("nodes", []),
            "edges": engine.raw_data.get("edges", []),
            "metadata": engine.raw_data.get("metadata", {}),
        }
    else:
        print(f"{C.RED}✗ Provide --input or both --old and --new snapshot paths.{C.RESET}")
        return

    diff = diff_graphs(old_data, new_data)

    if args.json:
        print(json.dumps(diff, indent=2, default=str))
    else:
        print(format_diff_report(diff))


# ── CLI Setup ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="kubepathaudit",
        description="KubePathAudit — Graph-Based Security Analysis for Cloud-Native Infrastructure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py analyze --input mock-cluster-graph.json
  python cli.py analyze --input mock-cluster-graph.json --pdf report.pdf
  python cli.py analyze --input mock-cluster-graph.json --json
  python cli.py blast-radius --source internet --hops 4 --input mock-cluster-graph.json
  python cli.py shortest-path --source internet --target prod-database --input mock-cluster-graph.json
  python cli.py detect-cycles --input mock-cluster-graph.json
  python cli.py critical-node --input mock-cluster-graph.json
  python cli.py ingest -o cluster-graph.json
  python cli.py snapshots
  python cli.py diff --input cluster-graph.json
        """,
    )

    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── analyze ──
    p_analyze = subparsers.add_parser("analyze", help="Run full security analysis (all 4 algorithms)")
    p_analyze.add_argument("--input", "-i", default="mock-cluster-graph.json", help="Path to cluster graph JSON")
    p_analyze.add_argument("--pdf", help="Export Kill Chain Report as PDF to this file path")
    p_analyze.add_argument("--json", action="store_true", help="Output results as JSON")
    p_analyze.add_argument("--hops", type=int, default=3, help="Max hops for blast radius (default: 3)")
    p_analyze.add_argument("--blast-source", help="Override source node for blast radius")
    p_analyze.add_argument("--path-source", help="Override source node for shortest path")
    p_analyze.add_argument("--path-target", help="Override target node for shortest path")
    p_analyze.add_argument("--diff", action="store_true", help="Diff against previous snapshot")
    p_analyze.add_argument("--snapshot", action="store_true", help="Save current scan as snapshot")
    p_analyze.add_argument("--snapshot-label", help="Label for the snapshot")
    p_analyze.set_defaults(func=cmd_analyze)

    # ── blast-radius ──
    p_blast = subparsers.add_parser("blast-radius", help="BFS blast radius from a source node")
    p_blast.add_argument("--source", "-s", required=True, help="Source node ID")
    p_blast.add_argument("--hops", "-n", type=int, default=3, help="Max hops (default: 3)")
    p_blast.add_argument("--input", "-i", default="mock-cluster-graph.json", help="Path to cluster graph JSON")
    p_blast.add_argument("--json", action="store_true", help="Output as JSON")
    p_blast.set_defaults(func=cmd_blast_radius)

    # ── shortest-path ──
    p_path = subparsers.add_parser("shortest-path", help="Dijkstra's shortest attack path")
    p_path.add_argument("--source", "-s", required=True, help="Source node ID")
    p_path.add_argument("--target", "-t", required=True, help="Target node ID")
    p_path.add_argument("--input", "-i", default="mock-cluster-graph.json", help="Path to cluster graph JSON")
    p_path.add_argument("--json", action="store_true", help="Output as JSON")
    p_path.set_defaults(func=cmd_shortest_path)

    # ── detect-cycles ──
    p_cycles = subparsers.add_parser("detect-cycles", help="DFS circular permission detection")
    p_cycles.add_argument("--input", "-i", default="mock-cluster-graph.json", help="Path to cluster graph JSON")
    p_cycles.add_argument("--json", action="store_true", help="Output as JSON")
    p_cycles.set_defaults(func=cmd_detect_cycles)

    # ── critical-node ──
    p_critical = subparsers.add_parser("critical-node", help="Identify highest-impact node to remove")
    p_critical.add_argument("--input", "-i", default="mock-cluster-graph.json", help="Path to cluster graph JSON")
    p_critical.add_argument("--json", action="store_true", help="Output as JSON")
    p_critical.set_defaults(func=cmd_critical_node)

    # ── ingest ──
    p_ingest = subparsers.add_parser("ingest", help="Ingest live Kubernetes cluster state via kubectl")
    p_ingest.add_argument("--output", "-o", default="cluster-graph.json", help="Output JSON file path")
    p_ingest.add_argument("--live-cve", action="store_true", help="Enable live NVD API CVE lookups")
    p_ingest.add_argument("--snapshot", action="store_true", help="Save ingested data as snapshot")
    p_ingest.set_defaults(func=cmd_ingest)

    # ── snapshots ──
    p_snapshots = subparsers.add_parser("snapshots", help="List all stored graph snapshots")
    p_snapshots.set_defaults(func=cmd_snapshots)

    # ── diff ──
    p_diff = subparsers.add_parser("diff", help="Compare two graph snapshots or current vs latest")
    p_diff.add_argument("--input", "-i", help="Current graph JSON to diff against latest snapshot")
    p_diff.add_argument("--old", help="Path to old snapshot file")
    p_diff.add_argument("--new", help="Path to new snapshot file")
    p_diff.add_argument("--json", action="store_true", help="Output as JSON")
    p_diff.set_defaults(func=cmd_diff)

    args = parser.parse_args()

    if getattr(args, 'no_color', False):
        C.disable()

    # Detect Windows terminal and disable color if output is piped
    if sys.platform == 'win32' and not sys.stdout.isatty():
        C.disable()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
```

## backend\cve_scorer.py

```python
"""
CVE Scorer — Static CVE database + optional NIST NVD API integration.
Provides CVSS scores for known container/Kubernetes vulnerabilities.
"""

import json
import urllib.request
import urllib.error
from typing import Optional


# ── Static CVE Database ────────────────────────────────────────
# Common Kubernetes & container CVEs with CVSS v3.1 scores.
STATIC_CVE_DB: dict[str, dict] = {
    # Kubernetes Dashboard
    "CVE-2018-18264": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Kubernetes Dashboard privilege escalation via skip-login",
        "affected": "kubernetesui/dashboard < v2.0.0",
    },
    "CVE-2023-49797": {
        "cvss": 8.1,
        "severity": "HIGH",
        "summary": "Kubernetes Dashboard cross-site request forgery",
        "affected": "kubernetesui/dashboard < v2.7.1",
    },
    # NGINX Ingress
    "CVE-2024-7646": {
        "cvss": 8.8,
        "severity": "HIGH",
        "summary": "NGINX Ingress annotation injection leading to arbitrary config",
        "affected": "ingress-nginx < 1.11.2",
    },
    "CVE-2023-5043": {
        "cvss": 7.6,
        "severity": "HIGH",
        "summary": "NGINX Ingress annotation injection via permanent-redirect",
        "affected": "ingress-nginx < 1.9.5",
    },
    "CVE-2021-25742": {
        "cvss": 7.6,
        "severity": "HIGH",
        "summary": "NGINX Ingress snippet injection",
        "affected": "ingress-nginx < 1.0.5",
    },
    # HTTP/2 Rapid Reset
    "CVE-2023-44487": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "HTTP/2 Rapid Reset denial-of-service attack",
        "affected": "Multiple HTTP/2 implementations",
    },
    # Prometheus
    "CVE-2024-6837": {
        "cvss": 5.4,
        "severity": "MEDIUM",
        "summary": "Prometheus stored XSS via crafted metric labels",
        "affected": "prometheus < v2.54.0",
    },
    # etcd
    "CVE-2023-47108": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "etcd OpenTelemetry contrib DoS via unbound cardinality",
        "affected": "etcd < 3.5.11",
    },
    "CVE-2023-32082": {
        "cvss": 5.3,
        "severity": "MEDIUM",
        "summary": "etcd information leak via LeaseTimeToLive API",
        "affected": "etcd < 3.5.9",
    },
    # Container runtime / runc
    "CVE-2024-21626": {
        "cvss": 8.6,
        "severity": "HIGH",
        "summary": "runc container breakout via leaked file descriptors",
        "affected": "runc < 1.1.12",
    },
    "CVE-2019-5736": {
        "cvss": 8.6,
        "severity": "HIGH",
        "summary": "runc host binary overwrite via container exec",
        "affected": "runc < 1.0.0-rc7",
    },
    # Kubernetes core
    "CVE-2024-3177": {
        "cvss": 2.7,
        "severity": "LOW",
        "summary": "Kubernetes imagePullSecrets bypass in ephemeral containers",
        "affected": "kubernetes < 1.30.0",
    },
    "CVE-2023-5528": {
        "cvss": 8.8,
        "severity": "HIGH",
        "summary": "Kubernetes Windows node command injection via volume mount",
        "affected": "kubernetes < 1.28.4",
    },
    "CVE-2023-2728": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "Kubernetes ServiceAccount token secret bypass via ephemeral containers",
        "affected": "kubernetes < 1.27.3",
    },
    "CVE-2022-3294": {
        "cvss": 8.8,
        "severity": "HIGH",
        "summary": "Kubernetes node address validation bypass",
        "affected": "kubernetes < 1.25.4",
    },
    "CVE-2022-3162": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "Kubernetes directory traversal in volume subpath",
        "affected": "kubernetes < 1.25.4",
    },
    # Istio / Envoy
    "CVE-2024-23322": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Envoy crash via HTTP/2 CONTINUATION flood",
        "affected": "envoy < 1.29.1",
    },
    "CVE-2023-35942": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "Istio gateway CORS bypass",
        "affected": "istio < 1.18.2",
    },
    # Helm
    "CVE-2022-23524": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Helm denial of service via crafted schema",
        "affected": "helm < 3.10.3",
    },
    # ArgoCD
    "CVE-2024-28175": {
        "cvss": 9.1,
        "severity": "CRITICAL",
        "summary": "Argo CD XSS leading to credential theft",
        "affected": "argocd < 2.10.4",
    },
    "CVE-2024-21661": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Argo CD denial of service via crafted manifest",
        "affected": "argocd < 2.10.3",
    },
    # CoreDNS
    "CVE-2023-49295": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "CoreDNS HPACK decoder DoS via crafted headers",
        "affected": "coredns < 1.11.2",
    },
    # containerd
    "CVE-2023-25153": {
        "cvss": 5.5,
        "severity": "MEDIUM",
        "summary": "containerd OCI image import denial of service",
        "affected": "containerd < 1.6.18",
    },
    "CVE-2022-23648": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "containerd host path leak via image config",
        "affected": "containerd < 1.6.1",
    },
    # Kube-proxy / networking
    "CVE-2023-3676": {
        "cvss": 8.8,
        "severity": "HIGH",
        "summary": "Kubernetes Windows node privilege escalation via pod spec",
        "affected": "kubernetes < 1.28.0",
    },
    # Calico
    "CVE-2024-2912": {
        "cvss": 9.8,
        "severity": "CRITICAL",
        "summary": "Calico privilege escalation via VXLAN configuration",
        "affected": "calico < 3.27.2",
    },
    # Flux
    "CVE-2022-39272": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Flux controller denial of service via malicious object",
        "affected": "flux < 0.35.0",
    },
    # Vault (often used with K8s)
    "CVE-2023-0620": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "HashiCorp Vault SQL injection in audit device",
        "affected": "vault < 1.13.1",
    },
    # Cert-manager
    "CVE-2022-2996": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "cert-manager improper path validation in ACME challenge",
        "affected": "cert-manager < 1.10.0",
    },
}


def lookup_cve(cve_id: str) -> Optional[dict]:
    """Look up a CVE from the static database."""
    return STATIC_CVE_DB.get(cve_id)


def get_cvss_score(cve_id: str) -> float:
    """Return the CVSS score for a CVE, or 5.0 as default unknown."""
    entry = STATIC_CVE_DB.get(cve_id)
    return entry["cvss"] if entry else 5.0


def lookup_cve_live(cve_id: str) -> Optional[dict]:
    """
    Query the NIST NVD API 2.0 for a CVE.
    Returns a dict with cvss, severity, and summary — or None on failure.
    Rate-limited: 5 requests/30 seconds for unauthenticated calls.
    """
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KubePathAudit/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        vulns = data.get("vulnerabilities", [])
        if not vulns:
            return None

        cve_data = vulns[0].get("cve", {})
        metrics = cve_data.get("metrics", {})

        # Try CVSS v3.1 first, then v3.0
        cvss_score = 0.0
        severity = "UNKNOWN"
        for version_key in ("cvssMetricV31", "cvssMetricV30"):
            if version_key in metrics:
                cvss_data = metrics[version_key][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore", 0.0)
                severity = cvss_data.get("baseSeverity", "UNKNOWN")
                break

        descriptions = cve_data.get("descriptions", [])
        summary = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                summary = desc.get("value", "")
                break

        return {
            "cvss": cvss_score,
            "severity": severity,
            "summary": summary[:200],
            "source": "NVD API 2.0",
        }
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError,
            TimeoutError, OSError):
        return None


def score_cve(cve_id: str, live: bool = False) -> dict:
    """
    Get CVE info: tries static DB first, then optionally falls back to NVD API.
    Always returns a dict with at minimum {cvss, severity, summary}.
    """
    # Static lookup first (fast)
    static = lookup_cve(cve_id)
    if static:
        return {**static, "source": "static"}

    # Live lookup if requested
    if live:
        live_result = lookup_cve_live(cve_id)
        if live_result:
            return live_result

    # Unknown CVE fallback
    return {
        "cvss": 5.0,
        "severity": "MEDIUM",
        "summary": f"Unknown CVE: {cve_id}",
        "source": "default",
    }


def score_image_cves(cves: list[str], live: bool = False) -> list[dict]:
    """Score a list of CVE IDs and return detailed results."""
    return [{"cve_id": cve, **score_cve(cve, live=live)} for cve in cves]


def compute_node_risk_score(cves: list[str], live: bool = False) -> float:
    """Compute aggregate risk score for a node based on its CVEs."""
    if not cves:
        return 0.0
    scores = [score_cve(cve, live=live)["cvss"] for cve in cves]
    # Use max score + 10% of sum of remaining scores (compound risk)
    scores.sort(reverse=True)
    total = scores[0]
    for s in scores[1:]:
        total += s * 0.1
    return round(total, 2)
```

## backend\graph_engine.py

```python
"""
K8sGraphEngine — Core graph analytics engine for KubePathAudit.
Uses NetworkX to build and analyze Kubernetes cluster attack graphs.
"""

import json
import copy
import networkx as nx
from pathlib import Path
from typing import Optional


class K8sGraphEngine:
    """
    Ingests a Kubernetes cluster state JSON and builds a directed graph.
    Provides 4 core security analysis algorithms plus remediation support.
    """

    def __init__(self, json_path: Optional[str] = None):
        self.graph = nx.DiGraph()
        self.raw_data = None
        self._original_data = None
        if json_path:
            self.load_graph(json_path)

    def load_graph(self, json_path: str) -> None:
        """Load cluster state from JSON and build the directed graph."""
        with open(json_path, "r", encoding="utf-8") as f:
            self.raw_data = json.load(f)
        self._original_data = copy.deepcopy(self.raw_data)
        self._build_graph()

    def load_graph_from_dict(self, data: dict) -> None:
        """Load cluster state from a Python dict (for custom uploads)."""
        self.raw_data = data
        self._original_data = copy.deepcopy(data)
        self._build_graph()

    def _build_graph(self) -> None:
        """Construct the NetworkX DiGraph from raw JSON data."""
        self.graph.clear()

        for node in self.raw_data.get("nodes", []):
            self.graph.add_node(
                node["id"],
                label=node.get("label", node["id"]),
                type=node.get("type", "unknown"),
                namespace=node.get("namespace", "default"),
                risk_level=node.get("risk_level", "low"),
                metadata=node.get("metadata", {}),
            )

        for edge in self.raw_data.get("edges", []):
            self.graph.add_edge(
                edge["source"],
                edge["target"],
                relationship=edge.get("relationship", "connects_to"),
                weight=edge.get("weight", 1.0),
                metadata=edge.get("metadata", {}),
            )

    def get_graph_data(self) -> dict:
        """Return full graph as nodes + links for frontend consumption."""
        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            nodes.append({"id": node_id, **attrs})

        links = []
        for src, tgt, attrs in self.graph.edges(data=True):
            links.append({"source": src, "target": tgt, **attrs})

        return {
            "nodes": nodes,
            "links": links,
            "metadata": self.raw_data.get("metadata", {}),
            "stats": {
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges(),
                "crown_jewels": len([n for n, d in self.graph.nodes(data=True) if d.get("risk_level") == "crown-jewel"]),
                "critical_nodes": len([n for n, d in self.graph.nodes(data=True) if d.get("risk_level") == "critical"]),
            },
        }

    # ──────────────────────────────────────────────
    # Algorithm 1: BFS — Blast Radius
    # ──────────────────────────────────────────────
    def bfs_blast_radius(self, source: str, max_hops: int = 3) -> dict:
        """
        BFS from a source node to find all reachable nodes within N hops.
        Returns the 'Danger Zone' — everything an attacker could reach.
        """
        if source not in self.graph:
            return {"error": f"Node '{source}' not found in graph", "affected_nodes": [], "affected_edges": []}

        visited = {}  # node_id -> hop distance
        queue = [(source, 0)]
        visited[source] = 0

        while queue:
            current, depth = queue.pop(0)
            if depth >= max_hops:
                continue
            for neighbor in self.graph.successors(current):
                if neighbor not in visited:
                    visited[neighbor] = depth + 1
                    queue.append((neighbor, depth + 1))

        affected_nodes = [
            {
                "id": node_id,
                "hop_distance": hop,
                **dict(self.graph.nodes[node_id]),
            }
            for node_id, hop in visited.items()
        ]

        affected_edges = []
        node_ids = set(visited.keys())
        for src, tgt, attrs in self.graph.edges(data=True):
            if src in node_ids and tgt in node_ids:
                affected_edges.append({"source": src, "target": tgt, **attrs})

        crown_jewels_reached = [
            n for n in affected_nodes
            if n.get("risk_level") == "crown-jewel"
        ]

        return {
            "source": source,
            "max_hops": max_hops,
            "affected_nodes": affected_nodes,
            "affected_edges": affected_edges,
            "total_affected": len(affected_nodes),
            "crown_jewels_reached": len(crown_jewels_reached),
            "crown_jewel_names": [n["id"] for n in crown_jewels_reached],
            "risk_summary": "CRITICAL" if crown_jewels_reached else "HIGH" if len(affected_nodes) > 5 else "MEDIUM",
        }

    # ──────────────────────────────────────────────
    # Algorithm 2: Dijkstra — Shortest Attack Path
    # ──────────────────────────────────────────────
    def dijkstra_shortest_path(self, source: str, target: str) -> dict:
        """
        Find the easiest (lowest-CVSS-weight) attack path from source to target.
        Uses Dijkstra's algorithm with CVSS-based edge weights.
        """
        if source not in self.graph:
            return {"error": f"Source node '{source}' not found"}
        if target not in self.graph:
            return {"error": f"Target node '{target}' not found"}

        try:
            path = nx.dijkstra_path(self.graph, source, target, weight="weight")
            total_weight = nx.dijkstra_path_length(self.graph, source, target, weight="weight")
        except nx.NetworkXNoPath:
            return {
                "error": f"No path exists from '{source}' to '{target}'",
                "path": [],
                "total_weight": float("inf"),
                "path_exists": False,
            }

        path_details = []
        for i, node_id in enumerate(path):
            node_data = dict(self.graph.nodes[node_id])
            step = {
                "step": i + 1,
                "node_id": node_id,
                **node_data,
            }
            if i < len(path) - 1:
                edge_data = self.graph.edges[path[i], path[i + 1]]
                step["edge_to_next"] = {
                    "target": path[i + 1],
                    "relationship": edge_data.get("relationship", ""),
                    "weight": edge_data.get("weight", 1.0),
                    "metadata": edge_data.get("metadata", {}),
                }
            path_details.append(step)

        difficulty = "TRIVIAL" if total_weight < 3 else "EASY" if total_weight < 6 else "MODERATE" if total_weight < 10 else "HARD"

        return {
            "source": source,
            "target": target,
            "path": [n for n in path],
            "path_details": path_details,
            "total_weight": round(total_weight, 2),
            "hop_count": len(path) - 1,
            "difficulty": difficulty,
            "path_exists": True,
            "kill_chain_summary": self._generate_kill_chain(path_details),
        }

    def _generate_kill_chain(self, path_details: list) -> list:
        """Generate a human-readable kill chain from path details."""
        chain = []
        for step in path_details:
            cves = step.get("metadata", {}).get("cves", [])
            entry = {
                "step": step["step"],
                "action": self._get_attack_action(step),
                "node": step.get("label", step["node_id"]),
                "node_type": step.get("type", "unknown"),
                "risk_level": step.get("risk_level", "unknown"),
                "cves_exploited": cves,
                "edge_info": step.get("edge_to_next", {}).get("relationship", "—"),
            }
            chain.append(entry)
        return chain

    @staticmethod
    def _get_attack_action(step: dict) -> str:
        """Map node type to a realistic attack action description."""
        actions = {
            "internet": "Initiate external reconnaissance",
            "ingress": "Exploit ingress controller vulnerability",
            "pod": "Compromise pod via exposed service",
            "serviceaccount": "Steal mounted ServiceAccount token",
            "rolebinding": "Leverage role binding escalation",
            "role": "Abuse role permissions",
            "clusterrole": "Exploit cluster-wide role privileges",
            "secret": "Exfiltrate stored credentials",
            "database": "Access and exfiltrate production data",
            "service": "Probe exposed service endpoint",
            "configmap": "Read configuration data",
        }
        return actions.get(step.get("type", ""), "Exploit node")

    # ──────────────────────────────────────────────
    # Algorithm 3: DFS — Cycle Detection
    # ──────────────────────────────────────────────
    def dfs_cycle_detection(self) -> dict:
        """
        DFS-based cycle detection to find circular permission loops.
        e.g., Service-A -> Service-B -> Service-A
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
        except Exception:
            cycles = []

        cycle_details = []
        for cycle in cycles:
            cycle_nodes = []
            total_weight = 0
            for i, node_id in enumerate(cycle):
                node_data = dict(self.graph.nodes[node_id])
                cycle_nodes.append({"id": node_id, **node_data})
                next_node = cycle[(i + 1) % len(cycle)]
                if self.graph.has_edge(node_id, next_node):
                    total_weight += self.graph.edges[node_id, next_node].get("weight", 1.0)

            risk = "CRITICAL" if any(n.get("risk_level") in ("critical", "crown-jewel") for n in cycle_nodes) else "HIGH" if len(cycle) > 2 else "MEDIUM"

            cycle_details.append({
                "cycle": [n["id"] for n in cycle_nodes],
                "cycle_nodes": cycle_nodes,
                "length": len(cycle),
                "total_weight": round(total_weight, 2),
                "risk": risk,
                "description": f"Circular path: {' → '.join(n.get('label', n['id']) for n in cycle_nodes)} → {cycle_nodes[0].get('label', cycle_nodes[0]['id'])}",
            })

        return {
            "total_cycles": len(cycles),
            "cycles": cycle_details,
            "has_cycles": len(cycles) > 0,
            "risk_summary": "CRITICAL" if any(c["risk"] == "CRITICAL" for c in cycle_details) else "HIGH" if cycle_details else "NONE",
        }

    # ──────────────────────────────────────────────
    # Algorithm 4: Critical Node Analysis
    # ──────────────────────────────────────────────
    def critical_node_analysis(self) -> dict:
        """
        Identify the single node whose removal breaks the most attack paths
        from entry points (internet) to crown jewels (secrets/databases).
        """
        entry_points = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("type") == "internet" or d.get("risk_level") == "entry-point"
        ]
        crown_jewels = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("risk_level") == "crown-jewel"
        ]

        if not entry_points or not crown_jewels:
            return {
                "error": "No entry points or crown jewels found in graph",
                "critical_node": None,
            }

        # Count baseline paths
        baseline_paths = 0
        path_pairs = []
        for entry in entry_points:
            for jewel in crown_jewels:
                paths = list(nx.all_simple_paths(self.graph, entry, jewel, cutoff=15))
                baseline_paths += len(paths)
                if paths:
                    path_pairs.append((entry, jewel, len(paths)))

        # For each candidate node, calculate impact of removal
        candidates = [
            n for n in self.graph.nodes()
            if n not in entry_points and n not in crown_jewels
        ]

        node_impacts = []
        for candidate in candidates:
            temp_graph = self.graph.copy()
            temp_graph.remove_node(candidate)

            remaining_paths = 0
            for entry in entry_points:
                for jewel in crown_jewels:
                    if entry in temp_graph and jewel in temp_graph:
                        paths = list(nx.all_simple_paths(temp_graph, entry, jewel, cutoff=15))
                        remaining_paths += len(paths)

            broken_paths = baseline_paths - remaining_paths
            impact_pct = (broken_paths / baseline_paths * 100) if baseline_paths > 0 else 0

            node_data = dict(self.graph.nodes[candidate])
            node_impacts.append({
                "node_id": candidate,
                "label": node_data.get("label", candidate),
                "type": node_data.get("type", "unknown"),
                "namespace": node_data.get("namespace", "unknown"),
                "risk_level": node_data.get("risk_level", "unknown"),
                "paths_broken": broken_paths,
                "paths_remaining": remaining_paths,
                "impact_percentage": round(impact_pct, 1),
                "metadata": node_data.get("metadata", {}),
            })

        node_impacts.sort(key=lambda x: x["paths_broken"], reverse=True)

        critical_node = node_impacts[0] if node_impacts else None

        betweenness = nx.betweenness_centrality(self.graph, weight="weight")

        return {
            "critical_node": critical_node,
            "top_5_nodes": node_impacts[:5],
            "baseline_paths": baseline_paths,
            "entry_points": entry_points,
            "crown_jewels": crown_jewels,
            "betweenness_centrality": {
                k: round(v, 4) for k, v in sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
            },
            "recommendation": f"Remove or restrict '{critical_node['label']}' to break {critical_node['paths_broken']}/{baseline_paths} attack paths ({critical_node['impact_percentage']}%)" if critical_node else "No critical node identified",
        }

    # ──────────────────────────────────────────────
    # Remediation
    # ──────────────────────────────────────────────
    def remove_node(self, node_id: str) -> dict:
        """Remove a node from the graph and return updated graph data."""
        if node_id not in self.graph:
            return {"error": f"Node '{node_id}' not found in graph"}

        removed_node = dict(self.graph.nodes[node_id])
        removed_edges = list(self.graph.in_edges(node_id)) + list(self.graph.out_edges(node_id))

        self.graph.remove_node(node_id)

        # Also update raw data to keep in sync
        if self.raw_data:
            self.raw_data["nodes"] = [n for n in self.raw_data["nodes"] if n["id"] != node_id]
            self.raw_data["edges"] = [
                e for e in self.raw_data["edges"]
                if e["source"] != node_id and e["target"] != node_id
            ]

        return {
            "removed_node": {"id": node_id, **removed_node},
            "removed_edge_count": len(removed_edges),
            "updated_graph": self.get_graph_data(),
            "message": f"Successfully removed '{removed_node.get('label', node_id)}' and {len(removed_edges)} associated edges",
        }

    def reset_graph(self) -> dict:
        """Reset graph back to original state."""
        if self._original_data:
            self.raw_data = copy.deepcopy(self._original_data)
            self._build_graph()
            return {"message": "Graph reset to original state", "graph": self.get_graph_data()}
        return {"error": "No original data to reset to"}
```

## backend\ingest.py

```python
"""
K8s Data Ingestion — Queries a live Kubernetes cluster via kubectl
and produces a cluster-graph.json file conforming to the KubePathAudit schema.

Falls back to mock data if kubectl is not available or no cluster is connected.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cve_scorer import compute_node_risk_score, score_cve


# ── kubectl helpers ───────────────────────────────────────────

def _run_kubectl(args: list[str], timeout: int = 30) -> Optional[dict]:
    """Run a kubectl command and return parsed JSON, or None on failure."""
    cmd = ["kubectl"] + args + ["-o", "json"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None


def _check_kubectl() -> bool:
    """Check if kubectl is available and connected to a cluster."""
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ── Resource fetchers ─────────────────────────────────────────

def _fetch_resource(resource_type: str, namespace: str = "") -> list[dict]:
    """Fetch a list of Kubernetes resources."""
    args = ["get", resource_type]
    if namespace:
        args += ["-n", namespace]
    else:
        args += ["--all-namespaces"]

    data = _run_kubectl(args)
    if data and "items" in data:
        return data["items"]
    return []


# ── Node builders ─────────────────────────────────────────────

def _pod_to_node(pod: dict) -> dict:
    """Convert a K8s Pod resource to a graph node."""
    metadata = pod.get("metadata", {})
    spec = pod.get("spec", {})
    name = metadata.get("name", "unknown-pod")
    namespace = metadata.get("namespace", "default")
    labels = metadata.get("labels", {})

    containers = spec.get("containers", [])
    images = [c.get("image", "") for c in containers]
    ports = []
    for c in containers:
        for p in c.get("ports", []):
            ports.append(p.get("containerPort", 0))

    # Determine risk level based on properties
    risk_level = "low"
    sa_name = spec.get("serviceAccountName", "default")
    if labels.get("exposed") == "true" or any("dashboard" in img.lower() for img in images):
        risk_level = "critical"
    elif namespace in ("kube-system",):
        risk_level = "critical"
    elif any(p in (80, 443, 8443, 8080) for p in ports):
        risk_level = "medium"

    return {
        "id": name,
        "label": labels.get("app", name),
        "type": "pod",
        "namespace": namespace,
        "risk_level": risk_level,
        "metadata": {
            "description": f"Pod running {', '.join(images[:2]) or 'unknown image'}",
            "image": images[0] if images else "",
            "cves": [],  # Will be populated by CVE scorer
            "cvss_scores": [],
            "ports": ports,
            "labels": labels,
            "service_account": sa_name,
            "icon": "server",
        },
    }


def _sa_to_node(sa: dict) -> dict:
    """Convert a K8s ServiceAccount to a graph node."""
    metadata = sa.get("metadata", {})
    name = metadata.get("name", "unknown-sa")
    namespace = metadata.get("namespace", "default")
    automount = sa.get("automountServiceAccountToken", True)

    risk_level = "medium" if automount else "low"
    if name in ("cluster-admin", "admin"):
        risk_level = "critical"

    return {
        "id": name,
        "label": name,
        "type": "serviceaccount",
        "namespace": namespace,
        "risk_level": risk_level,
        "metadata": {
            "description": f"ServiceAccount in {namespace}",
            "automount_token": automount,
            "icon": "user-check" if risk_level == "critical" else "user",
        },
    }


def _role_to_node(role: dict, is_cluster: bool = False) -> dict:
    """Convert a K8s Role/ClusterRole to a graph node."""
    metadata = role.get("metadata", {})
    name = metadata.get("name", "unknown-role")
    namespace = metadata.get("namespace", "cluster-wide") if not is_cluster else "cluster-wide"
    rules = role.get("rules", [])

    # Determine risk level from rules
    risk_level = "low"
    rule_summaries = []
    for rule in rules:
        resources = rule.get("resources", [])
        verbs = rule.get("verbs", [])
        summary = f"{','.join(resources)}:{','.join(verbs)}"
        rule_summaries.append(summary)

        if "*" in resources or "*" in verbs:
            risk_level = "critical"
        elif "secrets" in resources and any(v in verbs for v in ("get", "list", "*")):
            risk_level = "high"
        elif any(r in resources for r in ("pods/exec", "pods/attach")):
            risk_level = "high"
        elif risk_level == "low":
            risk_level = "medium"

    return {
        "id": name,
        "label": name,
        "type": "clusterrole" if is_cluster else "role",
        "namespace": namespace,
        "risk_level": risk_level,
        "metadata": {
            "description": f"{'ClusterRole' if is_cluster else 'Role'} with {len(rules)} rule(s)",
            "rules": rule_summaries,
            "icon": "shield-alert" if risk_level == "critical" else "shield",
        },
    }


def _binding_to_node_and_edges(binding: dict, is_cluster: bool = False) -> tuple[dict, list[dict]]:
    """Convert a RoleBinding/ClusterRoleBinding to a node + edges."""
    metadata = binding.get("metadata", {})
    name = metadata.get("name", "unknown-binding")
    namespace = metadata.get("namespace", "cluster-wide") if not is_cluster else "cluster-wide"
    role_ref = binding.get("roleRef", {})
    subjects = binding.get("subjects", [])

    node = {
        "id": name,
        "label": name,
        "type": "rolebinding",
        "namespace": namespace,
        "risk_level": "critical" if role_ref.get("name") == "cluster-admin" else "medium",
        "metadata": {
            "description": f"{'ClusterRoleBinding' if is_cluster else 'RoleBinding'}",
            "binding_type": "ClusterRoleBinding" if is_cluster else "RoleBinding",
            "icon": "link",
        },
    }

    edges = []
    # Edges from subjects → binding
    for subject in subjects:
        subject_name = subject.get("name", "")
        if subject_name:
            edges.append({
                "source": subject_name,
                "target": name,
                "relationship": "bound_by",
                "weight": 0.5 if role_ref.get("name") == "cluster-admin" else 1.0,
                "metadata": {"description": f"{subject.get('kind', 'Subject')} bound via {'ClusterRoleBinding' if is_cluster else 'RoleBinding'}"},
            })

    # Edge from binding → role
    role_name = role_ref.get("name", "")
    if role_name:
        edges.append({
            "source": name,
            "target": role_name,
            "relationship": "grants",
            "weight": 0.5 if role_name == "cluster-admin" else 1.0,
            "metadata": {"description": f"Binding grants {role_ref.get('kind', 'Role')}"},
        })

    return node, edges


def _secret_to_node(secret: dict) -> dict:
    """Convert a K8s Secret to a graph node."""
    metadata = secret.get("metadata", {})
    name = metadata.get("name", "unknown-secret")
    namespace = metadata.get("namespace", "default")
    secret_type = secret.get("type", "Opaque")
    keys = list(secret.get("data", {}).keys()) if "data" in secret else []

    # Skip service-account-token secrets (auto-generated)
    if secret_type == "kubernetes.io/service-account-token":
        return None

    # Determine risk by content heuristics
    risk_level = "medium"
    sensitive_keys = {"password", "secret", "key", "token", "credential", "aws", "db_password"}
    if any(k.lower() in sensitive_keys or any(s in k.lower() for s in sensitive_keys) for k in keys):
        risk_level = "crown-jewel"

    return {
        "id": name,
        "label": name,
        "type": "secret",
        "namespace": namespace,
        "risk_level": risk_level,
        "metadata": {
            "description": f"Secret ({secret_type}) with {len(keys)} key(s)",
            "secret_type": secret_type,
            "keys": keys,
            "icon": "key",
        },
    }


def _configmap_to_node(cm: dict) -> dict:
    """Convert a K8s ConfigMap to a graph node."""
    metadata = cm.get("metadata", {})
    name = metadata.get("name", "unknown-cm")
    namespace = metadata.get("namespace", "default")
    keys = list(cm.get("data", {}).keys()) if "data" in cm else []

    # Skip kube-system configmaps like kube-root-ca.crt
    if namespace == "kube-system" and name.startswith("kube-"):
        return None

    return {
        "id": name,
        "label": name,
        "type": "configmap",
        "namespace": namespace,
        "risk_level": "low",
        "metadata": {
            "description": f"ConfigMap with {len(keys)} key(s)",
            "keys": keys,
            "icon": "file-text",
        },
    }


# ── Edge builders ─────────────────────────────────────────────

def _build_pod_sa_edges(pods: list[dict]) -> list[dict]:
    """Build edges from pods to their service accounts."""
    edges = []
    for pod in pods:
        spec = pod.get("spec", {})
        pod_name = pod.get("metadata", {}).get("name", "")
        sa_name = spec.get("serviceAccountName", "default")
        if pod_name and sa_name and sa_name != "default":
            edges.append({
                "source": pod_name,
                "target": sa_name,
                "relationship": "uses_service_account",
                "weight": 0.5,
                "metadata": {"description": f"Pod mounts ServiceAccount '{sa_name}' token"},
            })
    return edges


def _build_role_secret_edges(roles: list[dict], secrets: list[dict]) -> list[dict]:
    """Build edges from roles that can read secrets to those secret nodes."""
    edges = []
    secret_names = {s.get("metadata", {}).get("name") for s in secrets if s.get("metadata", {}).get("name")}

    for role in roles:
        role_name = role.get("metadata", {}).get("name", "")
        rules = role.get("rules", [])
        for rule in rules:
            resources = rule.get("resources", [])
            verbs = rule.get("verbs", [])
            if ("secrets" in resources or "*" in resources) and any(v in verbs for v in ("get", "list", "*")):
                # This role can access secrets
                resource_names = rule.get("resourceNames", [])
                if resource_names:
                    # Specific secrets
                    for sname in resource_names:
                        if sname in secret_names:
                            edges.append({
                                "source": role_name,
                                "target": sname,
                                "relationship": "can_access",
                                "weight": 1.0,
                                "metadata": {"description": f"Role can read secret '{sname}'"},
                            })
                else:
                    # All secrets in namespace
                    for sname in secret_names:
                        edges.append({
                            "source": role_name,
                            "target": sname,
                            "relationship": "can_access",
                            "weight": 1.0,
                            "metadata": {"description": f"Role can read all secrets in namespace"},
                        })
    return edges


# ── Main ingestion function ───────────────────────────────────

def ingest_cluster(output_path: str = "cluster-graph.json", live_cve: bool = False) -> dict:
    """
    Ingest the live state of a Kubernetes cluster and export to JSON.
    
    Returns:
        dict: The cluster graph data structure.
    """
    if not _check_kubectl():
        print("⚠  kubectl is not available or no cluster is connected.")
        print("   Falling back to mock-cluster-graph.json")
        mock_path = Path(__file__).parent / "mock-cluster-graph.json"
        if mock_path.exists():
            with open(mock_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        else:
            print("✗  No mock data found either. Cannot proceed.")
            sys.exit(1)

    print("🔍 Querying Kubernetes cluster via kubectl...")

    # Fetch all resources
    print("  → Fetching Pods...")
    pods = _fetch_resource("pods")
    print(f"    Found {len(pods)} pods")

    print("  → Fetching ServiceAccounts...")
    service_accounts = _fetch_resource("serviceaccounts")
    print(f"    Found {len(service_accounts)} service accounts")

    print("  → Fetching Roles...")
    roles = _fetch_resource("roles")
    print(f"    Found {len(roles)} roles")

    print("  → Fetching ClusterRoles...")
    cluster_roles = _fetch_resource("clusterroles")
    print(f"    Found {len(cluster_roles)} cluster roles")

    print("  → Fetching RoleBindings...")
    role_bindings = _fetch_resource("rolebindings")
    print(f"    Found {len(role_bindings)} role bindings")

    print("  → Fetching ClusterRoleBindings...")
    cluster_role_bindings = _fetch_resource("clusterrolebindings")
    print(f"    Found {len(cluster_role_bindings)} cluster role bindings")

    print("  → Fetching Secrets...")
    secrets = _fetch_resource("secrets")
    print(f"    Found {len(secrets)} secrets")

    print("  → Fetching ConfigMaps...")
    configmaps = _fetch_resource("configmaps")
    print(f"    Found {len(configmaps)} configmaps")

    # Build nodes
    print("\n🔨 Building graph nodes...")
    nodes = []
    all_node_ids = set()

    # Add internet entry point
    nodes.append({
        "id": "internet",
        "label": "Internet",
        "type": "internet",
        "namespace": "external",
        "risk_level": "entry-point",
        "metadata": {"description": "External internet traffic entry point", "icon": "globe"},
    })
    all_node_ids.add("internet")

    for pod in pods:
        node = _pod_to_node(pod)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for sa in service_accounts:
        node = _sa_to_node(sa)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for role in roles:
        node = _role_to_node(role, is_cluster=False)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for cr in cluster_roles:
        node = _role_to_node(cr, is_cluster=True)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for secret in secrets:
        node = _secret_to_node(secret)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for cm in configmaps:
        node = _configmap_to_node(cm)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    # Build edges
    print("🔗 Building graph edges...")
    edges = []

    # Pod → ServiceAccount edges
    edges.extend(_build_pod_sa_edges(pods))

    # RoleBinding / ClusterRoleBinding → node + edge extraction
    for rb in role_bindings:
        node, binding_edges = _binding_to_node_and_edges(rb, is_cluster=False)
        if node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])
        edges.extend(binding_edges)

    for crb in cluster_role_bindings:
        node, binding_edges = _binding_to_node_and_edges(crb, is_cluster=True)
        if node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])
        edges.extend(binding_edges)

    # Role → Secret edges
    all_roles = roles + cluster_roles
    edges.extend(_build_role_secret_edges(all_roles, secrets))

    # Filter edges to only reference existing nodes
    edges = [e for e in edges if e["source"] in all_node_ids and e["target"] in all_node_ids]

    # Annotate CVEs using the scorer
    print("🛡️  Scoring CVEs...")
    for node in nodes:
        cves = node.get("metadata", {}).get("cves", [])
        if cves:
            node["metadata"]["cvss_scores"] = [
                score_cve(cve, live=live_cve)["cvss"] for cve in cves
            ]
            risk = compute_node_risk_score(cves, live=live_cve)
            if risk > 8.0 and node["risk_level"] not in ("crown-jewel", "entry-point"):
                node["risk_level"] = "critical"

    # Build the final graph document
    graph_data = {
        "metadata": {
            "cluster_name": _get_cluster_name(),
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario": "Live Cluster Scan",
            "description": f"Auto-ingested from live cluster. {len(nodes)} entities, {len(edges)} relationships.",
        },
        "nodes": nodes,
        "edges": edges,
    }

    # Write to file
    output = Path(output_path)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)

    print(f"\n✅ Cluster graph exported to: {output.resolve()}")
    print(f"   Nodes: {len(nodes)} | Edges: {len(edges)}")

    return graph_data


def _get_cluster_name() -> str:
    """Get the current Kubernetes cluster name from kubectl config."""
    try:
        result = subprocess.run(
            ["kubectl", "config", "current-context"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "unknown-cluster"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest Kubernetes cluster state into a graph JSON file.")
    parser.add_argument("-o", "--output", default="cluster-graph.json", help="Output JSON file path")
    parser.add_argument("--live-cve", action="store_true", help="Enable live NVD API CVE lookups")
    args = parser.parse_args()

    ingest_cluster(output_path=args.output, live_cve=args.live_cve)
```

## backend\kill-chain-report.pdf

*(Could not read file: 'utf-8' codec can't decode byte 0x93 in position 10: invalid start byte)*

## backend\main.py

```python
"""
KubePathAudit — FastAPI Backend
REST API for Kubernetes cluster security analysis.
"""

import json
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph_engine import K8sGraphEngine

# ── App Setup ──────────────────────────────────────
app = FastAPI(
    title="KubePathAudit API",
    description="Kubernetes Security Analysis Engine — Attack Path Visualization & Analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Initialize Engine ──────────────────────────────
DATA_DIR = Path(__file__).parent
DEFAULT_JSON = DATA_DIR / "mock-cluster-graph.json"

engine = K8sGraphEngine(str(DEFAULT_JSON))


# ── Request Models ─────────────────────────────────
class BlastRadiusRequest(BaseModel):
    source: str
    max_hops: int = 3


class ShortestPathRequest(BaseModel):
    source: str
    target: str


class RemediateRequest(BaseModel):
    node_id: str


# ── Endpoints ──────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "KubePathAudit API",
        "version": "1.0.0",
        "graph_loaded": engine.graph.number_of_nodes() > 0,
        "nodes": engine.graph.number_of_nodes(),
        "edges": engine.graph.number_of_edges(),
    }


@app.get("/api/graph")
def get_graph():
    """Return the full graph data for frontend rendering."""
    return engine.get_graph_data()


@app.post("/api/blast-radius")
def blast_radius(req: BlastRadiusRequest):
    """BFS-based blast radius analysis from a source node."""
    result = engine.bfs_blast_radius(req.source, req.max_hops)
    if "error" in result and not result.get("affected_nodes"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/api/shortest-path")
def shortest_path(req: ShortestPathRequest):
    """Dijkstra's shortest (easiest) attack path between two nodes."""
    result = engine.dijkstra_shortest_path(req.source, req.target)
    if "error" in result and not result.get("path_exists", True):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/cycles")
def detect_cycles():
    """DFS-based cycle detection for circular permission loops."""
    return engine.dfs_cycle_detection()


@app.get("/api/critical-node")
def critical_node():
    """Identify the most critical node whose removal breaks the most attack paths."""
    return engine.critical_node_analysis()


@app.post("/api/remediate")
def remediate(req: RemediateRequest):
    """Remove a node from the graph (simulating remediation)."""
    result = engine.remove_node(req.node_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/api/reset")
def reset_graph():
    """Reset the graph to its original state."""
    return engine.reset_graph()


@app.post("/api/upload")
async def upload_custom_graph(file: UploadFile = File(...)):
    """Upload a custom cluster graph JSON file for analysis."""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    # Validate structure
    if "nodes" not in data or "edges" not in data:
        raise HTTPException(
            status_code=400,
            detail="JSON must contain 'nodes' and 'edges' arrays. See the sample format for reference.",
        )

    for node in data["nodes"]:
        if "id" not in node:
            raise HTTPException(status_code=400, detail="Each node must have an 'id' field")

    for edge in data["edges"]:
        if "source" not in edge or "target" not in edge:
            raise HTTPException(status_code=400, detail="Each edge must have 'source' and 'target' fields")

    engine.load_graph_from_dict(data)

    return {
        "message": f"Custom graph loaded successfully: {data.get('metadata', {}).get('cluster_name', 'Custom Cluster')}",
        "graph": engine.get_graph_data(),
    }


@app.post("/api/export-pdf")
async def export_pdf():
    """Generate a professional Kill Chain PDF report using reportlab and return it as a download."""
    import io
    from datetime import datetime
    from fastapi.responses import StreamingResponse

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import HexColor
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab not installed on server")

    # Run all 4 algorithms
    graph_data = engine.get_graph_data()
    meta = graph_data.get("metadata", {})
    stats = graph_data["stats"]

    # Find entry points and crown jewels
    entry_points = [n for n, d in engine.graph.nodes(data=True) if d.get("risk_level") == "entry-point"]
    crown_jewels = [n for n, d in engine.graph.nodes(data=True) if d.get("risk_level") == "crown-jewel"]

    blast_result = None
    if entry_points:
        blast_result = engine.bfs_blast_radius(entry_points[0], 3)

    path_result = None
    if entry_points and crown_jewels:
        path_result = engine.dijkstra_shortest_path(entry_points[0], crown_jewels[0])

    cycle_result = engine.dfs_cycle_detection()
    critical_result = engine.critical_node_analysis()

    # Build PDF in memory
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "KPATitle", parent=styles["Title"],
        fontSize=24, textColor=HexColor("#0ea5e9"), spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "KPASubtitle", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#64748b"), spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "KPAHeading", parent=styles["Heading2"],
        fontSize=14, textColor=HexColor("#1e293b"), spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "KPABody", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#334155"), leading=14,
    ))
    styles.add(ParagraphStyle(
        "KPAWarning", parent=styles["Normal"],
        fontSize=11, textColor=HexColor("#dc2626"), leading=14, fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "KPAMono", parent=styles["Normal"],
        fontSize=9, textColor=HexColor("#475569"), fontName="Courier", leading=12,
    ))

    elements = []

    # Title
    elements.append(Paragraph("KubePathAudit — Kill Chain Report", styles["KPATitle"]))
    elements.append(Paragraph(
        f"Cluster: {meta.get('cluster_name', 'Unknown')} | "
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Nodes: {stats['total_nodes']} | Edges: {stats['total_edges']}",
        styles["KPASubtitle"],
    ))
    elements.append(Spacer(1, 8 * mm))

    # 1. Graph Summary
    elements.append(Paragraph("1. Graph Summary", styles["KPAHeading"]))
    summary_data = [
        ["Metric", "Value"],
        ["Total Nodes", str(stats["total_nodes"])],
        ["Total Edges", str(stats["total_edges"])],
        ["Crown Jewels", str(stats["crown_jewels"])],
        ["Critical Nodes", str(stats["critical_nodes"])],
    ]
    if meta.get("scenario"):
        summary_data.append(["Scenario", meta["scenario"]])

    t = Table(summary_data, colWidths=[70 * mm, 100 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0ea5e9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8fafc"), HexColor("#ffffff")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6 * mm))

    # 2. Attack Path / Kill Chain
    if path_result and path_result.get("path_exists"):
        elements.append(Paragraph("2. Attack Path — Kill Chain", styles["KPAHeading"]))
        elements.append(Paragraph(
            f"WARNING: {path_result['difficulty']} attack path detected: "
            f"{path_result['source']} -> {path_result['target']}",
            styles["KPAWarning"],
        ))
        elements.append(Spacer(1, 3 * mm))

        path_summary = [
            ["Metric", "Value"],
            ["Source", path_result["source"]],
            ["Target", path_result["target"]],
            ["Total Hops", str(path_result["hop_count"])],
            ["Path Risk Score", str(path_result["total_weight"])],
            ["Difficulty", path_result["difficulty"]],
        ]
        t2 = Table(path_summary, colWidths=[70 * mm, 100 * mm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#dc2626")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#fef2f2"), HexColor("#ffffff")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t2)
        elements.append(Spacer(1, 4 * mm))

        chain = path_result.get("kill_chain_summary", [])
        if chain:
            elements.append(Paragraph("Detailed Kill Chain Steps:", styles["KPABody"]))
            elements.append(Spacer(1, 2 * mm))
            chain_data = [["Step", "Node", "Type", "Action", "CVEs"]]
            for step in chain:
                cves = ", ".join(step.get("cves_exploited", [])) or "—"
                chain_data.append([
                    str(step["step"]), step["node"], step["node_type"],
                    step["action"][:40], cves,
                ])
            t3 = Table(chain_data, colWidths=[12 * mm, 35 * mm, 25 * mm, 55 * mm, 40 * mm])
            t3.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f8fafc"), HexColor("#ffffff")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(t3)
        elements.append(Spacer(1, 6 * mm))

    # 3. Blast Radius
    if blast_result and blast_result.get("affected_nodes"):
        elements.append(Paragraph("3. Blast Radius Analysis", styles["KPAHeading"]))
        elements.append(Paragraph(
            f"Source: {blast_result['source']} | "
            f"Max Hops: {blast_result['max_hops']} | "
            f"Affected: {blast_result['total_affected']} nodes | "
            f"Risk: {blast_result['risk_summary']}",
            styles["KPABody"],
        ))
        if blast_result.get("crown_jewels_reached"):
            elements.append(Paragraph(
                f"WARNING: Crown Jewels Reached: {', '.join(blast_result.get('crown_jewel_names', []))}",
                styles["KPAWarning"],
            ))
        elements.append(Spacer(1, 6 * mm))

    # 4. Cycle Detection
    if cycle_result:
        elements.append(Paragraph("4. Circular Permission Detection", styles["KPAHeading"]))
        if cycle_result["has_cycles"]:
            elements.append(Paragraph(
                f"WARNING: {cycle_result['total_cycles']} circular permission loop(s) detected! "
                f"Risk: {cycle_result['risk_summary']}",
                styles["KPAWarning"],
            ))
            for cycle in cycle_result["cycles"]:
                elements.append(Paragraph(f"  * {cycle['description']}", styles["KPAMono"]))
        else:
            elements.append(Paragraph("No circular permission loops detected.", styles["KPABody"]))
        elements.append(Spacer(1, 6 * mm))

    # 5. Critical Node
    if critical_result and critical_result.get("critical_node"):
        cn = critical_result["critical_node"]
        elements.append(Paragraph("5. Critical Node Analysis", styles["KPAHeading"]))
        elements.append(Paragraph(
            f"Recommendation: Remove or restrict '{cn['label']}' "
            f"to break {cn['paths_broken']}/{critical_result['baseline_paths']} attack paths "
            f"({cn['impact_percentage']}% impact).",
            styles["KPAWarning"],
        ))

        top5 = critical_result.get("top_5_nodes", [])
        if top5:
            elements.append(Spacer(1, 3 * mm))
            cn_data = [["Rank", "Node", "Type", "Paths Broken", "Impact %"]]
            for i, node in enumerate(top5, 1):
                cn_data.append([
                    str(i), node["label"], node["type"],
                    str(node["paths_broken"]), f"{node['impact_percentage']}%",
                ])
            t4 = Table(cn_data, colWidths=[15 * mm, 45 * mm, 30 * mm, 35 * mm, 25 * mm])
            t4.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#7c3aed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#faf5ff"), HexColor("#ffffff")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(t4)
        elements.append(Spacer(1, 6 * mm))

    # Footer
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(
        f"Generated by KubePathAudit v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Confidential",
        styles["KPASubtitle"],
    ))

    doc.build(elements)
    buf.seek(0)

    filename = f"KubePathAudit_KillChain_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## backend\mock-cluster-graph.json

```json
{
  "metadata": {
    "cluster_name": "prod-eks-cluster-01",
    "scan_timestamp": "2026-03-30T12:00:00Z",
    "scenario": "Tesla Breach Simulation",
    "description": "An internet-facing Kubernetes dashboard with excessive RBAC permissions leads to credential theft and database compromise."
  },
  "nodes": [
    {
      "id": "internet",
      "label": "Internet",
      "type": "internet",
      "namespace": "external",
      "risk_level": "entry-point",
      "metadata": {
        "description": "External internet traffic entry point",
        "icon": "globe"
      }
    },
    {
      "id": "ingress-nginx",
      "label": "Ingress Controller",
      "type": "ingress",
      "namespace": "ingress-nginx",
      "risk_level": "medium",
      "metadata": {
        "description": "NGINX Ingress Controller",
        "version": "1.9.4",
        "cves": ["CVE-2024-7646"],
        "cvss_scores": [8.8],
        "ports": [80, 443],
        "icon": "network"
      }
    },
    {
      "id": "tesla-dashboard-pod",
      "label": "Tesla Dashboard",
      "type": "pod",
      "namespace": "monitoring",
      "risk_level": "critical",
      "metadata": {
        "description": "Internet-facing Kubernetes Dashboard — misconfigured with no authentication",
        "image": "kubernetesui/dashboard:v2.7.0",
        "cves": ["CVE-2018-18264", "CVE-2023-49797"],
        "cvss_scores": [7.5, 8.1],
        "ports": [8443],
        "labels": {"app": "kubernetes-dashboard", "exposed": "true"},
        "icon": "monitor"
      }
    },
    {
      "id": "dashboard-sa",
      "label": "dashboard-admin-sa",
      "type": "serviceaccount",
      "namespace": "monitoring",
      "risk_level": "critical",
      "metadata": {
        "description": "ServiceAccount with cluster-admin privileges mounted to the dashboard pod",
        "automount_token": true,
        "icon": "user-check"
      }
    },
    {
      "id": "cluster-admin-binding",
      "label": "dashboard-cluster-admin",
      "type": "rolebinding",
      "namespace": "cluster-wide",
      "risk_level": "critical",
      "metadata": {
        "description": "ClusterRoleBinding granting cluster-admin to dashboard-admin-sa",
        "binding_type": "ClusterRoleBinding",
        "icon": "link"
      }
    },
    {
      "id": "cluster-admin-role",
      "label": "cluster-admin",
      "type": "clusterrole",
      "namespace": "cluster-wide",
      "risk_level": "critical",
      "metadata": {
        "description": "ClusterRole with full access to all resources: *.* (verbs: *)",
        "rules": ["*.*:*"],
        "icon": "shield-alert"
      }
    },
    {
      "id": "aws-cred-secret",
      "label": "aws-credentials",
      "type": "secret",
      "namespace": "production",
      "risk_level": "crown-jewel",
      "metadata": {
        "description": "AWS IAM access keys stored as Kubernetes Secret",
        "secret_type": "Opaque",
        "keys": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        "icon": "key"
      }
    },
    {
      "id": "prod-database",
      "label": "Production PostgreSQL",
      "type": "database",
      "namespace": "production",
      "risk_level": "crown-jewel",
      "metadata": {
        "description": "Production PostgreSQL database containing customer PII and financial data",
        "engine": "PostgreSQL 15.2",
        "data_classification": "PII + Financial",
        "records": "2.4M customer records",
        "icon": "database"
      }
    },
    {
      "id": "db-credentials-secret",
      "label": "db-credentials",
      "type": "secret",
      "namespace": "production",
      "risk_level": "crown-jewel",
      "metadata": {
        "description": "Database connection string and credentials",
        "secret_type": "Opaque",
        "keys": ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"],
        "icon": "key"
      }
    },
    {
      "id": "api-server-pod",
      "label": "API Server Pod",
      "type": "pod",
      "namespace": "production",
      "risk_level": "high",
      "metadata": {
        "description": "Main application API server",
        "image": "company/api-server:3.1.2",
        "cves": ["CVE-2023-44487"],
        "cvss_scores": [7.5],
        "ports": [8080],
        "labels": {"app": "api-server", "tier": "backend"},
        "icon": "server"
      }
    },
    {
      "id": "api-server-sa",
      "label": "api-server-sa",
      "type": "serviceaccount",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "ServiceAccount for the API server pod",
        "automount_token": true,
        "icon": "user"
      }
    },
    {
      "id": "api-role-binding",
      "label": "api-server-rb",
      "type": "rolebinding",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "RoleBinding for api-server to access production secrets",
        "binding_type": "RoleBinding",
        "icon": "link"
      }
    },
    {
      "id": "api-role",
      "label": "api-server-role",
      "type": "role",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "Role granting read access to specific secrets in production namespace",
        "rules": ["secrets:get,list (production)"],
        "icon": "shield"
      }
    },
    {
      "id": "worker-pod-1",
      "label": "Worker Pod 1",
      "type": "pod",
      "namespace": "production",
      "risk_level": "low",
      "metadata": {
        "description": "Background job worker processing queue messages",
        "image": "company/worker:2.8.0",
        "cves": [],
        "cvss_scores": [],
        "ports": [9090],
        "labels": {"app": "worker", "tier": "backend"},
        "icon": "cpu"
      }
    },
    {
      "id": "worker-pod-2",
      "label": "Worker Pod 2",
      "type": "pod",
      "namespace": "production",
      "risk_level": "low",
      "metadata": {
        "description": "Background job worker processing queue messages",
        "image": "company/worker:2.8.0",
        "cves": [],
        "cvss_scores": [],
        "ports": [9090],
        "labels": {"app": "worker", "tier": "backend"},
        "icon": "cpu"
      }
    },
    {
      "id": "monitoring-pod",
      "label": "Prometheus",
      "type": "pod",
      "namespace": "monitoring",
      "risk_level": "medium",
      "metadata": {
        "description": "Prometheus monitoring stack",
        "image": "prom/prometheus:v2.48.0",
        "cves": ["CVE-2024-6837"],
        "cvss_scores": [5.4],
        "ports": [9090],
        "labels": {"app": "prometheus"},
        "icon": "activity"
      }
    },
    {
      "id": "monitoring-sa",
      "label": "prometheus-sa",
      "type": "serviceaccount",
      "namespace": "monitoring",
      "risk_level": "low",
      "metadata": {
        "description": "ServiceAccount for Prometheus with read-only metrics access",
        "automount_token": true,
        "icon": "user"
      }
    },
    {
      "id": "monitoring-role-binding",
      "label": "prometheus-rb",
      "type": "rolebinding",
      "namespace": "monitoring",
      "risk_level": "low",
      "metadata": {
        "description": "ClusterRoleBinding for Prometheus metrics collection",
        "binding_type": "ClusterRoleBinding",
        "icon": "link"
      }
    },
    {
      "id": "monitoring-role",
      "label": "prometheus-reader",
      "type": "clusterrole",
      "namespace": "cluster-wide",
      "risk_level": "low",
      "metadata": {
        "description": "ClusterRole with read-only access to metrics endpoints",
        "rules": ["pods:get,list,watch", "nodes:get,list,watch", "metrics.k8s.io:get,list"],
        "icon": "shield"
      }
    },
    {
      "id": "etcd-pod",
      "label": "etcd",
      "type": "pod",
      "namespace": "kube-system",
      "risk_level": "critical",
      "metadata": {
        "description": "etcd key-value store — backbone of the cluster",
        "image": "registry.k8s.io/etcd:3.5.10",
        "cves": ["CVE-2023-47108"],
        "cvss_scores": [7.5],
        "ports": [2379, 2380],
        "icon": "hard-drive"
      }
    },
    {
      "id": "kube-apiserver",
      "label": "kube-apiserver",
      "type": "pod",
      "namespace": "kube-system",
      "risk_level": "critical",
      "metadata": {
        "description": "Kubernetes API Server — control plane component",
        "image": "registry.k8s.io/kube-apiserver:v1.28.4",
        "cves": [],
        "cvss_scores": [],
        "ports": [6443],
        "icon": "server"
      }
    },
    {
      "id": "configmap-app-config",
      "label": "app-config",
      "type": "configmap",
      "namespace": "production",
      "risk_level": "low",
      "metadata": {
        "description": "Application configuration (non-sensitive)",
        "keys": ["LOG_LEVEL", "FEATURE_FLAGS", "API_TIMEOUT"],
        "icon": "file-text"
      }
    },
    {
      "id": "network-policy-default",
      "label": "default-deny",
      "type": "networkpolicy",
      "namespace": "production",
      "risk_level": "info",
      "metadata": {
        "description": "Default deny network policy (not enforced on monitoring namespace!)",
        "enforcement": "partial",
        "icon": "shield-off"
      }
    },
    {
      "id": "svc-api-loadbalancer",
      "label": "api-service (LB)",
      "type": "service",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "LoadBalancer service exposing the API server externally",
        "service_type": "LoadBalancer",
        "ports": [443],
        "icon": "globe"
      }
    }
  ],
  "edges": [
    {
      "source": "internet",
      "target": "ingress-nginx",
      "relationship": "routes_to",
      "weight": 1.0,
      "metadata": {"description": "External traffic hits ingress controller", "protocol": "HTTPS"}
    },
    {
      "source": "ingress-nginx",
      "target": "tesla-dashboard-pod",
      "relationship": "forwards_to",
      "weight": 1.5,
      "metadata": {"description": "Ingress routes /dashboard to Tesla Dashboard pod (no auth!)", "protocol": "HTTPS", "auth": "none"}
    },
    {
      "source": "tesla-dashboard-pod",
      "target": "dashboard-sa",
      "relationship": "uses_service_account",
      "weight": 0.5,
      "metadata": {"description": "Dashboard pod auto-mounts privileged ServiceAccount token"}
    },
    {
      "source": "dashboard-sa",
      "target": "cluster-admin-binding",
      "relationship": "bound_by",
      "weight": 0.5,
      "metadata": {"description": "SA is bound to cluster-admin via ClusterRoleBinding"}
    },
    {
      "source": "cluster-admin-binding",
      "target": "cluster-admin-role",
      "relationship": "grants",
      "weight": 0.5,
      "metadata": {"description": "Binding grants cluster-admin ClusterRole"}
    },
    {
      "source": "cluster-admin-role",
      "target": "aws-cred-secret",
      "relationship": "can_access",
      "weight": 1.0,
      "metadata": {"description": "cluster-admin can read all secrets including AWS credentials"}
    },
    {
      "source": "cluster-admin-role",
      "target": "db-credentials-secret",
      "relationship": "can_access",
      "weight": 1.0,
      "metadata": {"description": "cluster-admin can read database credentials"}
    },
    {
      "source": "db-credentials-secret",
      "target": "prod-database",
      "relationship": "authenticates_to",
      "weight": 0.5,
      "metadata": {"description": "DB credentials used to connect to production database"}
    },
    {
      "source": "aws-cred-secret",
      "target": "prod-database",
      "relationship": "provides_access",
      "weight": 1.5,
      "metadata": {"description": "AWS credentials can be used to access RDS instance directly"}
    },
    {
      "source": "internet",
      "target": "svc-api-loadbalancer",
      "relationship": "routes_to",
      "weight": 2.0,
      "metadata": {"description": "External traffic to API LoadBalancer service", "protocol": "HTTPS"}
    },
    {
      "source": "svc-api-loadbalancer",
      "target": "api-server-pod",
      "relationship": "forwards_to",
      "weight": 2.0,
      "metadata": {"description": "LoadBalancer routes to API server pod", "protocol": "HTTPS", "auth": "JWT"}
    },
    {
      "source": "api-server-pod",
      "target": "api-server-sa",
      "relationship": "uses_service_account",
      "weight": 1.0,
      "metadata": {"description": "API server pod uses its service account"}
    },
    {
      "source": "api-server-sa",
      "target": "api-role-binding",
      "relationship": "bound_by",
      "weight": 1.0,
      "metadata": {"description": "SA bound via RoleBinding"}
    },
    {
      "source": "api-role-binding",
      "target": "api-role",
      "relationship": "grants",
      "weight": 1.0,
      "metadata": {"description": "Binding grants api-server-role"}
    },
    {
      "source": "api-role",
      "target": "db-credentials-secret",
      "relationship": "can_access",
      "weight": 2.0,
      "metadata": {"description": "Role grants read access to db-credentials secret"}
    },
    {
      "source": "api-server-pod",
      "target": "prod-database",
      "relationship": "connects_to",
      "weight": 1.5,
      "metadata": {"description": "API server connects to production database", "protocol": "TCP:5432"}
    },
    {
      "source": "api-server-pod",
      "target": "configmap-app-config",
      "relationship": "mounts",
      "weight": 3.0,
      "metadata": {"description": "API server mounts application config"}
    },
    {
      "source": "api-server-pod",
      "target": "worker-pod-1",
      "relationship": "sends_jobs_to",
      "weight": 2.5,
      "metadata": {"description": "API server dispatches background jobs", "protocol": "AMQP"}
    },
    {
      "source": "api-server-pod",
      "target": "worker-pod-2",
      "relationship": "sends_jobs_to",
      "weight": 2.5,
      "metadata": {"description": "API server dispatches background jobs", "protocol": "AMQP"}
    },
    {
      "source": "monitoring-pod",
      "target": "monitoring-sa",
      "relationship": "uses_service_account",
      "weight": 2.0,
      "metadata": {"description": "Prometheus uses its service account for API discovery"}
    },
    {
      "source": "monitoring-sa",
      "target": "monitoring-role-binding",
      "relationship": "bound_by",
      "weight": 2.0,
      "metadata": {"description": "SA bound via ClusterRoleBinding"}
    },
    {
      "source": "monitoring-role-binding",
      "target": "monitoring-role",
      "relationship": "grants",
      "weight": 2.0,
      "metadata": {"description": "Binding grants prometheus-reader ClusterRole"}
    },
    {
      "source": "monitoring-pod",
      "target": "api-server-pod",
      "relationship": "scrapes_metrics",
      "weight": 3.0,
      "metadata": {"description": "Prometheus scrapes metrics from API server", "protocol": "HTTP:8080/metrics"}
    },
    {
      "source": "monitoring-pod",
      "target": "worker-pod-1",
      "relationship": "scrapes_metrics",
      "weight": 3.0,
      "metadata": {"description": "Prometheus scrapes metrics from worker", "protocol": "HTTP:9090/metrics"}
    },
    {
      "source": "kube-apiserver",
      "target": "etcd-pod",
      "relationship": "reads_writes",
      "weight": 1.0,
      "metadata": {"description": "API server reads/writes cluster state to etcd", "protocol": "gRPC:2379"}
    },
    {
      "source": "cluster-admin-role",
      "target": "kube-apiserver",
      "relationship": "full_access",
      "weight": 0.5,
      "metadata": {"description": "cluster-admin has full access to the Kubernetes API"}
    },
    {
      "source": "tesla-dashboard-pod",
      "target": "monitoring-pod",
      "relationship": "network_access",
      "weight": 2.5,
      "metadata": {"description": "Dashboard can reach monitoring namespace (no NetworkPolicy!)"}
    },
    {
      "source": "monitoring-pod",
      "target": "tesla-dashboard-pod",
      "relationship": "network_access",
      "weight": 2.5,
      "metadata": {"description": "Bidirectional access in monitoring namespace"}
    }
  ]
}
```

## backend\requirements.txt

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
networkx==3.3
pydantic==2.9.0
python-multipart==0.0.9
reportlab==4.2.5
```

## backend\temporal.py

```python
"""
Temporal Analysis — Snapshot storage and graph diffing for KubePathAudit.
Stores timestamped graph snapshots and compares them to detect new attack paths.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import networkx as nx

from graph_engine import K8sGraphEngine


SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def ensure_snapshot_dir() -> Path:
    """Ensure the snapshots directory exists."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR


def save_snapshot(graph_data: dict, label: str = "") -> str:
    """
    Save a timestamped snapshot of the cluster graph.
    
    Returns:
        str: The path to the saved snapshot file.
    """
    ensure_snapshot_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = f"_{label}" if label else ""
    filename = f"snapshot_{timestamp}{suffix}.json"
    filepath = SNAPSHOT_DIR / filename

    snapshot = {
        "snapshot_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "label": label,
            "node_count": len(graph_data.get("nodes", [])),
            "edge_count": len(graph_data.get("edges", [])),
        },
        **graph_data,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    return str(filepath)


def list_snapshots() -> list[dict]:
    """List all stored snapshots with their metadata."""
    ensure_snapshot_dir()
    snapshots = []
    for f in sorted(SNAPSHOT_DIR.glob("snapshot_*.json"), reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            meta = data.get("snapshot_metadata", {})
            snapshots.append({
                "filename": f.name,
                "filepath": str(f),
                "timestamp": meta.get("timestamp", ""),
                "label": meta.get("label", ""),
                "node_count": meta.get("node_count", 0),
                "edge_count": meta.get("edge_count", 0),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return snapshots


def load_snapshot(filepath: str) -> Optional[dict]:
    """Load a snapshot file and return its graph data."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        return None


def get_latest_snapshot() -> Optional[dict]:
    """Get the most recent snapshot."""
    snapshots = list_snapshots()
    if not snapshots:
        return None
    return load_snapshot(snapshots[0]["filepath"])


def diff_graphs(old_data: dict, new_data: dict) -> dict:
    """
    Compare two graph snapshots and produce a detailed diff.
    
    Returns a dict describing:
    - New/removed nodes
    - New/removed edges
    - Risk level changes
    - New attack paths from entry points to crown jewels
    """
    old_nodes = {n["id"]: n for n in old_data.get("nodes", [])}
    new_nodes = {n["id"]: n for n in new_data.get("nodes", [])}

    old_edges = {(e["source"], e["target"]): e for e in old_data.get("edges", [])}
    new_edges = {(e["source"], e["target"]): e for e in new_data.get("edges", [])}

    old_node_ids = set(old_nodes.keys())
    new_node_ids = set(new_nodes.keys())

    old_edge_keys = set(old_edges.keys())
    new_edge_keys = set(new_edges.keys())

    # Node diff
    added_nodes = [new_nodes[nid] for nid in (new_node_ids - old_node_ids)]
    removed_nodes = [old_nodes[nid] for nid in (old_node_ids - new_node_ids)]

    # Edge diff
    added_edges = [new_edges[ek] for ek in (new_edge_keys - old_edge_keys)]
    removed_edges = [old_edges[ek] for ek in (old_edge_keys - new_edge_keys)]

    # Risk level changes
    risk_changes = []
    for nid in old_node_ids & new_node_ids:
        old_risk = old_nodes[nid].get("risk_level", "low")
        new_risk = new_nodes[nid].get("risk_level", "low")
        if old_risk != new_risk:
            risk_changes.append({
                "node_id": nid,
                "label": new_nodes[nid].get("label", nid),
                "old_risk": old_risk,
                "new_risk": new_risk,
                "escalation": _is_escalation(old_risk, new_risk),
            })

    # ── New attack paths ──────────────────────────────────
    new_attack_paths = _find_new_attack_paths(old_data, new_data)

    # Summary
    has_changes = bool(added_nodes or removed_nodes or added_edges or removed_edges or risk_changes)
    has_new_threats = bool(new_attack_paths) or any(rc["escalation"] for rc in risk_changes)

    return {
        "has_changes": has_changes,
        "has_new_threats": has_new_threats,
        "summary": {
            "nodes_added": len(added_nodes),
            "nodes_removed": len(removed_nodes),
            "edges_added": len(added_edges),
            "edges_removed": len(removed_edges),
            "risk_changes": len(risk_changes),
            "new_attack_paths": len(new_attack_paths),
        },
        "added_nodes": added_nodes,
        "removed_nodes": removed_nodes,
        "added_edges": added_edges,
        "removed_edges": removed_edges,
        "risk_changes": risk_changes,
        "new_attack_paths": new_attack_paths,
        "old_timestamp": old_data.get("snapshot_metadata", {}).get("timestamp",
                          old_data.get("metadata", {}).get("scan_timestamp", "unknown")),
        "new_timestamp": new_data.get("snapshot_metadata", {}).get("timestamp",
                          new_data.get("metadata", {}).get("scan_timestamp", "unknown")),
    }


RISK_ORDER = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
    "crown-jewel": 5,
    "entry-point": 1,
}


def _is_escalation(old: str, new: str) -> bool:
    """Check if a risk level change represents an escalation."""
    return RISK_ORDER.get(new, 0) > RISK_ORDER.get(old, 0)


def _find_new_attack_paths(old_data: dict, new_data: dict) -> list[dict]:
    """
    Find attack paths in the new graph that didn't exist in the old graph.
    Compares shortest paths from entry points to crown jewels.
    """
    old_engine = K8sGraphEngine()
    old_engine.load_graph_from_dict({
        "nodes": old_data.get("nodes", []),
        "edges": old_data.get("edges", []),
    })

    new_engine = K8sGraphEngine()
    new_engine.load_graph_from_dict({
        "nodes": new_data.get("nodes", []),
        "edges": new_data.get("edges", []),
    })

    # Find entry points and crown jewels in new graph
    entry_points = [
        n for n, d in new_engine.graph.nodes(data=True)
        if d.get("type") == "internet" or d.get("risk_level") == "entry-point"
    ]
    crown_jewels = [
        n for n, d in new_engine.graph.nodes(data=True)
        if d.get("risk_level") == "crown-jewel"
    ]

    new_attack_paths = []
    for entry in entry_points:
        for jewel in crown_jewels:
            # Check if path exists in new graph
            new_path_exists = nx.has_path(new_engine.graph, entry, jewel) if entry in new_engine.graph and jewel in new_engine.graph else False

            if not new_path_exists:
                continue

            # Check if it also existed in old graph
            old_path_exists = (
                entry in old_engine.graph
                and jewel in old_engine.graph
                and nx.has_path(old_engine.graph, entry, jewel)
            )

            if not old_path_exists:
                # This is a NEW attack path
                try:
                    path = nx.dijkstra_path(new_engine.graph, entry, jewel, weight="weight")
                    weight = nx.dijkstra_path_length(new_engine.graph, entry, jewel, weight="weight")
                    new_attack_paths.append({
                        "source": entry,
                        "target": jewel,
                        "path": path,
                        "hop_count": len(path) - 1,
                        "total_weight": round(weight, 2),
                        "severity": "CRITICAL",
                    })
                except nx.NetworkXNoPath:
                    pass

    return new_attack_paths


def format_diff_report(diff: dict) -> str:
    """Format a diff result into a human-readable report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  TEMPORAL ANALYSIS — Graph Diff Report")
    lines.append("=" * 70)
    lines.append(f"  Previous Scan: {diff['old_timestamp']}")
    lines.append(f"  Current Scan:  {diff['new_timestamp']}")
    lines.append("=" * 70)

    s = diff["summary"]
    if not diff["has_changes"]:
        lines.append("\n  ✅ No changes detected between snapshots.\n")
        return "\n".join(lines)

    lines.append("")

    if diff["has_new_threats"]:
        lines.append("  ⚠  NEW THREATS DETECTED!")
        lines.append("")

    # Summary stats
    lines.append(f"  📊 Changes Summary:")
    lines.append(f"     Nodes added:       {s['nodes_added']}")
    lines.append(f"     Nodes removed:     {s['nodes_removed']}")
    lines.append(f"     Edges added:       {s['edges_added']}")
    lines.append(f"     Edges removed:     {s['edges_removed']}")
    lines.append(f"     Risk changes:      {s['risk_changes']}")
    lines.append(f"     New attack paths:  {s['new_attack_paths']}")
    lines.append("")

    # Added nodes
    if diff["added_nodes"]:
        lines.append("  ➕ Added Nodes:")
        for n in diff["added_nodes"]:
            lines.append(f"     • {n.get('label', n['id'])} [{n.get('type', '?')}] "
                         f"(risk: {n.get('risk_level', '?')}) in {n.get('namespace', '?')}")
        lines.append("")

    # Removed nodes
    if diff["removed_nodes"]:
        lines.append("  ➖ Removed Nodes:")
        for n in diff["removed_nodes"]:
            lines.append(f"     • {n.get('label', n['id'])} [{n.get('type', '?')}]")
        lines.append("")

    # Added edges
    if diff["added_edges"]:
        lines.append("  🔗 Added Edges:")
        for e in diff["added_edges"][:10]:
            lines.append(f"     • {e['source']} → {e['target']} ({e.get('relationship', '?')})")
        if len(diff["added_edges"]) > 10:
            lines.append(f"     ... and {len(diff['added_edges']) - 10} more")
        lines.append("")

    # Risk changes
    if diff["risk_changes"]:
        lines.append("  🔺 Risk Level Changes:")
        for rc in diff["risk_changes"]:
            arrow = "⬆" if rc["escalation"] else "⬇"
            lines.append(f"     {arrow} {rc['label']}: {rc['old_risk']} → {rc['new_risk']}")
        lines.append("")

    # New attack paths — the most critical section
    if diff["new_attack_paths"]:
        lines.append("  🚨 NEW ATTACK PATHS DETECTED:")
        lines.append("  " + "-" * 50)
        for i, ap in enumerate(diff["new_attack_paths"], 1):
            lines.append(f"     Attack Path #{i}:")
            lines.append(f"       {' → '.join(ap['path'])}")
            lines.append(f"       Hops: {ap['hop_count']} | Weight: {ap['total_weight']} | Severity: {ap['severity']}")
            lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)
```

## backend\snapshots\snapshot_20260402_044827_baseline.json

```json
{
  "snapshot_metadata": {
    "timestamp": "2026-04-02T04:48:27.421727+00:00",
    "label": "baseline",
    "node_count": 24,
    "edge_count": 28
  },
  "nodes": [
    {
      "id": "internet",
      "label": "Internet",
      "type": "internet",
      "namespace": "external",
      "risk_level": "entry-point",
      "metadata": {
        "description": "External internet traffic entry point",
        "icon": "globe"
      }
    },
    {
      "id": "ingress-nginx",
      "label": "Ingress Controller",
      "type": "ingress",
      "namespace": "ingress-nginx",
      "risk_level": "medium",
      "metadata": {
        "description": "NGINX Ingress Controller",
        "version": "1.9.4",
        "cves": [
          "CVE-2024-7646"
        ],
        "cvss_scores": [
          8.8
        ],
        "ports": [
          80,
          443
        ],
        "icon": "network"
      }
    },
    {
      "id": "tesla-dashboard-pod",
      "label": "Tesla Dashboard",
      "type": "pod",
      "namespace": "monitoring",
      "risk_level": "critical",
      "metadata": {
        "description": "Internet-facing Kubernetes Dashboard \u2014 misconfigured with no authentication",
        "image": "kubernetesui/dashboard:v2.7.0",
        "cves": [
          "CVE-2018-18264",
          "CVE-2023-49797"
        ],
        "cvss_scores": [
          7.5,
          8.1
        ],
        "ports": [
          8443
        ],
        "labels": {
          "app": "kubernetes-dashboard",
          "exposed": "true"
        },
        "icon": "monitor"
      }
    },
    {
      "id": "dashboard-sa",
      "label": "dashboard-admin-sa",
      "type": "serviceaccount",
      "namespace": "monitoring",
      "risk_level": "critical",
      "metadata": {
        "description": "ServiceAccount with cluster-admin privileges mounted to the dashboard pod",
        "automount_token": true,
        "icon": "user-check"
      }
    },
    {
      "id": "cluster-admin-binding",
      "label": "dashboard-cluster-admin",
      "type": "rolebinding",
      "namespace": "cluster-wide",
      "risk_level": "critical",
      "metadata": {
        "description": "ClusterRoleBinding granting cluster-admin to dashboard-admin-sa",
        "binding_type": "ClusterRoleBinding",
        "icon": "link"
      }
    },
    {
      "id": "cluster-admin-role",
      "label": "cluster-admin",
      "type": "clusterrole",
      "namespace": "cluster-wide",
      "risk_level": "critical",
      "metadata": {
        "description": "ClusterRole with full access to all resources: *.* (verbs: *)",
        "rules": [
          "*.*:*"
        ],
        "icon": "shield-alert"
      }
    },
    {
      "id": "aws-cred-secret",
      "label": "aws-credentials",
      "type": "secret",
      "namespace": "production",
      "risk_level": "crown-jewel",
      "metadata": {
        "description": "AWS IAM access keys stored as Kubernetes Secret",
        "secret_type": "Opaque",
        "keys": [
          "AWS_ACCESS_KEY_ID",
          "AWS_SECRET_ACCESS_KEY"
        ],
        "icon": "key"
      }
    },
    {
      "id": "prod-database",
      "label": "Production PostgreSQL",
      "type": "database",
      "namespace": "production",
      "risk_level": "crown-jewel",
      "metadata": {
        "description": "Production PostgreSQL database containing customer PII and financial data",
        "engine": "PostgreSQL 15.2",
        "data_classification": "PII + Financial",
        "records": "2.4M customer records",
        "icon": "database"
      }
    },
    {
      "id": "db-credentials-secret",
      "label": "db-credentials",
      "type": "secret",
      "namespace": "production",
      "risk_level": "crown-jewel",
      "metadata": {
        "description": "Database connection string and credentials",
        "secret_type": "Opaque",
        "keys": [
          "DB_HOST",
          "DB_USER",
          "DB_PASSWORD",
          "DB_NAME"
        ],
        "icon": "key"
      }
    },
    {
      "id": "api-server-pod",
      "label": "API Server Pod",
      "type": "pod",
      "namespace": "production",
      "risk_level": "high",
      "metadata": {
        "description": "Main application API server",
        "image": "company/api-server:3.1.2",
        "cves": [
          "CVE-2023-44487"
        ],
        "cvss_scores": [
          7.5
        ],
        "ports": [
          8080
        ],
        "labels": {
          "app": "api-server",
          "tier": "backend"
        },
        "icon": "server"
      }
    },
    {
      "id": "api-server-sa",
      "label": "api-server-sa",
      "type": "serviceaccount",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "ServiceAccount for the API server pod",
        "automount_token": true,
        "icon": "user"
      }
    },
    {
      "id": "api-role-binding",
      "label": "api-server-rb",
      "type": "rolebinding",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "RoleBinding for api-server to access production secrets",
        "binding_type": "RoleBinding",
        "icon": "link"
      }
    },
    {
      "id": "api-role",
      "label": "api-server-role",
      "type": "role",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "Role granting read access to specific secrets in production namespace",
        "rules": [
          "secrets:get,list (production)"
        ],
        "icon": "shield"
      }
    },
    {
      "id": "worker-pod-1",
      "label": "Worker Pod 1",
      "type": "pod",
      "namespace": "production",
      "risk_level": "low",
      "metadata": {
        "description": "Background job worker processing queue messages",
        "image": "company/worker:2.8.0",
        "cves": [],
        "cvss_scores": [],
        "ports": [
          9090
        ],
        "labels": {
          "app": "worker",
          "tier": "backend"
        },
        "icon": "cpu"
      }
    },
    {
      "id": "worker-pod-2",
      "label": "Worker Pod 2",
      "type": "pod",
      "namespace": "production",
      "risk_level": "low",
      "metadata": {
        "description": "Background job worker processing queue messages",
        "image": "company/worker:2.8.0",
        "cves": [],
        "cvss_scores": [],
        "ports": [
          9090
        ],
        "labels": {
          "app": "worker",
          "tier": "backend"
        },
        "icon": "cpu"
      }
    },
    {
      "id": "monitoring-pod",
      "label": "Prometheus",
      "type": "pod",
      "namespace": "monitoring",
      "risk_level": "medium",
      "metadata": {
        "description": "Prometheus monitoring stack",
        "image": "prom/prometheus:v2.48.0",
        "cves": [
          "CVE-2024-6837"
        ],
        "cvss_scores": [
          5.4
        ],
        "ports": [
          9090
        ],
        "labels": {
          "app": "prometheus"
        },
        "icon": "activity"
      }
    },
    {
      "id": "monitoring-sa",
      "label": "prometheus-sa",
      "type": "serviceaccount",
      "namespace": "monitoring",
      "risk_level": "low",
      "metadata": {
        "description": "ServiceAccount for Prometheus with read-only metrics access",
        "automount_token": true,
        "icon": "user"
      }
    },
    {
      "id": "monitoring-role-binding",
      "label": "prometheus-rb",
      "type": "rolebinding",
      "namespace": "monitoring",
      "risk_level": "low",
      "metadata": {
        "description": "ClusterRoleBinding for Prometheus metrics collection",
        "binding_type": "ClusterRoleBinding",
        "icon": "link"
      }
    },
    {
      "id": "monitoring-role",
      "label": "prometheus-reader",
      "type": "clusterrole",
      "namespace": "cluster-wide",
      "risk_level": "low",
      "metadata": {
        "description": "ClusterRole with read-only access to metrics endpoints",
        "rules": [
          "pods:get,list,watch",
          "nodes:get,list,watch",
          "metrics.k8s.io:get,list"
        ],
        "icon": "shield"
      }
    },
    {
      "id": "etcd-pod",
      "label": "etcd",
      "type": "pod",
      "namespace": "kube-system",
      "risk_level": "critical",
      "metadata": {
        "description": "etcd key-value store \u2014 backbone of the cluster",
        "image": "registry.k8s.io/etcd:3.5.10",
        "cves": [
          "CVE-2023-47108"
        ],
        "cvss_scores": [
          7.5
        ],
        "ports": [
          2379,
          2380
        ],
        "icon": "hard-drive"
      }
    },
    {
      "id": "kube-apiserver",
      "label": "kube-apiserver",
      "type": "pod",
      "namespace": "kube-system",
      "risk_level": "critical",
      "metadata": {
        "description": "Kubernetes API Server \u2014 control plane component",
        "image": "registry.k8s.io/kube-apiserver:v1.28.4",
        "cves": [],
        "cvss_scores": [],
        "ports": [
          6443
        ],
        "icon": "server"
      }
    },
    {
      "id": "configmap-app-config",
      "label": "app-config",
      "type": "configmap",
      "namespace": "production",
      "risk_level": "low",
      "metadata": {
        "description": "Application configuration (non-sensitive)",
        "keys": [
          "LOG_LEVEL",
          "FEATURE_FLAGS",
          "API_TIMEOUT"
        ],
        "icon": "file-text"
      }
    },
    {
      "id": "network-policy-default",
      "label": "default-deny",
      "type": "networkpolicy",
      "namespace": "production",
      "risk_level": "info",
      "metadata": {
        "description": "Default deny network policy (not enforced on monitoring namespace!)",
        "enforcement": "partial",
        "icon": "shield-off"
      }
    },
    {
      "id": "svc-api-loadbalancer",
      "label": "api-service (LB)",
      "type": "service",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "LoadBalancer service exposing the API server externally",
        "service_type": "LoadBalancer",
        "ports": [
          443
        ],
        "icon": "globe"
      }
    }
  ],
  "edges": [
    {
      "source": "internet",
      "target": "ingress-nginx",
      "relationship": "routes_to",
      "weight": 1.0,
      "metadata": {
        "description": "External traffic hits ingress controller",
        "protocol": "HTTPS"
      }
    },
    {
      "source": "ingress-nginx",
      "target": "tesla-dashboard-pod",
      "relationship": "forwards_to",
      "weight": 1.5,
      "metadata": {
        "description": "Ingress routes /dashboard to Tesla Dashboard pod (no auth!)",
        "protocol": "HTTPS",
        "auth": "none"
      }
    },
    {
      "source": "tesla-dashboard-pod",
      "target": "dashboard-sa",
      "relationship": "uses_service_account",
      "weight": 0.5,
      "metadata": {
        "description": "Dashboard pod auto-mounts privileged ServiceAccount token"
      }
    },
    {
      "source": "dashboard-sa",
      "target": "cluster-admin-binding",
      "relationship": "bound_by",
      "weight": 0.5,
      "metadata": {
        "description": "SA is bound to cluster-admin via ClusterRoleBinding"
      }
    },
    {
      "source": "cluster-admin-binding",
      "target": "cluster-admin-role",
      "relationship": "grants",
      "weight": 0.5,
      "metadata": {
        "description": "Binding grants cluster-admin ClusterRole"
      }
    },
    {
      "source": "cluster-admin-role",
      "target": "aws-cred-secret",
      "relationship": "can_access",
      "weight": 1.0,
      "metadata": {
        "description": "cluster-admin can read all secrets including AWS credentials"
      }
    },
    {
      "source": "cluster-admin-role",
      "target": "db-credentials-secret",
      "relationship": "can_access",
      "weight": 1.0,
      "metadata": {
        "description": "cluster-admin can read database credentials"
      }
    },
    {
      "source": "db-credentials-secret",
      "target": "prod-database",
      "relationship": "authenticates_to",
      "weight": 0.5,
      "metadata": {
        "description": "DB credentials used to connect to production database"
      }
    },
    {
      "source": "aws-cred-secret",
      "target": "prod-database",
      "relationship": "provides_access",
      "weight": 1.5,
      "metadata": {
        "description": "AWS credentials can be used to access RDS instance directly"
      }
    },
    {
      "source": "internet",
      "target": "svc-api-loadbalancer",
      "relationship": "routes_to",
      "weight": 2.0,
      "metadata": {
        "description": "External traffic to API LoadBalancer service",
        "protocol": "HTTPS"
      }
    },
    {
      "source": "svc-api-loadbalancer",
      "target": "api-server-pod",
      "relationship": "forwards_to",
      "weight": 2.0,
      "metadata": {
        "description": "LoadBalancer routes to API server pod",
        "protocol": "HTTPS",
        "auth": "JWT"
      }
    },
    {
      "source": "api-server-pod",
      "target": "api-server-sa",
      "relationship": "uses_service_account",
      "weight": 1.0,
      "metadata": {
        "description": "API server pod uses its service account"
      }
    },
    {
      "source": "api-server-sa",
      "target": "api-role-binding",
      "relationship": "bound_by",
      "weight": 1.0,
      "metadata": {
        "description": "SA bound via RoleBinding"
      }
    },
    {
      "source": "api-role-binding",
      "target": "api-role",
      "relationship": "grants",
      "weight": 1.0,
      "metadata": {
        "description": "Binding grants api-server-role"
      }
    },
    {
      "source": "api-role",
      "target": "db-credentials-secret",
      "relationship": "can_access",
      "weight": 2.0,
      "metadata": {
        "description": "Role grants read access to db-credentials secret"
      }
    },
    {
      "source": "api-server-pod",
      "target": "prod-database",
      "relationship": "connects_to",
      "weight": 1.5,
      "metadata": {
        "description": "API server connects to production database",
        "protocol": "TCP:5432"
      }
    },
    {
      "source": "api-server-pod",
      "target": "configmap-app-config",
      "relationship": "mounts",
      "weight": 3.0,
      "metadata": {
        "description": "API server mounts application config"
      }
    },
    {
      "source": "api-server-pod",
      "target": "worker-pod-1",
      "relationship": "sends_jobs_to",
      "weight": 2.5,
      "metadata": {
        "description": "API server dispatches background jobs",
        "protocol": "AMQP"
      }
    },
    {
      "source": "api-server-pod",
      "target": "worker-pod-2",
      "relationship": "sends_jobs_to",
      "weight": 2.5,
      "metadata": {
        "description": "API server dispatches background jobs",
        "protocol": "AMQP"
      }
    },
    {
      "source": "monitoring-pod",
      "target": "monitoring-sa",
      "relationship": "uses_service_account",
      "weight": 2.0,
      "metadata": {
        "description": "Prometheus uses its service account for API discovery"
      }
    },
    {
      "source": "monitoring-sa",
      "target": "monitoring-role-binding",
      "relationship": "bound_by",
      "weight": 2.0,
      "metadata": {
        "description": "SA bound via ClusterRoleBinding"
      }
    },
    {
      "source": "monitoring-role-binding",
      "target": "monitoring-role",
      "relationship": "grants",
      "weight": 2.0,
      "metadata": {
        "description": "Binding grants prometheus-reader ClusterRole"
      }
    },
    {
      "source": "monitoring-pod",
      "target": "api-server-pod",
      "relationship": "scrapes_metrics",
      "weight": 3.0,
      "metadata": {
        "description": "Prometheus scrapes metrics from API server",
        "protocol": "HTTP:8080/metrics"
      }
    },
    {
      "source": "monitoring-pod",
      "target": "worker-pod-1",
      "relationship": "scrapes_metrics",
      "weight": 3.0,
      "metadata": {
        "description": "Prometheus scrapes metrics from worker",
        "protocol": "HTTP:9090/metrics"
      }
    },
    {
      "source": "kube-apiserver",
      "target": "etcd-pod",
      "relationship": "reads_writes",
      "weight": 1.0,
      "metadata": {
        "description": "API server reads/writes cluster state to etcd",
        "protocol": "gRPC:2379"
      }
    },
    {
      "source": "cluster-admin-role",
      "target": "kube-apiserver",
      "relationship": "full_access",
      "weight": 0.5,
      "metadata": {
        "description": "cluster-admin has full access to the Kubernetes API"
      }
    },
    {
      "source": "tesla-dashboard-pod",
      "target": "monitoring-pod",
      "relationship": "network_access",
      "weight": 2.5,
      "metadata": {
        "description": "Dashboard can reach monitoring namespace (no NetworkPolicy!)"
      }
    },
    {
      "source": "monitoring-pod",
      "target": "tesla-dashboard-pod",
      "relationship": "network_access",
      "weight": 2.5,
      "metadata": {
        "description": "Bidirectional access in monitoring namespace"
      }
    }
  ],
  "metadata": {
    "cluster_name": "prod-eks-cluster-01",
    "scan_timestamp": "2026-03-30T12:00:00Z",
    "scenario": "Tesla Breach Simulation",
    "description": "An internet-facing Kubernetes dashboard with excessive RBAC permissions leads to credential theft and database compromise."
  }
}
```

## frontend\.gitignore

```
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
```

## frontend\eslint.config.js

```javascript
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
  },
])
```

## frontend\index.html

```html
<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="KubePathAudit — Kubernetes Security Analysis Dashboard. Visualize attack paths, analyze blast radius, and identify critical nodes in your K8s cluster." />
    <title>KubePathAudit — K8s Security Analysis</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

## frontend\package.json

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "@radix-ui/react-dialog": "^1.1.15",
    "@radix-ui/react-dropdown-menu": "^2.1.16",
    "@radix-ui/react-scroll-area": "^1.2.10",
    "@radix-ui/react-select": "^2.2.6",
    "@radix-ui/react-separator": "^1.1.8",
    "@radix-ui/react-slider": "^1.3.6",
    "@radix-ui/react-slot": "^1.2.4",
    "@radix-ui/react-switch": "^1.2.6",
    "@radix-ui/react-tabs": "^1.1.13",
    "@radix-ui/react-tooltip": "^1.2.8",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "framer-motion": "^12.38.0",
    "html2pdf.js": "^0.14.0",
    "lucide-react": "^1.7.0",
    "react": "^19.2.4",
    "react-dom": "^19.2.4",
    "react-force-graph-2d": "^1.29.1",
    "tailwind-merge": "^3.5.0"
  },
  "devDependencies": {
    "@eslint/js": "^9.39.4",
    "@tailwindcss/vite": "^4.2.2",
    "@types/node": "^24.12.0",
    "@types/react": "^19.2.14",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^6.0.1",
    "eslint": "^9.39.4",
    "eslint-plugin-react-hooks": "^7.0.1",
    "eslint-plugin-react-refresh": "^0.5.2",
    "globals": "^17.4.0",
    "tailwindcss": "^4.2.2",
    "typescript": "~5.9.3",
    "typescript-eslint": "^8.57.0",
    "vite": "^8.0.1"
  }
}
```

## frontend\README.md

```markdown
# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
```

## frontend\tsconfig.app.json

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "ES2023",
    "useDefineForClassFields": true,
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "types": ["vite/client"],
    "skipLibCheck": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    },

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["src"]
}
```

## frontend\tsconfig.json

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

## frontend\tsconfig.node.json

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "ES2023",
    "lib": ["ES2023"],
    "module": "ESNext",
    "types": ["node"],
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["vite.config.ts"]
}
```

## frontend\vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

## frontend\src\App.tsx

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Moon, Sun, AlertTriangle, Activity, Database, Server,
  Lock, Wifi, WifiOff, Loader2, BarChart3, GitBranch
} from 'lucide-react';
import GraphCanvas from './components/GraphCanvas';
import SecuritySidebar from './components/SecuritySidebar';
import ControlPanel from './components/ControlPanel';
import KillChainReport from './components/KillChainReport';
import { api } from './lib/api';
import type {
  GraphNode, GraphEdge, GraphData, HighlightState,
  BlastRadiusResult, ShortestPathResult, CycleResult, CriticalNodeResult,
} from './lib/types';

function App() {
  // ── Theme ────────────────────────────────
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('kubepathaudit-theme');
    return saved ? saved === 'dark' : true;
  });
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('kubepathaudit-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // ── Graph State ──────────────────────────
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiLoading, setApiLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

  // ── UI State ─────────────────────────────
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [highlight, setHighlight] = useState<HighlightState>({
    nodes: new Set(), edges: new Set(), path: [], mode: 'none',
  });
  const [showKillChain, setShowKillChain] = useState(false);

  // ── Analysis Results ─────────────────────
  const [blastResult, setBlastResult] = useState<BlastRadiusResult | null>(null);
  const [pathResult, setPathResult] = useState<ShortestPathResult | null>(null);
  const [cycleResult, setCycleResult] = useState<CycleResult | null>(null);
  const [criticalResult, setCriticalResult] = useState<CriticalNodeResult | null>(null);

  // ── Graph container sizing ───────────────
  const graphContainerRef = useRef<HTMLDivElement>(null);
  const [graphSize, setGraphSize] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const updateSize = () => {
      if (graphContainerRef.current) {
        const rect = graphContainerRef.current.getBoundingClientRect();
        setGraphSize({ width: rect.width, height: rect.height });
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, [selectedNode]);

  // ── Load Graph ───────────────────────────
  const loadGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getGraph();
      setGraphData(data);
      setNodes(data.nodes);
      setLinks(data.links);
      setConnected(true);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend');
      setConnected(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  // ── Flash status ─────────────────────────
  const flash = (text: string, type: 'success' | 'error' | 'info') => {
    setStatusMessage({ text, type });
    setTimeout(() => setStatusMessage(null), 4000);
  };

  // ── Clear Highlights ─────────────────────
  const clearHighlight = () => {
    setHighlight({ nodes: new Set(), edges: new Set(), path: [], mode: 'none' });
    setBlastResult(null);
    setPathResult(null);
    setCycleResult(null);
    setCriticalResult(null);
  };

  // ── Algorithm Handlers ───────────────────
  const handleBlastRadius = async (source: string, hops: number) => {
    setApiLoading(true);
    try {
      const result = await api.blastRadius(source, hops);
      setBlastResult(result);

      const nodeIds = new Set(result.affected_nodes.map(n => n.id));
      const edgeIds = new Set(result.affected_edges.map(e => `${e.source}->${e.target}`));
      setHighlight({ nodes: nodeIds, edges: edgeIds, path: [], mode: 'blast-radius' });
      flash(`Blast radius: ${result.total_affected} nodes in danger zone`, result.risk_summary === 'CRITICAL' ? 'error' : 'info');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleShortestPath = async (source: string, target: string) => {
    setApiLoading(true);
    try {
      const result = await api.shortestPath(source, target);
      setPathResult(result);

      if (result.path_exists) {
        const nodeIds = new Set(result.path);
        const edgeIds = new Set<string>();
        for (let i = 0; i < result.path.length - 1; i++) {
          edgeIds.add(`${result.path[i]}->${result.path[i + 1]}`);
        }
        setHighlight({ nodes: nodeIds, edges: edgeIds, path: result.path, mode: 'shortest-path' });
        flash(`${result.difficulty} attack path found: ${result.hop_count} hops, weight ${result.total_weight}`,
          result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY' ? 'error' : 'info');
      } else {
        clearHighlight();
        flash('No attack path exists between these nodes ✓', 'success');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleDetectCycles = async () => {
    setApiLoading(true);
    try {
      const result = await api.detectCycles();
      setCycleResult(result);

      if (result.has_cycles) {
        const nodeIds = new Set<string>();
        const edgeIds = new Set<string>();
        result.cycles.forEach(c => {
          c.cycle.forEach(n => nodeIds.add(n));
          for (let i = 0; i < c.cycle.length; i++) {
            const next = c.cycle[(i + 1) % c.cycle.length];
            edgeIds.add(`${c.cycle[i]}->${next}`);
          }
        });
        setHighlight({ nodes: nodeIds, edges: edgeIds, path: [], mode: 'cycles' });
        flash(`${result.total_cycles} circular permission loop(s) detected`, 'error');
      } else {
        clearHighlight();
        flash('No circular permission loops found ✓', 'success');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleCriticalNode = async () => {
    setApiLoading(true);
    try {
      const result = await api.criticalNode();
      setCriticalResult(result);

      if (result.critical_node) {
        const nodeIds = new Set([result.critical_node.node_id]);
        setHighlight({ nodes: nodeIds, edges: new Set(), path: [], mode: 'critical-node' });
        flash(`Critical node: ${result.critical_node.label} (${result.critical_node.impact_percentage}% impact)`, 'info');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleRemediate = async (nodeId: string) => {
    setApiLoading(true);
    try {
      const result = await api.remediate(nodeId);
      const newGraph = result.updated_graph;
      setGraphData(newGraph);
      setNodes(newGraph.nodes);
      setLinks(newGraph.links);
      clearHighlight();
      setSelectedNode(null);
      setCriticalResult(null);
      flash(result.message, 'success');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleReset = async () => {
    setApiLoading(true);
    try {
      const result = await api.reset();
      setGraphData(result.graph);
      setNodes(result.graph.nodes);
      setLinks(result.graph.links);
      clearHighlight();
      setSelectedNode(null);
      flash('Graph reset to original state', 'success');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleUpload = async (file: File) => {
    setApiLoading(true);
    try {
      const result = await api.uploadGraph(file);
      setGraphData(result.graph);
      setNodes(result.graph.nodes);
      setLinks(result.graph.links);
      clearHighlight();
      setSelectedNode(null);
      flash(result.message, 'success');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
  };

  const handleFindPathToNode = (targetId: string) => {
    handleShortestPath('internet', targetId);
  };

  // ── Loading Screen ───────────────────────
  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-[#0a0f1e]' : 'bg-slate-50'}`}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center space-y-4"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <Shield className={`w-16 h-16 mx-auto ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
          </motion.div>
          <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>KubePathAudit</h1>
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Connecting to analysis engine...</p>
          <Loader2 className={`w-5 h-5 mx-auto animate-spin ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
        </motion.div>
      </div>
    );
  }

  // ── Error Screen ─────────────────────────
  if (error && !graphData) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-[#0a0f1e]' : 'bg-slate-50'}`}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4 max-w-md px-6"
        >
          <WifiOff className="w-16 h-16 mx-auto text-red-400" />
          <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Connection Failed</h1>
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{error}</p>
          <div className={`text-xs p-4 rounded-xl ${isDark ? 'bg-slate-800/50 text-slate-400' : 'bg-slate-100 text-slate-500'}`}>
            <p className="font-mono mb-2">Make sure the backend is running:</p>
            <code className={`block p-2 rounded ${isDark ? 'bg-slate-900' : 'bg-white'}`}>
              cd backend && uvicorn main:app --reload
            </code>
          </div>
          <button
            onClick={loadGraph}
            className="px-6 py-2.5 rounded-xl text-sm font-medium bg-gradient-to-r from-blue-600 to-cyan-600 text-white
              hover:from-blue-500 hover:to-cyan-500 transition-all hover:shadow-lg hover:shadow-blue-500/20"
          >
            Retry Connection
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-[#0a0f1e]' : 'bg-slate-50'}`}>

      {/* ─── Header ─────────────────────────── */}
      <header className={`shrink-0 flex items-center justify-between px-5 py-3 border-b z-40
        ${isDark ? 'bg-slate-900/80 border-slate-700/50' : 'bg-white/80 border-slate-200'}
        backdrop-blur-xl`}>
        <div className="flex items-center gap-3">
          <motion.div
            whileHover={{ rotate: 15, scale: 1.1 }}
            className="p-2 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 shadow-lg shadow-blue-500/20"
          >
            <Shield className="w-5 h-5 text-white" />
          </motion.div>
          <div>
            <h1 className={`text-lg font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
              KubePathAudit
            </h1>
            <p className={`text-[11px] ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              Kubernetes Security Analysis Dashboard
            </p>
          </div>
        </div>

        {/* Center - Stats */}
        {graphData && (
          <div className="hidden md:flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Server className={`w-3.5 h-3.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
              <span className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                {graphData.stats.total_nodes} Nodes
              </span>
            </div>
            <div className="flex items-center gap-2">
              <GitBranch className={`w-3.5 h-3.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
              <span className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                {graphData.stats.total_edges} Edges
              </span>
            </div>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              <span className="text-xs font-medium text-red-400">
                {graphData.stats.critical_nodes} Critical
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Database className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-xs font-medium text-yellow-400">
                {graphData.stats.crown_jewels} Crown Jewels
              </span>
            </div>
          </div>
        )}

        {/* Right */}
        <div className="flex items-center gap-3">
          {/* Connection status */}
          <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full status-dot ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              {connected ? 'Connected' : 'Offline'}
            </span>
          </div>

          {/* Cluster name */}
          {graphData?.metadata?.cluster_name && (
            <span className={`text-xs px-2.5 py-1 rounded-full font-mono
              ${isDark ? 'bg-slate-800 text-cyan-400 border border-slate-700' : 'bg-slate-100 text-blue-600 border border-slate-200'}`}>
              {graphData.metadata.cluster_name}
            </span>
          )}

          {/* Theme toggle */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsDark(!isDark)}
            className={`p-2 rounded-xl transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-yellow-400' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}`}
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </motion.button>
        </div>
      </header>

      {/* ─── Status Message ─────────────────── */}
      <AnimatePresence>
        {statusMessage && (
          <motion.div
            initial={{ y: -40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -40, opacity: 0 }}
            className={`absolute top-[60px] left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl shadow-lg text-xs font-medium flex items-center gap-2
              ${statusMessage.type === 'error' ? 'bg-red-500/90 text-white' :
                statusMessage.type === 'success' ? 'bg-green-500/90 text-white' :
                  'bg-blue-500/90 text-white'}
              backdrop-blur-sm`}
          >
            {statusMessage.type === 'error' && <AlertTriangle className="w-3.5 h-3.5" />}
            {statusMessage.type === 'success' && <Lock className="w-3.5 h-3.5" />}
            {statusMessage.type === 'info' && <Activity className="w-3.5 h-3.5" />}
            {statusMessage.text}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Main Layout ────────────────────── */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Panel: Controls */}
        <div className={`shrink-0 w-[320px] border-r overflow-hidden flex flex-col
          ${isDark ? 'bg-slate-900/50 border-slate-700/50' : 'bg-white border-slate-200'}`}>
          {/* Scenario Badge */}
          {graphData?.metadata?.scenario && (
            <div className={`mx-4 mt-3 px-3 py-2 rounded-xl text-xs border animate-border-pulse
              ${isDark ? 'bg-red-950/30 border-red-900/40 text-red-300' : 'bg-red-50 border-red-200 text-red-700'}`}>
              <span className="font-semibold">🎯 Active Scenario:</span> {graphData.metadata.scenario}
            </div>
          )}
          <div className="flex-1 overflow-y-auto">
            <ControlPanel
              nodes={nodes}
              onBlastRadius={handleBlastRadius}
              onShortestPath={handleShortestPath}
              onDetectCycles={handleDetectCycles}
              onCriticalNode={handleCriticalNode}
              onRemediate={handleRemediate}
              onReset={handleReset}
              onUpload={handleUpload}
              onShowKillChain={() => setShowKillChain(true)}
              criticalNodeResult={criticalResult}
              cycleResult={cycleResult}
              blastResult={blastResult}
              pathResult={pathResult}
              loading={apiLoading}
              isDark={isDark}
            />
          </div>
        </div>

        {/* Center: Graph Canvas */}
        <div
          ref={graphContainerRef}
          className={`flex-1 relative overflow-hidden cyber-grid ${isDark ? '' : ''}`}
        >
          {/* Clear highlight button */}
          <AnimatePresence>
            {highlight.mode !== 'none' && (
              <motion.button
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -20, opacity: 0 }}
                onClick={clearHighlight}
                className={`absolute top-3 left-3 z-20 px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5 transition-all
                  ${isDark ? 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 border border-slate-700' : 'bg-white/80 text-slate-600 hover:bg-white border border-slate-200'}
                  backdrop-blur-sm`}
              >
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                {highlight.mode === 'blast-radius' && 'Blast Radius Active'}
                {highlight.mode === 'shortest-path' && 'Attack Path Active'}
                {highlight.mode === 'cycles' && 'Cycles Highlighted'}
                {highlight.mode === 'critical-node' && 'Critical Node Highlighted'}
                <span className="ml-1">✕</span>
              </motion.button>
            )}
          </AnimatePresence>

          {/* Legend */}
          <div className={`absolute bottom-3 left-3 z-20 p-3 rounded-xl text-[10px] space-y-1.5
            ${isDark ? 'bg-slate-900/80 border border-slate-700/50' : 'bg-white/80 border border-slate-200'}
            backdrop-blur-sm`}>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-green-500" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Internet / Entry Point</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Critical Risk</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-yellow-500" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Crown Jewel</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-indigo-500" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Standard Entity</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-slate-500" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Low Risk / Utility</span>
            </div>
          </div>

          <GraphCanvas
            nodes={nodes}
            links={links}
            highlight={highlight}
            onNodeClick={handleNodeClick}
            width={graphSize.width}
            height={graphSize.height}
            isDark={isDark}
          />

          {/* Security Sidebar (overlays right side of graph) */}
          <SecuritySidebar
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            onBlastRadius={(nodeId) => handleBlastRadius(nodeId, 3)}
            onFindPath={handleFindPathToNode}
            isDark={isDark}
          />
        </div>
      </div>

      {/* ─── Kill Chain Report Modal ────────── */}
      <KillChainReport
        result={pathResult}
        isOpen={showKillChain}
        onClose={() => setShowKillChain(false)}
        isDark={isDark}
      />
    </div>
  );
}

export default App;
```

## frontend\src\index.css

```css
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));

@theme {
  --color-border: hsl(220 13% 91%);
  --color-input: hsl(220 13% 91%);
  --color-ring: hsl(224 76% 48%);
  --color-background: hsl(0 0% 100%);
  --color-foreground: hsl(224 71% 4%);
  --color-primary: hsl(224 76% 48%);
  --color-primary-foreground: hsl(0 0% 100%);
  --color-secondary: hsl(220 14% 96%);
  --color-secondary-foreground: hsl(224 71% 4%);
  --color-destructive: hsl(0 84% 60%);
  --color-destructive-foreground: hsl(0 0% 100%);
  --color-muted: hsl(220 14% 96%);
  --color-muted-foreground: hsl(220 9% 46%);
  --color-accent: hsl(220 14% 96%);
  --color-accent-foreground: hsl(224 71% 4%);
  --color-popover: hsl(0 0% 100%);
  --color-popover-foreground: hsl(224 71% 4%);
  --color-card: hsl(0 0% 100%);
  --color-card-foreground: hsl(224 71% 4%);
  --color-sidebar: hsl(0 0% 98%);
  --color-sidebar-foreground: hsl(240 5% 26%);
  --color-chart-1: hsl(12 76% 61%);
  --color-chart-2: hsl(173 58% 39%);
  --color-chart-3: hsl(197 37% 24%);
  --color-chart-4: hsl(43 74% 66%);
  --color-chart-5: hsl(27 87% 67%);
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;

  --color-cyber-red: hsl(0 90% 55%);
  --color-cyber-gold: hsl(45 100% 50%);
  --color-cyber-blue: hsl(210 100% 60%);
  --color-cyber-green: hsl(145 80% 45%);
  --color-cyber-purple: hsl(270 80% 60%);
  --color-cyber-cyan: hsl(185 100% 50%);
  --color-cyber-orange: hsl(25 100% 55%);
}

.dark {
  --color-border: hsl(215 20% 17%);
  --color-input: hsl(215 20% 17%);
  --color-ring: hsl(216 90% 58%);
  --color-background: hsl(222 47% 6%);
  --color-foreground: hsl(210 40% 98%);
  --color-primary: hsl(216 90% 58%);
  --color-primary-foreground: hsl(0 0% 100%);
  --color-secondary: hsl(215 20% 12%);
  --color-secondary-foreground: hsl(210 40% 98%);
  --color-destructive: hsl(0 84% 60%);
  --color-destructive-foreground: hsl(0 0% 100%);
  --color-muted: hsl(215 20% 12%);
  --color-muted-foreground: hsl(215 16% 57%);
  --color-accent: hsl(215 20% 15%);
  --color-accent-foreground: hsl(210 40% 98%);
  --color-popover: hsl(222 47% 8%);
  --color-popover-foreground: hsl(210 40% 98%);
  --color-card: hsl(222 47% 8%);
  --color-card-foreground: hsl(210 40% 98%);
  --color-sidebar: hsl(222 47% 7%);
  --color-sidebar-foreground: hsl(215 16% 70%);
}

/* ─── Base Styles ───────────────────────────── */
@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground antialiased;
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  }
}

/* ─── Scrollbar Styles ──────────────────────── */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: hsl(215 20% 30%);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: hsl(215 20% 40%);
}

/* ─── Cyber Glow Effects ────────────────────── */
.glow-blue {
  box-shadow: 0 0 15px hsl(216 90% 58% / 0.3), 0 0 45px hsl(216 90% 58% / 0.1);
}

.glow-red {
  box-shadow: 0 0 15px hsl(0 90% 55% / 0.3), 0 0 45px hsl(0 90% 55% / 0.1);
}

.glow-gold {
  box-shadow: 0 0 15px hsl(45 100% 50% / 0.3), 0 0 45px hsl(45 100% 50% / 0.1);
}

.glow-green {
  box-shadow: 0 0 15px hsl(145 80% 45% / 0.3), 0 0 45px hsl(145 80% 45% / 0.1);
}

.glow-cyan {
  box-shadow: 0 0 15px hsl(185 100% 50% / 0.3), 0 0 45px hsl(185 100% 50% / 0.1);
}

/* ─── Pulse Animation ───────────────────────── */
@keyframes pulse-glow {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }
}

.animate-pulse-glow {
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes scan-line {
  0% {
    transform: translateY(-100%);
  }

  100% {
    transform: translateY(100vh);
  }
}

.scan-line {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, hsl(216 90% 58% / 0.4), transparent);
  animation: scan-line 4s linear infinite;
  pointer-events: none;
  z-index: 9999;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out forwards;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }

  100% {
    background-position: 200% 0;
  }
}

.animate-shimmer {
  background: linear-gradient(90deg, transparent 0%, hsl(216 90% 58% / 0.08) 50%, transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes border-pulse {

  0%,
  100% {
    border-color: hsl(216 90% 58% / 0.3);
  }

  50% {
    border-color: hsl(216 90% 58% / 0.7);
  }
}

.animate-border-pulse {
  animation: border-pulse 2s ease-in-out infinite;
}

/* ─── Glassmorphism ─────────────────────────── */
.glass {
  background: hsl(222 47% 8% / 0.6);
  backdrop-filter: blur(16px);
  border: 1px solid hsl(215 20% 17% / 0.5);
}

:where(:not(.dark)) .glass {
  background: hsl(0 0% 100% / 0.7);
  border: 1px solid hsl(220 13% 91% / 0.8);
}

/* ─── Grid Background ──────────────────────── */
.cyber-grid {
  background-image:
    linear-gradient(hsl(216 90% 58% / 0.03) 1px, transparent 1px),
    linear-gradient(90deg, hsl(216 90% 58% / 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

:where(:not(.dark)) .cyber-grid {
  background-image:
    linear-gradient(hsl(224 76% 48% / 0.05) 1px, transparent 1px),
    linear-gradient(90deg, hsl(224 76% 48% / 0.05) 1px, transparent 1px);
}

/* ─── Graph Canvas ──────────────────────────── */
.graph-container canvas {
  border-radius: 0.75rem;
}

/* ─── Kill chain step connector ─────────────── */
.kill-chain-step::after {
  content: '';
  position: absolute;
  left: 1.25rem;
  bottom: -1.5rem;
  width: 2px;
  height: 1.5rem;
  background: linear-gradient(to bottom, hsl(0 90% 55%), transparent);
}

.kill-chain-step:last-child::after {
  display: none;
}

/* ─── Status dot animation ──────────────────── */
@keyframes dot-blink {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.3;
  }
}

.status-dot {
  animation: dot-blink 1.5s ease-in-out infinite;
}

/* ─── Tooltip ───────────────────────────────── */
.cyber-tooltip {
  background: hsl(222 47% 10%);
  color: hsl(210 40% 98%);
  border: 1px solid hsl(216 90% 58% / 0.3);
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  box-shadow: 0 4px 20px hsl(0 0% 0% / 0.3);
}

/* ─── Loading skeleton ──────────────────────── */
@keyframes skeleton-loading {
  0% {
    background-position: -200% 0;
  }

  100% {
    background-position: 200% 0;
  }
}

.skeleton {
  background: linear-gradient(90deg, hsl(215 20% 12%) 0%, hsl(215 20% 18%) 50%, hsl(215 20% 12%) 100%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: 0.375rem;
}

/* ─── Print Styles for PDF Export ───────────── */
@media print {
  @page {
    margin: 10mm;
    size: auto;
  }

  body * {
    visibility: hidden;
  }

  .printable-report,
  .printable-report * {
    visibility: visible;
  }

  .printable-report {
    position: absolute;
    left: 0;
    top: 0;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  .no-print,
  .no-print * {
    display: none !important;
  }

  /* Force background colors to print */
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
```

## frontend\src\main.tsx

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

## frontend\src\types.d.ts

```typescript
declare module 'html2pdf.js' {
  interface Html2PdfOptions {
    margin?: number | number[];
    filename?: string;
    image?: { type?: string; quality?: number };
    html2canvas?: { scale?: number; backgroundColor?: string };
    jsPDF?: { unit?: string; format?: string; orientation?: string };
  }

  interface Html2PdfInstance {
    set(options: Html2PdfOptions): Html2PdfInstance;
    from(element: HTMLElement): Html2PdfInstance;
    save(): Promise<void>;
  }

  function html2pdf(): Html2PdfInstance;
  export default html2pdf;
}

declare module 'react-force-graph-2d' {
  import { Component, RefObject } from 'react';
  
  export interface ForceGraphMethods {
    d3Force(forceName: string, force?: any): any;
    centerAt(x?: number, y?: number, ms?: number): void;
    zoom(amount: number, ms?: number): void;
    zoomToFit(ms?: number, padding?: number): void;
    screen2GraphCoords(x: number, y: number): { x: number; y: number };
    graph2ScreenCoords(x: number, y: number): { x: number; y: number };
  }
  
  const ForceGraph2D: React.ForwardRefExoticComponent<any & React.RefAttributes<ForceGraphMethods>>;
  export default ForceGraph2D;
  export type { ForceGraphMethods };
}
```

## frontend\src\components\ControlPanel.tsx

```typescript
import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crosshair, Route, RefreshCcw, AlertTriangle, Search, Trash2,
  Upload, Zap, RotateCcw, ChevronDown, ChevronUp, Loader2, Shield,
  TrendingUp, Target, Info
} from 'lucide-react';
import type { GraphNode, CriticalNodeResult, CycleResult, BlastRadiusResult, ShortestPathResult } from '@/lib/types';

interface Props {
  nodes: GraphNode[];
  onBlastRadius: (source: string, hops: number) => Promise<void>;
  onShortestPath: (source: string, target: string) => Promise<void>;
  onDetectCycles: () => Promise<void>;
  onCriticalNode: () => Promise<void>;
  onRemediate: (nodeId: string) => void;
  onReset: () => void;
  onUpload: (file: File) => void;
  onShowKillChain: () => void;
  criticalNodeResult: CriticalNodeResult | null;
  cycleResult: CycleResult | null;
  blastResult: BlastRadiusResult | null;
  pathResult: ShortestPathResult | null;
  loading: boolean;
  isDark: boolean;
}

export default function ControlPanel({
  nodes, onBlastRadius, onShortestPath, onDetectCycles, onCriticalNode,
  onRemediate, onReset, onUpload, onShowKillChain,
  criticalNodeResult, cycleResult, blastResult, pathResult,
  loading, isDark,
}: Props) {
  const [blastSource, setBlastSource] = useState('');
  const [blastHops, setBlastHops] = useState(3);
  const [pathSource, setPathSource] = useState('internet');
  const [pathTarget, setPathTarget] = useState('prod-database');
  const [expanded, setExpanded] = useState<string | null>('blast');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sectionClass = `rounded-xl border transition-all duration-300 overflow-hidden
    ${isDark ? 'bg-slate-900/50 border-slate-700/50 hover:border-slate-600/50' : 'bg-white border-slate-200 hover:border-slate-300'}`;
  const headerClass = `flex items-center justify-between w-full px-4 py-3 cursor-pointer transition-colors
    ${isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}`;
  const labelClass = `text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`;
  const selectClass = `w-full px-3 py-2 rounded-lg text-sm border transition-colors
    ${isDark
      ? 'bg-slate-800 border-slate-700 text-slate-200 focus:border-blue-500'
      : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500'} 
    outline-none focus:ring-1 focus:ring-blue-500/30`;

  const toggle = (id: string) => setExpanded(prev => prev === id ? null : id);

  return (
    <div className="space-y-3 p-4 overflow-y-auto h-full">
      {/* Title */}
      <div className="flex items-center justify-between mb-2">
        <h2 className={`text-sm font-bold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
          ⚡ Analysis Tools
        </h2>
        <div className="flex gap-1.5">
          <button
            onClick={() => fileInputRef.current?.click()}
            className={`p-2 rounded-lg text-xs transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}`}
            title="Upload Custom Graph"
          >
            <Upload className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onReset}
            className={`p-2 rounded-lg text-xs transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}`}
            title="Reset Graph"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onUpload(f);
            e.target.value = '';
          }}
        />
      </div>

      {/* 1. Blast Radius */}
      <div className={sectionClass}>
        <button onClick={() => toggle('blast')} className={headerClass}>
          <span className="flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-red-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Blast Radius (BFS)</span>
          </span>
          {expanded === 'blast' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'blast' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Find all nodes reachable within N hops from a compromised node.
              </p>
              <div>
                <label className={labelClass}>Source Node</label>
                <select value={blastSource} onChange={e => setBlastSource(e.target.value)} className={selectClass}>
                  <option value="">Select a node...</option>
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>{n.label} ({n.type})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>Max Hops: {blastHops}</label>
                <input
                  type="range"
                  min={1}
                  max={8}
                  value={blastHops}
                  onChange={e => setBlastHops(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-slate-700 accent-red-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
                  <span>1</span><span>4</span><span>8</span>
                </div>
              </div>
              <button
                disabled={!blastSource || loading}
                onClick={() => onBlastRadius(blastSource, blastHops)}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-red-600 to-orange-600 text-white
                  hover:from-red-500 hover:to-orange-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-red-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Analyze Blast Radius'}
              </button>
              {/* Result */}
              {blastResult && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2
                    ${blastResult.risk_summary === 'CRITICAL' ? (isDark ? 'bg-red-950/30 border-red-900/40' : 'bg-red-50 border-red-200') : (isDark ? 'bg-amber-950/30 border-amber-900/40' : 'bg-amber-50 border-amber-200')}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-bold ${blastResult.risk_summary === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}`}>
                      {blastResult.risk_summary} RISK
                    </span>
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>{blastResult.total_affected} nodes affected</span>
                  </div>
                  {blastResult.crown_jewels_reached > 0 && (
                    <p className="text-red-400">
                      ⚠️ {blastResult.crown_jewels_reached} Crown Jewel(s) reachable: {blastResult.crown_jewel_names.join(', ')}
                    </p>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 2. Shortest Attack Path */}
      <div className={sectionClass}>
        <button onClick={() => toggle('path')} className={headerClass}>
          <span className="flex items-center gap-2">
            <Route className="w-4 h-4 text-blue-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Attack Path (Dijkstra)</span>
          </span>
          {expanded === 'path' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'path' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Find the easiest attack path using CVSS-weighted edges.
              </p>
              <div>
                <label className={labelClass}>Source (Attacker Entry)</label>
                <select value={pathSource} onChange={e => setPathSource(e.target.value)} className={selectClass}>
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>{n.label} ({n.type})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass}>Target (Crown Jewel)</label>
                <select value={pathTarget} onChange={e => setPathTarget(e.target.value)} className={selectClass}>
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>{n.label} ({n.type})</option>
                  ))}
                </select>
              </div>
              <button
                disabled={!pathSource || !pathTarget || loading}
                onClick={() => onShortestPath(pathSource, pathTarget)}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-blue-600 to-cyan-600 text-white
                  hover:from-blue-500 hover:to-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-blue-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Find Shortest Path'}
              </button>
              {pathResult && pathResult.path_exists && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2 ${isDark ? 'bg-blue-950/30 border-blue-900/40' : 'bg-blue-50 border-blue-200'}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-bold ${pathResult.difficulty === 'TRIVIAL' || pathResult.difficulty === 'EASY' ? 'text-red-400' : 'text-blue-400'}`}>
                      {pathResult.difficulty} Attack
                    </span>
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>
                      {pathResult.hop_count} hops • Weight: {pathResult.total_weight}
                    </span>
                  </div>
                  <div className={`flex flex-wrap items-center gap-1 ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                    {pathResult.path.map((p, i) => (
                      <span key={p} className="flex items-center gap-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`}>{p}</span>
                        {i < pathResult.path.length - 1 && <span className="text-red-400">→</span>}
                      </span>
                    ))}
                  </div>
                  <button
                    onClick={onShowKillChain}
                    className="w-full mt-2 py-2 rounded-lg text-xs font-medium transition-all
                      bg-gradient-to-r from-purple-600 to-pink-600 text-white
                      hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/20"
                  >
                    📋 View Kill Chain Report
                  </button>
                </motion.div>
              )}
              {pathResult && !pathResult.path_exists && (
                <motion.div initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs ${isDark ? 'bg-green-950/30 border-green-900/40 text-green-400' : 'bg-green-50 border-green-200 text-green-700'}`}>
                  ✅ No attack path exists between these nodes.
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 3. Cycle Detection */}
      <div className={sectionClass}>
        <button onClick={() => toggle('cycles')} className={headerClass}>
          <span className="flex items-center gap-2">
            <RefreshCcw className="w-4 h-4 text-amber-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Cycle Detection (DFS)</span>
          </span>
          {expanded === 'cycles' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'cycles' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Detect circular permission loops in the RBAC graph.
              </p>
              <button
                disabled={loading}
                onClick={onDetectCycles}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-amber-600 to-yellow-600 text-white
                  hover:from-amber-500 hover:to-yellow-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-amber-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Detect Cycles'}
              </button>
              {cycleResult && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2 ${cycleResult.has_cycles ? (isDark ? 'bg-amber-950/30 border-amber-900/40' : 'bg-amber-50 border-amber-200') : (isDark ? 'bg-green-950/30 border-green-900/40' : 'bg-green-50 border-green-200')}`}
                >
                  {cycleResult.has_cycles ? (
                    <>
                      <span className="font-bold text-amber-400">⚠️ {cycleResult.total_cycles} cycle(s) found</span>
                      {cycleResult.cycles.map((c, i) => (
                        <div key={i} className={`p-2 rounded text-[11px] ${isDark ? 'bg-slate-800/50' : 'bg-slate-100'}`}>
                          <span className={`font-medium ${c.risk === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}`}>[{c.risk}]</span>{' '}
                          <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>{c.description}</span>
                        </div>
                      ))}
                    </>
                  ) : (
                    <span className="text-green-400">✅ No circular permission loops detected.</span>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 4. Critical Node */}
      <div className={sectionClass}>
        <button onClick={() => toggle('critical')} className={headerClass}>
          <span className="flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Critical Node Analysis</span>
          </span>
          {expanded === 'critical' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'critical' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Find the single node whose removal breaks the most attack paths.
              </p>
              <button
                disabled={loading}
                onClick={onCriticalNode}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-purple-600 to-violet-600 text-white
                  hover:from-purple-500 hover:to-violet-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-purple-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Identify Critical Node'}
              </button>
              {criticalNodeResult?.critical_node && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`space-y-3`}
                >
                  <div className={`p-3 rounded-lg border text-xs space-y-2 ${isDark ? 'bg-purple-950/30 border-purple-900/40' : 'bg-purple-50 border-purple-200'}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-purple-400">🎯 {criticalNodeResult.critical_node.label}</span>
                      <span className={`font-bold ${criticalNodeResult.critical_node.impact_percentage > 50 ? 'text-red-400' : 'text-amber-400'}`}>
                        {criticalNodeResult.critical_node.impact_percentage}% Impact
                      </span>
                    </div>
                    <p className={isDark ? 'text-slate-400' : 'text-slate-500'}>
                      Removing this node breaks {criticalNodeResult.critical_node.paths_broken}/{criticalNodeResult.baseline_paths} attack paths
                    </p>
                    <p className={isDark ? 'text-slate-300' : 'text-slate-600'}>
                      💡 {criticalNodeResult.recommendation}
                    </p>
                  </div>

                  {/* Top 5 */}
                  <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
                    <span className={`text-xs font-semibold ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Top Remediation Targets</span>
                    {criticalNodeResult.top_5_nodes.map((n, i) => (
                      <div key={n.node_id} className={`flex items-center justify-between py-1.5 text-xs ${i > 0 ? (isDark ? 'border-t border-slate-700/50' : 'border-t border-slate-200') : 'mt-1'}`}>
                        <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>
                          {i + 1}. {n.label}
                        </span>
                        <div className="flex items-center gap-2">
                          <div className={`w-16 h-1.5 rounded-full overflow-hidden ${isDark ? 'bg-slate-700' : 'bg-slate-200'}`}>
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-purple-500 to-red-500"
                              style={{ width: `${n.impact_percentage}%` }}
                            />
                          </div>
                          <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>{n.impact_percentage}%</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Remediate Button */}
                  <button
                    onClick={() => onRemediate(criticalNodeResult.critical_node!.node_id)}
                    className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                      bg-gradient-to-r from-green-600 to-emerald-600 text-white
                      hover:from-green-500 hover:to-emerald-500
                      hover:shadow-lg hover:shadow-green-500/20 active:scale-[0.98]
                      flex items-center justify-center gap-2"
                  >
                    <Shield className="w-4 h-4" />
                    Remediate: Remove {criticalNodeResult.critical_node.label}
                  </button>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
```

## frontend\src\components\GraphCanvas.tsx

```typescript
import { useCallback, useRef, useEffect, useMemo } from 'react';
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d';
import type { GraphNode, GraphEdge, HighlightState } from '@/lib/types';

interface Props {
  nodes: GraphNode[];
  links: GraphEdge[];
  highlight: HighlightState;
  onNodeClick: (node: GraphNode) => void;
  width: number;
  height: number;
  isDark: boolean;
}

const NODE_COLORS: Record<string, string> = {
  internet: '#22c55e',
  ingress: '#3b82f6',
  pod: '#6366f1',
  service: '#8b5cf6',
  serviceaccount: '#06b6d4',
  rolebinding: '#f59e0b',
  role: '#f59e0b',
  clusterrole: '#ef4444',
  secret: '#eab308',
  database: '#eab308',
  configmap: '#64748b',
  networkpolicy: '#64748b',
  namespace: '#94a3b8',
};

const RISK_COLORS: Record<string, string> = {
  'crown-jewel': '#eab308',
  'critical': '#ef4444',
  'high': '#f97316',
  'medium': '#f59e0b',
  'low': '#22c55e',
  'entry-point': '#22c55e',
  'info': '#64748b',
};

const NODE_ICONS: Record<string, string> = {
  internet: '🌐',
  ingress: '🔀',
  pod: '📦',
  service: '🔌',
  serviceaccount: '👤',
  rolebinding: '🔗',
  role: '🛡️',
  clusterrole: '⚔️',
  secret: '🔑',
  database: '🗄️',
  configmap: '📋',
  networkpolicy: '🚧',
};

export default function GraphCanvas({ nodes, links, highlight, onNodeClick, width, height, isDark }: Props) {
  const fgRef = useRef<ForceGraphMethods | undefined>();

  const graphData = useMemo(() => {
    return {
      nodes: nodes.map(n => ({ ...n })),
      links: links.map(l => ({ ...l })),
    };
  }, [nodes, links]);

  useEffect(() => {
    const fg = fgRef.current;
    if (fg) {
      fg.d3Force('charge')?.strength(-300);
      fg.d3Force('link')?.distance(80);
    }
  }, [graphData]);

  const getNodeColor = useCallback((node: GraphNode) => {
    if (highlight.nodes.size > 0) {
      if (highlight.nodes.has(node.id)) {
        if (highlight.path.includes(node.id)) {
          return '#ef4444';
        }
        return RISK_COLORS[node.risk_level] || NODE_COLORS[node.type] || '#6366f1';
      }
      return isDark ? '#1e293b' : '#cbd5e1';
    }
    return RISK_COLORS[node.risk_level] || NODE_COLORS[node.type] || '#6366f1';
  }, [highlight, isDark]);

  const getNodeSize = useCallback((node: GraphNode) => {
    const baseSize = node.type === 'internet' ? 10 :
      node.risk_level === 'crown-jewel' ? 9 :
        node.risk_level === 'critical' ? 8 :
          node.type === 'pod' ? 7 : 6;

    if (highlight.nodes.size > 0 && highlight.nodes.has(node.id)) {
      return baseSize * 1.4;
    }
    if (highlight.nodes.size > 0 && !highlight.nodes.has(node.id)) {
      return baseSize * 0.6;
    }
    return baseSize;
  }, [highlight]);

  const paintNode = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const size = getNodeSize(node);
    const color = getNodeColor(node);
    const x = node.x ?? 0;
    const y = node.y ?? 0;
    const isHighlighted = highlight.nodes.size === 0 || highlight.nodes.has(node.id);
    const isOnPath = highlight.path.includes(node.id);

    // Outer glow for highlighted / critical nodes
    if (isHighlighted && (node.risk_level === 'critical' || node.risk_level === 'crown-jewel' || isOnPath)) {
      const glowSize = size + 4;
      const gradient = ctx.createRadialGradient(x, y, size * 0.5, x, y, glowSize);
      gradient.addColorStop(0, color + '60');
      gradient.addColorStop(1, color + '00');
      ctx.beginPath();
      ctx.arc(x, y, glowSize, 0, 2 * Math.PI);
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // Main node circle
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI);
    ctx.fillStyle = isHighlighted ? color : (isDark ? '#1e293b' : '#e2e8f0');
    ctx.fill();

    // Border
    ctx.strokeStyle = isHighlighted ? color : (isDark ? '#334155' : '#94a3b8');
    ctx.lineWidth = isOnPath ? 2 : 1;
    ctx.stroke();

    // Icon (if zoomed in enough)
    if (globalScale > 0.8) {
      const icon = NODE_ICONS[node.type] || '⚪';
      ctx.font = `${Math.max(size * 0.9, 6)}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(icon, x, y);
    }

    // Label (if zoomed in)
    if (globalScale > 1.2) {
      ctx.font = `${Math.max(11 / globalScale, 3)}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isHighlighted
        ? (isDark ? '#f1f5f9' : '#1e293b')
        : (isDark ? '#475569' : '#94a3b8');
      ctx.fillText(node.label || node.id, x, y + size + 3);
    }
  }, [getNodeColor, getNodeSize, highlight, isDark]);

  const getLinkColor = useCallback((link: { source: GraphNode | string; target: GraphNode | string }) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
    const targetId = typeof link.target === 'string' ? link.target : link.target.id;
    const edgeKey = `${sourceId}->${targetId}`;

    if (highlight.edges.size > 0 && highlight.edges.has(edgeKey)) {
      return '#ef4444';
    }
    if (highlight.nodes.size > 0) {
      if (highlight.nodes.has(sourceId) && highlight.nodes.has(targetId)) {
        return isDark ? 'rgba(99,102,241,0.5)' : 'rgba(99,102,241,0.4)';
      }
      return isDark ? 'rgba(30,41,59,0.3)' : 'rgba(203,213,225,0.3)';
    }
    return isDark ? 'rgba(71,85,105,0.4)' : 'rgba(148,163,184,0.3)';
  }, [highlight, isDark]);

  const getLinkWidth = useCallback((link: { source: GraphNode | string; target: GraphNode | string }) => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
    const targetId = typeof link.target === 'string' ? link.target : link.target.id;
    const edgeKey = `${sourceId}->${targetId}`;
    if (highlight.edges.size > 0 && highlight.edges.has(edgeKey)) {
      return 3;
    }
    return 1;
  }, [highlight]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    onNodeClick(node);
    const fg = fgRef.current;
    if (fg) {
      fg.centerAt(node.x, node.y, 600);
      fg.zoom(2.5, 600);
    }
  }, [onNodeClick]);

  return (
    <div className="graph-container relative w-full h-full">
      <ForceGraph2D
        ref={fgRef as any}
        graphData={graphData}
        width={width}
        height={height}
        nodeCanvasObject={paintNode as any}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          const size = getNodeSize(node);
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, size + 2, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        linkColor={getLinkColor as any}
        linkWidth={getLinkWidth as any}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={0.85}
        linkDirectionalParticles={(link: any) => {
          const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
          const targetId = typeof link.target === 'string' ? link.target : link.target.id;
          const edgeKey = `${sourceId}->${targetId}`;
          return highlight.edges.has(edgeKey) ? 3 : 0;
        }}
        linkDirectionalParticleSpeed={0.006}
        linkDirectionalParticleWidth={3}
        linkDirectionalParticleColor={() => '#ef4444'}
        linkCurvature={0.1}
        onNodeClick={handleNodeClick as any}
        backgroundColor={isDark ? '#0a0f1e' : '#f8fafc'}
        cooldownTicks={100}
        onEngineStop={() => fgRef.current?.zoomToFit(400, 40)}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.3}
        maxZoom={8}
      />
      {/* Zoom hints */}
      <div className={`absolute bottom-3 right-3 text-xs px-3 py-1.5 rounded-full
        ${isDark ? 'bg-slate-800/80 text-slate-400' : 'bg-white/80 text-slate-500'} 
        backdrop-blur-sm border ${isDark ? 'border-slate-700/50' : 'border-slate-200'}`}>
        Scroll to zoom • Drag to pan • Click nodes
      </div>
    </div>
  );
}
```

## frontend\src\components\KillChainReport.tsx

```typescript
import { useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, FileText, AlertTriangle, ArrowRight, Shield, ChevronRight } from 'lucide-react';
import type { ShortestPathResult } from '@/lib/types';

interface Props {
  result: ShortestPathResult | null;
  isOpen: boolean;
  onClose: () => void;
  isDark: boolean;
}

const STEP_COLORS: Record<string, string> = {
  'crown-jewel': 'from-yellow-500 to-amber-600',
  'critical': 'from-red-500 to-rose-600',
  'high': 'from-orange-500 to-red-500',
  'medium': 'from-amber-500 to-orange-500',
  'low': 'from-green-500 to-emerald-500',
  'entry-point': 'from-green-500 to-teal-500',
  'info': 'from-slate-500 to-slate-600',
};

export default function KillChainReport({ result, isOpen, onClose, isDark }: Props) {
  const reportRef = useRef<HTMLDivElement>(null);

  if (!result || !isOpen) return null;

  const handleExportPDF = async () => {
    try {
      const res = await fetch('/api/export-pdf', { method: 'POST' });
      if (!res.ok) throw new Error('PDF generation failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KubePathAudit_KillChain_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF export failed:', err);
      alert('Failed to generate PDF. Make sure the backend is running.');
    }
  };

  const chain = result.kill_chain_summary || [];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ y: 40, opacity: 0, scale: 0.95 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: 40, opacity: 0, scale: 0.95 }}
          transition={{ type: 'spring', damping: 25 }}
          className={`relative z-10 flex flex-col w-full max-w-2xl max-h-[85vh] rounded-2xl shadow-2xl
            ${isDark ? 'bg-slate-900 border border-slate-700/50' : 'bg-white border border-slate-200'}
            shadow-black/30`}
        >
          {/* Header */}
          <div className={`shrink-0 z-20 flex items-center justify-between px-6 py-4 border-b rounded-t-2xl
            ${isDark ? 'bg-slate-900/95 border-slate-700/50' : 'bg-white/95 border-slate-200'}`}>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-red-500 to-orange-500">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Kill Chain Report</h2>
                <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Attack Path Analysis — {new Date().toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 no-print">
              <button
                onClick={handleExportPDF}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                  bg-gradient-to-r from-blue-600 to-cyan-600 text-white
                  hover:from-blue-500 hover:to-cyan-500 hover:shadow-lg hover:shadow-blue-500/20"
              >
                <Download className="w-3.5 h-3.5" />
                Export PDF
              </button>
              <button
                onClick={onClose}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Report Content - Scrolling Area */}
          <div className="flex-1 overflow-y-auto printable-report">
            <div ref={reportRef} className="p-6">
            {/* Summary Banner */}
            <div className={`p-4 rounded-xl mb-6 border
              ${result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY'
                ? (isDark ? 'bg-red-950/40 border-red-900/50' : 'bg-red-50 border-red-200')
                : (isDark ? 'bg-amber-950/40 border-amber-900/50' : 'bg-amber-50 border-amber-200')
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className={`w-5 h-5 ${result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY' ? 'text-red-400' : 'text-amber-400'}`} />
                <span className={`text-sm font-bold ${result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY' ? 'text-red-400' : 'text-amber-400'}`}>
                  {result.difficulty} Attack Path Detected
                </span>
              </div>
              <div className={`grid grid-cols-3 gap-4 mt-3 text-center`}>
                <div>
                  <p className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{result.hop_count}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Total Hops</p>
                </div>
                <div>
                  <p className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{result.total_weight}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>CVSS Weight</p>
                </div>
                <div>
                  <p className={`text-2xl font-bold ${
                    result.difficulty === 'TRIVIAL' ? 'text-red-400' :
                    result.difficulty === 'EASY' ? 'text-orange-400' :
                    result.difficulty === 'MODERATE' ? 'text-amber-400' : 'text-green-400'
                  }`}>{result.difficulty}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Difficulty</p>
                </div>
              </div>
            </div>

            {/* Path Overview */}
            <div className="mb-6">
              <h3 className={`text-sm font-bold mb-3 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Attack Path Overview
              </h3>
              <div className="flex flex-wrap items-center gap-1.5">
                {result.path.map((nodeId, i) => (
                  <span key={nodeId} className="flex items-center gap-1.5">
                    <span className={`px-2 py-1 rounded-md text-xs font-mono font-medium
                      ${isDark ? 'bg-slate-800 text-slate-200 border border-slate-700' : 'bg-slate-100 text-slate-700 border border-slate-200'}`}>
                      {nodeId}
                    </span>
                    {i < result.path.length - 1 && (
                      <ArrowRight className="w-3.5 h-3.5 text-red-400 shrink-0" />
                    )}
                  </span>
                ))}
              </div>
            </div>

            {/* Kill Chain Steps */}
            <div>
              <h3 className={`text-sm font-bold mb-4 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Detailed Kill Chain
              </h3>
              <div className="space-y-4">
                {chain.map((step, i) => {
                  const gradient = STEP_COLORS[step.risk_level] || STEP_COLORS.info;
                  return (
                    <motion.div
                      key={step.step}
                      initial={{ x: -30, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: i * 0.08 }}
                      className="relative"
                    >
                      <div className={`flex gap-4 p-4 rounded-xl border transition-all
                        ${isDark ? 'bg-slate-800/50 border-slate-700/50 hover:bg-slate-800' : 'bg-slate-50 border-slate-200 hover:bg-white'}`}>
                        {/* Step Number */}
                        <div className={`shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br ${gradient}
                          flex items-center justify-center text-white font-bold text-sm shadow-lg`}>
                          {step.step}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-slate-900'}`}>
                              {step.node}
                            </span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium uppercase
                              ${isDark ? 'bg-slate-700 text-slate-300' : 'bg-slate-200 text-slate-600'}`}>
                              {step.node_type}
                            </span>
                          </div>
                          <p className={`text-xs mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                            {step.action}
                          </p>
                          <div className="flex flex-wrap items-center gap-2">
                            {step.cves_exploited.length > 0 && step.cves_exploited.map(cve => (
                              <span key={cve} className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-red-500/20 text-red-400">
                                {cve}
                              </span>
                            ))}
                            {step.edge_info && step.edge_info !== '—' && (
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${isDark ? 'bg-slate-700 text-slate-400' : 'bg-slate-200 text-slate-500'}`}>
                                → {step.edge_info}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Connector */}
                      {i < chain.length - 1 && (
                        <div className="absolute left-[2.15rem] top-[3.5rem] w-0.5 h-4 bg-gradient-to-b from-red-500/50 to-transparent" />
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Footer */}
            <div className={`mt-6 pt-4 border-t text-center ${isDark ? 'border-slate-700/50' : 'border-slate-200'}`}>
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Generated by KubePathAudit • {new Date().toLocaleString()} • Confidential
              </p>
            </div>
          </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
```

## frontend\src\components\SecuritySidebar.tsx

```typescript
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, AlertTriangle, Database, Key, Server, Globe, Link2, User,
  Cpu, Activity, HardDrive, FileText, ShieldOff, ShieldAlert, Network, Monitor,
  X, Crosshair, Route, ChevronRight
} from 'lucide-react';
import type { GraphNode } from '@/lib/types';

interface Props {
  node: GraphNode | null;
  onClose: () => void;
  onBlastRadius: (nodeId: string) => void;
  onFindPath: (target: string) => void;
  isDark: boolean;
}

const ICON_MAP: Record<string, React.ReactNode> = {
  globe: <Globe className="w-5 h-5" />,
  network: <Network className="w-5 h-5" />,
  monitor: <Monitor className="w-5 h-5" />,
  server: <Server className="w-5 h-5" />,
  'user-check': <User className="w-5 h-5" />,
  user: <User className="w-5 h-5" />,
  link: <Link2 className="w-5 h-5" />,
  shield: <Shield className="w-5 h-5" />,
  'shield-alert': <ShieldAlert className="w-5 h-5" />,
  'shield-off': <ShieldOff className="w-5 h-5" />,
  key: <Key className="w-5 h-5" />,
  database: <Database className="w-5 h-5" />,
  cpu: <Cpu className="w-5 h-5" />,
  activity: <Activity className="w-5 h-5" />,
  'hard-drive': <HardDrive className="w-5 h-5" />,
  'file-text': <FileText className="w-5 h-5" />,
};

const RISK_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  'crown-jewel': { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: '👑 Crown Jewel' },
  'critical': { bg: 'bg-red-500/20', text: 'text-red-400', label: '🔴 Critical' },
  'high': { bg: 'bg-orange-500/20', text: 'text-orange-400', label: '🟠 High' },
  'medium': { bg: 'bg-amber-500/20', text: 'text-amber-400', label: '🟡 Medium' },
  'low': { bg: 'bg-green-500/20', text: 'text-green-400', label: '🟢 Low' },
  'entry-point': { bg: 'bg-green-500/20', text: 'text-green-400', label: '🌐 Entry Point' },
  'info': { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'ℹ️ Info' },
};

export default function SecuritySidebar({ node, onClose, onBlastRadius, onFindPath, isDark }: Props) {
  if (!node) return null;

  const risk = RISK_BADGE[node.risk_level] || RISK_BADGE.info;
  const icon = ICON_MAP[node.metadata?.icon || ''] || <Server className="w-5 h-5" />;
  const cves = node.metadata?.cves || [];
  const cvssScores = node.metadata?.cvss_scores || [];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ x: 400, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 400, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className={`absolute top-0 right-0 w-[380px] h-full z-30 overflow-y-auto
          ${isDark 
            ? 'bg-slate-900/95 border-l border-slate-700/50' 
            : 'bg-white/95 border-l border-slate-200'}
          backdrop-blur-xl`}
      >
        {/* Header */}
        <div className={`sticky top-0 z-10 px-5 py-4 border-b backdrop-blur-xl
          ${isDark ? 'border-slate-700/50 bg-slate-900/90' : 'border-slate-200 bg-white/90'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${isDark ? 'bg-slate-800' : 'bg-slate-100'}
                ${node.risk_level === 'critical' ? 'glow-red' : node.risk_level === 'crown-jewel' ? 'glow-gold' : ''}`}>
                {icon}
              </div>
              <div>
                <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                  {node.label}
                </h3>
                <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  {node.type.toUpperCase()}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="px-5 py-4 space-y-5">
          {/* Risk Badge */}
          <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className={`inline-flex px-3 py-1.5 rounded-full text-xs font-medium ${risk.bg} ${risk.text}`}>
            {risk.label}
          </motion.div>

          {/* Description */}
          {node.metadata?.description && (
            <div>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Description
              </h4>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                {node.metadata.description}
              </p>
            </div>
          )}

          {/* Properties */}
          <div className={`grid grid-cols-2 gap-3 p-3 rounded-xl ${isDark ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
            <div>
              <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Namespace</span>
              <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.namespace}</p>
            </div>
            <div>
              <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Type</span>
              <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.type}</p>
            </div>
            {node.metadata?.image && (
              <div className="col-span-2">
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Image</span>
                <p className={`text-xs font-mono break-all ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>{node.metadata.image}</p>
              </div>
            )}
            {node.metadata?.version && (
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Version</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.metadata.version}</p>
              </div>
            )}
            {node.metadata?.ports && node.metadata.ports.length > 0 && (
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Ports</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.metadata.ports.join(', ')}</p>
              </div>
            )}
            {node.metadata?.engine && (
              <div className="col-span-2">
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Engine</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.metadata.engine}</p>
              </div>
            )}
            {node.metadata?.records && (
              <div className="col-span-2">
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Data Volume</span>
                <p className={`text-sm font-medium text-amber-400`}>{node.metadata.records}</p>
              </div>
            )}
            {node.metadata?.data_classification && (
              <div className="col-span-2">
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Classification</span>
                <p className="text-sm font-medium text-red-400">⚠️ {node.metadata.data_classification}</p>
              </div>
            )}
          </div>

          {/* CVEs */}
          {cves.length > 0 && (
            <div>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                Vulnerabilities ({cves.length})
              </h4>
              <div className="space-y-2">
                {cves.map((cve, i) => (
                  <motion.div
                    key={cve}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: i * 0.1 }}
                    className={`flex items-center justify-between p-2.5 rounded-lg ${isDark ? 'bg-red-950/30 border border-red-900/30' : 'bg-red-50 border border-red-200'}`}
                  >
                    <span className={`text-xs font-mono font-medium ${isDark ? 'text-red-300' : 'text-red-700'}`}>{cve}</span>
                    {cvssScores[i] !== undefined && (
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${cvssScores[i]! >= 7 ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
                        CVSS {cvssScores[i]}
                      </span>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* RBAC Rules */}
          {node.metadata?.rules && (
            <div>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                RBAC Rules
              </h4>
              <div className="space-y-1">
                {(node.metadata.rules as string[]).map((rule, i) => (
                  <div key={i} className={`text-xs font-mono p-2 rounded ${isDark ? 'bg-slate-800 text-cyan-400' : 'bg-slate-100 text-blue-600'}`}>
                    {rule}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Secret Keys */}
          {node.metadata?.keys && (
            <div>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Secret Keys
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {(node.metadata.keys as string[]).map((key) => (
                  <span key={key} className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'bg-amber-900/30 text-amber-300 border border-amber-800/30' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>
                    {key}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Labels */}
          {node.metadata?.labels && Object.keys(node.metadata.labels).length > 0 && (
            <div>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Labels
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(node.metadata.labels).map(([k, v]) => (
                  <span key={k} className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'}`}>
                    {k}={v}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-2 pt-2">
            <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
              Analysis Actions
            </h4>
            <button
              onClick={() => onBlastRadius(node.id)}
              className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all
                bg-gradient-to-r from-red-600 to-orange-600 text-white hover:from-red-500 hover:to-orange-500
                hover:shadow-lg hover:shadow-red-500/20 active:scale-[0.98]"
            >
              <span className="flex items-center gap-2">
                <Crosshair className="w-4 h-4" />
                Run Blast Radius
              </span>
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onFindPath(node.id)}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all
                ${isDark 
                  ? 'bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700' 
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'}
                hover:shadow-lg active:scale-[0.98]`}
            >
              <span className="flex items-center gap-2">
                <Route className="w-4 h-4" />
                Find Attack Path to This Node
              </span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
```

## frontend\src\lib\api.ts

```typescript
import type {
  GraphData,
  BlastRadiusResult,
  ShortestPathResult,
  CycleResult,
  CriticalNodeResult,
} from './types';

const BASE_URL = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Health check
  health: () => fetchJSON<{ status: string }>('/health'),

  // Get full graph
  getGraph: () => fetchJSON<GraphData>('/graph'),

  // BFS Blast Radius
  blastRadius: (source: string, maxHops: number = 3) =>
    fetchJSON<BlastRadiusResult>('/blast-radius', {
      method: 'POST',
      body: JSON.stringify({ source, max_hops: maxHops }),
    }),

  // Dijkstra Shortest Path
  shortestPath: (source: string, target: string) =>
    fetchJSON<ShortestPathResult>('/shortest-path', {
      method: 'POST',
      body: JSON.stringify({ source, target }),
    }),

  // DFS Cycle Detection
  detectCycles: () => fetchJSON<CycleResult>('/cycles'),

  // Critical Node Analysis
  criticalNode: () => fetchJSON<CriticalNodeResult>('/critical-node'),

  // Remediate (remove node)
  remediate: (nodeId: string) =>
    fetchJSON<{ removed_node: unknown; updated_graph: GraphData; message: string }>('/remediate', {
      method: 'POST',
      body: JSON.stringify({ node_id: nodeId }),
    }),

  // Reset graph
  reset: () =>
    fetchJSON<{ message: string; graph: GraphData }>('/reset', {
      method: 'POST',
    }),

  // Upload custom graph
  uploadGraph: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Upload error: ${res.status}`);
    }
    return res.json() as Promise<{ message: string; graph: GraphData }>;
  },
};
```

## frontend\src\lib\types.ts

```typescript
// ─── Node Types ───────────────────────────────
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  namespace: string;
  risk_level: string;
  metadata: NodeMetadata;
  // Force graph properties
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface NodeMetadata {
  description?: string;
  image?: string;
  cves?: string[];
  cvss_scores?: number[];
  ports?: number[];
  labels?: Record<string, string>;
  icon?: string;
  version?: string;
  secret_type?: string;
  keys?: string[];
  engine?: string;
  data_classification?: string;
  records?: string;
  automount_token?: boolean;
  binding_type?: string;
  rules?: string[];
  service_type?: string;
  enforcement?: string;
  [key: string]: unknown;
}

// ─── Edge Types ───────────────────────────────
export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  weight: number;
  metadata: Record<string, unknown>;
}

// ─── Graph Data ───────────────────────────────
export interface GraphData {
  nodes: GraphNode[];
  links: GraphEdge[];
  metadata: {
    cluster_name?: string;
    scan_timestamp?: string;
    scenario?: string;
    description?: string;
  };
  stats: {
    total_nodes: number;
    total_edges: number;
    crown_jewels: number;
    critical_nodes: number;
  };
}

// ─── Algorithm Results ────────────────────────
export interface BlastRadiusResult {
  source: string;
  max_hops: number;
  affected_nodes: (GraphNode & { hop_distance: number })[];
  affected_edges: GraphEdge[];
  total_affected: number;
  crown_jewels_reached: number;
  crown_jewel_names: string[];
  risk_summary: string;
}

export interface ShortestPathResult {
  source: string;
  target: string;
  path: string[];
  path_details: PathStep[];
  total_weight: number;
  hop_count: number;
  difficulty: string;
  path_exists: boolean;
  kill_chain_summary: KillChainStep[];
  error?: string;
}

export interface PathStep {
  step: number;
  node_id: string;
  label: string;
  type: string;
  namespace: string;
  risk_level: string;
  metadata: NodeMetadata;
  edge_to_next?: {
    target: string;
    relationship: string;
    weight: number;
    metadata: Record<string, unknown>;
  };
}

export interface KillChainStep {
  step: number;
  action: string;
  node: string;
  node_type: string;
  risk_level: string;
  cves_exploited: string[];
  edge_info: string;
}

export interface CycleResult {
  total_cycles: number;
  cycles: CycleDetail[];
  has_cycles: boolean;
  risk_summary: string;
}

export interface CycleDetail {
  cycle: string[];
  cycle_nodes: GraphNode[];
  length: number;
  total_weight: number;
  risk: string;
  description: string;
}

export interface CriticalNodeResult {
  critical_node: CriticalNodeInfo | null;
  top_5_nodes: CriticalNodeInfo[];
  baseline_paths: number;
  entry_points: string[];
  crown_jewels: string[];
  betweenness_centrality: Record<string, number>;
  recommendation: string;
}

export interface CriticalNodeInfo {
  node_id: string;
  label: string;
  type: string;
  namespace: string;
  risk_level: string;
  paths_broken: number;
  paths_remaining: number;
  impact_percentage: number;
  metadata: NodeMetadata;
}

// ─── UI State ─────────────────────────────────
export type AnalysisMode = 'none' | 'blast-radius' | 'shortest-path' | 'cycles' | 'critical-node';

export interface HighlightState {
  nodes: Set<string>;
  edges: Set<string>;
  path: string[];
  mode: AnalysisMode;
}
```

## frontend\src\lib\utils.ts

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

