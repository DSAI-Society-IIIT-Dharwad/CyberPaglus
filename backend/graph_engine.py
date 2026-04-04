"""
K8sGraphEngine — Core graph analytics engine for KubePathAudit.
Uses NetworkX to build and analyze Kubernetes cluster attack graphs.
"""

import json
import copy
import networkx as nx
from pathlib import Path
from typing import Optional

from advanced_weight_scorer import AdvancedWeightScorer


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

    def recalculate_edge_weights_advanced(self, include_details: bool = False) -> dict:
        """
        Recalculate all edge weights using the AdvancedWeightScorer.
        Replaces simple CVSS-based weights with comprehensive multi-parameter scoring.
        
        Args:
            include_details: If True, include detailed component breakdown for each edge
            
        Returns:
            dict with summary and optionally detailed weight reports
        """
        weight_reports = []
        updated_count = 0
        
        for src, tgt, edge_attr in self.graph.edges(data=True):
            # Get node data
            source_node = dict(self.graph.nodes[src])
            target_node = dict(self.graph.nodes[tgt])
            relationship = edge_attr.get("relationship", "connects_to")
            
            # Build graph context for blast radius calculation
            graph_context = {
                "outbound_edges": list(self.graph.successors(tgt))
            }
            
            # Calculate new weight
            new_weight = AdvancedWeightScorer.calculate_edge_weight(
                source_node, target_node, relationship, graph_context
            )
            
            # Update edge weight in graph
            self.graph[src][tgt]["weight"] = new_weight
            updated_count += 1
            
            # Store report if requested
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
            "factors": [
                "Asset Criticality (25%)",
                "Privilege Escalation (25%)",
                "Network Reachability (20%)",
                "RBAC Restrictions (20%)",
                "Blast Radius (10%)"
            ],
            "weight_reports": weight_reports if include_details else []
        }

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
    # Top Critical Attack Paths Analysis
    # ──────────────────────────────────────────────
    def get_top_critical_paths(self, max_paths: int = 3) -> dict:
        """
        Find the top critical attack paths from entry points to crown jewels.
        Returns paths ranked by total attack difficulty (lowest weight = most critical).
        Includes descriptions and mitigation suggestions for each path.
        """
        entry_points = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("type") == "internet" or d.get("risk_level") == "entry-point"
        ]
        crown_jewels = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("risk_level") == "crown-jewel"
        ]

        if not entry_points:
            return {"error": "No entry points found in graph"}
        if not crown_jewels:
            return {"error": "No crown jewels found in graph"}

        all_paths = []

        # Calculate paths from all entry points to all crown jewels
        for source in entry_points:
            for target in crown_jewels:
                try:
                    path = nx.dijkstra_path(self.graph, source, target, weight="weight")
                    total_weight = nx.dijkstra_path_length(self.graph, source, target, weight="weight")

                    path_details = []
                    vulnerabilities = []
                    risk_factors = []

                    for i, node_id in enumerate(path):
                        node_data = dict(self.graph.nodes[node_id])
                        step = {
                            "step": i + 1,
                            "node_id": node_id,
                            "label": node_data.get("label", node_id),
                            "type": node_data.get("type", "unknown"),
                            "risk_level": node_data.get("risk_level", "unknown"),
                        }

                        # Collect vulnerabilities and risk factors
                        if node_data.get("metadata", {}).get("cvss_scores"):
                            vulnerabilities.extend(node_data["metadata"]["cvss_scores"])

                        if node_data.get("risk_level") in ("critical", "crown-jewel"):
                            risk_factors.append(f"Critical asset: {node_data.get('label', node_id)}")

                        if i < len(path) - 1:
                            edge_data = self.graph.edges[path[i], path[i + 1]]
                            step["edge_to_next"] = {
                                "target": path[i + 1],
                                "relationship": edge_data.get("relationship", ""),
                                "weight": edge_data.get("weight", 1.0),
                            }

                            # Check for dangerous relationships
                            relationship = edge_data.get("relationship", "")
                            if "secret" in relationship.lower() or "token" in relationship.lower():
                                risk_factors.append("Credential access via secrets/tokens")
                            if "serviceaccount" in relationship.lower():
                                risk_factors.append("Service account privilege escalation")

                        path_details.append(step)

                    # Generate description and mitigation
                    description = self._generate_path_description(path_details, total_weight)
                    mitigation = self._generate_mitigation_suggestions(path_details, risk_factors)

                    difficulty = "TRIVIAL" if total_weight < 3 else "EASY" if total_weight < 6 else "MODERATE" if total_weight < 10 else "HARD"

                    all_paths.append({
                        "rank": 0,  # Will be set after sorting
                        "source": source,
                        "target": target,
                        "path": [n for n in path],
                        "path_details": path_details,
                        "total_weight": round(total_weight, 2),
                        "hop_count": len(path) - 1,
                        "difficulty": difficulty,
                        "description": description,
                        "mitigation_suggestions": mitigation,
                        "vulnerabilities_found": len(vulnerabilities),
                        "risk_factors": risk_factors,
                        "criticality_score": self._calculate_path_criticality(path_details),
                    })

                except nx.NetworkXNoPath:
                    continue

        # Sort by total weight (lowest = most critical) and take top N
        all_paths.sort(key=lambda x: x["total_weight"])
        top_paths = all_paths[:max_paths]

        # Update ranks
        for i, path in enumerate(top_paths, 1):
            path["rank"] = i

        return {
            "total_paths_found": len(all_paths),
            "top_critical_paths": top_paths,
            "entry_points_count": len(entry_points),
            "crown_jewels_count": len(crown_jewels),
            "summary": f"Found {len(all_paths)} attack paths, showing top {len(top_paths)} most critical ones",
        }

    def _generate_path_description(self, path_details: list, total_weight: float) -> str:
        """Generate a human-readable description of the attack path."""
        if not path_details:
            return "Empty path"

        start_node = path_details[0]
        end_node = path_details[-1]

        # Build path summary
        path_summary = []
        for step in path_details:
            node_type = step.get("type", "unknown")
            risk_level = step.get("risk_level", "unknown")
            label = step.get("label", step["node_id"])

            if risk_level == "entry-point":
                path_summary.append(f"enters via {label}")
            elif risk_level == "crown-jewel":
                path_summary.append(f"reaches {label}")
            elif node_type == "serviceaccount":
                path_summary.append(f"escalates through {label}")
            elif node_type == "secret":
                path_summary.append(f"accesses {label}")
            elif node_type == "pod":
                path_summary.append(f"compromises {label}")
            else:
                path_summary.append(f"moves to {label}")

        description = " → ".join(path_summary)

        # Add difficulty assessment
        if total_weight < 3:
            difficulty_desc = "highly exploitable"
        elif total_weight < 6:
            difficulty_desc = "moderately easy to exploit"
        elif total_weight < 10:
            difficulty_desc = "challenging but possible"
        else:
            difficulty_desc = "very difficult to exploit"

        return f"Attack path: {description}. This path is {difficulty_desc} (difficulty score: {total_weight:.1f})."

    def _generate_mitigation_suggestions(self, path_details: list, risk_factors: list) -> list:
        """Generate specific mitigation suggestions for the attack path."""
        suggestions = []

        # Analyze each step for specific recommendations
        for step in path_details:
            node_type = step.get("type", "")
            risk_level = step.get("risk_level", "")
            metadata = step.get("metadata", {})

            if node_type == "ingress":
                suggestions.append("Restrict ingress access with network policies or authentication")
            elif node_type == "serviceaccount":
                suggestions.append("Use minimal RBAC permissions for service accounts")
                if metadata.get("automount_token"):
                    suggestions.append("Disable automountServiceAccountToken for pods that don't need it")
            elif node_type == "secret":
                suggestions.append("Use sealed secrets or external secret management")
                suggestions.append("Implement secret rotation policies")
            elif node_type == "pod":
                suggestions.append("Run pods with non-root user and read-only filesystem")
                suggestions.append("Use security contexts and pod security standards")
            elif risk_level == "crown-jewel":
                suggestions.append(f"Implement strict access controls for {step.get('label', 'critical asset')}")

        # Add general suggestions based on risk factors
        if any("secret" in rf.lower() for rf in risk_factors):
            suggestions.append("Audit and minimize secret access across the cluster")
        if any("serviceaccount" in rf.lower() for rf in risk_factors):
            suggestions.append("Review and tighten RBAC policies for service accounts")
        if any("credential" in rf.lower() for rf in risk_factors):
            suggestions.append("Implement credential rotation and least-privilege access")

        # Add network segmentation suggestions
        hop_count = len(path_details) - 1
        if hop_count > 3:
            suggestions.append("Implement network policies to limit lateral movement")
        if hop_count > 5:
            suggestions.append("Consider microsegmentation to break long attack chains")

        # Remove duplicates and limit to top 5
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:5]

    def _calculate_path_criticality(self, path_details: list) -> float:
        """Calculate a criticality score for the path (higher = more critical)."""
        score = 0

        for step in path_details:
            risk_level = step.get("risk_level", "")
            if risk_level == "crown-jewel":
                score += 10
            elif risk_level == "critical":
                score += 7
            elif risk_level == "high":
                score += 5
            elif risk_level == "medium":
                score += 3

            node_type = step.get("type", "")
            if node_type == "secret":
                score += 8
            elif node_type == "serviceaccount":
                score += 6
            elif node_type == "database":
                score += 7

        return score

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
