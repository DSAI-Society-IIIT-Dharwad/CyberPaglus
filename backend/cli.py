#!/usr/bin/env python3
"""
KubeInsights CLI — Command-line security analysis tool for Kubernetes clusters.

Usage:
    python cli.py analyze --input mock-cluster-graph.json
    python cli.py analyze --input mock-cluster-graph.json --full-report
    python cli.py blast-radius --source pod-webfront --hops 3
    python cli.py shortest-path --source user-dev1 --target db-production
    python cli.py detect-cycles
    python cli.py critical-node
    python cli.py ingest -o cluster-graph.json
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

# ── Unicode Compatibility Fallback ──────────────────────────────
# Forces UTF-8 encoding for console output to prevent Windows crashes
# This is placed at the top to protect all subsequent operations.
if sys.stdout.encoding != 'utf-8':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# ── Unicode Compatibility Helper ──────────────────────────────

def safe_print(text: str, file=sys.stdout):
    """
    Print text safely by handling UnicodeEncodeError on restricted terminals.
    Uses ASCII fallbacks for common decorative characters.
    """
    # Character mapping for common decorative symbols
    fallbacks = {
        "\u2550": "=",  # ═
        "\u2014": "--", # —
        "\u26a0": "[!]", # ⚠
        "\u2713": "[OK]", # ✓
        "\u2192": "->",  # →
        "\u2605": "[*]", # ★
        "\u2588": "#",   # █
        "\u2500": "-",   # ─
    }

    try:
        # Try printing directly first
        print(text, file=file)
    except UnicodeEncodeError:
        # If encoding fails, apply fallbacks
        safe_text = text
        for char, fallback in fallbacks.items():
            safe_text = safe_text.replace(char, fallback)
        
        # Final attempt with 'backslashreplace' just in case
        try:
            print(safe_text, file=file)
        except UnicodeEncodeError:
            print(text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding), file=file)

# Reconfigure stdout to UTF-8 if supported (Python 3.7+)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# ── Severity helpers ──────────────────────────────────────────

def _severity_label(risk_score: float) -> str:
    """Map a cumulative risk score to a severity label."""
    if risk_score >= 20.0:
        return "CRITICAL"
    elif risk_score >= 10.0:
        return "HIGH"
    elif risk_score >= 5.0:
        return "MEDIUM"
    else:
        return "LOW"


# ── Helpers ────────────────────────────────────────────────────

def _load_engine(input_path: str) -> K8sGraphEngine:
    """Load the graph engine from a JSON file."""
    path = Path(input_path)
    if not path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    engine = K8sGraphEngine(str(path))
    return engine


# ── Full Report Formatting (matches sample-output.txt) ────────

def _print_full_report(engine: K8sGraphEngine, hops: int = 3):
    """
    Print the full Kill Chain Report in the exact format
    specified by the hackathon sample-output.txt.

    Sections:
        1. Attack Path Detection (Dijkstra) — all source→sink shortest paths
        2. Blast Radius Analysis (BFS) — per-source, grouped by hop
        3. Circular Permission Detection (DFS)
        4. Critical Node Analysis — removal-and-recount
        5. Summary
    """
    meta = engine.raw_data.get("metadata", {})
    cluster_name = meta.get("cluster", meta.get("cluster_name", "unknown"))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n_nodes = engine.graph.number_of_nodes()
    n_edges = engine.graph.number_of_edges()

    bar = "\u2550" * 66  # ═

    # ── Header ────────────────────────────────────────────────
    safe_print(bar)
    safe_print(f"  KILL CHAIN REPORT  \u2014  {now}")
    safe_print(f"  Cluster : {cluster_name}")
    safe_print(f"  Nodes   : {n_nodes}  |  Edges: {n_edges}")
    safe_print(bar)
    safe_print("")

    # ══════════════════════════════════════════════════════════
    # SECTION 1 — ATTACK PATH DETECTION (Dijkstra)
    # ══════════════════════════════════════════════════════════
    all_paths = engine.find_all_attack_paths()

    safe_print("[ SECTION 1 \u2014 ATTACK PATH DETECTION (Dijkstra) ]")
    safe_print(f"  \u26a0  {len(all_paths)} attack path(s) detected")
    safe_print("")

    for idx, ap in enumerate(all_paths, 1):
        severity = _severity_label(ap["cost"])
        safe_print(f"  Path #{idx}  |  {ap['hops']} hops  |  Risk Score: {ap['cost']}  [{severity}]")
        safe_print(f"  {'-' * 60}")

        for edge in ap["path_edges"]:
            src_name = edge["source_name"]
            src_type = edge["source_type"]
            tgt_name = edge["target_name"]
            tgt_type = edge["target_type"]
            rel = edge["relationship"]
            cve = edge.get("cve")
            cvss = edge.get("cvss")

            line = f"  {src_name} ({src_type})  --[{rel}]-->  {tgt_name} ({tgt_type})"
            if cve:
                line += f"  [{cve}, CVSS {cvss}]"
            safe_print(line)

        safe_print("")

    # ══════════════════════════════════════════════════════════
    # SECTION 2 — BLAST RADIUS ANALYSIS (BFS)
    # ══════════════════════════════════════════════════════════
    safe_print(f"[ SECTION 2 \u2014 BLAST RADIUS ANALYSIS (BFS, depth={hops}) ]")
    safe_print("")

    sources = engine._get_sources()
    total_blast_nodes = 0

    for src in sources:
        result = engine.bfs_blast_radius(src, hops)
        label = result.get("source_label", src)
        total = result["total_affected"]
        total_blast_nodes += total

        safe_print(f"  Source: {label}  \u2192  {total} reachable resource(s) within {hops} hops")

        layers = result.get("hop_layers", {})
        for hop_num in sorted(layers.keys()):
            names = [n.get("label", n["id"]) for n in layers[hop_num]]
            safe_print(f"    Hop {hop_num}: {', '.join(names)}")

        safe_print("")

    # ══════════════════════════════════════════════════════════
    # SECTION 3 — CIRCULAR PERMISSION DETECTION (DFS)
    # ══════════════════════════════════════════════════════════
    cycle_result = engine.dfs_cycle_detection()

    safe_print("[ SECTION 3 \u2014 CIRCULAR PERMISSION DETECTION (DFS) ]")
    if cycle_result["has_cycles"]:
        safe_print(f"  \u26a0  {cycle_result['total_cycles']} cycle(s) detected")
        safe_print("")
        for i, cycle in enumerate(cycle_result["cycles"], 1):
            safe_print(f"  Cycle #{i}: {cycle['description']}")
    else:
        safe_print("  \u2713 No circular permission loops detected.")
    safe_print("")

    # ══════════════════════════════════════════════════════════
    # SECTION 4 — CRITICAL NODE ANALYSIS
    # ══════════════════════════════════════════════════════════
    safe_print("[ SECTION 4 \u2014 CRITICAL NODE ANALYSIS ]")
    safe_print("  Computing... (removing each node and recounting paths)")
    safe_print("")

    critical_result = engine.critical_node_analysis()
    baseline = critical_result.get("baseline_paths", 0)
    safe_print(f"  Baseline attack paths : {baseline}")
    safe_print("")

    cn = critical_result.get("critical_node")
    if cn:
        safe_print(f"  \u2605  RECOMMENDATION:")
        safe_print(f"     Remove permission binding '{cn['label']}' ({cn['type']}) "
              f"to eliminate {cn['paths_broken']} of {baseline} attack paths.")
        safe_print("")

        top5 = critical_result.get("top_5_nodes", [])
        if top5:
            max_broken = top5[0]["paths_broken"] if top5 else 1
            safe_print("  Top 5 highest-impact nodes to remove:")
            for node in top5:
                name_padded = f"{node['label']:<30}"
                type_padded = f"({node['type']:<15})"
                bar_len = int(node["paths_broken"] / max_broken * 20) if max_broken > 0 else 0
                bar_str = "\u2588" * bar_len
                safe_print(f"    {name_padded} {type_padded}  -{node['paths_broken']} paths  {bar_str}")
        safe_print("")

    # ══════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════
    critical_label = cn["label"] if cn else "none"
    safe_print(bar)
    safe_print("  SUMMARY")
    safe_print(f"  Attack paths found   : {len(all_paths)}")
    safe_print(f"  Circular permissions : {cycle_result['total_cycles']}")
    safe_print(f"  Total blast-radius nodes exposed : {total_blast_nodes}")
    safe_print(f"  Critical node to remove : {critical_label}")
    safe_print(bar)
    safe_print("")


# ── Individual Algorithm Output ──────────────────────────────

def _print_blast_radius(engine: K8sGraphEngine, result: dict):
    """Print blast radius results for a single source."""
    if "error" in result and not result.get("affected_nodes"):
        print(f"\nError: {result['error']}")
        return

    label = result.get("source_label", result["source"])
    total = result["total_affected"]
    hops = result["max_hops"]

    safe_print(f"\nBlast Radius Analysis")
    safe_print(f"{'─' * 50}")
    safe_print(f"  Source: {label}  \u2192  {total} reachable resource(s) within {hops} hops")

    layers = result.get("hop_layers", {})
    for hop_num in sorted(layers.keys()):
        names = [n.get("label", n["id"]) for n in layers[hop_num]]
        safe_print(f"    Hop {hop_num}: {', '.join(names)}")
    safe_print("")


def _print_shortest_path(result: dict):
    """Print shortest path / kill chain results."""
    if result.get("path_exists") is False:
        src = result.get('source', '?')
        tgt = result.get('target', '?')
        print(f"\nNo path found from '{src}' to '{tgt}'")
        return

    if "error" in result:
        print(f"\nError: {result['error']}")
        return

    path_details = result.get("path_details", [])
    cost = result["total_weight"]
    hop_count = result["hop_count"]
    severity = _severity_label(cost)

    print(f"\nAttack Path  |  {hop_count} hops  |  Risk Score: {cost}  [{severity}]")
    print(f"{'─' * 60}")

    for i in range(len(path_details) - 1):
        step = path_details[i]
        edge = step.get("edge_to_next", {})
        next_step = path_details[i + 1]

        src_name = step.get("label", step["node_id"])
        src_type = step.get("type", "?")
        tgt_name = next_step.get("label", next_step["node_id"])
        tgt_type = next_step.get("type", "?")
        rel = edge.get("relationship", "")
        cve = edge.get("cve")
        cvss = edge.get("cvss")

        line = f"  {src_name} ({src_type})  --[{rel}]-->  {tgt_name} ({tgt_type})"
        if cve:
            line += f"  [{cve}, CVSS {cvss}]"
        print(line)
    print()


def _print_cycles(result: dict):
    """Print cycle detection results."""
    if not result["has_cycles"]:
        print("\nNo circular permission loops detected.")
        return

    print(f"\nCircular Permission Detection")
    print(f"{'─' * 50}")
    print(f"  {result['total_cycles']} cycle(s) detected")
    print()
    for i, cycle in enumerate(result["cycles"], 1):
        print(f"  Cycle #{i}: {cycle['description']}")
    print()


def _print_critical_node(result: dict):
    """Print critical node analysis results."""
    if "error" in result:
        print(f"\nError: {result['error']}")
        return

    cn = result.get("critical_node")
    baseline = result.get("baseline_paths", 0)

    print(f"\nCritical Node Analysis")
    print(f"{'─' * 50}")
    print(f"  Baseline attack paths: {baseline}")
    print()

    if cn:
        print(f"  Critical Node: {cn['label']} ({cn['type']})")
        print(f"  Paths Eliminated: {cn['paths_broken']} of {baseline}")
        print(f"  Impact: {cn['impact_percentage']}%")
        print()

        top5 = result.get("top_5_nodes", [])
        if top5:
            max_broken = top5[0]["paths_broken"] if top5 else 1
            print("  Top 5 highest-impact nodes:")
            for node in top5:
                name_padded = f"{node['label']:<30}"
                type_padded = f"({node['type']:<15})"
                bar_len = int(node["paths_broken"] / max_broken * 20) if max_broken > 0 else 0
                bar_str = "\u2588" * bar_len
                print(f"    {name_padded} {type_padded}  -{node['paths_broken']} paths  {bar_str}")
    else:
        print("  No critical chokepoint node identified.")
    print()


# ── PDF Report Generation ─────────────────────────────────────

def _generate_pdf(engine: K8sGraphEngine, output_path: str):
    """Generate a PDF Kill Chain Report using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.colors import HexColor
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        print("Error: reportlab is required for PDF generation.")
        print("  Install it with: pip install reportlab")
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
        fontSize=24, textColor=HexColor("#0ea5e9"), spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "KPASubtitle", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#64748b"), spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        "KPAHeading", parent=styles["Heading2"],
        fontSize=14, textColor=HexColor("#1e293b"),
        spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "KPABody", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#334155"), leading=14,
    ))
    styles.add(ParagraphStyle(
        "KPAWarning", parent=styles["Normal"],
        fontSize=11, textColor=HexColor("#dc2626"),
        leading=14, fontName="Helvetica-Bold",
    ))

    elements = []

    meta = engine.raw_data.get("metadata", {})
    cluster_name = meta.get("cluster", meta.get("cluster_name", "Unknown"))
    stats = engine.get_graph_data()["stats"]

    elements.append(Paragraph("KubeInsights \u2014 Kill Chain Report", styles["KPATitle"]))
    elements.append(Paragraph(
        f"Cluster: {cluster_name} | "
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Nodes: {stats['total_nodes']} | Edges: {stats['total_edges']}",
        styles["KPASubtitle"],
    ))
    elements.append(Spacer(1, 8 * mm))

    # Attack paths
    all_paths = engine.find_all_attack_paths()
    if all_paths:
        elements.append(Paragraph("1. Attack Path Detection (Dijkstra)", styles["KPAHeading"]))
        elements.append(Paragraph(
            f"{len(all_paths)} attack path(s) detected across all source-to-sink pairs.",
            styles["KPAWarning"],
        ))

        for idx, ap in enumerate(all_paths[:10], 1):  # Top 10 in PDF
            severity = _severity_label(ap["cost"])
            path_str = " \u2192 ".join(
                engine.graph.nodes[n].get("label", n) for n in ap["path"]
            )
            elements.append(Paragraph(
                f"Path #{idx}: {path_str} | {ap['hops']} hops | Score: {ap['cost']} [{severity}]",
                styles["KPABody"],
            ))
        elements.append(Spacer(1, 6 * mm))

    # Critical node
    critical_result = engine.critical_node_analysis()
    cn = critical_result.get("critical_node")
    if cn:
        elements.append(Paragraph("2. Critical Node Analysis", styles["KPAHeading"]))
        elements.append(Paragraph(
            f"Recommendation: Remove '{cn['label']}' ({cn['type']}) to eliminate "
            f"{cn['paths_broken']}/{critical_result['baseline_paths']} attack paths "
            f"({cn['impact_percentage']}% impact).",
            styles["KPAWarning"],
        ))

    # Cycles
    cycle_result = engine.dfs_cycle_detection()
    elements.append(Paragraph("3. Circular Permission Detection", styles["KPAHeading"]))
    if cycle_result["has_cycles"]:
        for cycle in cycle_result["cycles"]:
            elements.append(Paragraph(f"Cycle: {cycle['description']}", styles["KPABody"]))
    else:
        elements.append(Paragraph("No circular permission loops detected.", styles["KPABody"]))

    # Footer
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph(
        f"Generated by KubeInsights CLI v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles["KPASubtitle"],
    ))

    doc.build(elements)
    print(f"\nPDF report saved to: {output_path}")


# ── Subcommand Handlers ───────────────────────────────────────

def cmd_analyze(args):
    """Run all 4 algorithms and produce a full Kill Chain Report."""
    engine = _load_engine(args.input)

    if args.json:
        # JSON mode — run everything and output as JSON
        all_paths = engine.find_all_attack_paths()
        cycle_result = engine.dfs_cycle_detection()
        critical_result = engine.critical_node_analysis()

        sources = engine._get_sources()
        blast_results = {}
        for src in sources:
            blast_results[src] = engine.bfs_blast_radius(src, args.hops)

        output = {
            "graph_stats": engine.get_graph_data()["stats"],
            "attack_paths": all_paths,
            "blast_radius": blast_results,
            "cycles": cycle_result,
            "critical_node": critical_result,
        }
        print(json.dumps(output, indent=2, default=str))
        return

    # Full text report
    _print_full_report(engine, hops=args.hops)

    # Temporal diff
    if args.diff:
        prev_snapshot = get_latest_snapshot()
        if prev_snapshot:
            current_data = {
                "nodes": engine.raw_data.get("nodes", []),
                "edges": engine.raw_data.get("edges", []),
                "metadata": engine.raw_data.get("metadata", {}),
            }
            diff = diff_graphs(prev_snapshot, current_data)
            print(format_diff_report(diff))
        else:
            print("No previous snapshot found for diff. Saving current state as first snapshot.")

    # Save snapshot
    if args.snapshot:
        raw_data = {
            "nodes": engine.raw_data.get("nodes", []),
            "edges": engine.raw_data.get("edges", []),
            "metadata": engine.raw_data.get("metadata", {}),
        }
        snapshot_path = save_snapshot(raw_data, label=args.snapshot_label or "")
        print(f"Snapshot saved: {snapshot_path}")

    # PDF
    if args.pdf:
        _generate_pdf(engine, args.pdf)


def cmd_blast_radius(args):
    """Run BFS blast radius from a source node."""
    engine = _load_engine(args.input)
    result = engine.bfs_blast_radius(args.source, args.hops)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_blast_radius(engine, result)


def cmd_shortest_path(args):
    """Run Dijkstra's shortest path between two nodes."""
    engine = _load_engine(args.input)
    result = engine.dijkstra_shortest_path(args.source, args.target)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_shortest_path(result)


def cmd_detect_cycles(args):
    """Run DFS cycle detection."""
    engine = _load_engine(args.input)
    result = engine.dfs_cycle_detection()

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_cycles(result)


def cmd_critical_node(args):
    """Run critical node analysis."""
    engine = _load_engine(args.input)
    result = engine.critical_node_analysis()

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_critical_node(result)


def cmd_top_critical_paths(args):
    """Show top critical attack paths."""
    engine = _load_engine(args.input)
    result = engine.get_top_critical_paths(max_paths=args.count)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        paths = result.get("top_critical_paths", [])
        if not paths:
            print("\nNo attack paths found.")
            return

        print(f"\nTop {len(paths)} Critical Attack Paths")
        print(f"{'─' * 60}")
        for p in paths:
            severity = _severity_label(p["total_weight"])
            path_nodes = [s.get("label", s["node_id"]) for s in p["path_details"]]
            print(f"  #{p['rank']}  {' → '.join(path_nodes)}")
            print(f"       {p['hop_count']} hops | Score: {p['total_weight']} [{severity}]")
            if p.get("mitigation_suggestions"):
                for sug in p["mitigation_suggestions"][:2]:
                    print(f"       → {sug}")
            print()


def cmd_ingest(args):
    """Ingest live cluster state via kubectl."""
    from ingest import ingest_cluster
    data = ingest_cluster(output_path=args.output, live_cve=args.live_cve)

    if args.snapshot:
        snapshot_path = save_snapshot(data, label="ingest")
        print(f"Snapshot saved: {snapshot_path}")

    print(f"\nIngestion complete. Run analysis with:")
    print(f"  python cli.py analyze --input {args.output}")


def cmd_snapshots(args):
    """List all stored snapshots."""
    snapshots = list_snapshots()
    if not snapshots:
        print("\nNo snapshots found. Run an analysis with --snapshot to create one.")
        return

    print(f"\nStored Snapshots")
    print(f"{'─' * 70}")
    for i, s in enumerate(snapshots, 1):
        label = f" [{s['label']}]" if s.get("label") else ""
        print(f"  {i}. {s['filename']}{label}")
        print(f"     Timestamp: {s['timestamp']} | "
              f"Nodes: {s['node_count']} | Edges: {s['edge_count']}")
    print()


def cmd_diff(args):
    """Diff two snapshots or current state vs latest snapshot."""
    if args.old and args.new:
        from temporal import load_snapshot
        old_data = load_snapshot(args.old)
        new_data = load_snapshot(args.new)
        if not old_data or not new_data:
            print("Error: Could not load one or both snapshot files.")
            return
    elif args.input:
        old_data = get_latest_snapshot()
        if not old_data:
            print("Error: No previous snapshot found. Cannot diff.")
            return
        engine = _load_engine(args.input)
        new_data = {
            "nodes": engine.raw_data.get("nodes", []),
            "edges": engine.raw_data.get("edges", []),
            "metadata": engine.raw_data.get("metadata", {}),
        }
    else:
        print("Error: Provide --input or both --old and --new snapshot paths.")
        return

    diff = diff_graphs(old_data, new_data)

    if args.json:
        print(json.dumps(diff, indent=2, default=str))
    else:
        print(format_diff_report(diff))


# ── CLI Setup ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="kubeinsights",
        description="KubeInsights — Kubernetes Attack Path Visualizer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py analyze --input mock-cluster-graph.json
  python cli.py analyze --input mock-cluster-graph.json --full-report
  python cli.py analyze --input mock-cluster-graph.json --pdf report.pdf
  python cli.py analyze --input mock-cluster-graph.json --json
  python cli.py blast-radius --source pod-webfront --hops 3 --input mock-cluster-graph.json
  python cli.py shortest-path --source user-dev1 --target db-production --input mock-cluster-graph.json
  python cli.py detect-cycles --input mock-cluster-graph.json
  python cli.py critical-node --input mock-cluster-graph.json
  python cli.py ingest -o cluster-graph.json
  python cli.py snapshots
  python cli.py diff --input cluster-graph.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ── analyze (full report) ──
    p_analyze = subparsers.add_parser("analyze", help="Run full security analysis (all 4 algorithms)")
    p_analyze.add_argument("--input", "-i", default="mock-cluster-graph.json", help="Path to cluster graph JSON")
    p_analyze.add_argument("--full-report", action="store_true", help="Generate full Kill Chain report (default behavior)")
    p_analyze.add_argument("--pdf", help="Export Kill Chain Report as PDF")
    p_analyze.add_argument("--json", action="store_true", help="Output results as JSON")
    p_analyze.add_argument("--hops", type=int, default=3, help="Max hops for blast radius (default: 3)")
    p_analyze.add_argument("--blast-source", help="Override source node for blast radius")
    p_analyze.add_argument("--path-source", help="Override source for shortest path")
    p_analyze.add_argument("--path-target", help="Override target for shortest path")
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

    # ── top-critical-paths ──
    p_top_paths = subparsers.add_parser("top-critical-paths", help="Show top critical attack paths")
    p_top_paths.add_argument("--input", "-i", default="mock-cluster-graph.json", help="Path to cluster graph JSON")
    p_top_paths.add_argument("--count", "-n", type=int, default=3, help="Number of paths (default: 3)")
    p_top_paths.add_argument("--json", action="store_true", help="Output as JSON")
    p_top_paths.set_defaults(func=cmd_top_critical_paths)

    # ── ingest ──
    p_ingest = subparsers.add_parser("ingest", help="Ingest live Kubernetes cluster state via kubectl")
    p_ingest.add_argument("--output", "-o", default="cluster-graph.json", help="Output JSON path")
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

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
