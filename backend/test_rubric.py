import sys
from graph_engine import K8sGraphEngine

e = K8sGraphEngine("mock-cluster-graph.json")
lines = []

lines.append(f"Nodes: {e.graph.number_of_nodes()}, Edges: {e.graph.number_of_edges()}")

# BFS-1
bfs1 = e.bfs_blast_radius("pod-webfront", 3)
layers = bfs1.get("hop_layers", {})
lines.append(f"\n=== BFS-1: pod-webfront, hops=3 ===")
lines.append(f"Total reachable: {bfs1['total_affected']}")
for h in sorted(layers.keys()):
    names = sorted([n.get("label", n["id"]) for n in layers[h]])
    lines.append(f"  Hop {h}: {names}")

# BFS-2
bfs2 = e.bfs_blast_radius("user-cicd", 2)
layers2 = bfs2.get("hop_layers", {})
lines.append(f"\n=== BFS-2: user-cicd, hops=2 ===")
lines.append(f"Total reachable: {bfs2['total_affected']}")
for h in sorted(layers2.keys()):
    names = sorted([n.get("label", n["id"]) for n in layers2[h]])
    lines.append(f"  Hop {h}: {names}")

# DIJK-1
dijk1 = e.dijkstra_shortest_path("user-dev1", "db-production")
path_names = [e.graph.nodes[n].get("label", n) for n in dijk1["path"]]
lines.append(f"\n=== DIJK-1: user-dev1 -> db-production ===")
lines.append(f"Path: {' -> '.join(path_names)}")
lines.append(f"Cost: {dijk1['total_weight']}, Hops: {dijk1['hop_count']}")

# DIJK-2
dijk2 = e.dijkstra_shortest_path("internet", "ns-kube-system")
path_names2 = [e.graph.nodes[n].get("label", n) for n in dijk2["path"]]
lines.append(f"\n=== DIJK-2: internet -> ns-kube-system ===")
lines.append(f"Path: {' -> '.join(path_names2)}")
lines.append(f"Cost: {dijk2['total_weight']}, Hops: {dijk2['hop_count']}")

# DIJK-3 (no path)
dijk3 = e.dijkstra_shortest_path("svc-service-a", "db-analytics")
lines.append(f"\n=== DIJK-3: no-path test ===")
lines.append(f"Path exists: {dijk3.get('path_exists', 'N/A')}")
lines.append(f"Error: {dijk3.get('error', 'none')}")

# DFS-1
cycles = e.dfs_cycle_detection()
lines.append(f"\n=== DFS-1: Cycle Detection ===")
lines.append(f"Cycles found: {cycles['total_cycles']}")
for c in cycles["cycles"]:
    lines.append(f"  {c['description']}")

# CNA-1
cna = e.critical_node_analysis()
lines.append(f"\n=== CNA-1: Critical Node ===")
lines.append(f"Baseline paths: {cna['baseline_paths']}")
cn = cna["critical_node"]
if cn:
    lines.append(f"Critical: {cn['label']} ({cn['type']}), broken: {cn['paths_broken']}")
lines.append("Top 5:")
for n in cna["top_5_nodes"]:
    lines.append(f"  {n['label']:30} ({n['type']:15}) -{n['paths_broken']} paths")

# All paths
all_paths = e.find_all_attack_paths()
lines.append(f"\n=== All Attack Paths: {len(all_paths)} ===")
for i, p in enumerate(all_paths, 1):
    src_name = e.graph.nodes[p["source"]].get("label", p["source"])
    tgt_name = e.graph.nodes[p["target"]].get("label", p["target"])
    lines.append(f"  #{i}: {src_name} -> {tgt_name} | {p['hops']} hops | cost={p['cost']}")

with open("test_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Done! Results in test_results.txt")
