import json
import random

NUM_NODES = 300
NUM_EDGES = 600

types = ['pod', 'service', 'internet', 'namespace', 'node', 'database', 'serviceaccount', 'rolebinding', 'clusterrole', 'secret', 'ingress']
risk_levels = ['critical', 'high', 'medium', 'low', 'info', 'crown-jewel', 'entry-point']
cve_list = ["CVE-2018-18264", "CVE-2023-49797", "CVE-2024-7646", "CVE-2024-28175", "CVE-2024-2912"]

nodes = []
edges = []

# Guaranteed entry point and crown jewel to make sure attack paths exist
nodes.append({
    "id": "internet-0",
    "label": "Public Internet",
    "type": "internet",
    "risk_level": "entry-point",
    "cves": []
})
nodes.append({
    "id": "db-cj-0",
    "label": "Core Production DB",
    "type": "database",
    "risk_level": "crown-jewel",
    "cves": []
})

for i in range(1, NUM_NODES - 1):
    ntype = random.choice(types)
    rlevel = random.choice(risk_levels)
    cves = []
    
    # Introduce some CVEs
    if random.random() < 0.2:
        cves.append(random.choice(cve_list))
        if random.random() < 0.1:
            cves.append(random.choice(cve_list))

    # Nginx ingress logic
    if ntype == 'ingress':
        rlevel = 'entry-point'
        
    if ntype == 'database' and random.random() < 0.3:
        rlevel = 'crown-jewel'

    nodes.append({
        "id": f"node-{i}",
        "label": f"{ntype.capitalize()} {i}",
        "type": ntype,
        "risk_level": rlevel,
        "cves": cves
    })

# Ensure connectivity from entry point to crown jewel by creating a forced path
forced_path = ["internet-0"] + [f"node-{random.randint(1, NUM_NODES - 2)}" for _ in range(4)] + ["db-cj-0"]
for i in range(len(forced_path) - 1):
    edges.append({
        "id": f"edge-forced-{i}",
        "source": forced_path[i],
        "target": forced_path[i+1],
        "type": "communicates_with"
    })

# Add random edges
for i in range(NUM_EDGES - len(forced_path) + 1):
    src = random.choice(nodes)["id"]
    dst = random.choice(nodes)["id"]
    if src != dst:
        edges.append({
            "id": f"edge-{i}",
            "source": src,
            "target": dst,
            "type": random.choice(["communicates_with", "mounts", "bound_to", "runs_on", "routes_to"])
        })

graph = {
    "metadata": {
        "cluster_name": f"Massive-Scale-Test-{NUM_NODES}",
        "scenario": "Load Testing Analysis"
    },
    "nodes": nodes,
    "edges": edges
}

with open("massive-cluster.json", "w") as f:
    json.dump(graph, f, indent=2)

print(f"Generated massive-cluster.json with {len(nodes)} nodes and {len(edges)} edges.")
