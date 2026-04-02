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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
