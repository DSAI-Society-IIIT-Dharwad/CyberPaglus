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
