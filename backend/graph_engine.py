"""
KubeInsights — Core graph analytics engine
Uses NetworkX to build and analyze Kubernetes cluster attack graphs.

Supports two JSON schemas:
  - Legacy: nodes have {id, label, type, namespace, risk_level, metadata}
  - Rubric: nodes have {id, name, type, namespace, risk_score, is_source, is_sink, cves}
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

    Algorithms:
        1. BFS  — Blast Radius (reachable nodes within N hops)
        2. Dijkstra — Shortest (cheapest) attack path
        3. DFS  — Cycle detection (circular permissions)
        4. Critical Node — Removal-and-recount (graph surgery)
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
        """Load cluster state from a Python dict (for API uploads)."""
        self.raw_data = data
        self._original_data = copy.deepcopy(data)
        self._build_graph()

    # ──────────────────────────────────────────────
    # Graph Construction (dual-schema)
    # ──────────────────────────────────────────────

    def _build_graph(self) -> None:
        """
        Construct the NetworkX DiGraph from raw JSON data.
        Handles both legacy and rubric schemas transparently.
        """
        self.graph.clear()

        for node in self.raw_data.get("nodes", []):
            node_id = node["id"]

            # Detect schema: rubric has 'name' + 'is_source'; legacy has 'label' + 'risk_level'
            is_rubric = "is_source" in node or "risk_score" in node

            if is_rubric:
                label = node.get("name", node.get("label", node_id))
                node_type = node.get("type", "unknown")
                namespace = node.get("namespace", "default")
                risk_score = float(node.get("risk_score", 0.0))
                is_source = bool(node.get("is_source", False))
                is_sink = bool(node.get("is_sink", False))
                cves = list(node.get("cves", []))

                # Derive risk_level from flags and score
                if is_source:
                    risk_level = "entry-point"
                elif is_sink:
                    risk_level = "crown-jewel"
                elif risk_score >= 9.0:
                    risk_level = "critical"
                elif risk_score >= 7.0:
                    risk_level = "high"
                elif risk_score >= 4.0:
                    risk_level = "medium"
                else:
                    risk_level = "low"

                metadata = {
                    "description": f"{node_type} in {namespace}",
                    "cves": cves,
                    "risk_score": risk_score,
                }
            else:
                label = node.get("label", node_id)
                node_type = node.get("type", "unknown")
                namespace = node.get("namespace", "default")
                risk_level = node.get("risk_level", "low")
                risk_score = float(node.get("risk_score", 0.0))
                is_source = risk_level == "entry-point"
                is_sink = risk_level == "crown-jewel"
                cves = node.get("metadata", {}).get("cves", [])
                metadata = node.get("metadata", {})

            self.graph.add_node(
                node_id,
                label=label,
                type=node_type,
                namespace=namespace,
                risk_level=risk_level,
                risk_score=risk_score,
                is_source=is_source,
                is_sink=is_sink,
                cves=cves,
                metadata=metadata,
            )

        for edge in self.raw_data.get("edges", []):
            # Skip comment-only entries (rubric format has comment lines)
            if "source" not in edge or "target" not in edge:
                continue

            self.graph.add_edge(
                edge["source"],
                edge["target"],
                relationship=edge.get("relationship", "connects_to"),
                weight=float(edge.get("weight", 1.0)),
                cve=edge.get("cve"),
                cvss=edge.get("cvss"),
                metadata=edge.get("metadata", {}),
            )

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _get_sources(self) -> list:
        """Return all source / entry-point node IDs."""
        return [n for n, d in self.graph.nodes(data=True) if d.get("is_source")]

    def _get_sinks(self) -> list:
        """Return all sink / crown-jewel node IDs."""
        return [n for n, d in self.graph.nodes(data=True) if d.get("is_sink")]

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
                "crown_jewels": len([n for n, d in self.graph.nodes(data=True)
                                     if d.get("risk_level") == "crown-jewel" or d.get("is_sink")]),
                "critical_nodes": len([n for n, d in self.graph.nodes(data=True)
                                       if d.get("risk_level") == "critical"]),
            },
        }

    # ──────────────────────────────────────────────
    # Algorithm 1: BFS — Blast Radius
    # ──────────────────────────────────────────────

    def bfs_blast_radius(self, source: str, max_hops: int = 3) -> dict:
        """
        BFS from a source node to find all reachable nodes within N hops.
        Returns nodes grouped by hop layer for the report.

        Args:
            source: Starting node ID.
            max_hops: Maximum search depth.

        Returns:
            dict with affected_nodes, hop_layers, totals.
        """
        if source not in self.graph:
            return {
                "error": f"Node '{source}' not found in graph",
                "affected_nodes": [], "affected_edges": [],
            }

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

        # Build per-node details (excluding the source itself)
        affected_nodes = []
        for node_id, hop in visited.items():
            if node_id == source:
                continue
            affected_nodes.append({
                "id": node_id,
                "hop_distance": hop,
                **dict(self.graph.nodes[node_id]),
            })

        # Group by hop layer
        hop_layers = {}
        for node in affected_nodes:
            h = node["hop_distance"]
            if h not in hop_layers:
                hop_layers[h] = []
            hop_layers[h].append(node)

        # Edges within the blast zone
        affected_edges = []
        node_ids = set(visited.keys())
        for src, tgt, attrs in self.graph.edges(data=True):
            if src in node_ids and tgt in node_ids:
                affected_edges.append({"source": src, "target": tgt, **attrs})

        crown_jewels_reached = [
            n for n in affected_nodes
            if n.get("risk_level") == "crown-jewel" or n.get("is_sink")
        ]

        source_label = self.graph.nodes[source].get("label", source)

        return {
            "source": source,
            "source_label": source_label,
            "max_hops": max_hops,
            "affected_nodes": affected_nodes,
            "affected_edges": affected_edges,
            "hop_layers": hop_layers,
            "total_affected": len(affected_nodes),
            "crown_jewels_reached": len(crown_jewels_reached),
            "crown_jewel_names": [n["id"] for n in crown_jewels_reached],
            "risk_summary": (
                "CRITICAL" if crown_jewels_reached
                else "HIGH" if len(affected_nodes) > 5
                else "MEDIUM"
            ),
        }

    # ──────────────────────────────────────────────
    # Algorithm 2: Dijkstra — Shortest Attack Path
    # ──────────────────────────────────────────────

    def dijkstra_shortest_path(self, source: str, target: str) -> dict:
        """
        Find the cheapest attack path from source to target using edge weights.

        Args:
            source: Source node ID.
            target: Target node ID.

        Returns:
            dict with path, cost, hop_count, CVE details, kill chain.
        """
        if source not in self.graph:
            return {"error": f"Source node '{source}' not found", "path_exists": False}
        if target not in self.graph:
            return {"error": f"Target node '{target}' not found", "path_exists": False}

        try:
            path = nx.dijkstra_path(self.graph, source, target, weight="weight")
            total_weight = nx.dijkstra_path_length(self.graph, source, target, weight="weight")
        except nx.NetworkXNoPath:
            return {
                "error": f"No path found from '{source}' to '{target}'",
                "source": source,
                "target": target,
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
                edge_data = dict(self.graph.edges[path[i], path[i + 1]])
                step["edge_to_next"] = {
                    "target": path[i + 1],
                    "relationship": edge_data.get("relationship", ""),
                    "weight": edge_data.get("weight", 1.0),
                    "cve": edge_data.get("cve"),
                    "cvss": edge_data.get("cvss"),
                    "metadata": edge_data.get("metadata", {}),
                }
            path_details.append(step)

        difficulty = (
            "TRIVIAL" if total_weight < 3 else
            "EASY" if total_weight < 6 else
            "MODERATE" if total_weight < 10 else
            "HARD"
        )

        return {
            "source": source,
            "target": target,
            "path": list(path),
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
            cves = step.get("cves", step.get("metadata", {}).get("cves", []))
            entry = {
                "step": step["step"],
                "action": self._get_attack_action(step),
                "node": step.get("label", step["node_id"]),
                "node_type": step.get("type", "unknown"),
                "risk_level": step.get("risk_level", "unknown"),
                "cves_exploited": cves if cves else [],
                "edge_info": step.get("edge_to_next", {}).get("relationship", "—"),
            }
            chain.append(entry)
        return chain

    @staticmethod
    def _get_attack_action(step: dict) -> str:
        """Map node type to a realistic attack action description."""
        actions = {
            "externalactor": "Initiate external reconnaissance",
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
            "node": "Compromise cluster node",
            "namespace": "Access namespace resources",
            "persistentvolume": "Access persistent storage",
            "user": "User account access",
        }
        t = step.get("type", "").lower()
        return actions.get(t, "Exploit node")

    # ──────────────────────────────────────────────
    # All Attack Paths (Dijkstra, all source→sink)
    # ──────────────────────────────────────────────

    def find_all_attack_paths(self) -> list:
        """
        Find the Dijkstra shortest path from every source to every sink.
        Returns a list sorted by cost (ascending).

        Each entry: {source, target, path, cost, hops, path_edges}
        """
        sources = self._get_sources()
        sinks = self._get_sinks()

        paths = []
        for src in sources:
            for sink in sinks:
                try:
                    path = nx.dijkstra_path(self.graph, src, sink, weight="weight")
                    cost = nx.dijkstra_path_length(self.graph, src, sink, weight="weight")

                    # Collect edge details along the path
                    path_edges = []
                    for i in range(len(path) - 1):
                        edge_data = dict(self.graph.edges[path[i], path[i + 1]])
                        src_node = self.graph.nodes[path[i]]
                        tgt_node = self.graph.nodes[path[i + 1]]
                        path_edges.append({
                            "source_id": path[i],
                            "target_id": path[i + 1],
                            "source_name": src_node.get("label", path[i]),
                            "target_name": tgt_node.get("label", path[i + 1]),
                            "source_type": src_node.get("type", "?"),
                            "target_type": tgt_node.get("type", "?"),
                            "relationship": edge_data.get("relationship", ""),
                            "weight": edge_data.get("weight", 1.0),
                            "cve": edge_data.get("cve"),
                            "cvss": edge_data.get("cvss"),
                        })

                    paths.append({
                        "source": src,
                        "target": sink,
                        "path": path,
                        "cost": round(cost, 1),
                        "hops": len(path) - 1,
                        "path_edges": path_edges,
                    })
                except nx.NetworkXNoPath:
                    continue

        paths.sort(key=lambda p: p["cost"])
        return paths

    # ──────────────────────────────────────────────
    # Algorithm 3: DFS — Cycle Detection
    # ──────────────────────────────────────────────

    def dfs_cycle_detection(self) -> dict:
        """
        DFS-based cycle detection to find circular permission loops.
        Returns cycles as ordered node lists, no duplicates.
        """
        try:
            try:
                cycles = list(nx.simple_cycles(self.graph, length_bound=5))
            except TypeError:
                # Fallback for older NetworkX
                cycles = []
                sccs = [c for c in nx.strongly_connected_components(self.graph) if len(c) > 1]
                for scc in sccs:
                    subgraph = self.graph.subgraph(scc)
                    try:
                        edges = nx.find_cycle(subgraph)
                        cycle = [u for u, v in edges]
                        cycles.append(cycle)
                    except nx.NetworkXNoCycle:
                        pass
        except Exception:
            cycles = []

        # Deduplicate cycles (normalize: start from smallest node)
        seen = set()
        unique_cycles = []
        for cycle in cycles:
            normalized = tuple(sorted(cycle))
            if normalized not in seen:
                seen.add(normalized)
                unique_cycles.append(cycle)

        cycle_details = []
        for cycle in unique_cycles:
            cycle_nodes = []
            total_weight = 0
            for i, node_id in enumerate(cycle):
                node_data = dict(self.graph.nodes[node_id])
                cycle_nodes.append({"id": node_id, **node_data})
                next_node = cycle[(i + 1) % len(cycle)]
                if self.graph.has_edge(node_id, next_node):
                    total_weight += self.graph.edges[node_id, next_node].get("weight", 1.0)

            labels = [n.get("label", n["id"]) for n in cycle_nodes]
            risk = (
                "CRITICAL" if any(n.get("risk_level") in ("critical", "crown-jewel") for n in cycle_nodes)
                else "HIGH" if len(cycle) > 2
                else "MEDIUM"
            )

            cycle_details.append({
                "cycle": [n["id"] for n in cycle_nodes],
                "cycle_nodes": cycle_nodes,
                "length": len(cycle),
                "total_weight": round(total_weight, 2),
                "risk": risk,
                "description": " \u2194 ".join(labels) + " \u2194 " + labels[0],
            })

        return {
            "total_cycles": len(unique_cycles),
            "cycles": cycle_details,
            "has_cycles": len(unique_cycles) > 0,
            "risk_summary": (
                "CRITICAL" if any(c["risk"] == "CRITICAL" for c in cycle_details)
                else "HIGH" if cycle_details
                else "NONE"
            ),
        }

    # ──────────────────────────────────────────────
    # Algorithm 4: Critical Node Analysis
    #   Brute-force removal-and-recount methodology
    # ──────────────────────────────────────────────

    def critical_node_analysis(self, cutoff: int = 10) -> dict:
        """
        Identify the single non-source, non-sink node whose removal
        eliminates the greatest number of source-to-sink simple paths.

        Methodology:
            1. Count baseline paths using nx.all_simple_paths with cutoff.
            2. For each candidate node, copy the graph, remove the node,
               recount paths. The original graph is never mutated.
            3. Rank by paths eliminated.

        Args:
            cutoff: Maximum path length for all_simple_paths (default 10).

        Returns:
            dict with critical_node, top_5_nodes, baseline_paths, recommendation.
        """
        sources = self._get_sources()
        sinks = self._get_sinks()

        if not sources or not sinks:
            return {
                "error": "No entry points or crown jewels found in graph",
                "critical_node": None,
            }

        # 1. Count baseline paths
        baseline = 0
        for s in sources:
            for t in sinks:
                try:
                    baseline += len(list(nx.all_simple_paths(self.graph, s, t, cutoff=cutoff)))
                except nx.NetworkXNoPath:
                    pass

        # 2. Identify candidates (exclude sources and sinks)
        source_set = set(sources)
        sink_set = set(sinks)
        candidates = [
            n for n in self.graph.nodes()
            if n not in source_set and n not in sink_set
        ]

        # 3. Test removal of each candidate on a COPY of the graph
        node_impacts = []
        for candidate in candidates:
            test_graph = self.graph.copy()
            test_graph.remove_node(candidate)

            remaining = 0
            for s in sources:
                if s not in test_graph:
                    continue
                for t in sinks:
                    if t not in test_graph:
                        continue
                    try:
                        remaining += len(list(nx.all_simple_paths(test_graph, s, t, cutoff=cutoff)))
                    except nx.NetworkXNoPath:
                        pass

            eliminated = baseline - remaining
            node_data = dict(self.graph.nodes[candidate])

            node_impacts.append({
                "node_id": candidate,
                "label": node_data.get("label", candidate),
                "type": node_data.get("type", "unknown"),
                "namespace": node_data.get("namespace", "unknown"),
                "risk_level": node_data.get("risk_level", "unknown"),
                "paths_broken": eliminated,
                "impact_percentage": round((eliminated / baseline) * 100, 1) if baseline > 0 else 0,
                "metadata": node_data.get("metadata", {}),
            })

        node_impacts.sort(key=lambda x: x["paths_broken"], reverse=True)

        critical = node_impacts[0] if node_impacts else None

        return {
            "critical_node": critical,
            "top_5_nodes": node_impacts[:5],
            "baseline_paths": baseline,
            "entry_points": [self.graph.nodes[s].get("label", s) for s in sources],
            "crown_jewels": [self.graph.nodes[t].get("label", t) for t in sinks],
            "recommendation": (
                f"Remove permission binding '{critical['label']}' ({critical['type']}) "
                f"to eliminate {critical['paths_broken']} of {baseline} attack paths."
                if critical else "No critical node identified"
            ),
        }

    # ──────────────────────────────────────────────
    # Top Critical Attack Paths (legacy API compat)
    # ──────────────────────────────────────────────

    def get_top_critical_paths(self, max_paths: int = 3) -> dict:
        """
        Find the top critical attack paths from entry points to crown jewels.
        Returns paths ranked by total attack weight (lowest = most critical).
        """
        all_paths = self.find_all_attack_paths()

        top_paths = []
        for i, p in enumerate(all_paths[:max_paths], 1):
            source_data = self.graph.nodes[p["source"]]
            target_data = self.graph.nodes[p["target"]]
            difficulty = (
                "TRIVIAL" if p["cost"] < 3 else
                "EASY" if p["cost"] < 6 else
                "MODERATE" if p["cost"] < 10 else
                "HARD"
            )

            path_details = []
            for j, node_id in enumerate(p["path"]):
                nd = dict(self.graph.nodes[node_id])
                step = {
                    "step": j + 1,
                    "node_id": node_id,
                    "label": nd.get("label", node_id),
                    "type": nd.get("type", "unknown"),
                    "risk_level": nd.get("risk_level", "unknown"),
                }
                if j < len(p["path"]) - 1:
                    ed = dict(self.graph.edges[p["path"][j], p["path"][j + 1]])
                    step["edge_to_next"] = {
                        "target": p["path"][j + 1],
                        "relationship": ed.get("relationship", ""),
                        "weight": ed.get("weight", 1.0),
                    }
                path_details.append(step)

            top_paths.append({
                "rank": i,
                "source": p["source"],
                "target": p["target"],
                "path": p["path"],
                "path_details": path_details,
                "total_weight": p["cost"],
                "hop_count": p["hops"],
                "difficulty": difficulty,
                "description": f"Attack path from {source_data.get('label')} to {target_data.get('label')}",
                "mitigation_suggestions": self._generate_mitigation_suggestions(path_details, []),
                "vulnerabilities_found": 0,
                "risk_factors": [],
                "criticality_score": 0,
            })

        return {
            "total_paths_found": len(all_paths),
            "top_critical_paths": top_paths,
            "entry_points_count": len(self._get_sources()),
            "crown_jewels_count": len(self._get_sinks()),
            "summary": f"Found {len(all_paths)} attack paths, showing top {len(top_paths)} most critical ones",
        }

    def _generate_mitigation_suggestions(self, path_details: list, risk_factors: list) -> list:
        """Generate specific mitigation suggestions for the attack path."""
        suggestions = []
        for step in path_details:
            node_type = step.get("type", "")
            edge = step.get("edge_to_next", {})
            relationship = edge.get("relationship", "")
            label = step.get("label", step.get("node_id", ""))

            if node_type in ("serviceaccount", "ServiceAccount"):
                suggestions.append(f"Remove RoleBinding for {label}")
            elif node_type in ("role", "Role", "clusterrole", "ClusterRole"):
                suggestions.append(f"Restrict permissions on {label}")
            elif node_type in ("pod", "Pod"):
                cves = step.get("cves", [])
                if cves:
                    suggestions.append(f"Patch {', '.join(cves)} on {label}")
                else:
                    suggestions.append(f"Apply NetworkPolicy to {label}")
            elif node_type in ("secret", "Secret"):
                suggestions.append(f"Rotate credentials in {label}")

        return list(dict.fromkeys(suggestions))[:5]

    # ──────────────────────────────────────────────
    # Advanced Weight Scorer (legacy compat)
    # ──────────────────────────────────────────────

    def recalculate_edge_weights_advanced(self, include_details: bool = False) -> dict:
        """Recalculate all edge weights using the AdvancedWeightScorer."""
        try:
            from advanced_weight_scorer import AdvancedWeightScorer
        except ImportError:
            return {"status": "error", "message": "AdvancedWeightScorer not available"}

        weight_reports = []
        updated_count = 0

        for src, tgt, edge_attr in self.graph.edges(data=True):
            source_node = dict(self.graph.nodes[src])
            target_node = dict(self.graph.nodes[tgt])
            relationship = edge_attr.get("relationship", "connects_to")
            graph_context = {"outbound_edges": list(self.graph.successors(tgt))}

            new_weight = AdvancedWeightScorer.calculate_edge_weight(
                source_node, target_node, relationship, graph_context
            )
            self.graph[src][tgt]["weight"] = new_weight
            updated_count += 1

            if include_details:
                report = AdvancedWeightScorer.generate_weight_report(
                    source_node, target_node, relationship, graph_context
                )
                report["old_weight"] = edge_attr.get("weight", 1.0)
                report["new_weight"] = new_weight
                weight_reports.append(report)

        return {
            "status": "success",
            "edges_updated": updated_count,
            "scoring_method": "AdvancedWeightScorer (5-parameter multi-factor)",
            "weight_reports": weight_reports if include_details else [],
        }

    # ──────────────────────────────────────────────
    # Remediation
    # ──────────────────────────────────────────────

    def remove_node(self, node_id: str) -> dict:
        """Remove a node from the graph (simulating remediation)."""
        if node_id not in self.graph:
            return {"error": f"Node '{node_id}' not found in graph"}

        removed_node = dict(self.graph.nodes[node_id])
        removed_edges = list(self.graph.in_edges(node_id)) + list(self.graph.out_edges(node_id))

        self.graph.remove_node(node_id)

        if self.raw_data:
            self.raw_data["nodes"] = [n for n in self.raw_data["nodes"] if n["id"] != node_id]
            self.raw_data["edges"] = [
                e for e in self.raw_data["edges"]
                if e.get("source") != node_id and e.get("target") != node_id
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
