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

import asyncio
import threading
import time
from graph_engine import K8sGraphEngine
from ingest import ingest_cluster

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

# ── Background Ingestor ────────────────────────────

def run_periodic_ingest(interval: int = 60):
    """Run the cluster ingestion process every N seconds."""
    print(f"🚀 Starting background ingestor (interval: {interval}s)...")
    while True:
        try:
            # Run ingestion (this updates cluster-graph.json and returns data)
            data = ingest_cluster(output_path="cluster-graph.json")
            
            # Hot-reload the engine with new data
            engine.load_graph_from_dict(data)
            print(f"✅ Auto-ingestion complete. Graph updated at {time.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"❌ Background ingestion error: {e}")
        
        time.sleep(interval)

# Start ingestor in a separate thread
ingest_thread = threading.Thread(target=run_periodic_ingest, daemon=True)
ingest_thread.start()


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


@app.get("/api/top-critical-paths")
def top_critical_paths(max_paths: int = 3):
    """Get top critical attack paths with descriptions and mitigation suggestions."""
    return engine.get_top_critical_paths(max_paths=max_paths)


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


@app.post("/api/recalculate-weights")
def recalculate_weights(include_details: bool = False):
    """
    Recalculate all edge weights using the Advanced Weight Scorer.
    Replaces simple CVSS-based weights with 5-parameter multi-factor analysis.
    
    Parameters:
        include_details: If True, returns detailed breakdown for each edge weight calculation
    """
    result = engine.recalculate_edge_weights_advanced(include_details=include_details)
    return {
        "status": "success",
        "recalculation": result,
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
