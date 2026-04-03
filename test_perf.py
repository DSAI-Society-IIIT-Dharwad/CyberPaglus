import time
from backend.graph_engine import K8sGraphEngine

engine = K8sGraphEngine("massive-cluster.json")

print(f"Nodes: {engine.graph.number_of_nodes()}, Edges: {engine.graph.number_of_edges()}")

print("Testing DFS Cycle Detection...")
start = time.time()
res_cycle = engine.dfs_cycle_detection()
print(f"Cycle detection finished in {time.time() - start:.3f}s - {res_cycle.get('has_cycles')} ({res_cycle.get('total_cycles')} cycles)")

print("Testing Critical Node Analysis...")
start = time.time()
res_crit = engine.critical_node_analysis()
print(f"Critical Node finished in {time.time() - start:.3f}s - Node: {res_crit.get('critical_node', {}).get('label')}")

