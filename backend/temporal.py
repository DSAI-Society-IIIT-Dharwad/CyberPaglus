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
