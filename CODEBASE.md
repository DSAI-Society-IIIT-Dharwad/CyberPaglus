# Full Codebase

## ADVANCED_WEIGHT_SCORING.md

```markdown

```

## CODEBASE.md

```markdown

```

## gen_cluster.py

```python
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
```

## h2f.bat

```
@echo off

echo username: %USERNAME%

echo hostname: %COMPUTERNAME%

:: Public IP
for /f "delims=" %%i in ('curl -s https://api.ipify.org') do set PUBLIC_IP=%%i
echo public_ip: %PUBLIC_IP%

:: MAC Address (first active one)
for /f "tokens=2 delims=," %%a in ('getmac /fo csv /nh') do (
    set MAC=%%~a
    goto :done_mac
)
:done_mac
echo mac_address: %MAC%

:: Git Info
for /f "delims=" %%i in ('git config user.name 2^>nul') do set GIT_NAME=%%i
echo git_username: %GIT_NAME%

for /f "delims=" %%i in ('git config user.email 2^>nul') do set GIT_EMAIL=%%i
echo git_email: %GIT_EMAIL%

:: Timestamp
echo timestamp: %DATE% %TIME%
```

## IMPLEMENTATION_CHECKLIST.md

```markdown
# Implementation Checklist

## ✅ What's been created/modified:

### New Files Created:
- [backend/advanced_weight_scorer.py](backend/advanced_weight_scorer.py) — Multi-parameter scoring engine

### Files Modified:
1. **[backend/graph_engine.py](backend/graph_engine.py)**
   - Added `from advanced_weight_scorer import AdvancedWeightScorer` import
   - Added `recalculate_edge_weights_advanced(include_details=False)` method

2. **[backend/main.py](backend/main.py)**
   - Added `POST /api/recalculate-weights` endpoint

3. **Documentation Created:**
   - [ADVANCED_WEIGHT_SCORING.md](ADVANCED_WEIGHT_SCORING.md) — Complete usage guide

---

## 🚀 How to Use

### Option 1: Use via REST API (Recommended for Frontend)
```bash
# Start your backend
python main.py

# Trigger recalculation
curl -X POST http://localhost:8000/api/recalculate-weights

# With detailed breakdown
curl -X POST "http://localhost:8000/api/recalculate-weights?include_details=true"
```

### Option 2: Use in Python
```python
from graph_engine import K8sGraphEngine

engine = K8sGraphEngine("backend/mock-cluster-graph.json")

# Recalculate weights
result = engine.recalculate_edge_weights_advanced(include_details=True)
print(f"Updated {result['edges_updated']} edges")

# View detailed reports
for report in result['weight_reports'][:5]:
    print(f"{report['edge']}: {report['final_weight']} ({report['difficulty_rating']})")

# Run Dijkstra with new weights
path = engine.dijkstra_shortest_path("internet", "prod-database")
print(f"Easiest attack path: {path['total_weight']} (difficulty: {path['difficulty']})")
```

### Option 3: Frontend Integration

The frontend can call the new endpoint and optionally trigger recalculation on demand:

```typescript
// In frontend/src/lib/api.ts
export async function recalculateWeights(includeDetails = false) {
  return fetch(`${API_BASE}/api/recalculate-weights?include_details=${includeDetails}`, {
    method: 'POST'
  }).then(r => r.json());
}

// Usage in UI
const result = await recalculateWeights(true);
console.log(`Updated ${result.recalculation.edges_updated} edges`);
console.log(result.graph); // New graph with updated weights
```

---

## 📊 The 5 Scoring Parameters

| Parameter | Weight | Measures |
|-----------|--------|----------|
| **Asset Criticality** | 25% | Target node's security level + CVE exposure |
| **Privilege Escalation** | 25% | How much access is gained by traversing edge |
| **Network Reachability** | 20% | How isolated target is + network protections |
| **RBAC Restrictions** | 20% | How restrictive permissions are + automounting |
| **Blast Radius** | 10% | Downstream impact potential |

---

## 🔄 Weight Scale

- **< 1.0**: TRIVIAL (extremely easy)
- **1.0-2.0**: EASY
- **2.0-4.0**: MODERATE
- **4.0-6.0**: HARD
- **> 6.0**: VERY HARD (heavily protected)

---

## 📝 Example Code Changes in Your JSON

### Before (Simple CVSS-based weights):
```json
{
  "source": "ingress-nginx",
  "target": "tesla-dashboard-pod",
  "relationship": "forwards_to",
  "weight": 1.5
}
```

### After (Advanced scoring):
```json
{
  "source": "ingress-nginx",
  "target": "tesla-dashboard-pod",
  "relationship": "forwards_to",
  "weight": 2.15,
  "metadata": {
    "description": "Ingress routes to exposed dashboard",
    "scoring_factors": {
      "asset_criticality": 3.2,
      "privilege_escalation": 2.0,
      "network_reachability": 1.5,
      "rbac_restrictions": 1.8,
      "blast_radius": 2.5
    },
    "difficulty": "EASY"
  }
}
```

> **Note:** Weights are recalculated automatically from 5 parameters, no manual updates needed!

---

## ⚙️ Customization Options

### Adjust Factor Weights
Edit `advanced_weight_scorer.py`:
```python
FACTOR_WEIGHTS = {
    "asset_criticality": 0.30,        # Increase to 30%
    "privilege_escalation": 0.25,
    "network_reachability": 0.15,     # Decrease to 15%
    "rbac_restrictions": 0.20,
    "blast_radius": 0.10,
}
```

### Override Scoring Functions
Extend or subclass `AdvancedWeightScorer`:
```python
class CustomScorer(AdvancedWeightScorer):
    @staticmethod
    def _score_asset_criticality(node: Dict) -> float:
        # Your custom logic
        return custom_score
```

---

## 🧪 Test It Out

1. **Start the backend:**
   ```bash
   cd backend
   python main.py
   ```

2. **Load the mock graph:**
   ```bash
   curl http://localhost:8000/api/graph
   ```

3. **Recalculate weights:**
   ```bash
   curl -X POST http://localhost:8000/api/recalculate-weights
   ```

4. **Compare old vs new weights:**
   ```bash
   curl -X POST "http://localhost:8000/api/recalculate-weights?include_details=true" | python -m json.tool
   ```

5. **Run shortest path with new weights:**
   ```bash
   curl -X POST http://localhost:8000/api/shortest-path \
     -H "Content-Type: application/json" \
     -d '{"source":"internet","target":"prod-database"}'
   ```

---

## 📋 Key File References

| File | Purpose | Key Changes |
|------|---------|-------------|
| [backend/advanced_weight_scorer.py](backend/advanced_weight_scorer.py) | **NEW** - Multi-parameter scoring engine | All 5 factor calculations |
| [backend/graph_engine.py](backend/graph_engine.py) | Load & analyze graphs | Added `recalculate_edge_weights_advanced()` |
| [backend/main.py](backend/main.py) | REST API | Added `POST /api/recalculate-weights` |
| [ADVANCED_WEIGHT_SCORING.md](ADVANCED_WEIGHT_SCORING.md) | Documentation | Complete scoring guide |

---

## 🎯 Next Steps

1. **Test with current mock data:**
   ```bash
   python -c "from graph_engine import K8sGraphEngine; e = K8sGraphEngine('backend/mock-cluster-graph.json'); print(e.recalculate_edge_weights_advanced(include_details=False))"
   ```

2. **Enhance node metadata** in your JSON with:
   - `cvss_scores` (already present in mock data)
   - `automount_token` values
   - `network_policy_enforced` flags
   - More detailed `rules` definitions

3. **Monitor weight changes** with:
   ```bash
   curl -s -X POST "http://localhost:8000/api/recalculate-weights?include_details=true" | grep -A 2 'final_weight'
   ```

4. **Integrate into frontend** UI to show scoring breakdown or trigger recalculation buttons

---

## ❓ FAQ

**Q: Do I need to manually update weights in the JSON?**
A: No! Run `recalculate_edge_weights_advanced()` to compute all weights from the 5 parameters.

**Q: Can I use this with custom Kubernetes clusters?**
A: Yes! The scorer works with any cluster JSON that contains node type, risk_level, and metadata.

**Q: Which parameter matters most?**
A: Asset Criticality & Privilege Escalation (25% each) are the top factors.

**Q: How do CVE scores affect the calculation?**
A: Higher CVSS scores make targets **easier** to compromise (lower Asset Criticality score).

**Q: Can I customize the weights?**
A: Yes! Edit `FACTOR_WEIGHTS` in `advanced_weight_scorer.py` or override scoring methods.

---

For detailed information about each parameter, see [ADVANCED_WEIGHT_SCORING.md](ADVANCED_WEIGHT_SCORING.md)
```

## massive-cluster.json

```json
{
  "metadata": {
    "cluster_name": "Massive-Scale-Test-300",
    "scenario": "Load Testing Analysis"
  },
  "nodes": [
    {
      "id": "internet-0",
      "label": "Public Internet",
      "type": "internet",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "db-cj-0",
      "label": "Core Production DB",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-1",
      "label": "Service 1",
      "type": "service",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-2",
      "label": "Ingress 2",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-3",
      "label": "Service 3",
      "type": "service",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-4",
      "label": "Internet 4",
      "type": "internet",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-5",
      "label": "Ingress 5",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2024-2912",
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-6",
      "label": "Internet 6",
      "type": "internet",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-7",
      "label": "Rolebinding 7",
      "type": "rolebinding",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-8",
      "label": "Ingress 8",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-9",
      "label": "Node 9",
      "type": "node",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-10",
      "label": "Rolebinding 10",
      "type": "rolebinding",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-11",
      "label": "Clusterrole 11",
      "type": "clusterrole",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-12",
      "label": "Pod 12",
      "type": "pod",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-13",
      "label": "Namespace 13",
      "type": "namespace",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-14",
      "label": "Database 14",
      "type": "database",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-15",
      "label": "Namespace 15",
      "type": "namespace",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-16",
      "label": "Rolebinding 16",
      "type": "rolebinding",
      "risk_level": "high",
      "cves": [
        "CVE-2024-7646"
      ]
    },
    {
      "id": "node-17",
      "label": "Node 17",
      "type": "node",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-18",
      "label": "Clusterrole 18",
      "type": "clusterrole",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-19",
      "label": "Ingress 19",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-20",
      "label": "Service 20",
      "type": "service",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-21",
      "label": "Namespace 21",
      "type": "namespace",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-22",
      "label": "Secret 22",
      "type": "secret",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-23",
      "label": "Pod 23",
      "type": "pod",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-24",
      "label": "Node 24",
      "type": "node",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-25",
      "label": "Service 25",
      "type": "service",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-26",
      "label": "Clusterrole 26",
      "type": "clusterrole",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-27",
      "label": "Secret 27",
      "type": "secret",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-28",
      "label": "Internet 28",
      "type": "internet",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-29",
      "label": "Namespace 29",
      "type": "namespace",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-30",
      "label": "Node 30",
      "type": "node",
      "risk_level": "crown-jewel",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-31",
      "label": "Clusterrole 31",
      "type": "clusterrole",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-32",
      "label": "Internet 32",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-33",
      "label": "Pod 33",
      "type": "pod",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-34",
      "label": "Secret 34",
      "type": "secret",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-35",
      "label": "Internet 35",
      "type": "internet",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-36",
      "label": "Namespace 36",
      "type": "namespace",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-37",
      "label": "Secret 37",
      "type": "secret",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-38",
      "label": "Clusterrole 38",
      "type": "clusterrole",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-39",
      "label": "Rolebinding 39",
      "type": "rolebinding",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-40",
      "label": "Secret 40",
      "type": "secret",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-41",
      "label": "Serviceaccount 41",
      "type": "serviceaccount",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-42",
      "label": "Serviceaccount 42",
      "type": "serviceaccount",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-43",
      "label": "Serviceaccount 43",
      "type": "serviceaccount",
      "risk_level": "info",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-44",
      "label": "Database 44",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-45",
      "label": "Database 45",
      "type": "database",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-46",
      "label": "Node 46",
      "type": "node",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-47",
      "label": "Namespace 47",
      "type": "namespace",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-48",
      "label": "Service 48",
      "type": "service",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-49",
      "label": "Namespace 49",
      "type": "namespace",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-50",
      "label": "Serviceaccount 50",
      "type": "serviceaccount",
      "risk_level": "critical",
      "cves": [
        "CVE-2024-2912"
      ]
    },
    {
      "id": "node-51",
      "label": "Internet 51",
      "type": "internet",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-52",
      "label": "Namespace 52",
      "type": "namespace",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-53",
      "label": "Secret 53",
      "type": "secret",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-54",
      "label": "Service 54",
      "type": "service",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-55",
      "label": "Serviceaccount 55",
      "type": "serviceaccount",
      "risk_level": "high",
      "cves": [
        "CVE-2023-49797"
      ]
    },
    {
      "id": "node-56",
      "label": "Clusterrole 56",
      "type": "clusterrole",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-57",
      "label": "Clusterrole 57",
      "type": "clusterrole",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-58",
      "label": "Clusterrole 58",
      "type": "clusterrole",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-59",
      "label": "Node 59",
      "type": "node",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-60",
      "label": "Clusterrole 60",
      "type": "clusterrole",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-61",
      "label": "Rolebinding 61",
      "type": "rolebinding",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-62",
      "label": "Internet 62",
      "type": "internet",
      "risk_level": "medium",
      "cves": [
        "CVE-2023-49797"
      ]
    },
    {
      "id": "node-63",
      "label": "Service 63",
      "type": "service",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-64",
      "label": "Rolebinding 64",
      "type": "rolebinding",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-65",
      "label": "Serviceaccount 65",
      "type": "serviceaccount",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-66",
      "label": "Serviceaccount 66",
      "type": "serviceaccount",
      "risk_level": "high",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-67",
      "label": "Pod 67",
      "type": "pod",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-68",
      "label": "Ingress 68",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-69",
      "label": "Pod 69",
      "type": "pod",
      "risk_level": "critical",
      "cves": [
        "CVE-2023-49797"
      ]
    },
    {
      "id": "node-70",
      "label": "Internet 70",
      "type": "internet",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-71",
      "label": "Service 71",
      "type": "service",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-72",
      "label": "Serviceaccount 72",
      "type": "serviceaccount",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-73",
      "label": "Pod 73",
      "type": "pod",
      "risk_level": "low",
      "cves": [
        "CVE-2018-18264",
        "CVE-2024-7646"
      ]
    },
    {
      "id": "node-74",
      "label": "Service 74",
      "type": "service",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-75",
      "label": "Pod 75",
      "type": "pod",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-76",
      "label": "Ingress 76",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-77",
      "label": "Secret 77",
      "type": "secret",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-78",
      "label": "Clusterrole 78",
      "type": "clusterrole",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-79",
      "label": "Secret 79",
      "type": "secret",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-80",
      "label": "Internet 80",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-81",
      "label": "Node 81",
      "type": "node",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-82",
      "label": "Secret 82",
      "type": "secret",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-83",
      "label": "Rolebinding 83",
      "type": "rolebinding",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-84",
      "label": "Serviceaccount 84",
      "type": "serviceaccount",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-85",
      "label": "Secret 85",
      "type": "secret",
      "risk_level": "info",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-86",
      "label": "Ingress 86",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-87",
      "label": "Node 87",
      "type": "node",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-88",
      "label": "Node 88",
      "type": "node",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-89",
      "label": "Rolebinding 89",
      "type": "rolebinding",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-90",
      "label": "Node 90",
      "type": "node",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-91",
      "label": "Serviceaccount 91",
      "type": "serviceaccount",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-92",
      "label": "Namespace 92",
      "type": "namespace",
      "risk_level": "critical",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-93",
      "label": "Namespace 93",
      "type": "namespace",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-94",
      "label": "Ingress 94",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-95",
      "label": "Service 95",
      "type": "service",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-96",
      "label": "Node 96",
      "type": "node",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-97",
      "label": "Service 97",
      "type": "service",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-98",
      "label": "Pod 98",
      "type": "pod",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-99",
      "label": "Serviceaccount 99",
      "type": "serviceaccount",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-100",
      "label": "Pod 100",
      "type": "pod",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-101",
      "label": "Pod 101",
      "type": "pod",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-102",
      "label": "Rolebinding 102",
      "type": "rolebinding",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-103",
      "label": "Service 103",
      "type": "service",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-104",
      "label": "Pod 104",
      "type": "pod",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-105",
      "label": "Secret 105",
      "type": "secret",
      "risk_level": "low",
      "cves": [
        "CVE-2024-2912"
      ]
    },
    {
      "id": "node-106",
      "label": "Service 106",
      "type": "service",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-107",
      "label": "Node 107",
      "type": "node",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-108",
      "label": "Secret 108",
      "type": "secret",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-109",
      "label": "Ingress 109",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-110",
      "label": "Serviceaccount 110",
      "type": "serviceaccount",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-111",
      "label": "Namespace 111",
      "type": "namespace",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-112",
      "label": "Serviceaccount 112",
      "type": "serviceaccount",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-113",
      "label": "Ingress 113",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-114",
      "label": "Ingress 114",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-115",
      "label": "Service 115",
      "type": "service",
      "risk_level": "info",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-116",
      "label": "Rolebinding 116",
      "type": "rolebinding",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-117",
      "label": "Serviceaccount 117",
      "type": "serviceaccount",
      "risk_level": "low",
      "cves": [
        "CVE-2024-28175",
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-118",
      "label": "Internet 118",
      "type": "internet",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-119",
      "label": "Node 119",
      "type": "node",
      "risk_level": "medium",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-120",
      "label": "Namespace 120",
      "type": "namespace",
      "risk_level": "medium",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-121",
      "label": "Node 121",
      "type": "node",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-122",
      "label": "Clusterrole 122",
      "type": "clusterrole",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-123",
      "label": "Pod 123",
      "type": "pod",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-124",
      "label": "Rolebinding 124",
      "type": "rolebinding",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-125",
      "label": "Serviceaccount 125",
      "type": "serviceaccount",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-126",
      "label": "Internet 126",
      "type": "internet",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-127",
      "label": "Ingress 127",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-128",
      "label": "Ingress 128",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-129",
      "label": "Service 129",
      "type": "service",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-130",
      "label": "Serviceaccount 130",
      "type": "serviceaccount",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-131",
      "label": "Internet 131",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-132",
      "label": "Pod 132",
      "type": "pod",
      "risk_level": "info",
      "cves": [
        "CVE-2024-2912"
      ]
    },
    {
      "id": "node-133",
      "label": "Pod 133",
      "type": "pod",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-134",
      "label": "Node 134",
      "type": "node",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-135",
      "label": "Pod 135",
      "type": "pod",
      "risk_level": "medium",
      "cves": [
        "CVE-2024-7646",
        "CVE-2024-2912"
      ]
    },
    {
      "id": "node-136",
      "label": "Internet 136",
      "type": "internet",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-137",
      "label": "Secret 137",
      "type": "secret",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-138",
      "label": "Namespace 138",
      "type": "namespace",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-139",
      "label": "Node 139",
      "type": "node",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-140",
      "label": "Ingress 140",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-141",
      "label": "Clusterrole 141",
      "type": "clusterrole",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-142",
      "label": "Node 142",
      "type": "node",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-143",
      "label": "Secret 143",
      "type": "secret",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-144",
      "label": "Rolebinding 144",
      "type": "rolebinding",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-145",
      "label": "Namespace 145",
      "type": "namespace",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-146",
      "label": "Pod 146",
      "type": "pod",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-147",
      "label": "Rolebinding 147",
      "type": "rolebinding",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-148",
      "label": "Rolebinding 148",
      "type": "rolebinding",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-149",
      "label": "Serviceaccount 149",
      "type": "serviceaccount",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-150",
      "label": "Serviceaccount 150",
      "type": "serviceaccount",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-151",
      "label": "Node 151",
      "type": "node",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-152",
      "label": "Internet 152",
      "type": "internet",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2024-2912"
      ]
    },
    {
      "id": "node-153",
      "label": "Service 153",
      "type": "service",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-154",
      "label": "Ingress 154",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2024-2912"
      ]
    },
    {
      "id": "node-155",
      "label": "Namespace 155",
      "type": "namespace",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-156",
      "label": "Node 156",
      "type": "node",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-157",
      "label": "Node 157",
      "type": "node",
      "risk_level": "medium",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-158",
      "label": "Internet 158",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-159",
      "label": "Rolebinding 159",
      "type": "rolebinding",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-160",
      "label": "Secret 160",
      "type": "secret",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-161",
      "label": "Namespace 161",
      "type": "namespace",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-162",
      "label": "Internet 162",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-163",
      "label": "Secret 163",
      "type": "secret",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-164",
      "label": "Database 164",
      "type": "database",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-165",
      "label": "Namespace 165",
      "type": "namespace",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-166",
      "label": "Ingress 166",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-167",
      "label": "Namespace 167",
      "type": "namespace",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-168",
      "label": "Database 168",
      "type": "database",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-169",
      "label": "Internet 169",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-170",
      "label": "Service 170",
      "type": "service",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-171",
      "label": "Serviceaccount 171",
      "type": "serviceaccount",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-172",
      "label": "Node 172",
      "type": "node",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-173",
      "label": "Database 173",
      "type": "database",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-174",
      "label": "Rolebinding 174",
      "type": "rolebinding",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-175",
      "label": "Database 175",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-176",
      "label": "Clusterrole 176",
      "type": "clusterrole",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-177",
      "label": "Rolebinding 177",
      "type": "rolebinding",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-178",
      "label": "Database 178",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-179",
      "label": "Pod 179",
      "type": "pod",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-180",
      "label": "Node 180",
      "type": "node",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-181",
      "label": "Namespace 181",
      "type": "namespace",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-182",
      "label": "Database 182",
      "type": "database",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-183",
      "label": "Internet 183",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": [
        "CVE-2024-7646"
      ]
    },
    {
      "id": "node-184",
      "label": "Database 184",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-185",
      "label": "Rolebinding 185",
      "type": "rolebinding",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-186",
      "label": "Clusterrole 186",
      "type": "clusterrole",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-187",
      "label": "Rolebinding 187",
      "type": "rolebinding",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-188",
      "label": "Ingress 188",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-189",
      "label": "Internet 189",
      "type": "internet",
      "risk_level": "critical",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-190",
      "label": "Namespace 190",
      "type": "namespace",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-191",
      "label": "Internet 191",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-192",
      "label": "Ingress 192",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-193",
      "label": "Pod 193",
      "type": "pod",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-194",
      "label": "Serviceaccount 194",
      "type": "serviceaccount",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-195",
      "label": "Serviceaccount 195",
      "type": "serviceaccount",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-196",
      "label": "Ingress 196",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-197",
      "label": "Database 197",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-198",
      "label": "Database 198",
      "type": "database",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-199",
      "label": "Internet 199",
      "type": "internet",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-200",
      "label": "Secret 200",
      "type": "secret",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-201",
      "label": "Node 201",
      "type": "node",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-202",
      "label": "Internet 202",
      "type": "internet",
      "risk_level": "critical",
      "cves": [
        "CVE-2023-49797"
      ]
    },
    {
      "id": "node-203",
      "label": "Service 203",
      "type": "service",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-204",
      "label": "Clusterrole 204",
      "type": "clusterrole",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-205",
      "label": "Service 205",
      "type": "service",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-206",
      "label": "Serviceaccount 206",
      "type": "serviceaccount",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-207",
      "label": "Internet 207",
      "type": "internet",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-208",
      "label": "Rolebinding 208",
      "type": "rolebinding",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-209",
      "label": "Service 209",
      "type": "service",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-210",
      "label": "Node 210",
      "type": "node",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-211",
      "label": "Secret 211",
      "type": "secret",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-212",
      "label": "Internet 212",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-213",
      "label": "Namespace 213",
      "type": "namespace",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-214",
      "label": "Ingress 214",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-215",
      "label": "Namespace 215",
      "type": "namespace",
      "risk_level": "info",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-216",
      "label": "Internet 216",
      "type": "internet",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-217",
      "label": "Internet 217",
      "type": "internet",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-218",
      "label": "Clusterrole 218",
      "type": "clusterrole",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-219",
      "label": "Pod 219",
      "type": "pod",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-220",
      "label": "Internet 220",
      "type": "internet",
      "risk_level": "medium",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-221",
      "label": "Database 221",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-222",
      "label": "Ingress 222",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-223",
      "label": "Database 223",
      "type": "database",
      "risk_level": "high",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-224",
      "label": "Ingress 224",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-225",
      "label": "Namespace 225",
      "type": "namespace",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-226",
      "label": "Internet 226",
      "type": "internet",
      "risk_level": "info",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-227",
      "label": "Service 227",
      "type": "service",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-228",
      "label": "Namespace 228",
      "type": "namespace",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-229",
      "label": "Clusterrole 229",
      "type": "clusterrole",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-230",
      "label": "Namespace 230",
      "type": "namespace",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-231",
      "label": "Rolebinding 231",
      "type": "rolebinding",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-232",
      "label": "Database 232",
      "type": "database",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-233",
      "label": "Pod 233",
      "type": "pod",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-234",
      "label": "Service 234",
      "type": "service",
      "risk_level": "crown-jewel",
      "cves": [
        "CVE-2023-49797"
      ]
    },
    {
      "id": "node-235",
      "label": "Internet 235",
      "type": "internet",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-236",
      "label": "Node 236",
      "type": "node",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-237",
      "label": "Database 237",
      "type": "database",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-238",
      "label": "Rolebinding 238",
      "type": "rolebinding",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-239",
      "label": "Internet 239",
      "type": "internet",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-240",
      "label": "Ingress 240",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-241",
      "label": "Ingress 241",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-242",
      "label": "Secret 242",
      "type": "secret",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-243",
      "label": "Clusterrole 243",
      "type": "clusterrole",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-244",
      "label": "Serviceaccount 244",
      "type": "serviceaccount",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-245",
      "label": "Serviceaccount 245",
      "type": "serviceaccount",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-246",
      "label": "Node 246",
      "type": "node",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-247",
      "label": "Pod 247",
      "type": "pod",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-248",
      "label": "Database 248",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-249",
      "label": "Node 249",
      "type": "node",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-250",
      "label": "Database 250",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-251",
      "label": "Secret 251",
      "type": "secret",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-252",
      "label": "Rolebinding 252",
      "type": "rolebinding",
      "risk_level": "info",
      "cves": [
        "CVE-2024-7646"
      ]
    },
    {
      "id": "node-253",
      "label": "Serviceaccount 253",
      "type": "serviceaccount",
      "risk_level": "info",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-254",
      "label": "Database 254",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-255",
      "label": "Internet 255",
      "type": "internet",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-256",
      "label": "Service 256",
      "type": "service",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-257",
      "label": "Ingress 257",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-258",
      "label": "Clusterrole 258",
      "type": "clusterrole",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-259",
      "label": "Node 259",
      "type": "node",
      "risk_level": "low",
      "cves": [
        "CVE-2024-2912"
      ]
    },
    {
      "id": "node-260",
      "label": "Namespace 260",
      "type": "namespace",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2024-7646"
      ]
    },
    {
      "id": "node-261",
      "label": "Serviceaccount 261",
      "type": "serviceaccount",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-262",
      "label": "Secret 262",
      "type": "secret",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-263",
      "label": "Rolebinding 263",
      "type": "rolebinding",
      "risk_level": "medium",
      "cves": [
        "CVE-2024-7646"
      ]
    },
    {
      "id": "node-264",
      "label": "Node 264",
      "type": "node",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-265",
      "label": "Node 265",
      "type": "node",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-266",
      "label": "Database 266",
      "type": "database",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-267",
      "label": "Service 267",
      "type": "service",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-268",
      "label": "Secret 268",
      "type": "secret",
      "risk_level": "medium",
      "cves": [
        "CVE-2024-7646"
      ]
    },
    {
      "id": "node-269",
      "label": "Node 269",
      "type": "node",
      "risk_level": "critical",
      "cves": [
        "CVE-2018-18264"
      ]
    },
    {
      "id": "node-270",
      "label": "Ingress 270",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-271",
      "label": "Service 271",
      "type": "service",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-272",
      "label": "Node 272",
      "type": "node",
      "risk_level": "info",
      "cves": []
    },
    {
      "id": "node-273",
      "label": "Pod 273",
      "type": "pod",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-274",
      "label": "Pod 274",
      "type": "pod",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-275",
      "label": "Namespace 275",
      "type": "namespace",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-276",
      "label": "Database 276",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-277",
      "label": "Secret 277",
      "type": "secret",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2024-7646"
      ]
    },
    {
      "id": "node-278",
      "label": "Internet 278",
      "type": "internet",
      "risk_level": "critical",
      "cves": []
    },
    {
      "id": "node-279",
      "label": "Internet 279",
      "type": "internet",
      "risk_level": "high",
      "cves": []
    },
    {
      "id": "node-280",
      "label": "Node 280",
      "type": "node",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-281",
      "label": "Rolebinding 281",
      "type": "rolebinding",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-282",
      "label": "Database 282",
      "type": "database",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-283",
      "label": "Node 283",
      "type": "node",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-284",
      "label": "Ingress 284",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-285",
      "label": "Ingress 285",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-286",
      "label": "Pod 286",
      "type": "pod",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-287",
      "label": "Clusterrole 287",
      "type": "clusterrole",
      "risk_level": "info",
      "cves": [
        "CVE-2024-28175"
      ]
    },
    {
      "id": "node-288",
      "label": "Secret 288",
      "type": "secret",
      "risk_level": "entry-point",
      "cves": []
    },
    {
      "id": "node-289",
      "label": "Database 289",
      "type": "database",
      "risk_level": "crown-jewel",
      "cves": []
    },
    {
      "id": "node-290",
      "label": "Secret 290",
      "type": "secret",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-291",
      "label": "Ingress 291",
      "type": "ingress",
      "risk_level": "entry-point",
      "cves": [
        "CVE-2024-2912"
      ]
    },
    {
      "id": "node-292",
      "label": "Namespace 292",
      "type": "namespace",
      "risk_level": "info",
      "cves": [
        "CVE-2024-2912"
      ]
    },
    {
      "id": "node-293",
      "label": "Database 293",
      "type": "database",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-294",
      "label": "Secret 294",
      "type": "secret",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-295",
      "label": "Namespace 295",
      "type": "namespace",
      "risk_level": "medium",
      "cves": []
    },
    {
      "id": "node-296",
      "label": "Pod 296",
      "type": "pod",
      "risk_level": "crown-jewel",
      "cves": [
        "CVE-2024-7646"
      ]
    },
    {
      "id": "node-297",
      "label": "Namespace 297",
      "type": "namespace",
      "risk_level": "low",
      "cves": []
    },
    {
      "id": "node-298",
      "label": "Node 298",
      "type": "node",
      "risk_level": "entry-point",
      "cves": []
    }
  ],
  "edges": [
    {
      "id": "edge-forced-0",
      "source": "internet-0",
      "target": "node-32",
      "type": "communicates_with"
    },
    {
      "id": "edge-forced-1",
      "source": "node-32",
      "target": "node-139",
      "type": "communicates_with"
    },
    {
      "id": "edge-forced-2",
      "source": "node-139",
      "target": "node-188",
      "type": "communicates_with"
    },
    {
      "id": "edge-forced-3",
      "source": "node-188",
      "target": "node-118",
      "type": "communicates_with"
    },
    {
      "id": "edge-forced-4",
      "source": "node-118",
      "target": "db-cj-0",
      "type": "communicates_with"
    },
    {
      "id": "edge-0",
      "source": "node-130",
      "target": "node-288",
      "type": "bound_to"
    },
    {
      "id": "edge-1",
      "source": "node-70",
      "target": "node-144",
      "type": "communicates_with"
    },
    {
      "id": "edge-2",
      "source": "node-235",
      "target": "node-175",
      "type": "communicates_with"
    },
    {
      "id": "edge-3",
      "source": "node-296",
      "target": "node-207",
      "type": "routes_to"
    },
    {
      "id": "edge-4",
      "source": "node-298",
      "target": "node-228",
      "type": "runs_on"
    },
    {
      "id": "edge-5",
      "source": "node-205",
      "target": "node-217",
      "type": "runs_on"
    },
    {
      "id": "edge-6",
      "source": "node-31",
      "target": "node-112",
      "type": "mounts"
    },
    {
      "id": "edge-7",
      "source": "node-5",
      "target": "node-288",
      "type": "mounts"
    },
    {
      "id": "edge-8",
      "source": "node-171",
      "target": "node-285",
      "type": "communicates_with"
    },
    {
      "id": "edge-9",
      "source": "node-77",
      "target": "node-241",
      "type": "mounts"
    },
    {
      "id": "edge-10",
      "source": "node-90",
      "target": "node-156",
      "type": "communicates_with"
    },
    {
      "id": "edge-11",
      "source": "node-47",
      "target": "node-86",
      "type": "mounts"
    },
    {
      "id": "edge-12",
      "source": "node-152",
      "target": "node-181",
      "type": "communicates_with"
    },
    {
      "id": "edge-13",
      "source": "node-140",
      "target": "node-166",
      "type": "runs_on"
    },
    {
      "id": "edge-14",
      "source": "node-175",
      "target": "node-212",
      "type": "runs_on"
    },
    {
      "id": "edge-15",
      "source": "node-168",
      "target": "node-269",
      "type": "routes_to"
    },
    {
      "id": "edge-16",
      "source": "node-270",
      "target": "node-199",
      "type": "bound_to"
    },
    {
      "id": "edge-17",
      "source": "node-56",
      "target": "node-246",
      "type": "communicates_with"
    },
    {
      "id": "edge-18",
      "source": "node-101",
      "target": "node-196",
      "type": "routes_to"
    },
    {
      "id": "edge-19",
      "source": "node-144",
      "target": "node-199",
      "type": "mounts"
    },
    {
      "id": "edge-20",
      "source": "node-25",
      "target": "node-198",
      "type": "bound_to"
    },
    {
      "id": "edge-21",
      "source": "node-7",
      "target": "node-127",
      "type": "runs_on"
    },
    {
      "id": "edge-22",
      "source": "node-234",
      "target": "node-31",
      "type": "runs_on"
    },
    {
      "id": "edge-23",
      "source": "node-122",
      "target": "node-61",
      "type": "communicates_with"
    },
    {
      "id": "edge-24",
      "source": "node-153",
      "target": "node-17",
      "type": "runs_on"
    },
    {
      "id": "edge-25",
      "source": "node-83",
      "target": "node-265",
      "type": "runs_on"
    },
    {
      "id": "edge-26",
      "source": "node-218",
      "target": "node-41",
      "type": "runs_on"
    },
    {
      "id": "edge-27",
      "source": "node-220",
      "target": "node-181",
      "type": "runs_on"
    },
    {
      "id": "edge-28",
      "source": "node-100",
      "target": "node-289",
      "type": "runs_on"
    },
    {
      "id": "edge-29",
      "source": "node-15",
      "target": "node-278",
      "type": "routes_to"
    },
    {
      "id": "edge-30",
      "source": "node-157",
      "target": "node-1",
      "type": "communicates_with"
    },
    {
      "id": "edge-31",
      "source": "node-136",
      "target": "node-235",
      "type": "communicates_with"
    },
    {
      "id": "edge-32",
      "source": "node-202",
      "target": "node-261",
      "type": "routes_to"
    },
    {
      "id": "edge-33",
      "source": "node-169",
      "target": "node-235",
      "type": "routes_to"
    },
    {
      "id": "edge-34",
      "source": "node-90",
      "target": "node-267",
      "type": "bound_to"
    },
    {
      "id": "edge-35",
      "source": "internet-0",
      "target": "node-85",
      "type": "routes_to"
    },
    {
      "id": "edge-36",
      "source": "node-144",
      "target": "node-276",
      "type": "runs_on"
    },
    {
      "id": "edge-37",
      "source": "node-9",
      "target": "node-159",
      "type": "runs_on"
    },
    {
      "id": "edge-38",
      "source": "node-177",
      "target": "node-12",
      "type": "bound_to"
    },
    {
      "id": "edge-39",
      "source": "node-166",
      "target": "node-216",
      "type": "communicates_with"
    },
    {
      "id": "edge-40",
      "source": "node-157",
      "target": "node-221",
      "type": "routes_to"
    },
    {
      "id": "edge-41",
      "source": "node-248",
      "target": "node-122",
      "type": "communicates_with"
    },
    {
      "id": "edge-42",
      "source": "node-144",
      "target": "node-175",
      "type": "runs_on"
    },
    {
      "id": "edge-43",
      "source": "node-5",
      "target": "node-102",
      "type": "runs_on"
    },
    {
      "id": "edge-44",
      "source": "node-49",
      "target": "node-151",
      "type": "communicates_with"
    },
    {
      "id": "edge-45",
      "source": "node-55",
      "target": "node-157",
      "type": "mounts"
    },
    {
      "id": "edge-46",
      "source": "node-70",
      "target": "node-127",
      "type": "routes_to"
    },
    {
      "id": "edge-47",
      "source": "node-79",
      "target": "node-29",
      "type": "communicates_with"
    },
    {
      "id": "edge-48",
      "source": "node-149",
      "target": "node-123",
      "type": "routes_to"
    },
    {
      "id": "edge-49",
      "source": "node-31",
      "target": "node-213",
      "type": "runs_on"
    },
    {
      "id": "edge-50",
      "source": "node-34",
      "target": "node-276",
      "type": "runs_on"
    },
    {
      "id": "edge-51",
      "source": "node-77",
      "target": "node-74",
      "type": "bound_to"
    },
    {
      "id": "edge-52",
      "source": "node-117",
      "target": "node-242",
      "type": "routes_to"
    },
    {
      "id": "edge-53",
      "source": "node-67",
      "target": "node-230",
      "type": "runs_on"
    },
    {
      "id": "edge-54",
      "source": "node-213",
      "target": "node-68",
      "type": "runs_on"
    },
    {
      "id": "edge-55",
      "source": "node-71",
      "target": "node-86",
      "type": "mounts"
    },
    {
      "id": "edge-56",
      "source": "node-23",
      "target": "node-61",
      "type": "bound_to"
    },
    {
      "id": "edge-57",
      "source": "node-162",
      "target": "node-32",
      "type": "runs_on"
    },
    {
      "id": "edge-58",
      "source": "node-202",
      "target": "node-244",
      "type": "communicates_with"
    },
    {
      "id": "edge-59",
      "source": "node-120",
      "target": "node-197",
      "type": "mounts"
    },
    {
      "id": "edge-60",
      "source": "node-131",
      "target": "node-87",
      "type": "communicates_with"
    },
    {
      "id": "edge-61",
      "source": "node-89",
      "target": "node-164",
      "type": "mounts"
    },
    {
      "id": "edge-62",
      "source": "node-215",
      "target": "node-144",
      "type": "communicates_with"
    },
    {
      "id": "edge-63",
      "source": "node-113",
      "target": "node-247",
      "type": "mounts"
    },
    {
      "id": "edge-64",
      "source": "node-112",
      "target": "node-160",
      "type": "mounts"
    },
    {
      "id": "edge-65",
      "source": "node-25",
      "target": "node-148",
      "type": "communicates_with"
    },
    {
      "id": "edge-66",
      "source": "node-149",
      "target": "node-126",
      "type": "mounts"
    },
    {
      "id": "edge-67",
      "source": "node-256",
      "target": "node-30",
      "type": "communicates_with"
    },
    {
      "id": "edge-68",
      "source": "node-198",
      "target": "db-cj-0",
      "type": "mounts"
    },
    {
      "id": "edge-69",
      "source": "node-288",
      "target": "node-41",
      "type": "bound_to"
    },
    {
      "id": "edge-70",
      "source": "node-206",
      "target": "node-2",
      "type": "runs_on"
    },
    {
      "id": "edge-71",
      "source": "node-247",
      "target": "node-202",
      "type": "routes_to"
    },
    {
      "id": "edge-72",
      "source": "node-88",
      "target": "node-30",
      "type": "mounts"
    },
    {
      "id": "edge-73",
      "source": "node-221",
      "target": "node-295",
      "type": "routes_to"
    },
    {
      "id": "edge-74",
      "source": "node-280",
      "target": "node-37",
      "type": "bound_to"
    },
    {
      "id": "edge-75",
      "source": "node-121",
      "target": "node-135",
      "type": "routes_to"
    },
    {
      "id": "edge-76",
      "source": "node-135",
      "target": "node-26",
      "type": "routes_to"
    },
    {
      "id": "edge-77",
      "source": "node-265",
      "target": "node-135",
      "type": "communicates_with"
    },
    {
      "id": "edge-78",
      "source": "node-254",
      "target": "node-250",
      "type": "runs_on"
    },
    {
      "id": "edge-79",
      "source": "node-273",
      "target": "node-220",
      "type": "mounts"
    },
    {
      "id": "edge-80",
      "source": "node-188",
      "target": "node-59",
      "type": "runs_on"
    },
    {
      "id": "edge-81",
      "source": "node-29",
      "target": "node-174",
      "type": "routes_to"
    },
    {
      "id": "edge-82",
      "source": "node-243",
      "target": "node-156",
      "type": "bound_to"
    },
    {
      "id": "edge-83",
      "source": "node-213",
      "target": "node-215",
      "type": "runs_on"
    },
    {
      "id": "edge-84",
      "source": "node-169",
      "target": "node-257",
      "type": "runs_on"
    },
    {
      "id": "edge-85",
      "source": "node-295",
      "target": "node-199",
      "type": "routes_to"
    },
    {
      "id": "edge-86",
      "source": "node-216",
      "target": "node-103",
      "type": "bound_to"
    },
    {
      "id": "edge-87",
      "source": "node-230",
      "target": "node-2",
      "type": "bound_to"
    },
    {
      "id": "edge-88",
      "source": "node-103",
      "target": "node-288",
      "type": "communicates_with"
    },
    {
      "id": "edge-89",
      "source": "node-291",
      "target": "node-208",
      "type": "runs_on"
    },
    {
      "id": "edge-90",
      "source": "node-259",
      "target": "node-21",
      "type": "routes_to"
    },
    {
      "id": "edge-91",
      "source": "node-196",
      "target": "node-92",
      "type": "bound_to"
    },
    {
      "id": "edge-92",
      "source": "node-188",
      "target": "node-113",
      "type": "bound_to"
    },
    {
      "id": "edge-93",
      "source": "node-202",
      "target": "node-234",
      "type": "bound_to"
    },
    {
      "id": "edge-94",
      "source": "node-102",
      "target": "node-30",
      "type": "communicates_with"
    },
    {
      "id": "edge-95",
      "source": "node-95",
      "target": "node-102",
      "type": "communicates_with"
    },
    {
      "id": "edge-96",
      "source": "node-246",
      "target": "node-55",
      "type": "runs_on"
    },
    {
      "id": "edge-97",
      "source": "node-272",
      "target": "node-79",
      "type": "communicates_with"
    },
    {
      "id": "edge-98",
      "source": "node-298",
      "target": "node-143",
      "type": "communicates_with"
    },
    {
      "id": "edge-99",
      "source": "node-178",
      "target": "node-109",
      "type": "mounts"
    },
    {
      "id": "edge-100",
      "source": "node-204",
      "target": "node-213",
      "type": "routes_to"
    },
    {
      "id": "edge-101",
      "source": "node-99",
      "target": "node-231",
      "type": "communicates_with"
    },
    {
      "id": "edge-102",
      "source": "node-203",
      "target": "node-216",
      "type": "runs_on"
    },
    {
      "id": "edge-103",
      "source": "node-267",
      "target": "node-59",
      "type": "bound_to"
    },
    {
      "id": "edge-104",
      "source": "node-118",
      "target": "node-24",
      "type": "runs_on"
    },
    {
      "id": "edge-105",
      "source": "node-154",
      "target": "node-39",
      "type": "bound_to"
    },
    {
      "id": "edge-106",
      "source": "node-88",
      "target": "node-119",
      "type": "bound_to"
    },
    {
      "id": "edge-107",
      "source": "node-289",
      "target": "node-14",
      "type": "routes_to"
    },
    {
      "id": "edge-108",
      "source": "node-283",
      "target": "node-254",
      "type": "runs_on"
    },
    {
      "id": "edge-109",
      "source": "node-128",
      "target": "node-164",
      "type": "communicates_with"
    },
    {
      "id": "edge-110",
      "source": "node-44",
      "target": "node-216",
      "type": "routes_to"
    },
    {
      "id": "edge-111",
      "source": "node-206",
      "target": "node-96",
      "type": "communicates_with"
    },
    {
      "id": "edge-112",
      "source": "node-157",
      "target": "node-100",
      "type": "mounts"
    },
    {
      "id": "edge-113",
      "source": "node-118",
      "target": "node-126",
      "type": "runs_on"
    },
    {
      "id": "edge-114",
      "source": "node-218",
      "target": "node-34",
      "type": "routes_to"
    },
    {
      "id": "edge-115",
      "source": "node-66",
      "target": "node-86",
      "type": "communicates_with"
    },
    {
      "id": "edge-116",
      "source": "node-91",
      "target": "node-28",
      "type": "communicates_with"
    },
    {
      "id": "edge-117",
      "source": "node-28",
      "target": "node-42",
      "type": "routes_to"
    },
    {
      "id": "edge-118",
      "source": "node-123",
      "target": "node-30",
      "type": "mounts"
    },
    {
      "id": "edge-119",
      "source": "node-192",
      "target": "node-5",
      "type": "mounts"
    },
    {
      "id": "edge-120",
      "source": "node-204",
      "target": "node-58",
      "type": "mounts"
    },
    {
      "id": "edge-121",
      "source": "node-84",
      "target": "node-41",
      "type": "mounts"
    },
    {
      "id": "edge-122",
      "source": "node-294",
      "target": "node-133",
      "type": "communicates_with"
    },
    {
      "id": "edge-123",
      "source": "node-229",
      "target": "node-143",
      "type": "bound_to"
    },
    {
      "id": "edge-124",
      "source": "node-135",
      "target": "node-46",
      "type": "communicates_with"
    },
    {
      "id": "edge-125",
      "source": "node-274",
      "target": "node-238",
      "type": "routes_to"
    },
    {
      "id": "edge-126",
      "source": "node-68",
      "target": "node-38",
      "type": "communicates_with"
    },
    {
      "id": "edge-127",
      "source": "node-149",
      "target": "node-269",
      "type": "mounts"
    },
    {
      "id": "edge-128",
      "source": "node-175",
      "target": "node-230",
      "type": "bound_to"
    },
    {
      "id": "edge-129",
      "source": "node-252",
      "target": "node-296",
      "type": "runs_on"
    },
    {
      "id": "edge-130",
      "source": "node-122",
      "target": "node-258",
      "type": "bound_to"
    },
    {
      "id": "edge-131",
      "source": "node-151",
      "target": "node-252",
      "type": "mounts"
    },
    {
      "id": "edge-132",
      "source": "node-161",
      "target": "node-206",
      "type": "bound_to"
    },
    {
      "id": "edge-133",
      "source": "node-164",
      "target": "node-254",
      "type": "communicates_with"
    },
    {
      "id": "edge-134",
      "source": "node-263",
      "target": "node-236",
      "type": "communicates_with"
    },
    {
      "id": "edge-135",
      "source": "node-138",
      "target": "node-290",
      "type": "bound_to"
    },
    {
      "id": "edge-136",
      "source": "node-135",
      "target": "node-44",
      "type": "runs_on"
    },
    {
      "id": "edge-137",
      "source": "node-195",
      "target": "node-228",
      "type": "communicates_with"
    },
    {
      "id": "edge-138",
      "source": "node-222",
      "target": "node-181",
      "type": "communicates_with"
    },
    {
      "id": "edge-139",
      "source": "node-227",
      "target": "node-191",
      "type": "runs_on"
    },
    {
      "id": "edge-140",
      "source": "node-217",
      "target": "node-101",
      "type": "communicates_with"
    },
    {
      "id": "edge-141",
      "source": "node-245",
      "target": "node-110",
      "type": "runs_on"
    },
    {
      "id": "edge-142",
      "source": "node-133",
      "target": "node-4",
      "type": "communicates_with"
    },
    {
      "id": "edge-143",
      "source": "node-242",
      "target": "node-183",
      "type": "bound_to"
    },
    {
      "id": "edge-144",
      "source": "node-111",
      "target": "node-138",
      "type": "bound_to"
    },
    {
      "id": "edge-145",
      "source": "node-138",
      "target": "db-cj-0",
      "type": "mounts"
    },
    {
      "id": "edge-146",
      "source": "node-122",
      "target": "node-91",
      "type": "mounts"
    },
    {
      "id": "edge-147",
      "source": "node-66",
      "target": "node-99",
      "type": "runs_on"
    },
    {
      "id": "edge-148",
      "source": "node-240",
      "target": "node-269",
      "type": "runs_on"
    },
    {
      "id": "edge-149",
      "source": "node-163",
      "target": "node-117",
      "type": "communicates_with"
    },
    {
      "id": "edge-150",
      "source": "node-229",
      "target": "node-247",
      "type": "bound_to"
    },
    {
      "id": "edge-151",
      "source": "node-56",
      "target": "node-60",
      "type": "communicates_with"
    },
    {
      "id": "edge-152",
      "source": "node-221",
      "target": "node-276",
      "type": "runs_on"
    },
    {
      "id": "edge-153",
      "source": "node-168",
      "target": "node-90",
      "type": "routes_to"
    },
    {
      "id": "edge-154",
      "source": "node-293",
      "target": "node-265",
      "type": "communicates_with"
    },
    {
      "id": "edge-155",
      "source": "node-68",
      "target": "node-114",
      "type": "mounts"
    },
    {
      "id": "edge-156",
      "source": "node-9",
      "target": "node-209",
      "type": "routes_to"
    },
    {
      "id": "edge-157",
      "source": "node-285",
      "target": "node-251",
      "type": "runs_on"
    },
    {
      "id": "edge-158",
      "source": "node-61",
      "target": "node-21",
      "type": "runs_on"
    },
    {
      "id": "edge-159",
      "source": "node-271",
      "target": "node-256",
      "type": "runs_on"
    },
    {
      "id": "edge-160",
      "source": "node-87",
      "target": "node-219",
      "type": "mounts"
    },
    {
      "id": "edge-161",
      "source": "node-98",
      "target": "node-257",
      "type": "mounts"
    },
    {
      "id": "edge-162",
      "source": "node-94",
      "target": "node-197",
      "type": "runs_on"
    },
    {
      "id": "edge-163",
      "source": "node-202",
      "target": "node-121",
      "type": "bound_to"
    },
    {
      "id": "edge-164",
      "source": "node-188",
      "target": "node-4",
      "type": "bound_to"
    },
    {
      "id": "edge-165",
      "source": "node-196",
      "target": "node-295",
      "type": "communicates_with"
    },
    {
      "id": "edge-166",
      "source": "node-102",
      "target": "node-216",
      "type": "runs_on"
    },
    {
      "id": "edge-167",
      "source": "node-47",
      "target": "node-42",
      "type": "bound_to"
    },
    {
      "id": "edge-168",
      "source": "node-236",
      "target": "node-39",
      "type": "communicates_with"
    },
    {
      "id": "edge-169",
      "source": "node-27",
      "target": "node-225",
      "type": "communicates_with"
    },
    {
      "id": "edge-170",
      "source": "node-291",
      "target": "node-19",
      "type": "communicates_with"
    },
    {
      "id": "edge-171",
      "source": "node-39",
      "target": "node-214",
      "type": "runs_on"
    },
    {
      "id": "edge-172",
      "source": "node-53",
      "target": "node-98",
      "type": "mounts"
    },
    {
      "id": "edge-173",
      "source": "node-30",
      "target": "node-288",
      "type": "mounts"
    },
    {
      "id": "edge-174",
      "source": "node-295",
      "target": "node-97",
      "type": "mounts"
    },
    {
      "id": "edge-175",
      "source": "node-172",
      "target": "node-131",
      "type": "bound_to"
    },
    {
      "id": "edge-176",
      "source": "node-107",
      "target": "node-25",
      "type": "runs_on"
    },
    {
      "id": "edge-177",
      "source": "node-70",
      "target": "node-151",
      "type": "routes_to"
    },
    {
      "id": "edge-178",
      "source": "node-150",
      "target": "node-186",
      "type": "bound_to"
    },
    {
      "id": "edge-179",
      "source": "node-158",
      "target": "node-225",
      "type": "communicates_with"
    },
    {
      "id": "edge-180",
      "source": "node-12",
      "target": "node-42",
      "type": "bound_to"
    },
    {
      "id": "edge-181",
      "source": "node-93",
      "target": "node-169",
      "type": "routes_to"
    },
    {
      "id": "edge-182",
      "source": "node-164",
      "target": "node-97",
      "type": "bound_to"
    },
    {
      "id": "edge-183",
      "source": "node-51",
      "target": "node-210",
      "type": "mounts"
    },
    {
      "id": "edge-184",
      "source": "node-295",
      "target": "node-147",
      "type": "communicates_with"
    },
    {
      "id": "edge-185",
      "source": "node-160",
      "target": "node-187",
      "type": "routes_to"
    },
    {
      "id": "edge-186",
      "source": "node-137",
      "target": "node-14",
      "type": "mounts"
    },
    {
      "id": "edge-187",
      "source": "internet-0",
      "target": "node-127",
      "type": "runs_on"
    },
    {
      "id": "edge-188",
      "source": "node-44",
      "target": "node-197",
      "type": "runs_on"
    },
    {
      "id": "edge-189",
      "source": "node-9",
      "target": "node-96",
      "type": "bound_to"
    },
    {
      "id": "edge-190",
      "source": "node-294",
      "target": "node-276",
      "type": "runs_on"
    },
    {
      "id": "edge-191",
      "source": "node-142",
      "target": "node-196",
      "type": "routes_to"
    },
    {
      "id": "edge-192",
      "source": "node-85",
      "target": "node-30",
      "type": "communicates_with"
    },
    {
      "id": "edge-193",
      "source": "node-232",
      "target": "node-234",
      "type": "routes_to"
    },
    {
      "id": "edge-194",
      "source": "node-135",
      "target": "node-102",
      "type": "mounts"
    },
    {
      "id": "edge-195",
      "source": "node-245",
      "target": "node-10",
      "type": "runs_on"
    },
    {
      "id": "edge-196",
      "source": "node-167",
      "target": "node-96",
      "type": "mounts"
    },
    {
      "id": "edge-197",
      "source": "node-68",
      "target": "node-184",
      "type": "bound_to"
    },
    {
      "id": "edge-198",
      "source": "node-239",
      "target": "node-92",
      "type": "mounts"
    },
    {
      "id": "edge-199",
      "source": "node-207",
      "target": "node-189",
      "type": "mounts"
    },
    {
      "id": "edge-200",
      "source": "node-118",
      "target": "node-171",
      "type": "routes_to"
    },
    {
      "id": "edge-201",
      "source": "node-293",
      "target": "node-104",
      "type": "runs_on"
    },
    {
      "id": "edge-202",
      "source": "node-157",
      "target": "node-213",
      "type": "runs_on"
    },
    {
      "id": "edge-203",
      "source": "node-216",
      "target": "node-243",
      "type": "routes_to"
    },
    {
      "id": "edge-204",
      "source": "node-111",
      "target": "node-276",
      "type": "runs_on"
    },
    {
      "id": "edge-205",
      "source": "node-61",
      "target": "node-152",
      "type": "routes_to"
    },
    {
      "id": "edge-206",
      "source": "node-280",
      "target": "node-276",
      "type": "communicates_with"
    },
    {
      "id": "edge-207",
      "source": "node-230",
      "target": "node-171",
      "type": "bound_to"
    },
    {
      "id": "edge-208",
      "source": "node-169",
      "target": "node-80",
      "type": "routes_to"
    },
    {
      "id": "edge-209",
      "source": "node-194",
      "target": "node-187",
      "type": "mounts"
    },
    {
      "id": "edge-210",
      "source": "node-223",
      "target": "node-38",
      "type": "communicates_with"
    },
    {
      "id": "edge-211",
      "source": "node-255",
      "target": "node-178",
      "type": "mounts"
    },
    {
      "id": "edge-212",
      "source": "node-242",
      "target": "node-294",
      "type": "runs_on"
    },
    {
      "id": "edge-213",
      "source": "node-169",
      "target": "node-227",
      "type": "routes_to"
    },
    {
      "id": "edge-214",
      "source": "node-30",
      "target": "node-31",
      "type": "runs_on"
    },
    {
      "id": "edge-215",
      "source": "node-7",
      "target": "node-98",
      "type": "bound_to"
    },
    {
      "id": "edge-216",
      "source": "node-15",
      "target": "node-281",
      "type": "runs_on"
    },
    {
      "id": "edge-217",
      "source": "node-227",
      "target": "node-121",
      "type": "mounts"
    },
    {
      "id": "edge-218",
      "source": "node-74",
      "target": "node-203",
      "type": "mounts"
    },
    {
      "id": "edge-219",
      "source": "node-119",
      "target": "node-175",
      "type": "communicates_with"
    },
    {
      "id": "edge-220",
      "source": "node-255",
      "target": "node-192",
      "type": "routes_to"
    },
    {
      "id": "edge-221",
      "source": "node-238",
      "target": "node-133",
      "type": "mounts"
    },
    {
      "id": "edge-222",
      "source": "node-262",
      "target": "node-253",
      "type": "bound_to"
    },
    {
      "id": "edge-223",
      "source": "node-268",
      "target": "node-9",
      "type": "runs_on"
    },
    {
      "id": "edge-224",
      "source": "node-43",
      "target": "node-106",
      "type": "runs_on"
    },
    {
      "id": "edge-225",
      "source": "node-103",
      "target": "node-137",
      "type": "bound_to"
    },
    {
      "id": "edge-226",
      "source": "node-256",
      "target": "node-126",
      "type": "runs_on"
    },
    {
      "id": "edge-227",
      "source": "node-274",
      "target": "node-174",
      "type": "communicates_with"
    },
    {
      "id": "edge-228",
      "source": "node-244",
      "target": "node-251",
      "type": "runs_on"
    },
    {
      "id": "edge-229",
      "source": "node-118",
      "target": "node-100",
      "type": "routes_to"
    },
    {
      "id": "edge-230",
      "source": "node-64",
      "target": "node-45",
      "type": "bound_to"
    },
    {
      "id": "edge-231",
      "source": "node-191",
      "target": "node-168",
      "type": "runs_on"
    },
    {
      "id": "edge-232",
      "source": "node-251",
      "target": "node-29",
      "type": "runs_on"
    },
    {
      "id": "edge-233",
      "source": "node-68",
      "target": "node-140",
      "type": "runs_on"
    },
    {
      "id": "edge-234",
      "source": "node-88",
      "target": "node-220",
      "type": "routes_to"
    },
    {
      "id": "edge-235",
      "source": "node-116",
      "target": "node-163",
      "type": "communicates_with"
    },
    {
      "id": "edge-236",
      "source": "node-107",
      "target": "node-97",
      "type": "communicates_with"
    },
    {
      "id": "edge-237",
      "source": "node-19",
      "target": "node-248",
      "type": "routes_to"
    },
    {
      "id": "edge-238",
      "source": "node-25",
      "target": "node-125",
      "type": "routes_to"
    },
    {
      "id": "edge-239",
      "source": "node-274",
      "target": "node-298",
      "type": "mounts"
    },
    {
      "id": "edge-240",
      "source": "node-50",
      "target": "node-162",
      "type": "mounts"
    },
    {
      "id": "edge-241",
      "source": "node-163",
      "target": "node-108",
      "type": "runs_on"
    },
    {
      "id": "edge-242",
      "source": "node-35",
      "target": "node-99",
      "type": "mounts"
    },
    {
      "id": "edge-243",
      "source": "node-23",
      "target": "node-87",
      "type": "runs_on"
    },
    {
      "id": "edge-244",
      "source": "node-133",
      "target": "node-78",
      "type": "bound_to"
    },
    {
      "id": "edge-245",
      "source": "node-107",
      "target": "node-16",
      "type": "routes_to"
    },
    {
      "id": "edge-246",
      "source": "node-158",
      "target": "node-17",
      "type": "communicates_with"
    },
    {
      "id": "edge-247",
      "source": "node-292",
      "target": "node-186",
      "type": "bound_to"
    },
    {
      "id": "edge-248",
      "source": "node-101",
      "target": "node-197",
      "type": "bound_to"
    },
    {
      "id": "edge-249",
      "source": "node-13",
      "target": "node-80",
      "type": "communicates_with"
    },
    {
      "id": "edge-250",
      "source": "node-198",
      "target": "node-210",
      "type": "routes_to"
    },
    {
      "id": "edge-251",
      "source": "node-95",
      "target": "node-290",
      "type": "runs_on"
    },
    {
      "id": "edge-252",
      "source": "node-124",
      "target": "node-177",
      "type": "routes_to"
    },
    {
      "id": "edge-253",
      "source": "node-281",
      "target": "node-111",
      "type": "communicates_with"
    },
    {
      "id": "edge-254",
      "source": "node-148",
      "target": "node-90",
      "type": "runs_on"
    },
    {
      "id": "edge-255",
      "source": "node-279",
      "target": "node-1",
      "type": "bound_to"
    },
    {
      "id": "edge-256",
      "source": "node-30",
      "target": "node-161",
      "type": "runs_on"
    },
    {
      "id": "edge-257",
      "source": "node-45",
      "target": "node-17",
      "type": "bound_to"
    },
    {
      "id": "edge-258",
      "source": "node-126",
      "target": "node-17",
      "type": "runs_on"
    },
    {
      "id": "edge-259",
      "source": "node-280",
      "target": "node-52",
      "type": "runs_on"
    },
    {
      "id": "edge-260",
      "source": "internet-0",
      "target": "node-269",
      "type": "communicates_with"
    },
    {
      "id": "edge-261",
      "source": "node-159",
      "target": "node-143",
      "type": "runs_on"
    },
    {
      "id": "edge-262",
      "source": "node-52",
      "target": "node-72",
      "type": "communicates_with"
    },
    {
      "id": "edge-263",
      "source": "node-40",
      "target": "node-198",
      "type": "mounts"
    },
    {
      "id": "edge-264",
      "source": "node-182",
      "target": "node-100",
      "type": "mounts"
    },
    {
      "id": "edge-265",
      "source": "node-137",
      "target": "node-134",
      "type": "communicates_with"
    },
    {
      "id": "edge-266",
      "source": "node-146",
      "target": "node-35",
      "type": "communicates_with"
    },
    {
      "id": "edge-267",
      "source": "node-66",
      "target": "node-202",
      "type": "routes_to"
    },
    {
      "id": "edge-268",
      "source": "node-8",
      "target": "node-204",
      "type": "communicates_with"
    },
    {
      "id": "edge-269",
      "source": "node-138",
      "target": "node-268",
      "type": "runs_on"
    },
    {
      "id": "edge-270",
      "source": "node-225",
      "target": "node-180",
      "type": "mounts"
    },
    {
      "id": "edge-271",
      "source": "node-119",
      "target": "node-175",
      "type": "runs_on"
    },
    {
      "id": "edge-272",
      "source": "node-224",
      "target": "node-258",
      "type": "mounts"
    },
    {
      "id": "edge-273",
      "source": "node-219",
      "target": "node-53",
      "type": "communicates_with"
    },
    {
      "id": "edge-274",
      "source": "node-8",
      "target": "node-226",
      "type": "routes_to"
    },
    {
      "id": "edge-275",
      "source": "node-256",
      "target": "node-27",
      "type": "mounts"
    },
    {
      "id": "edge-276",
      "source": "node-286",
      "target": "node-150",
      "type": "runs_on"
    },
    {
      "id": "edge-277",
      "source": "node-8",
      "target": "node-113",
      "type": "routes_to"
    },
    {
      "id": "edge-278",
      "source": "node-226",
      "target": "node-236",
      "type": "mounts"
    },
    {
      "id": "edge-279",
      "source": "node-1",
      "target": "node-204",
      "type": "mounts"
    },
    {
      "id": "edge-280",
      "source": "node-223",
      "target": "node-156",
      "type": "bound_to"
    },
    {
      "id": "edge-281",
      "source": "node-287",
      "target": "node-23",
      "type": "communicates_with"
    },
    {
      "id": "edge-282",
      "source": "node-284",
      "target": "node-289",
      "type": "routes_to"
    },
    {
      "id": "edge-283",
      "source": "node-158",
      "target": "node-2",
      "type": "runs_on"
    },
    {
      "id": "edge-284",
      "source": "node-186",
      "target": "node-137",
      "type": "runs_on"
    },
    {
      "id": "edge-285",
      "source": "node-222",
      "target": "node-161",
      "type": "communicates_with"
    },
    {
      "id": "edge-286",
      "source": "node-298",
      "target": "node-83",
      "type": "routes_to"
    },
    {
      "id": "edge-287",
      "source": "node-238",
      "target": "node-63",
      "type": "mounts"
    },
    {
      "id": "edge-288",
      "source": "node-166",
      "target": "node-46",
      "type": "bound_to"
    },
    {
      "id": "edge-289",
      "source": "node-68",
      "target": "node-152",
      "type": "mounts"
    },
    {
      "id": "edge-290",
      "source": "node-85",
      "target": "node-157",
      "type": "routes_to"
    },
    {
      "id": "edge-291",
      "source": "node-19",
      "target": "node-232",
      "type": "communicates_with"
    },
    {
      "id": "edge-292",
      "source": "node-180",
      "target": "node-194",
      "type": "mounts"
    },
    {
      "id": "edge-293",
      "source": "node-16",
      "target": "node-120",
      "type": "communicates_with"
    },
    {
      "id": "edge-294",
      "source": "node-139",
      "target": "node-71",
      "type": "bound_to"
    },
    {
      "id": "edge-295",
      "source": "node-95",
      "target": "node-97",
      "type": "bound_to"
    },
    {
      "id": "edge-296",
      "source": "node-287",
      "target": "node-253",
      "type": "bound_to"
    },
    {
      "id": "edge-297",
      "source": "node-258",
      "target": "node-65",
      "type": "mounts"
    },
    {
      "id": "edge-298",
      "source": "node-199",
      "target": "node-94",
      "type": "mounts"
    },
    {
      "id": "edge-299",
      "source": "node-240",
      "target": "node-177",
      "type": "bound_to"
    },
    {
      "id": "edge-300",
      "source": "node-259",
      "target": "node-86",
      "type": "bound_to"
    },
    {
      "id": "edge-301",
      "source": "node-69",
      "target": "node-15",
      "type": "mounts"
    },
    {
      "id": "edge-302",
      "source": "node-235",
      "target": "node-236",
      "type": "routes_to"
    },
    {
      "id": "edge-303",
      "source": "node-191",
      "target": "node-1",
      "type": "routes_to"
    },
    {
      "id": "edge-304",
      "source": "node-272",
      "target": "node-298",
      "type": "routes_to"
    },
    {
      "id": "edge-305",
      "source": "node-133",
      "target": "node-247",
      "type": "mounts"
    },
    {
      "id": "edge-306",
      "source": "node-22",
      "target": "node-208",
      "type": "communicates_with"
    },
    {
      "id": "edge-307",
      "source": "node-56",
      "target": "node-127",
      "type": "runs_on"
    },
    {
      "id": "edge-308",
      "source": "node-133",
      "target": "node-82",
      "type": "bound_to"
    },
    {
      "id": "edge-309",
      "source": "node-180",
      "target": "node-146",
      "type": "mounts"
    },
    {
      "id": "edge-310",
      "source": "node-103",
      "target": "node-111",
      "type": "routes_to"
    },
    {
      "id": "edge-311",
      "source": "node-10",
      "target": "node-134",
      "type": "runs_on"
    },
    {
      "id": "edge-312",
      "source": "node-54",
      "target": "node-149",
      "type": "communicates_with"
    },
    {
      "id": "edge-313",
      "source": "node-165",
      "target": "node-204",
      "type": "bound_to"
    },
    {
      "id": "edge-314",
      "source": "node-50",
      "target": "node-225",
      "type": "bound_to"
    },
    {
      "id": "edge-315",
      "source": "node-275",
      "target": "node-222",
      "type": "routes_to"
    },
    {
      "id": "edge-316",
      "source": "node-24",
      "target": "node-74",
      "type": "runs_on"
    },
    {
      "id": "edge-317",
      "source": "node-155",
      "target": "node-186",
      "type": "communicates_with"
    },
    {
      "id": "edge-318",
      "source": "node-61",
      "target": "node-149",
      "type": "bound_to"
    },
    {
      "id": "edge-319",
      "source": "node-120",
      "target": "node-23",
      "type": "routes_to"
    },
    {
      "id": "edge-320",
      "source": "node-146",
      "target": "node-267",
      "type": "runs_on"
    },
    {
      "id": "edge-321",
      "source": "node-171",
      "target": "node-281",
      "type": "runs_on"
    },
    {
      "id": "edge-322",
      "source": "node-64",
      "target": "node-99",
      "type": "runs_on"
    },
    {
      "id": "edge-323",
      "source": "node-42",
      "target": "node-178",
      "type": "bound_to"
    },
    {
      "id": "edge-324",
      "source": "node-217",
      "target": "node-112",
      "type": "routes_to"
    },
    {
      "id": "edge-325",
      "source": "node-94",
      "target": "node-261",
      "type": "communicates_with"
    },
    {
      "id": "edge-326",
      "source": "node-250",
      "target": "node-50",
      "type": "runs_on"
    },
    {
      "id": "edge-327",
      "source": "node-212",
      "target": "node-71",
      "type": "routes_to"
    },
    {
      "id": "edge-328",
      "source": "node-170",
      "target": "node-110",
      "type": "routes_to"
    },
    {
      "id": "edge-329",
      "source": "node-94",
      "target": "node-286",
      "type": "bound_to"
    },
    {
      "id": "edge-330",
      "source": "node-194",
      "target": "node-268",
      "type": "bound_to"
    },
    {
      "id": "edge-331",
      "source": "node-84",
      "target": "node-266",
      "type": "runs_on"
    },
    {
      "id": "edge-332",
      "source": "node-91",
      "target": "node-38",
      "type": "bound_to"
    },
    {
      "id": "edge-333",
      "source": "node-200",
      "target": "node-111",
      "type": "runs_on"
    },
    {
      "id": "edge-334",
      "source": "node-276",
      "target": "node-83",
      "type": "routes_to"
    },
    {
      "id": "edge-335",
      "source": "node-213",
      "target": "node-161",
      "type": "mounts"
    },
    {
      "id": "edge-336",
      "source": "node-14",
      "target": "node-206",
      "type": "routes_to"
    },
    {
      "id": "edge-337",
      "source": "node-21",
      "target": "node-262",
      "type": "routes_to"
    },
    {
      "id": "edge-338",
      "source": "node-294",
      "target": "node-175",
      "type": "mounts"
    },
    {
      "id": "edge-339",
      "source": "node-262",
      "target": "node-88",
      "type": "mounts"
    },
    {
      "id": "edge-340",
      "source": "node-180",
      "target": "node-258",
      "type": "runs_on"
    },
    {
      "id": "edge-341",
      "source": "node-153",
      "target": "node-132",
      "type": "routes_to"
    },
    {
      "id": "edge-342",
      "source": "node-175",
      "target": "node-128",
      "type": "bound_to"
    },
    {
      "id": "edge-343",
      "source": "node-1",
      "target": "node-147",
      "type": "bound_to"
    },
    {
      "id": "edge-344",
      "source": "node-264",
      "target": "node-259",
      "type": "routes_to"
    },
    {
      "id": "edge-345",
      "source": "node-54",
      "target": "node-295",
      "type": "runs_on"
    },
    {
      "id": "edge-346",
      "source": "node-173",
      "target": "node-76",
      "type": "mounts"
    },
    {
      "id": "edge-347",
      "source": "node-138",
      "target": "node-191",
      "type": "runs_on"
    },
    {
      "id": "edge-348",
      "source": "node-250",
      "target": "node-206",
      "type": "mounts"
    },
    {
      "id": "edge-349",
      "source": "node-189",
      "target": "node-285",
      "type": "bound_to"
    },
    {
      "id": "edge-350",
      "source": "node-31",
      "target": "node-287",
      "type": "communicates_with"
    },
    {
      "id": "edge-351",
      "source": "node-85",
      "target": "node-296",
      "type": "runs_on"
    },
    {
      "id": "edge-352",
      "source": "node-287",
      "target": "node-3",
      "type": "mounts"
    },
    {
      "id": "edge-353",
      "source": "node-208",
      "target": "node-212",
      "type": "mounts"
    },
    {
      "id": "edge-354",
      "source": "node-68",
      "target": "node-79",
      "type": "communicates_with"
    },
    {
      "id": "edge-355",
      "source": "node-164",
      "target": "node-62",
      "type": "runs_on"
    },
    {
      "id": "edge-356",
      "source": "node-294",
      "target": "node-195",
      "type": "communicates_with"
    },
    {
      "id": "edge-357",
      "source": "node-213",
      "target": "node-235",
      "type": "communicates_with"
    },
    {
      "id": "edge-358",
      "source": "node-81",
      "target": "node-53",
      "type": "communicates_with"
    },
    {
      "id": "edge-359",
      "source": "node-135",
      "target": "node-34",
      "type": "bound_to"
    },
    {
      "id": "edge-360",
      "source": "node-142",
      "target": "node-112",
      "type": "mounts"
    },
    {
      "id": "edge-361",
      "source": "node-214",
      "target": "node-19",
      "type": "communicates_with"
    },
    {
      "id": "edge-362",
      "source": "node-269",
      "target": "node-240",
      "type": "bound_to"
    },
    {
      "id": "edge-363",
      "source": "node-197",
      "target": "node-90",
      "type": "routes_to"
    },
    {
      "id": "edge-364",
      "source": "node-73",
      "target": "node-286",
      "type": "routes_to"
    },
    {
      "id": "edge-365",
      "source": "node-96",
      "target": "node-98",
      "type": "mounts"
    },
    {
      "id": "edge-366",
      "source": "node-109",
      "target": "node-177",
      "type": "mounts"
    },
    {
      "id": "edge-367",
      "source": "node-2",
      "target": "node-204",
      "type": "routes_to"
    },
    {
      "id": "edge-368",
      "source": "node-290",
      "target": "node-257",
      "type": "routes_to"
    },
    {
      "id": "edge-369",
      "source": "node-160",
      "target": "node-126",
      "type": "routes_to"
    },
    {
      "id": "edge-370",
      "source": "node-176",
      "target": "node-47",
      "type": "communicates_with"
    },
    {
      "id": "edge-371",
      "source": "node-143",
      "target": "node-37",
      "type": "mounts"
    },
    {
      "id": "edge-372",
      "source": "node-86",
      "target": "node-280",
      "type": "mounts"
    },
    {
      "id": "edge-373",
      "source": "node-22",
      "target": "node-94",
      "type": "runs_on"
    },
    {
      "id": "edge-374",
      "source": "node-97",
      "target": "node-137",
      "type": "mounts"
    },
    {
      "id": "edge-375",
      "source": "node-243",
      "target": "node-106",
      "type": "routes_to"
    },
    {
      "id": "edge-376",
      "source": "node-264",
      "target": "node-288",
      "type": "mounts"
    },
    {
      "id": "edge-377",
      "source": "node-130",
      "target": "node-201",
      "type": "bound_to"
    },
    {
      "id": "edge-378",
      "source": "node-67",
      "target": "node-200",
      "type": "mounts"
    },
    {
      "id": "edge-379",
      "source": "node-234",
      "target": "node-10",
      "type": "routes_to"
    },
    {
      "id": "edge-380",
      "source": "node-258",
      "target": "node-29",
      "type": "bound_to"
    },
    {
      "id": "edge-381",
      "source": "node-157",
      "target": "node-37",
      "type": "communicates_with"
    },
    {
      "id": "edge-382",
      "source": "internet-0",
      "target": "node-293",
      "type": "routes_to"
    },
    {
      "id": "edge-383",
      "source": "node-139",
      "target": "node-119",
      "type": "routes_to"
    },
    {
      "id": "edge-384",
      "source": "node-74",
      "target": "node-190",
      "type": "runs_on"
    },
    {
      "id": "edge-385",
      "source": "node-96",
      "target": "node-143",
      "type": "routes_to"
    },
    {
      "id": "edge-386",
      "source": "node-135",
      "target": "node-70",
      "type": "mounts"
    },
    {
      "id": "edge-387",
      "source": "node-122",
      "target": "node-133",
      "type": "routes_to"
    },
    {
      "id": "edge-388",
      "source": "node-239",
      "target": "node-255",
      "type": "runs_on"
    },
    {
      "id": "edge-389",
      "source": "node-46",
      "target": "node-55",
      "type": "mounts"
    },
    {
      "id": "edge-390",
      "source": "node-207",
      "target": "node-173",
      "type": "routes_to"
    },
    {
      "id": "edge-391",
      "source": "node-247",
      "target": "node-93",
      "type": "bound_to"
    },
    {
      "id": "edge-392",
      "source": "node-282",
      "target": "node-169",
      "type": "mounts"
    },
    {
      "id": "edge-393",
      "source": "node-261",
      "target": "node-137",
      "type": "communicates_with"
    },
    {
      "id": "edge-394",
      "source": "node-66",
      "target": "node-25",
      "type": "communicates_with"
    },
    {
      "id": "edge-395",
      "source": "node-289",
      "target": "node-186",
      "type": "bound_to"
    },
    {
      "id": "edge-396",
      "source": "node-240",
      "target": "node-196",
      "type": "mounts"
    },
    {
      "id": "edge-397",
      "source": "node-112",
      "target": "node-174",
      "type": "bound_to"
    },
    {
      "id": "edge-398",
      "source": "node-159",
      "target": "node-6",
      "type": "runs_on"
    },
    {
      "id": "edge-399",
      "source": "node-177",
      "target": "node-146",
      "type": "communicates_with"
    },
    {
      "id": "edge-400",
      "source": "node-15",
      "target": "node-5",
      "type": "mounts"
    },
    {
      "id": "edge-401",
      "source": "node-253",
      "target": "node-134",
      "type": "communicates_with"
    },
    {
      "id": "edge-402",
      "source": "node-252",
      "target": "node-285",
      "type": "runs_on"
    },
    {
      "id": "edge-403",
      "source": "node-115",
      "target": "node-148",
      "type": "mounts"
    },
    {
      "id": "edge-404",
      "source": "node-209",
      "target": "node-216",
      "type": "runs_on"
    },
    {
      "id": "edge-405",
      "source": "node-130",
      "target": "node-139",
      "type": "mounts"
    },
    {
      "id": "edge-406",
      "source": "node-74",
      "target": "node-270",
      "type": "bound_to"
    },
    {
      "id": "edge-407",
      "source": "node-136",
      "target": "node-295",
      "type": "mounts"
    },
    {
      "id": "edge-408",
      "source": "node-100",
      "target": "node-265",
      "type": "runs_on"
    },
    {
      "id": "edge-409",
      "source": "node-61",
      "target": "node-204",
      "type": "routes_to"
    },
    {
      "id": "edge-410",
      "source": "node-298",
      "target": "node-38",
      "type": "communicates_with"
    },
    {
      "id": "edge-411",
      "source": "node-290",
      "target": "node-235",
      "type": "bound_to"
    },
    {
      "id": "edge-412",
      "source": "node-232",
      "target": "node-140",
      "type": "bound_to"
    },
    {
      "id": "edge-413",
      "source": "node-25",
      "target": "node-139",
      "type": "communicates_with"
    },
    {
      "id": "edge-414",
      "source": "node-57",
      "target": "node-14",
      "type": "routes_to"
    },
    {
      "id": "edge-415",
      "source": "node-148",
      "target": "node-240",
      "type": "bound_to"
    },
    {
      "id": "edge-416",
      "source": "node-138",
      "target": "node-7",
      "type": "communicates_with"
    },
    {
      "id": "edge-417",
      "source": "internet-0",
      "target": "node-166",
      "type": "communicates_with"
    },
    {
      "id": "edge-418",
      "source": "node-85",
      "target": "node-227",
      "type": "routes_to"
    },
    {
      "id": "edge-419",
      "source": "node-138",
      "target": "node-257",
      "type": "communicates_with"
    },
    {
      "id": "edge-420",
      "source": "node-212",
      "target": "node-189",
      "type": "routes_to"
    },
    {
      "id": "edge-421",
      "source": "node-63",
      "target": "node-274",
      "type": "routes_to"
    },
    {
      "id": "edge-422",
      "source": "node-289",
      "target": "node-80",
      "type": "communicates_with"
    },
    {
      "id": "edge-423",
      "source": "node-133",
      "target": "node-118",
      "type": "routes_to"
    },
    {
      "id": "edge-424",
      "source": "node-43",
      "target": "node-130",
      "type": "mounts"
    },
    {
      "id": "edge-425",
      "source": "node-207",
      "target": "node-177",
      "type": "bound_to"
    },
    {
      "id": "edge-426",
      "source": "node-128",
      "target": "node-198",
      "type": "mounts"
    },
    {
      "id": "edge-427",
      "source": "node-98",
      "target": "node-69",
      "type": "mounts"
    },
    {
      "id": "edge-428",
      "source": "node-73",
      "target": "node-125",
      "type": "communicates_with"
    },
    {
      "id": "edge-429",
      "source": "node-274",
      "target": "node-165",
      "type": "communicates_with"
    },
    {
      "id": "edge-430",
      "source": "node-265",
      "target": "node-295",
      "type": "routes_to"
    },
    {
      "id": "edge-431",
      "source": "node-185",
      "target": "node-218",
      "type": "routes_to"
    },
    {
      "id": "edge-432",
      "source": "node-62",
      "target": "node-284",
      "type": "bound_to"
    },
    {
      "id": "edge-433",
      "source": "node-9",
      "target": "node-124",
      "type": "bound_to"
    },
    {
      "id": "edge-434",
      "source": "node-120",
      "target": "node-165",
      "type": "runs_on"
    },
    {
      "id": "edge-435",
      "source": "node-5",
      "target": "node-263",
      "type": "runs_on"
    },
    {
      "id": "edge-436",
      "source": "node-90",
      "target": "node-212",
      "type": "runs_on"
    },
    {
      "id": "edge-437",
      "source": "node-47",
      "target": "node-107",
      "type": "communicates_with"
    },
    {
      "id": "edge-438",
      "source": "node-40",
      "target": "node-81",
      "type": "routes_to"
    },
    {
      "id": "edge-439",
      "source": "node-60",
      "target": "node-231",
      "type": "mounts"
    },
    {
      "id": "edge-440",
      "source": "node-86",
      "target": "node-72",
      "type": "bound_to"
    },
    {
      "id": "edge-441",
      "source": "node-206",
      "target": "node-274",
      "type": "runs_on"
    },
    {
      "id": "edge-442",
      "source": "node-185",
      "target": "node-125",
      "type": "communicates_with"
    },
    {
      "id": "edge-443",
      "source": "node-8",
      "target": "node-150",
      "type": "communicates_with"
    },
    {
      "id": "edge-444",
      "source": "node-235",
      "target": "node-134",
      "type": "communicates_with"
    },
    {
      "id": "edge-445",
      "source": "node-187",
      "target": "node-280",
      "type": "routes_to"
    },
    {
      "id": "edge-446",
      "source": "node-236",
      "target": "node-196",
      "type": "mounts"
    },
    {
      "id": "edge-447",
      "source": "node-19",
      "target": "node-248",
      "type": "communicates_with"
    },
    {
      "id": "edge-448",
      "source": "node-251",
      "target": "node-233",
      "type": "communicates_with"
    },
    {
      "id": "edge-449",
      "source": "node-173",
      "target": "node-97",
      "type": "routes_to"
    },
    {
      "id": "edge-450",
      "source": "node-120",
      "target": "node-298",
      "type": "runs_on"
    },
    {
      "id": "edge-451",
      "source": "node-7",
      "target": "node-296",
      "type": "routes_to"
    },
    {
      "id": "edge-452",
      "source": "node-148",
      "target": "node-245",
      "type": "runs_on"
    },
    {
      "id": "edge-453",
      "source": "node-288",
      "target": "node-104",
      "type": "runs_on"
    },
    {
      "id": "edge-454",
      "source": "node-212",
      "target": "node-298",
      "type": "bound_to"
    },
    {
      "id": "edge-455",
      "source": "node-129",
      "target": "node-291",
      "type": "runs_on"
    },
    {
      "id": "edge-456",
      "source": "node-139",
      "target": "node-109",
      "type": "runs_on"
    },
    {
      "id": "edge-457",
      "source": "node-13",
      "target": "node-230",
      "type": "bound_to"
    },
    {
      "id": "edge-458",
      "source": "node-22",
      "target": "node-261",
      "type": "routes_to"
    },
    {
      "id": "edge-459",
      "source": "node-63",
      "target": "node-123",
      "type": "mounts"
    },
    {
      "id": "edge-460",
      "source": "node-196",
      "target": "node-174",
      "type": "communicates_with"
    },
    {
      "id": "edge-461",
      "source": "node-110",
      "target": "node-274",
      "type": "communicates_with"
    },
    {
      "id": "edge-462",
      "source": "node-236",
      "target": "node-9",
      "type": "routes_to"
    },
    {
      "id": "edge-463",
      "source": "node-196",
      "target": "node-64",
      "type": "bound_to"
    },
    {
      "id": "edge-464",
      "source": "node-281",
      "target": "node-88",
      "type": "communicates_with"
    },
    {
      "id": "edge-465",
      "source": "node-167",
      "target": "node-90",
      "type": "runs_on"
    },
    {
      "id": "edge-466",
      "source": "node-270",
      "target": "node-42",
      "type": "runs_on"
    },
    {
      "id": "edge-467",
      "source": "node-289",
      "target": "node-106",
      "type": "communicates_with"
    },
    {
      "id": "edge-468",
      "source": "node-156",
      "target": "node-176",
      "type": "mounts"
    },
    {
      "id": "edge-469",
      "source": "node-189",
      "target": "node-263",
      "type": "communicates_with"
    },
    {
      "id": "edge-470",
      "source": "node-280",
      "target": "node-276",
      "type": "routes_to"
    },
    {
      "id": "edge-471",
      "source": "node-212",
      "target": "node-253",
      "type": "routes_to"
    },
    {
      "id": "edge-472",
      "source": "node-175",
      "target": "node-279",
      "type": "runs_on"
    },
    {
      "id": "edge-473",
      "source": "node-225",
      "target": "node-259",
      "type": "communicates_with"
    },
    {
      "id": "edge-474",
      "source": "node-67",
      "target": "node-259",
      "type": "bound_to"
    },
    {
      "id": "edge-475",
      "source": "node-285",
      "target": "node-175",
      "type": "routes_to"
    },
    {
      "id": "edge-476",
      "source": "node-164",
      "target": "node-166",
      "type": "mounts"
    },
    {
      "id": "edge-477",
      "source": "node-141",
      "target": "node-132",
      "type": "runs_on"
    },
    {
      "id": "edge-478",
      "source": "node-24",
      "target": "node-33",
      "type": "runs_on"
    },
    {
      "id": "edge-479",
      "source": "node-157",
      "target": "node-287",
      "type": "bound_to"
    },
    {
      "id": "edge-480",
      "source": "node-178",
      "target": "node-114",
      "type": "runs_on"
    },
    {
      "id": "edge-481",
      "source": "node-184",
      "target": "node-216",
      "type": "bound_to"
    },
    {
      "id": "edge-482",
      "source": "node-237",
      "target": "node-124",
      "type": "bound_to"
    },
    {
      "id": "edge-483",
      "source": "node-196",
      "target": "node-67",
      "type": "communicates_with"
    },
    {
      "id": "edge-484",
      "source": "node-67",
      "target": "node-242",
      "type": "mounts"
    },
    {
      "id": "edge-485",
      "source": "node-63",
      "target": "node-285",
      "type": "runs_on"
    },
    {
      "id": "edge-486",
      "source": "node-261",
      "target": "node-89",
      "type": "runs_on"
    },
    {
      "id": "edge-487",
      "source": "node-277",
      "target": "node-286",
      "type": "routes_to"
    },
    {
      "id": "edge-488",
      "source": "node-198",
      "target": "node-26",
      "type": "runs_on"
    },
    {
      "id": "edge-489",
      "source": "node-169",
      "target": "node-136",
      "type": "communicates_with"
    },
    {
      "id": "edge-490",
      "source": "node-268",
      "target": "node-60",
      "type": "bound_to"
    },
    {
      "id": "edge-491",
      "source": "node-176",
      "target": "node-15",
      "type": "routes_to"
    },
    {
      "id": "edge-492",
      "source": "node-169",
      "target": "node-19",
      "type": "bound_to"
    },
    {
      "id": "edge-493",
      "source": "node-4",
      "target": "db-cj-0",
      "type": "communicates_with"
    },
    {
      "id": "edge-494",
      "source": "node-116",
      "target": "node-32",
      "type": "mounts"
    },
    {
      "id": "edge-495",
      "source": "node-276",
      "target": "node-163",
      "type": "routes_to"
    },
    {
      "id": "edge-496",
      "source": "node-48",
      "target": "node-276",
      "type": "runs_on"
    },
    {
      "id": "edge-497",
      "source": "node-133",
      "target": "node-148",
      "type": "bound_to"
    },
    {
      "id": "edge-498",
      "source": "node-190",
      "target": "node-261",
      "type": "runs_on"
    },
    {
      "id": "edge-499",
      "source": "node-21",
      "target": "node-182",
      "type": "runs_on"
    },
    {
      "id": "edge-500",
      "source": "node-211",
      "target": "node-202",
      "type": "mounts"
    },
    {
      "id": "edge-501",
      "source": "node-170",
      "target": "node-175",
      "type": "bound_to"
    },
    {
      "id": "edge-502",
      "source": "node-182",
      "target": "node-128",
      "type": "mounts"
    },
    {
      "id": "edge-503",
      "source": "node-146",
      "target": "node-271",
      "type": "communicates_with"
    },
    {
      "id": "edge-504",
      "source": "node-68",
      "target": "node-251",
      "type": "bound_to"
    },
    {
      "id": "edge-505",
      "source": "node-297",
      "target": "node-245",
      "type": "runs_on"
    },
    {
      "id": "edge-506",
      "source": "node-52",
      "target": "node-265",
      "type": "bound_to"
    },
    {
      "id": "edge-507",
      "source": "node-241",
      "target": "node-265",
      "type": "runs_on"
    },
    {
      "id": "edge-508",
      "source": "node-78",
      "target": "node-12",
      "type": "bound_to"
    },
    {
      "id": "edge-509",
      "source": "node-176",
      "target": "node-179",
      "type": "bound_to"
    },
    {
      "id": "edge-510",
      "source": "node-292",
      "target": "node-278",
      "type": "bound_to"
    },
    {
      "id": "edge-511",
      "source": "node-263",
      "target": "node-195",
      "type": "mounts"
    },
    {
      "id": "edge-512",
      "source": "node-182",
      "target": "node-134",
      "type": "routes_to"
    },
    {
      "id": "edge-513",
      "source": "node-114",
      "target": "node-136",
      "type": "mounts"
    },
    {
      "id": "edge-514",
      "source": "node-290",
      "target": "node-13",
      "type": "bound_to"
    },
    {
      "id": "edge-515",
      "source": "node-202",
      "target": "node-144",
      "type": "runs_on"
    },
    {
      "id": "edge-516",
      "source": "node-91",
      "target": "node-141",
      "type": "runs_on"
    },
    {
      "id": "edge-517",
      "source": "node-81",
      "target": "node-297",
      "type": "runs_on"
    },
    {
      "id": "edge-518",
      "source": "node-171",
      "target": "node-33",
      "type": "runs_on"
    },
    {
      "id": "edge-519",
      "source": "node-70",
      "target": "node-175",
      "type": "mounts"
    },
    {
      "id": "edge-520",
      "source": "node-226",
      "target": "node-221",
      "type": "bound_to"
    },
    {
      "id": "edge-521",
      "source": "node-172",
      "target": "node-155",
      "type": "runs_on"
    },
    {
      "id": "edge-522",
      "source": "node-78",
      "target": "node-8",
      "type": "runs_on"
    },
    {
      "id": "edge-523",
      "source": "node-126",
      "target": "node-298",
      "type": "communicates_with"
    },
    {
      "id": "edge-524",
      "source": "node-273",
      "target": "node-103",
      "type": "routes_to"
    },
    {
      "id": "edge-525",
      "source": "node-270",
      "target": "node-277",
      "type": "runs_on"
    },
    {
      "id": "edge-526",
      "source": "node-165",
      "target": "node-105",
      "type": "communicates_with"
    },
    {
      "id": "edge-527",
      "source": "node-261",
      "target": "node-15",
      "type": "communicates_with"
    },
    {
      "id": "edge-528",
      "source": "node-82",
      "target": "node-206",
      "type": "runs_on"
    },
    {
      "id": "edge-529",
      "source": "node-213",
      "target": "node-11",
      "type": "communicates_with"
    },
    {
      "id": "edge-530",
      "source": "node-284",
      "target": "node-286",
      "type": "routes_to"
    },
    {
      "id": "edge-531",
      "source": "node-31",
      "target": "node-225",
      "type": "communicates_with"
    },
    {
      "id": "edge-532",
      "source": "node-124",
      "target": "node-220",
      "type": "mounts"
    },
    {
      "id": "edge-533",
      "source": "node-109",
      "target": "node-77",
      "type": "bound_to"
    },
    {
      "id": "edge-534",
      "source": "node-157",
      "target": "node-59",
      "type": "routes_to"
    },
    {
      "id": "edge-535",
      "source": "node-200",
      "target": "node-260",
      "type": "bound_to"
    },
    {
      "id": "edge-536",
      "source": "node-239",
      "target": "node-32",
      "type": "communicates_with"
    },
    {
      "id": "edge-537",
      "source": "node-137",
      "target": "node-57",
      "type": "routes_to"
    },
    {
      "id": "edge-538",
      "source": "node-53",
      "target": "node-158",
      "type": "communicates_with"
    },
    {
      "id": "edge-539",
      "source": "node-133",
      "target": "node-285",
      "type": "mounts"
    },
    {
      "id": "edge-540",
      "source": "node-151",
      "target": "node-287",
      "type": "bound_to"
    },
    {
      "id": "edge-541",
      "source": "node-183",
      "target": "node-216",
      "type": "mounts"
    },
    {
      "id": "edge-542",
      "source": "node-134",
      "target": "node-104",
      "type": "runs_on"
    },
    {
      "id": "edge-543",
      "source": "node-197",
      "target": "node-199",
      "type": "runs_on"
    },
    {
      "id": "edge-544",
      "source": "node-259",
      "target": "node-2",
      "type": "bound_to"
    },
    {
      "id": "edge-545",
      "source": "node-248",
      "target": "node-25",
      "type": "runs_on"
    },
    {
      "id": "edge-546",
      "source": "node-144",
      "target": "node-285",
      "type": "routes_to"
    },
    {
      "id": "edge-547",
      "source": "node-230",
      "target": "node-133",
      "type": "runs_on"
    },
    {
      "id": "edge-548",
      "source": "node-85",
      "target": "node-294",
      "type": "communicates_with"
    },
    {
      "id": "edge-549",
      "source": "node-193",
      "target": "node-285",
      "type": "communicates_with"
    },
    {
      "id": "edge-550",
      "source": "node-76",
      "target": "node-244",
      "type": "bound_to"
    },
    {
      "id": "edge-551",
      "source": "node-171",
      "target": "node-27",
      "type": "routes_to"
    },
    {
      "id": "edge-552",
      "source": "node-39",
      "target": "node-141",
      "type": "routes_to"
    },
    {
      "id": "edge-553",
      "source": "node-126",
      "target": "node-173",
      "type": "bound_to"
    },
    {
      "id": "edge-554",
      "source": "node-290",
      "target": "node-191",
      "type": "mounts"
    },
    {
      "id": "edge-555",
      "source": "node-162",
      "target": "node-49",
      "type": "runs_on"
    },
    {
      "id": "edge-556",
      "source": "node-279",
      "target": "node-45",
      "type": "bound_to"
    },
    {
      "id": "edge-557",
      "source": "node-14",
      "target": "node-7",
      "type": "routes_to"
    },
    {
      "id": "edge-558",
      "source": "node-173",
      "target": "node-21",
      "type": "runs_on"
    },
    {
      "id": "edge-559",
      "source": "node-141",
      "target": "node-54",
      "type": "routes_to"
    },
    {
      "id": "edge-560",
      "source": "node-260",
      "target": "node-73",
      "type": "routes_to"
    },
    {
      "id": "edge-561",
      "source": "node-146",
      "target": "node-289",
      "type": "bound_to"
    },
    {
      "id": "edge-562",
      "source": "node-252",
      "target": "node-60",
      "type": "bound_to"
    },
    {
      "id": "edge-563",
      "source": "node-88",
      "target": "node-152",
      "type": "routes_to"
    },
    {
      "id": "edge-564",
      "source": "node-250",
      "target": "node-141",
      "type": "routes_to"
    },
    {
      "id": "edge-565",
      "source": "node-283",
      "target": "node-284",
      "type": "routes_to"
    },
    {
      "id": "edge-566",
      "source": "node-158",
      "target": "node-75",
      "type": "bound_to"
    },
    {
      "id": "edge-567",
      "source": "node-114",
      "target": "node-31",
      "type": "bound_to"
    },
    {
      "id": "edge-568",
      "source": "node-31",
      "target": "node-39",
      "type": "bound_to"
    },
    {
      "id": "edge-569",
      "source": "node-162",
      "target": "node-183",
      "type": "communicates_with"
    },
    {
      "id": "edge-570",
      "source": "node-162",
      "target": "node-292",
      "type": "bound_to"
    },
    {
      "id": "edge-571",
      "source": "node-138",
      "target": "node-142",
      "type": "routes_to"
    },
    {
      "id": "edge-572",
      "source": "node-56",
      "target": "node-139",
      "type": "communicates_with"
    },
    {
      "id": "edge-573",
      "source": "node-46",
      "target": "node-61",
      "type": "routes_to"
    },
    {
      "id": "edge-574",
      "source": "node-49",
      "target": "node-133",
      "type": "communicates_with"
    },
    {
      "id": "edge-575",
      "source": "node-79",
      "target": "node-5",
      "type": "routes_to"
    },
    {
      "id": "edge-576",
      "source": "node-48",
      "target": "node-265",
      "type": "bound_to"
    },
    {
      "id": "edge-577",
      "source": "node-250",
      "target": "node-235",
      "type": "mounts"
    },
    {
      "id": "edge-578",
      "source": "node-145",
      "target": "node-195",
      "type": "routes_to"
    },
    {
      "id": "edge-579",
      "source": "node-2",
      "target": "node-188",
      "type": "runs_on"
    },
    {
      "id": "edge-580",
      "source": "node-235",
      "target": "db-cj-0",
      "type": "bound_to"
    },
    {
      "id": "edge-581",
      "source": "node-226",
      "target": "node-223",
      "type": "runs_on"
    },
    {
      "id": "edge-582",
      "source": "node-241",
      "target": "node-106",
      "type": "mounts"
    },
    {
      "id": "edge-583",
      "source": "node-64",
      "target": "node-47",
      "type": "communicates_with"
    },
    {
      "id": "edge-584",
      "source": "node-12",
      "target": "node-241",
      "type": "bound_to"
    },
    {
      "id": "edge-585",
      "source": "node-181",
      "target": "node-227",
      "type": "routes_to"
    },
    {
      "id": "edge-586",
      "source": "node-293",
      "target": "node-196",
      "type": "communicates_with"
    },
    {
      "id": "edge-587",
      "source": "node-199",
      "target": "node-227",
      "type": "bound_to"
    },
    {
      "id": "edge-588",
      "source": "node-240",
      "target": "node-223",
      "type": "communicates_with"
    },
    {
      "id": "edge-589",
      "source": "node-182",
      "target": "node-245",
      "type": "communicates_with"
    },
    {
      "id": "edge-590",
      "source": "node-116",
      "target": "node-222",
      "type": "runs_on"
    },
    {
      "id": "edge-591",
      "source": "node-254",
      "target": "node-70",
      "type": "routes_to"
    },
    {
      "id": "edge-592",
      "source": "node-56",
      "target": "node-21",
      "type": "runs_on"
    },
    {
      "id": "edge-593",
      "source": "node-85",
      "target": "node-198",
      "type": "bound_to"
    },
    {
      "id": "edge-594",
      "source": "node-85",
      "target": "node-171",
      "type": "mounts"
    }
  ]
}
```

## README.md

```markdown
# KubeInsights — Kubernetes Attack Path Visualizer

> Graph-Based Security Analysis for Cloud-Native Infrastructure

KubeInsights is a security analysis tool that models Kubernetes cluster permissions as a directed graph and discovers attack paths from entry points (internet, users) to crown jewels (databases, secrets, persistent volumes).

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/TheCodeNotTakenT-T/kuber-attack-path-project.git
cd kuber-attack-path-project

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Run full analysis
python cli.py analyze --input mock-cluster-graph.json
```

### Requirements

- Python 3.10+
- Dependencies: `networkx`, `fastapi`, `uvicorn`, `pydantic`, `python-multipart`, `reportlab`

---

## CLI Usage

### Full Security Report

Runs all 4 algorithms and generates a comprehensive Kill Chain report:

```bash
python cli.py analyze --input mock-cluster-graph.json
```

**Expected output** (abbreviated):

```
══════════════════════════════════════════════════════════════════
  KILL CHAIN REPORT  —  2026-04-03 02:25:35
  Cluster : mock-prod-cluster
  Nodes   : 41  |  Edges: 48
══════════════════════════════════════════════════════════════════

[ SECTION 1 — ATTACK PATH DETECTION (Dijkstra) ]
  ⚠  18 attack path(s) detected
  Path #1  |  3 hops  |  Risk Score: 9.5  [MEDIUM]
  ...

[ SECTION 2 — BLAST RADIUS ANALYSIS (BFS, depth=3) ]
  Source: internet  →  13 reachable resource(s) within 3 hops
  ...

[ SECTION 3 — CIRCULAR PERMISSION DETECTION (DFS) ]
  ⚠  1 cycle(s) detected
  Cycle #1: service-a ↔ service-b ↔ service-a

[ SECTION 4 — CRITICAL NODE ANALYSIS ]
  Baseline attack paths : 46
  ★  RECOMMENDATION:
     Remove permission binding 'web-frontend' (Pod) to eliminate 32 of 46 attack paths.
```

### Individual Algorithm Commands

```bash
# BFS Blast Radius — find all nodes reachable within N hops
python cli.py blast-radius --source pod-webfront --hops 3 --input mock-cluster-graph.json

# Dijkstra Shortest Path — find cheapest attack path between two nodes
python cli.py shortest-path --source user-dev1 --target db-production --input mock-cluster-graph.json

# DFS Cycle Detection — find circular permission loops
python cli.py detect-cycles --input mock-cluster-graph.json

# Critical Node Analysis — identify the most impactful node to remove
python cli.py critical-node --input mock-cluster-graph.json
```

### Additional Options

```bash
# JSON output (for scripting/integration)
python cli.py analyze --input mock-cluster-graph.json --json

# PDF export
python cli.py analyze --input mock-cluster-graph.json --pdf report.pdf

# Live cluster ingestion (requires kubectl)
python cli.py ingest -o cluster-graph.json

# Temporal diff (compare snapshots)
python cli.py analyze --input mock-cluster-graph.json --snapshot --diff
```

---

## Algorithms

### 1. BFS — Blast Radius Analysis

Performs a **Breadth-First Search** from a source node to discover all reachable resources within N hops. Results are grouped by hop layer to show the "danger zone" — everything an attacker could reach from a compromised entry point.

- **Input:** Source node ID, max hops (default: 3)
- **Output:** Nodes grouped by hop distance, total count, risk summary

### 2. Dijkstra — Shortest Attack Path

Uses **Dijkstra's algorithm** with edge weights (attack difficulty scores) to find the lowest-cost path from an attacker's entry point to a high-value target. Lower total weight = easier attack.

- **Input:** Source and target node IDs
- **Output:** Ordered node sequence, total cost, hop count, CVE annotations on edges
- **Severity Labels:** `CRITICAL` (≥20), `HIGH` (10–19.9), `MEDIUM` (5–9.9), `LOW` (<5)

### 3. DFS — Cycle Detection

Detects **circular permission loops** using DFS-based cycle finding (via `nx.simple_cycles` with length bound). These represent mutual admin grants or privilege escalation loops.

- **Input:** Full graph
- **Output:** List of cycles as ordered node sequences, deduplicated

### 4. Critical Node Analysis — Graph Surgery

Identifies the **single non-source, non-sink node** whose removal eliminates the greatest number of source-to-sink attack paths. Uses brute-force removal-and-recount methodology:

1. Count baseline paths using `nx.all_simple_paths` with cutoff depth
2. For each candidate, **copy** the graph (original never mutated), remove the node, recount paths
3. Rank by paths eliminated

- **Input:** Full graph with source/sink annotations
- **Output:** Critical node, paths eliminated count, top-5 ranking

---

## Schema Documentation

### `cluster-graph.json` Format

The input JSON file follows this schema:

```json
{
  "metadata": {
    "cluster": "cluster-name",
    "generated": "2026-04-03",
    "node_count": 40,
    "edge_count": 48,
    "description": "Cluster description"
  },
  "nodes": [ ... ],
  "edges": [ ... ]
}
```

### Node Schema

Each node represents a Kubernetes resource:

| Field        | Type       | Description                                          |
|-------------|------------|------------------------------------------------------|
| `id`        | `string`   | Unique internal identifier (e.g., `pod-webfront`)    |
| `type`      | `string`   | Resource type: `Pod`, `ServiceAccount`, `Role`, `ClusterRole`, `Secret`, `ConfigMap`, `Service`, `Database`, `Node`, `Namespace`, `PersistentVolume`, `User`, `ExternalActor` |
| `name`      | `string`   | Human-readable display name (e.g., `web-frontend`)   |
| `namespace` | `string`   | Kubernetes namespace                                  |
| `risk_score`| `float`    | Numeric risk score (0.0–10.0)                        |
| `is_source` | `boolean`  | `true` if this is an attacker entry point            |
| `is_sink`   | `boolean`  | `true` if this is a high-value target (crown jewel)  |
| `cves`      | `string[]` | List of CVE identifiers (e.g., `["CVE-2024-1234"]`)  |

**Example node:**
```json
{
  "id": "pod-webfront",
  "type": "Pod",
  "name": "web-frontend",
  "namespace": "default",
  "risk_score": 7.5,
  "is_source": false,
  "is_sink": false,
  "cves": ["CVE-2024-1234"]
}
```

### Edge Schema

Each edge represents a relationship between two resources:

| Field          | Type           | Description                                      |
|---------------|----------------|--------------------------------------------------|
| `source`      | `string`       | Source node ID                                    |
| `target`      | `string`       | Target node ID                                    |
| `relationship`| `string`       | Relationship type (see below)                     |
| `weight`      | `float`        | Attack difficulty score (lower = easier)          |
| `cve`         | `string\|null` | CVE exploited on this edge (if any)               |
| `cvss`        | `float\|null`  | CVSS score of the exploited CVE                   |

**Relationship types:**
- `can-exec` — User can execute commands in a pod
- `uses` — Pod uses a ServiceAccount
- `bound-to` — ServiceAccount is bound to a Role via RoleBinding
- `can-read` — Role can read a Secret/ConfigMap
- `grants-access-to` — Secret grants access to a database/system
- `reaches` — External actor reaches a service
- `routes-to` — Service routes traffic to a pod
- `calls` — Pod calls a service endpoint
- `falls-back-to` — Pod falls back to default ServiceAccount
- `admin-grant` — Mutual admin permission (cycle indicator)
- `mounts` — Node mounts a PersistentVolume
- `reads` — Pod reads a ConfigMap
- `exposes-endpoint` — ConfigMap exposes a database endpoint
- `impersonates` — User impersonates a ServiceAccount
- `can-exec-on` — Role can execute on a Node

**Weight semantics:** Edge weights represent attack difficulty on a 0–10 scale. Lower weights indicate easier exploitation. The sum of edge weights along a path gives the total attack difficulty score.

**Example edge:**
```json
{
  "source": "user-dev1",
  "target": "pod-webfront",
  "relationship": "can-exec",
  "weight": 5.0,
  "cve": "CVE-2024-1234",
  "cvss": 8.1
}
```

---

## Project Structure

```
kuber-attack-path-project/
├── backend/
│   ├── cli.py                    # CLI tool (main entry point)
│   ├── graph_engine.py           # Core graph analytics engine (NetworkX)
│   ├── main.py                   # FastAPI REST API server
│   ├── ingest.py                 # Live cluster ingestion via kubectl
│   ├── cve_scorer.py             # CVE/CVSS scoring (NVD API + static DB)
│   ├── advanced_weight_scorer.py # Multi-factor edge weight calculation
│   ├── temporal.py               # Snapshot storage & temporal diffing
│   ├── mock-cluster-graph.json   # Mock cluster data for testing
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # Main React component
│   │   ├── components/           # UI components (graph viz, sidebar, etc.)
│   │   └── lib/                  # Utilities and type definitions
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## Bonus Features

### B1: Interactive Graph Visualization (+5)

A React + D3.js frontend renders the attack graph in the browser with:
- Color-coded nodes by risk level (red = critical, green = safe)
- Attack path highlighting
- Zoom/pan navigation
- Node tooltips showing name, type, risk score, CVEs

**Run the frontend:**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### B2: Live CVE Scoring (+5)

Integration with NIST NVD API for real-time CVSS score lookups:
- Automatic CVE scoring based on container image vulnerabilities
- Fallback to static CVE database when API is unavailable
- Rate limiting handled gracefully

### B3: Temporal Analysis (+5)

Snapshot-based temporal diffing:
- Store graph snapshots over time
- Detect new nodes, edges, and attack paths between scans
- Alert output describes changes and risk delta

```bash
# Save a snapshot
python cli.py analyze --input cluster-graph.json --snapshot

# Compare with latest snapshot
python cli.py diff --input cluster-graph.json
```
```

## test_output.txt

```
﻿python : Traceback 
(most recent call last):
At line:1 char:1
+ python cli.py analyze 
--input 
mock-cluster-graph.json 
2>&1 | Out-File ...
+ ~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~
    + CategoryInfo      
        : NotSpecified: 
(T    raceback (most 
recent     call 
last)::String)     [], 
RemoteException
    + 
FullyQualifiedError    
Id : NativeCommandErr   
 or
 
  File "C:\Users\akars\O
neDrive\Desktop\kuber 
attack path visualizer\b
ackend\cli.py", line 
724, in <module>
    main()
    ~~~~^^
  File "C:\Users\akars\O
neDrive\Desktop\kuber 
attack path visualizer\b
ackend\cli.py", line 
720, in main
    args.func(args)
    ~~~~~~~~~^^^^^^
  File "C:\Users\akars\O
neDrive\Desktop\kuber 
attack path visualizer\b
ackend\cli.py", line 
457, in cmd_analyze
    _print_full_report(e
ngine, hops=args.hops)
    ~~~~~~~~~~~~~~~~~~^^
^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\akars\O
neDrive\Desktop\kuber 
attack path visualizer\b
ackend\cli.py", line 
80, in 
_print_full_report
    print(bar)
    ~~~~~^^^^^
  File "C:\Users\akars\A
ppData\Local\Programs\Py
thon\Python313\Lib\encod
ings\cp1252.py", line 
19, in encode
    return codecs.charma
p_encode(input,self.erro
rs,encoding_table)[0]
           ~~~~~~~~~~~~~
~~~~~~~~^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 
'charmap' codec can't 
encode characters in 
position 0-65: 
character maps to 
<undefined>
```

## test_perf.py

```python
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

```

## backend\advanced_weight_scorer.py

```python
"""
Advanced Edge Weight Scorer — Multi-parameter risk evaluation
Replaces simple CVSS-based weights with comprehensive attack difficulty scoring.
"""

from typing import Dict, Optional, List


class AdvancedWeightScorer:
    """
    Calculates edge weights based on 5 key factors:
    1. Asset Criticality (target node severity)
    2. Privilege Escalation Potential (how much access gained)
    3. Network Reachability (direct vs lateral movement)
    4. RBAC Permissions (restrictiveness of permissions required)
    5. Blast Radius (downstream impact potential)
    """

    # Factor weights (how much each factor contributes to total)
    FACTOR_WEIGHTS = {
        "asset_criticality": 0.25,
        "privilege_escalation": 0.25,
        "network_reachability": 0.20,
        "rbac_restrictions": 0.20,
        "blast_radius": 0.10,
    }

    @staticmethod
    def calculate_edge_weight(
        source_node: Dict,
        target_node: Dict,
        relationship: str,
        graph_context: Optional[Dict] = None
    ) -> float:
        """
        Calculate composite edge weight (0.1 to 10.0 scale).
        Lower weight = easier path to exploit.
        
        Args:
            source_node: Source node data dict with metadata
            target_node: Target node data dict with metadata
            relationship: Edge relationship type (e.g., 'uses_service_account')
            graph_context: Optional context with full graph for blast radius calc
            
        Returns:
            float: Edge weight (0.1-10.0)
        """
        weights = {
            "asset_criticality": AdvancedWeightScorer._score_asset_criticality(target_node),
            "privilege_escalation": AdvancedWeightScorer._score_privilege_escalation(
                source_node, target_node, relationship
            ),
            "network_reachability": AdvancedWeightScorer._score_network_reachability(
                source_node, target_node, relationship
            ),
            "rbac_restrictions": AdvancedWeightScorer._score_rbac_restrictions(target_node),
            "blast_radius": AdvancedWeightScorer._score_blast_radius(
                target_node, graph_context
            ),
        }

        # Calculate weighted composite score
        composite = sum(
            weights[factor] * AdvancedWeightScorer.FACTOR_WEIGHTS[factor]
            for factor in weights
        )

        # Clamp to 0.1-10.0 range
        return max(0.1, min(10.0, composite))

    @staticmethod
    def _score_asset_criticality(node: Dict) -> float:
        """
        Score based on target node's criticality (risk_level).
        Lower = easier to attack (attractive target).
        """
        risk_level = node.get("risk_level", "low").lower()
        criticality_map = {
            "entry-point": 1.0,      # Internet = easy entry
            "low": 2.0,              # Low risk = less protected
            "medium": 4.0,           # Medium = some protection
            "high": 5.0,             # High = well-protected
            "critical": 6.0,         # Critical = heavily protected
            "crown-jewel": 7.0,      # Crown jewels = maximum protection
        }
        base_score = criticality_map.get(risk_level, 3.0)

        # CVEs make targets EASIER to compromise
        cvss_scores = node.get("metadata", {}).get("cvss_scores", [])
        if cvss_scores:
            avg_cvss = sum(cvss_scores) / len(cvss_scores)
            # Higher CVSS = easier to exploit = lower score
            base_score *= (1 - avg_cvss / 20.0)

        return base_score

    @staticmethod
    def _score_privilege_escalation(
        source_node: Dict, target_node: Dict, relationship: str
    ) -> float:
        """
        Score privilege escalation potential.
        How much access/privilege is gained by traversing this edge?
        """
        source_type = source_node.get("type", "")
        target_type = target_node.get("type", "")

        # Define privilege escalation paths (low score = high escalation potential)
        escalation_map = {
            # ServiceAccount escalation paths
            ("pod", "serviceaccount"): 1.5,           # Direct token access = HIGH escalation
            ("ingress", "pod"): 2.0,                  # Pod compromise
            ("pod", "secret"): 1.0,                   # Secret extraction = CRITICAL
            ("secret", "database"): 0.8,              # DB access via credentials
            ("secret", "external_system"): 0.9,       # External access (AWS, etc.)
            
            # Permission escalation
            ("serviceaccount", "rolebinding"): 1.2,   # SA -> binding
            ("rolebinding", "clusterrole"): 1.5,      # Role binding escalation
            ("rolebinding", "role"): 1.8,
            ("role", "pod"): 2.5,                     # Role grants access to pod
            
            # Lateral movement
            ("pod", "pod"): 3.5,                      # Pod-to-pod = harder
            ("service", "pod"): 2.8,                  # Service to pod
            ("configmap", "pod"): 2.0,                # ConfigMap injection
        }

        base_score = escalation_map.get((source_type, target_type), 3.0)

        # Relationship-specific modifiers
        if relationship == "can_access" or relationship == "authenticates_to":
            base_score *= 0.7  # Direct access is easier
        elif relationship == "bound_by":
            base_score *= 0.8  # Binding = strong escalation
        elif "lateral" in relationship.lower():
            base_score *= 1.2  # Lateral movement harder

        return base_score

    @staticmethod
    def _score_network_reachability(
        source_node: Dict, target_node: Dict, relationship: str
    ) -> float:
        """
        Score network reachability difficulty.
        Can the target be reached from source? Is it isolated?
        """
        source_type = source_node.get("type", "")
        target_type = target_node.get("type", "")
        target_namespace = target_node.get("namespace", "default")
        source_namespace = source_node.get("namespace", "default")

        # Cross-namespace is harder than same-namespace
        same_namespace = source_namespace == target_namespace
        
        # Network isolation scoring
        isolation_map = {
            "external": 0.5,           # Internet = easiest (external)
            "ingress": 1.0,            # Ingress = direct entry
            "pod": 2.0,                # Pod = container isolation
            "service": 1.5,            # Service = load balanced
            "secret": 2.5,             # Secret = k8s API access
            "configmap": 2.5,
            "database": 4.0,           # Database = external system
            "rolebinding": 3.0,        # RBAC = meta-layer
            "role": 3.0,
            "clusterrole": 3.5,        # Cluster-wide = more abstract
            "serviceaccount": 2.5,
        }

        base_score = isolation_map.get(target_type, 3.0)

        # Same namespace = easier lateral movement
        if same_namespace:
            base_score *= 0.8
        else:
            base_score *= 1.2

        # Network policies affect reachability
        target_metadata = target_node.get("metadata", {})
        if target_metadata.get("network_policy_enforced"):
            base_score *= 1.5

        return base_score

    @staticmethod
    def _score_rbac_restrictions(node: Dict) -> float:
        """
        Score RBAC permission restrictions.
        How restrictive are the permissions needed to access this node?
        """
        node_type = node.get("type", "")
        metadata = node.get("metadata", {})

        # Permission restrictiveness baseline
        restriction_map = {
            "pod": 2.0,                # Pod access = namespace scope
            "secret": 1.5,             # Secrets = explicit access needed
            "configmap": 2.0,
            "serviceaccount": 1.8,
            "role": 1.5,               # RBAC = explicit permissions
            "rolebinding": 1.5,
            "clusterrole": 1.2,        # Cluster roles = more permissive patterns
            "database": 2.5,           # External = direct creds needed
            "service": 2.5,
            "ingress": 2.0,
            "external_system": 3.0,
        }

        base_score = restriction_map.get(node_type, 2.0)

        # Rules/permissions detail
        rules = metadata.get("rules", [])
        if rules:
            # Wildcard rules = less restrictive
            wildcard_count = sum(1 for r in rules if "*" in str(r))
            if wildcard_count > 0:
                base_score *= 0.7  # Wildcards = easier (less restrictive)

        # Automation mounts (automount_token) = easier access
        if metadata.get("automount_token") is True:
            base_score *= 0.6

        return base_score

    @staticmethod
    def _score_blast_radius(
        target_node: Dict, graph_context: Optional[Dict] = None
    ) -> float:
        """
        Score blast radius (downstream impact potential).
        How many downstream resources could be compromised if this node is breached?
        """
        risk_level = target_node.get("risk_level", "low").lower()

        # Direct blast radius from risk level
        blast_map = {
            "entry-point": 2.0,       # Entry = can reach many
            "low": 1.0,               # Low = limited impact
            "medium": 1.5,
            "high": 2.5,              # High risk = critical impact
            "critical": 3.5,
            "crown-jewel": 4.0,       # Crown jewel = highest impact
        }

        base_score = blast_map.get(risk_level, 2.0)

        # If graph context provided, calculate actual downstream nodes
        if graph_context and "outbound_edges" in graph_context:
            outbound_count = len(graph_context.get("outbound_edges", []))
            # More outbound edges = larger blast radius
            base_score += (outbound_count * 0.2)

        return base_score

    @staticmethod
    def generate_weight_report(
        source_node: Dict,
        target_node: Dict,
        relationship: str,
        graph_context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate detailed breakdown of weight calculation for debugging/UI.
        """
        weights = {
            "asset_criticality": AdvancedWeightScorer._score_asset_criticality(target_node),
            "privilege_escalation": AdvancedWeightScorer._score_privilege_escalation(
                source_node, target_node, relationship
            ),
            "network_reachability": AdvancedWeightScorer._score_network_reachability(
                source_node, target_node, relationship
            ),
            "rbac_restrictions": AdvancedWeightScorer._score_rbac_restrictions(target_node),
            "blast_radius": AdvancedWeightScorer._score_blast_radius(target_node, graph_context),
        }

        composite = sum(
            weights[factor] * AdvancedWeightScorer.FACTOR_WEIGHTS[factor]
            for factor in weights
        )
        final_weight = max(0.1, min(10.0, composite))

        return {
            "edge": f"{source_node.get('id')} -> {target_node.get('id')}",
            "relationship": relationship,
            "component_scores": weights,
            "factor_weights": AdvancedWeightScorer.FACTOR_WEIGHTS,
            "composite_before_clamp": round(composite, 3),
            "final_weight": round(final_weight, 3),
            "difficulty_rating": AdvancedWeightScorer._rate_difficulty(final_weight),
        }

    @staticmethod
    def _rate_difficulty(weight: float) -> str:
        """Convert weight to user-friendly difficulty rating."""
        if weight < 1.0:
            return "TRIVIAL"
        elif weight < 2.0:
            return "EASY"
        elif weight < 4.0:
            return "MODERATE"
        elif weight < 6.0:
            return "HARD"
        else:
            return "VERY HARD"
```

## backend\attack_path_discovery.py

*(Could not read file: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte)*

## backend\attack_path_discovery_utf8.py

```python
﻿"""
K8sGraphEngine ΓÇö Core graph analytics engine for KubePathAudit.
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

    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # Algorithm 1: BFS ΓÇö Blast Radius
    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    def bfs_blast_radius(self, source: str, max_hops: int = 3) -> dict:
        """
        BFS from a source node to find all reachable nodes within N hops.
        Returns the 'Danger Zone' ΓÇö everything an attacker could reach.
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

    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # Algorithm 2: Dijkstra ΓÇö Shortest Attack Path
    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
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
                "edge_info": step.get("edge_to_next", {}).get("relationship", "ΓÇö"),
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

    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # Algorithm 3: DFS ΓÇö Cycle Detection
    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
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
                "description": f"Circular path: {' ΓåÆ '.join(n.get('label', n['id']) for n in cycle_nodes)} ΓåÆ {cycle_nodes[0].get('label', cycle_nodes[0]['id'])}",
            })

        return {
            "total_cycles": len(cycles),
            "cycles": cycle_details,
            "has_cycles": len(cycles) > 0,
            "risk_summary": "CRITICAL" if any(c["risk"] == "CRITICAL" for c in cycle_details) else "HIGH" if cycle_details else "NONE",
        }

    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # Algorithm 4: Critical Node Analysis
    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
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

    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # Top Critical Attack Paths Analysis
    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
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

        description = " ΓåÆ ".join(path_summary)

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

    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # Remediation
    # ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
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
```

## backend\attack_report.pdf

*(Could not read file: 'utf-8' codec can't decode byte 0x93 in position 10: invalid start byte)*

## backend\cli.py

```python
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
    print(bar)
    print(f"  KILL CHAIN REPORT  \u2014  {now}")
    print(f"  Cluster : {cluster_name}")
    print(f"  Nodes   : {n_nodes}  |  Edges: {n_edges}")
    print(bar)
    print()

    # ══════════════════════════════════════════════════════════
    # SECTION 1 — ATTACK PATH DETECTION (Dijkstra)
    # ══════════════════════════════════════════════════════════
    all_paths = engine.find_all_attack_paths()

    print("[ SECTION 1 \u2014 ATTACK PATH DETECTION (Dijkstra) ]")
    print(f"  \u26a0  {len(all_paths)} attack path(s) detected")
    print()

    for idx, ap in enumerate(all_paths, 1):
        severity = _severity_label(ap["cost"])
        print(f"  Path #{idx}  |  {ap['hops']} hops  |  Risk Score: {ap['cost']}  [{severity}]")
        print(f"  {'─' * 60}")

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
            print(line)

        print()

    # ══════════════════════════════════════════════════════════
    # SECTION 2 — BLAST RADIUS ANALYSIS (BFS)
    # ══════════════════════════════════════════════════════════
    print(f"[ SECTION 2 \u2014 BLAST RADIUS ANALYSIS (BFS, depth={hops}) ]")
    print()

    sources = engine._get_sources()
    total_blast_nodes = 0

    for src in sources:
        result = engine.bfs_blast_radius(src, hops)
        label = result.get("source_label", src)
        total = result["total_affected"]
        total_blast_nodes += total

        print(f"  Source: {label}  \u2192  {total} reachable resource(s) within {hops} hops")

        layers = result.get("hop_layers", {})
        for hop_num in sorted(layers.keys()):
            names = [n.get("label", n["id"]) for n in layers[hop_num]]
            print(f"    Hop {hop_num}: {', '.join(names)}")

        print()

    # ══════════════════════════════════════════════════════════
    # SECTION 3 — CIRCULAR PERMISSION DETECTION (DFS)
    # ══════════════════════════════════════════════════════════
    cycle_result = engine.dfs_cycle_detection()

    print("[ SECTION 3 \u2014 CIRCULAR PERMISSION DETECTION (DFS) ]")
    if cycle_result["has_cycles"]:
        print(f"  \u26a0  {cycle_result['total_cycles']} cycle(s) detected")
        print()
        for i, cycle in enumerate(cycle_result["cycles"], 1):
            print(f"  Cycle #{i}: {cycle['description']}")
    else:
        print("  \u2713 No circular permission loops detected.")
    print()

    # ══════════════════════════════════════════════════════════
    # SECTION 4 — CRITICAL NODE ANALYSIS
    # ══════════════════════════════════════════════════════════
    print("[ SECTION 4 \u2014 CRITICAL NODE ANALYSIS ]")
    print("  Computing... (removing each node and recounting paths)")
    print()

    critical_result = engine.critical_node_analysis()
    baseline = critical_result.get("baseline_paths", 0)
    print(f"  Baseline attack paths : {baseline}")
    print()

    cn = critical_result.get("critical_node")
    if cn:
        print(f"  \u2605  RECOMMENDATION:")
        print(f"     Remove permission binding '{cn['label']}' ({cn['type']}) "
              f"to eliminate {cn['paths_broken']} of {baseline} attack paths.")
        print()

        top5 = critical_result.get("top_5_nodes", [])
        if top5:
            max_broken = top5[0]["paths_broken"] if top5 else 1
            print("  Top 5 highest-impact nodes to remove:")
            for node in top5:
                name_padded = f"{node['label']:<30}"
                type_padded = f"({node['type']:<15})"
                bar_len = int(node["paths_broken"] / max_broken * 20) if max_broken > 0 else 0
                bar_str = "\u2588" * bar_len
                print(f"    {name_padded} {type_padded}  -{node['paths_broken']} paths  {bar_str}")
        print()

    # ══════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════
    critical_label = cn["label"] if cn else "none"
    print(bar)
    print("  SUMMARY")
    print(f"  Attack paths found   : {len(all_paths)}")
    print(f"  Circular permissions : {cycle_result['total_cycles']}")
    print(f"  Total blast-radius nodes exposed : {total_blast_nodes}")
    print(f"  Critical node to remove : {critical_label}")
    print(bar)
    print()


# ── Individual Algorithm Output ──────────────────────────────

def _print_blast_radius(engine: K8sGraphEngine, result: dict):
    """Print blast radius results for a single source."""
    if "error" in result and not result.get("affected_nodes"):
        print(f"\nError: {result['error']}")
        return

    label = result.get("source_label", result["source"])
    total = result["total_affected"]
    hops = result["max_hops"]

    print(f"\nBlast Radius Analysis")
    print(f"{'─' * 50}")
    print(f"  Source: {label}  →  {total} reachable resource(s) within {hops} hops")

    layers = result.get("hop_layers", {})
    for hop_num in sorted(layers.keys()):
        names = [n.get("label", n["id"]) for n in layers[hop_num]]
        print(f"    Hop {hop_num}: {', '.join(names)}")
    print()


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
```

## backend\cve_scorer.py

```python
"""
CVE Scorer — Static CVE database + optional NIST NVD API integration.
Provides CVSS scores for known container/Kubernetes vulnerabilities.
"""

import json
import urllib.request
import urllib.error
from typing import Optional


# ── Static CVE Database ────────────────────────────────────────
# Common Kubernetes & container CVEs with CVSS v3.1 scores.
STATIC_CVE_DB: dict[str, dict] = {
    # Kubernetes Dashboard
    "CVE-2018-18264": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Kubernetes Dashboard privilege escalation via skip-login",
        "affected": "kubernetesui/dashboard < v2.0.0",
    },
    "CVE-2023-49797": {
        "cvss": 8.1,
        "severity": "HIGH",
        "summary": "Kubernetes Dashboard cross-site request forgery",
        "affected": "kubernetesui/dashboard < v2.7.1",
    },
    # NGINX Ingress
    "CVE-2024-7646": {
        "cvss": 8.8,
        "severity": "HIGH",
        "summary": "NGINX Ingress annotation injection leading to arbitrary config",
        "affected": "ingress-nginx < 1.11.2",
    },
    "CVE-2023-5043": {
        "cvss": 7.6,
        "severity": "HIGH",
        "summary": "NGINX Ingress annotation injection via permanent-redirect",
        "affected": "ingress-nginx < 1.9.5",
    },
    "CVE-2021-25742": {
        "cvss": 7.6,
        "severity": "HIGH",
        "summary": "NGINX Ingress snippet injection",
        "affected": "ingress-nginx < 1.0.5",
    },
    # HTTP/2 Rapid Reset
    "CVE-2023-44487": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "HTTP/2 Rapid Reset denial-of-service attack",
        "affected": "Multiple HTTP/2 implementations",
    },
    # Prometheus
    "CVE-2024-6837": {
        "cvss": 5.4,
        "severity": "MEDIUM",
        "summary": "Prometheus stored XSS via crafted metric labels",
        "affected": "prometheus < v2.54.0",
    },
    # etcd
    "CVE-2023-47108": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "etcd OpenTelemetry contrib DoS via unbound cardinality",
        "affected": "etcd < 3.5.11",
    },
    "CVE-2023-32082": {
        "cvss": 5.3,
        "severity": "MEDIUM",
        "summary": "etcd information leak via LeaseTimeToLive API",
        "affected": "etcd < 3.5.9",
    },
    # Container runtime / runc
    "CVE-2024-21626": {
        "cvss": 8.6,
        "severity": "HIGH",
        "summary": "runc container breakout via leaked file descriptors",
        "affected": "runc < 1.1.12",
    },
    "CVE-2019-5736": {
        "cvss": 8.6,
        "severity": "HIGH",
        "summary": "runc host binary overwrite via container exec",
        "affected": "runc < 1.0.0-rc7",
    },
    # Kubernetes core
    "CVE-2024-3177": {
        "cvss": 2.7,
        "severity": "LOW",
        "summary": "Kubernetes imagePullSecrets bypass in ephemeral containers",
        "affected": "kubernetes < 1.30.0",
    },
    "CVE-2023-5528": {
        "cvss": 8.8,
        "severity": "HIGH",
        "summary": "Kubernetes Windows node command injection via volume mount",
        "affected": "kubernetes < 1.28.4",
    },
    "CVE-2023-2728": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "Kubernetes ServiceAccount token secret bypass via ephemeral containers",
        "affected": "kubernetes < 1.27.3",
    },
    "CVE-2022-3294": {
        "cvss": 8.8,
        "severity": "HIGH",
        "summary": "Kubernetes node address validation bypass",
        "affected": "kubernetes < 1.25.4",
    },
    "CVE-2022-3162": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "Kubernetes directory traversal in volume subpath",
        "affected": "kubernetes < 1.25.4",
    },
    # Istio / Envoy
    "CVE-2024-23322": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Envoy crash via HTTP/2 CONTINUATION flood",
        "affected": "envoy < 1.29.1",
    },
    "CVE-2023-35942": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "Istio gateway CORS bypass",
        "affected": "istio < 1.18.2",
    },
    # Helm
    "CVE-2022-23524": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Helm denial of service via crafted schema",
        "affected": "helm < 3.10.3",
    },
    # ArgoCD
    "CVE-2024-28175": {
        "cvss": 9.1,
        "severity": "CRITICAL",
        "summary": "Argo CD XSS leading to credential theft",
        "affected": "argocd < 2.10.4",
    },
    "CVE-2024-21661": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Argo CD denial of service via crafted manifest",
        "affected": "argocd < 2.10.3",
    },
    # CoreDNS
    "CVE-2023-49295": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "CoreDNS HPACK decoder DoS via crafted headers",
        "affected": "coredns < 1.11.2",
    },
    # containerd
    "CVE-2023-25153": {
        "cvss": 5.5,
        "severity": "MEDIUM",
        "summary": "containerd OCI image import denial of service",
        "affected": "containerd < 1.6.18",
    },
    "CVE-2022-23648": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "containerd host path leak via image config",
        "affected": "containerd < 1.6.1",
    },
    # Kube-proxy / networking
    "CVE-2023-3676": {
        "cvss": 8.8,
        "severity": "HIGH",
        "summary": "Kubernetes Windows node privilege escalation via pod spec",
        "affected": "kubernetes < 1.28.0",
    },
    # Calico
    "CVE-2024-2912": {
        "cvss": 9.8,
        "severity": "CRITICAL",
        "summary": "Calico privilege escalation via VXLAN configuration",
        "affected": "calico < 3.27.2",
    },
    # Flux
    "CVE-2022-39272": {
        "cvss": 7.5,
        "severity": "HIGH",
        "summary": "Flux controller denial of service via malicious object",
        "affected": "flux < 0.35.0",
    },
    # Vault (often used with K8s)
    "CVE-2023-0620": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "HashiCorp Vault SQL injection in audit device",
        "affected": "vault < 1.13.1",
    },
    # Cert-manager
    "CVE-2022-2996": {
        "cvss": 6.5,
        "severity": "MEDIUM",
        "summary": "cert-manager improper path validation in ACME challenge",
        "affected": "cert-manager < 1.10.0",
    },
}


def lookup_cve(cve_id: str) -> Optional[dict]:
    """Look up a CVE from the static database."""
    return STATIC_CVE_DB.get(cve_id)


def get_cvss_score(cve_id: str) -> float:
    """Return the CVSS score for a CVE, or 5.0 as default unknown."""
    entry = STATIC_CVE_DB.get(cve_id)
    return entry["cvss"] if entry else 5.0


def lookup_cve_live(cve_id: str) -> Optional[dict]:
    """
    Query the NIST NVD API 2.0 for a CVE.
    Returns a dict with cvss, severity, and summary — or None on failure.
    Rate-limited: 5 requests/30 seconds for unauthenticated calls.
    """
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KubePathAudit/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        vulns = data.get("vulnerabilities", [])
        if not vulns:
            return None

        cve_data = vulns[0].get("cve", {})
        metrics = cve_data.get("metrics", {})

        # Try CVSS v3.1 first, then v3.0
        cvss_score = 0.0
        severity = "UNKNOWN"
        for version_key in ("cvssMetricV31", "cvssMetricV30"):
            if version_key in metrics:
                cvss_data = metrics[version_key][0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore", 0.0)
                severity = cvss_data.get("baseSeverity", "UNKNOWN")
                break

        descriptions = cve_data.get("descriptions", [])
        summary = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                summary = desc.get("value", "")
                break

        return {
            "cvss": cvss_score,
            "severity": severity,
            "summary": summary[:200],
            "source": "NVD API 2.0",
        }
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError,
            TimeoutError, OSError):
        return None


def score_cve(cve_id: str, live: bool = False) -> dict:
    """
    Get CVE info: tries static DB first, then optionally falls back to NVD API.
    Always returns a dict with at minimum {cvss, severity, summary}.
    """
    # Static lookup first (fast)
    static = lookup_cve(cve_id)
    if static:
        return {**static, "source": "static"}

    # Live lookup if requested
    if live:
        live_result = lookup_cve_live(cve_id)
        if live_result:
            return live_result

    # Unknown CVE fallback
    return {
        "cvss": 5.0,
        "severity": "MEDIUM",
        "summary": f"Unknown CVE: {cve_id}",
        "source": "default",
    }


def score_image_cves(cves: list[str], live: bool = False) -> list[dict]:
    """Score a list of CVE IDs and return detailed results."""
    return [{"cve_id": cve, **score_cve(cve, live=live)} for cve in cves]


def compute_node_risk_score(cves: list[str], live: bool = False) -> float:
    """Compute aggregate risk score for a node based on its CVEs."""
    if not cves:
        return 0.0
    scores = [score_cve(cve, live=live)["cvss"] for cve in cves]
    # Use max score + 10% of sum of remaining scores (compound risk)
    scores.sort(reverse=True)
    total = scores[0]
    for s in scores[1:]:
        total += s * 0.1
    return round(total, 2)
```

## backend\e2e_results.txt

```

============================================================
  TEST: Full Report
  CMD: python cli.py analyze --input mock-cluster-graph.json
============================================================
══════════════════════════════════════════════════════════════════
  KILL CHAIN REPORT  —  2026-04-04 22:41:21
  Cluster : mock-prod-cluster
  Nodes   : 41  |  Edges: 48
══════════════════════════════════════════════════════════════════

[ SECTION 1 — ATTACK PATH DETECTION (Dijkstra) ]
  ⚠  18 attack path(s) detected

  Path #1  |  3 hops  |  Risk Score: 9.5  [MEDIUM]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[reads]-->  db-url-config (ConfigMap)
  db-url-config (ConfigMap)  --[exposes-endpoint]-->  analytics-db (Database)

  Path #2  |  4 hops  |  Risk Score: 11.5  [HIGH]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  loadbalancer-svc (Service)
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[reads]-->  db-url-config (ConfigMap)
  db-url-config (ConfigMap)  --[exposes-endpoint]-->  analytics-db (Database)

  Path #3  |  3 hops  |  Risk Score: 14.0  [HIGH]
  ────────────────────────────────────────────────────────────
  cicd-bot (User)  --[impersonates]-->  sa-cicd (ServiceAccount)
  sa-cicd (ServiceAccount)  --[can-read]-->  cicd-deploy-token (Secret)
  cicd-deploy-token (Secret)  --[grants-access-to]-->  production-db (Database)

  Path #4  |  4 hops  |  Risk Score: 15.0  [HIGH]
  ────────────────────────────────────────────────────────────
  dev-2 (User)  --[can-exec]-->  log-aggregator (Pod)  [CVE-2024-9999, CVSS 6.5]
  log-aggregator (Pod)  --[uses]-->  sa-logger (ServiceAccount)
  sa-logger (ServiceAccount)  --[bound-to]-->  node-reader (Role)
  node-reader (Role)  --[can-read]-->  worker-node-1 (Node)

  Path #5  |  5 hops  |  Risk Score: 15.5  [HIGH]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[calls]-->  internal-api-svc (Service)
  internal-api-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[reads]-->  db-url-config (ConfigMap)
  db-url-config (ConfigMap)  --[exposes-endpoint]-->  analytics-db (Database)

  Path #6  |  4 hops  |  Risk Score: 17.0  [HIGH]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  background-worker (Pod)
  background-worker (Pod)  --[uses]-->  sa-worker (ServiceAccount)
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]

  Path #7  |  4 hops  |  Risk Score: 18.5  [HIGH]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[uses]-->  sa-worker (ServiceAccount)  [CVE-2023-4567, CVSS 7.2]
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]

  Path #8  |  5 hops  |  Risk Score: 20.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  dev-2 (User)  --[can-exec]-->  log-aggregator (Pod)  [CVE-2024-9999, CVSS 6.5]
  log-aggregator (Pod)  --[uses]-->  sa-logger (ServiceAccount)
  sa-logger (ServiceAccount)  --[bound-to]-->  node-reader (Role)
  node-reader (Role)  --[can-read]-->  worker-node-1 (Node)
  worker-node-1 (Node)  --[mounts]-->  data-pvc (PersistentVolume)

  Path #9  |  5 hops  |  Risk Score: 20.5  [CRITICAL]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  loadbalancer-svc (Service)
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[uses]-->  sa-worker (ServiceAccount)  [CVE-2023-4567, CVSS 7.2]
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]

  Path #10  |  5 hops  |  Risk Score: 22.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  background-worker (Pod)
  background-worker (Pod)  --[uses]-->  sa-worker (ServiceAccount)
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]
  worker-node-1 (Node)  --[mounts]-->  data-pvc (PersistentVolume)

  Path #11  |  5 hops  |  Risk Score: 22.1  [CRITICAL]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  web-frontend (Pod)
  web-frontend (Pod)  --[uses]-->  sa-webapp (ServiceAccount)
  sa-webapp (ServiceAccount)  --[bound-to]-->  secret-reader (Role)
  secret-reader (Role)  --[can-read]-->  db-credentials (Secret)
  db-credentials (Secret)  --[grants-access-to]-->  production-db (Database)

  Path #12  |  5 hops  |  Risk Score: 23.1  [CRITICAL]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[uses]-->  sa-webapp (ServiceAccount)
  sa-webapp (ServiceAccount)  --[bound-to]-->  secret-reader (Role)
  secret-reader (Role)  --[can-read]-->  db-credentials (Secret)
  db-credentials (Secret)  --[grants-access-to]-->  production-db (Database)

  Path #13  |  5 hops  |  Risk Score: 23.5  [CRITICAL]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[uses]-->  sa-worker (ServiceAccount)  [CVE-2023-4567, CVSS 7.2]
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]
  worker-node-1 (Node)  --[mounts]-->  data-pvc (PersistentVolume)

  Path #14  |  5 hops  |  Risk Score: 24.1  [CRITICAL]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[uses]-->  sa-webapp (ServiceAccount)
  sa-webapp (ServiceAccount)  --[bound-to]-->  secret-reader (Role)
  secret-reader (Role)  --[can-read]-->  db-credentials (Secret)
  db-credentials (Secret)  --[grants-access-to]-->  production-db (Database)

  Path #15  |  6 hops  |  Risk Score: 25.5  [CRITICAL]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  loadbalancer-svc (Service)
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[uses]-->  sa-worker (ServiceAccount)  [CVE-2023-4567, CVSS 7.2]
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]
  worker-node-1 (Node)  --[mounts]-->  data-pvc (PersistentVolume)

  Path #16  |  5 hops  |  Risk Score: 31.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  web-frontend (Pod)
  web-frontend (Pod)  --[falls-back-to]-->  default (ServiceAccount)
  default (ServiceAccount)  --[bound-to]-->  cluster-admin (ClusterRole)
  cluster-admin (ClusterRole)  --[can-read]-->  admin-token (Secret)
  admin-token (Secret)  --[grants-access-to]-->  kube-system (Namespace)

  Path #17  |  5 hops  |  Risk Score: 32.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[falls-back-to]-->  default (ServiceAccount)
  default (ServiceAccount)  --[bound-to]-->  cluster-admin (ClusterRole)
  cluster-admin (ClusterRole)  --[can-read]-->  admin-token (Secret)
  admin-token (Secret)  --[grants-access-to]-->  kube-system (Namespace)

  Path #18  |  5 hops  |  Risk Score: 33.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[falls-back-to]-->  default (ServiceAccount)
  default (ServiceAccount)  --[bound-to]-->  cluster-admin (ClusterRole)
  cluster-admin (ClusterRole)  --[can-read]-->  admin-token (Secret)
  admin-token (Secret)  --[grants-access-to]-->  kube-system (Namespace)

[ SECTION 2 — BLAST RADIUS ANALYSIS (BFS, depth=3) ]

  Source: internet  →  13 reachable resource(s) within 3 hops
    Hop 1: loadbalancer-svc, web-frontend
    Hop 2: api-server, sa-webapp, default, internal-api-svc
    Hop 3: sa-worker, db-url-config, api-key, secret-reader, tls-cert, cluster-admin, db-credentials

  Source: dev-1  →  13 reachable resource(s) within 3 hops
    Hop 1: web-frontend, background-worker
    Hop 2: sa-webapp, default, internal-api-svc, sa-worker
    Hop 3: secret-reader, tls-cert, api-key, cluster-admin, db-credentials, api-server, pod-exec

  Source: dev-2  →  4 reachable resource(s) within 3 hops
    Hop 1: log-aggregator
    Hop 2: sa-logger, app-env-config
    Hop 3: node-reader

  Source: cicd-bot  →  4 reachable resource(s) within 3 hops
    Hop 1: sa-cicd
    Hop 2: deployer, cicd-deploy-token
    Hop 3: production-db

  Source: loadbalancer-svc  →  14 reachable resource(s) within 3 hops
    Hop 1: api-server, web-frontend
    Hop 2: sa-worker, db-url-config, api-key, sa-webapp, default, internal-api-svc
    Hop 3: pod-exec, analytics-db, secret-reader, tls-cert, cluster-admin, db-credentials

[ SECTION 3 — CIRCULAR PERMISSION DETECTION (DFS) ]
  ⚠  1 cycle(s) detected

  Cycle #1: service-a ↔ service-b ↔ service-a

[ SECTION 4 — CRITICAL NODE ANALYSIS ]
  Computing... (removing each node and recounting paths)

  Baseline attack paths : 46

  ★  RECOMMENDATION:
     Remove permission binding 'web-frontend' (Pod) to eliminate 32 of 46 attack paths.

  Top 5 highest-impact nodes to remove:
    web-frontend                   (Pod            )  -32 paths  ████████████████████
    api-server                     (Pod            )  -24 paths  ███████████████
    internal-api-svc               (Service        )  -16 paths  ██████████
    sa-worker                      (ServiceAccount )  -14 paths  ████████
    pod-exec                       (Role           )  -14 paths  ████████

══════════════════════════════════════════════════════════════════
  SUMMARY
  Attack paths found   : 18
  Circular permissions : 1
  Total blast-radius nodes exposed : 48
  Critical node to remove : web-frontend
══════════════════════════════════════════════════════════════════


EXIT CODE: 0

============================================================
  TEST: Blast Radius
  CMD: python cli.py blast-radius --source pod-webfront --hops 3 --input mock-cluster-graph.json
============================================================

Blast Radius Analysis
──────────────────────────────────────────────────
  Source: web-frontend  →  15 reachable resource(s) within 3 hops
    Hop 1: sa-webapp, default, internal-api-svc
    Hop 2: secret-reader, tls-cert, api-key, cluster-admin, db-credentials, api-server
    Hop 3: analytics-db, admin-token, default, production-db, sa-worker, db-url-config


EXIT CODE: 0

============================================================
  TEST: Shortest Path
  CMD: python cli.py shortest-path --source user-dev1 --target db-production --input mock-cluster-graph.json
============================================================

Attack Path  |  5 hops  |  Risk Score: 24.1  [CRITICAL]
────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[uses]-->  sa-webapp (ServiceAccount)
  sa-webapp (ServiceAccount)  --[bound-to]-->  secret-reader (Role)
  secret-reader (Role)  --[can-read]-->  db-credentials (Secret)
  db-credentials (Secret)  --[grants-access-to]-->  production-db (Database)


EXIT CODE: 0

============================================================
  TEST: No Path
  CMD: python cli.py shortest-path --source svc-service-a --target db-analytics --input mock-cluster-graph.json
============================================================

No path found from 'svc-service-a' to 'db-analytics'

EXIT CODE: 0

============================================================
  TEST: Cycles
  CMD: python cli.py detect-cycles --input mock-cluster-graph.json
============================================================

Circular Permission Detection
──────────────────────────────────────────────────
  1 cycle(s) detected

  Cycle #1: service-b ↔ service-a ↔ service-b


EXIT CODE: 0

============================================================
  TEST: Help
  CMD: python cli.py --help
============================================================
usage: kubeinsights [-h]
                    {analyze,blast-radius,shortest-path,detect-cycles,critical-node,top-critical-paths,ingest,snapshots,diff} ...

KubeInsights — Kubernetes Attack Path Visualizer CLI

positional arguments:
  {analyze,blast-radius,shortest-path,detect-cycles,critical-node,top-critical-paths,ingest,snapshots,diff}
                        Available commands
    analyze             Run full security analysis (all 4 algorithms)
    blast-radius        BFS blast radius from a source node
    shortest-path       Dijkstra's shortest attack path
    detect-cycles       DFS circular permission detection
    critical-node       Identify highest-impact node to remove
    top-critical-paths  Show top critical attack paths
    ingest              Ingest live Kubernetes cluster state via kubectl
    snapshots           List all stored graph snapshots
    diff                Compare two graph snapshots or current vs latest

options:
  -h, --help            show this help message and exit

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
        

EXIT CODE: 0
```

## backend\graph_engine.py

```python
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
```

## backend\ingest.py

```python
"""
K8s Data Ingestion — Queries a live Kubernetes cluster via kubectl
and produces a cluster-graph.json file conforming to the KubeInsights schema.

Falls back to mock data if kubectl is not available or no cluster is connected.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cve_scorer import compute_node_risk_score, score_cve


# ── kubectl helpers ───────────────────────────────────────────

def _run_kubectl(args: list[str], timeout: int = 30) -> Optional[dict]:
    """Run a kubectl command and return parsed JSON, or None on failure."""
    cmd = ["kubectl"] + args + ["-o", "json"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None


def _check_kubectl() -> bool:
    """Check if kubectl is available and connected to a cluster."""
    try:
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ── Resource fetchers ─────────────────────────────────────────

def _fetch_resource(resource_type: str, namespace: str = "") -> list[dict]:
    """Fetch a list of Kubernetes resources."""
    args = ["get", resource_type]
    if namespace:
        args += ["-n", namespace]
    else:
        args += ["--all-namespaces"]

    data = _run_kubectl(args)
    if data and "items" in data:
        return data["items"]
    return []


# ── Node builders ─────────────────────────────────────────────

def _pod_to_node(pod: dict) -> dict:
    """Convert a K8s Pod resource to a graph node."""
    metadata = pod.get("metadata", {})
    spec = pod.get("spec", {})
    name = metadata.get("name", "unknown-pod")
    uid = metadata.get("uid", name)
    namespace = metadata.get("namespace", "default")
    labels = metadata.get("labels", {})

    containers = spec.get("containers", [])
    container_data = []
    ports = []
    all_images = []

    for c in containers:
        c_name = c.get("name", "")
        image = c.get("image", "")
        all_images.append(image)
        c_ports = [p.get("containerPort", 0) for p in c.get("ports", [])]
        ports.extend(c_ports)
        container_data.append({
            "name": c_name,
            "image": image,
            "ports": c_ports,
            "cves": [], # Placeholder for CVEs
        })

    # Determine risk level based on properties
    risk_level = "low"
    sa_name = spec.get("serviceAccountName", "default")
    if labels.get("exposed") == "true" or any("dashboard" in img.lower() for img in all_images):
        risk_level = "critical"
    elif namespace in ("kube-system",):
        risk_level = "critical"
    elif any(p in (80, 443, 8443, 8080) for p in ports):
        risk_level = "medium"

    return {
        "id": uid,
        "label": labels.get("app", name),
        "type": "pod",
        "namespace": namespace,
        "risk_level": risk_level,
        "metadata": {
            "name": name,
            "description": f"Pod running {len(containers)} container(s): {', '.join(all_images[:2])}",
            "containers": container_data,
            "images": all_images,
            "cves": [],  # High-level CVE list for the pod
            "cvss_scores": [],
            "ports": ports,
            "labels": labels,
            "service_account": sa_name,
            "icon": "server",
            "uid": uid,
        },
    }


def _sa_to_node(sa: dict) -> dict:
    """Convert a K8s ServiceAccount to a graph node."""
    metadata = sa.get("metadata", {})
    name = metadata.get("name", "unknown-sa")
    uid = metadata.get("uid", name)
    namespace = metadata.get("namespace", "default")
    automount = sa.get("automountServiceAccountToken", True)

    risk_level = "medium" if automount else "low"
    if name in ("cluster-admin", "admin"):
        risk_level = "critical"

    return {
        "id": uid,
        "label": name,
        "type": "serviceaccount",
        "namespace": namespace,
        "risk_level": risk_level,
        "metadata": {
            "name": name,
            "description": f"ServiceAccount in {namespace}",
            "automount_token": automount,
            "icon": "user-check" if risk_level == "critical" else "user",
            "uid": uid,
        },
    }


def _role_to_node(role: dict, is_cluster: bool = False) -> dict:
    """Convert a K8s Role/ClusterRole to a graph node."""
    metadata = role.get("metadata", {})
    name = metadata.get("name", "unknown-role")
    uid = metadata.get("uid", name)
    namespace = metadata.get("namespace", "cluster-wide") if not is_cluster else "cluster-wide"
    rules = role.get("rules", [])

    # Determine risk level from rules
    risk_level = "low"
    rule_summaries = []
    for rule in rules:
        resources = rule.get("resources", [])
        verbs = rule.get("verbs", [])
        summary = f"{','.join(resources)}:{','.join(verbs)}"
        rule_summaries.append(summary)

        if "*" in resources or "*" in verbs:
            risk_level = "critical"
        elif "secrets" in resources and any(v in verbs for v in ("get", "list", "*")):
            risk_level = "high"
        elif any(r in resources for r in ("pods/exec", "pods/attach")):
            risk_level = "high"
        elif risk_level == "low":
            risk_level = "medium"

    return {
        "id": uid,
        "label": name,
        "type": "clusterrole" if is_cluster else "role",
        "namespace": namespace,
        "risk_level": risk_level,
        "metadata": {
            "name": name,
            "description": f"{'ClusterRole' if is_cluster else 'Role'} with {len(rules)} rule(s)",
            "rules": rule_summaries,
            "icon": "shield-alert" if risk_level == "critical" else "shield",
            "uid": uid,
        },
    }


def _binding_to_node_and_edges(binding: dict, resource_resolver: dict, is_cluster: bool = False) -> tuple[dict, list[dict]]:
    """Convert a RoleBinding/ClusterRoleBinding to a node + edges."""
    metadata = binding.get("metadata", {})
    name = metadata.get("name", "unknown-binding")
    uid = metadata.get("uid", name)
    namespace = metadata.get("namespace", "cluster-wide") if not is_cluster else "cluster-wide"
    role_ref = binding.get("roleRef", {})
    subjects = binding.get("subjects", [])

    node = {
        "id": uid,
        "label": name,
        "type": "rolebinding",
        "namespace": namespace,
        "risk_level": "critical" if role_ref.get("name") == "cluster-admin" else "medium",
        "metadata": {
            "name": name,
            "description": f"{'ClusterRoleBinding' if is_cluster else 'RoleBinding'}",
            "binding_type": "ClusterRoleBinding" if is_cluster else "RoleBinding",
            "icon": "link",
            "uid": uid,
        },
    }

    edges = []
    # Edges from subjects → binding
    for subject in subjects:
        s_kind = subject.get("kind", "Subject")
        s_name = subject.get("name", "")
        s_ns = subject.get("namespace", namespace) if not is_cluster else subject.get("namespace", "default")
        
        # Resolve subject UID
        s_key = (s_kind.lower(), s_ns, s_name)
        s_uid = resource_resolver.get(s_key, s_name)

        if s_name:
            edges.append({
                "source": s_uid,
                "target": uid,
                "relationship": "bound_by",
                "weight": 0.5 if role_ref.get("name") == "cluster-admin" else 1.0,
                "metadata": {"description": f"{s_kind} '{s_name}' bound via node"},
            })

    # Edge from binding → role
    r_name = role_ref.get("name", "")
    r_kind = role_ref.get("kind", "Role")
    r_ns = namespace if r_kind == "Role" else "cluster-wide"
    
    r_key = (r_kind.lower(), r_ns, r_name)
    r_uid = resource_resolver.get(r_key, r_name)

    if r_name:
        edges.append({
            "source": uid,
            "target": r_uid,
            "relationship": "grants",
            "weight": 0.5 if r_name == "cluster-admin" else 1.0,
            "metadata": {"description": f"Binding grants {r_kind} '{r_name}'"},
        })

    return node, edges


def _secret_to_node(secret: dict) -> dict:
    """Convert a K8s Secret to a graph node."""
    metadata = secret.get("metadata", {})
    name = metadata.get("name", "unknown-secret")
    uid = metadata.get("uid", name)
    namespace = metadata.get("namespace", "default")
    secret_type = secret.get("type", "Opaque")
    keys = list(secret.get("data", {}).keys()) if "data" in secret else []

    # Skip service-account-token secrets (auto-generated)
    if secret_type == "kubernetes.io/service-account-token":
        return None

    # Determine risk by content heuristics
    risk_level = "medium"
    sensitive_keys = {"password", "secret", "key", "token", "credential", "aws", "db_password"}
    if any(k.lower() in sensitive_keys or any(s in k.lower() for s in sensitive_keys) for k in keys):
        risk_level = "crown-jewel"

    return {
        "id": uid,
        "label": name,
        "type": "secret",
        "namespace": namespace,
        "risk_level": risk_level,
        "metadata": {
            "name": name,
            "description": f"Secret ({secret_type}) with {len(keys)} key(s)",
            "secret_type": secret_type,
            "keys": keys,
            "icon": "key",
            "uid": uid,
        },
    }


def _configmap_to_node(cm: dict) -> dict:
    """Convert a K8s ConfigMap to a graph node."""
    metadata = cm.get("metadata", {})
    name = metadata.get("name", "unknown-cm")
    uid = metadata.get("uid", name)
    namespace = metadata.get("namespace", "default")
    keys = list(cm.get("data", {}).keys()) if "data" in cm else []

    # Skip kube-system configmaps like kube-root-ca.crt
    if namespace == "kube-system" and name.startswith("kube-"):
        return None

    return {
        "id": uid,
        "label": name,
        "type": "configmap",
        "namespace": namespace,
        "risk_level": "low",
        "metadata": {
            "name": name,
            "description": f"ConfigMap with {len(keys)} key(s)",
            "keys": keys,
            "icon": "file-text",
            "uid": uid,
        },
    }


# ── Edge builders ─────────────────────────────────────────────

def _build_pod_sa_edges(pods: list[dict], resource_resolver: dict) -> list[dict]:
    """Build edges from pods to their service accounts."""
    edges = []
    for pod in pods:
        p_meta = pod.get("metadata", {})
        p_name = p_meta.get("name", "")
        p_ns = p_meta.get("namespace", "default")
        p_uid = p_meta.get("uid", p_name)
        
        spec = pod.get("spec", {})
        sa_name = spec.get("serviceAccountName", "default")
        
        # Resolve ServiceAccount UID
        sa_key = ("serviceaccount", p_ns, sa_name)
        sa_uid = resource_resolver.get(sa_key, str(sa_name))
        
        if p_uid and sa_uid and sa_name != "default":
            edges.append({
                "source": p_uid,
                "target": sa_uid,
                "relationship": "uses_service_account",
                "weight": 0.5,
                "metadata": {"description": f"Pod '{p_name}' mounts ServiceAccount '{sa_name}'"},
            })
    return edges


def _build_role_secret_edges(roles: list[dict], secrets: list[dict], resource_resolver: dict) -> list[dict]:
    """Build edges from roles that can read secrets to those secret nodes."""
    edges = []
    
    # Map for secrets in each namespace
    ns_secrets = {}
    for s in secrets:
        metadata = s.get("metadata", {})
        ns = metadata.get("namespace", "default")
        name = metadata.get("name", "")
        uid = metadata.get("uid", name)
        if ns not in ns_secrets:
            ns_secrets[ns] = []
        ns_secrets[ns].append((name, uid))

    for role in roles:
        r_meta = role.get("metadata", {})
        r_name = r_meta.get("name", "")
        r_ns = r_meta.get("namespace", "cluster-wide")
        r_uid = r_meta.get("uid", r_name)
        
        rules = role.get("rules", [])
        for rule in rules:
            resources = rule.get("resources", [])
            verbs = rule.get("verbs", [])
            if ("secrets" in resources or "*" in resources) and any(v in verbs for v in ("get", "list", "*")):
                resource_names = rule.get("resourceNames", [])
                
                # Determine which namespaces to check
                target_namespaces = [r_ns] if r_ns != "cluster-wide" else ns_secrets.keys()
                
                for ns in target_namespaces:
                    if ns not in ns_secrets: continue
                    for s_name, s_uid in ns_secrets[ns]:
                        if not resource_names or s_name in resource_names:
                            edges.append({
                                "source": r_uid,
                                "target": s_uid,
                                "relationship": "can_access",
                                "weight": 1.0,
                                "metadata": {"description": f"Role can read secret '{s_name}'"},
                            })
    return edges


# ── Main ingestion function ───────────────────────────────────

def ingest_cluster(output_path: str = "cluster-graph.json", live_cve: bool = False) -> dict:
    """
    Ingest the live state of a Kubernetes cluster and export to JSON.
    
    Returns:
        dict: The cluster graph data structure.
    """
    if not _check_kubectl():
        print("⚠  kubectl is not available or no cluster is connected.")
        print("   Falling back to mock-cluster-graph.json")
        mock_path = Path(__file__).parent / "mock-cluster-graph.json"
        if mock_path.exists():
            with open(mock_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        else:
            print("✗  No mock data found either. Cannot proceed.")
            sys.exit(1)

    print("🔍 Querying Kubernetes cluster via kubectl...")

    # Fetch all resources
    print("  → Fetching Pods...")
    pods = _fetch_resource("pods")
    print(f"    Found {len(pods)} pods")

    print("  → Fetching ServiceAccounts...")
    service_accounts = _fetch_resource("serviceaccounts")
    print(f"    Found {len(service_accounts)} service accounts")

    print("  → Fetching Roles...")
    roles = _fetch_resource("roles")
    print(f"    Found {len(roles)} roles")

    print("  → Fetching ClusterRoles...")
    cluster_roles = _fetch_resource("clusterroles")
    print(f"    Found {len(cluster_roles)} cluster roles")

    print("  → Fetching RoleBindings...")
    role_bindings = _fetch_resource("rolebindings")
    print(f"    Found {len(role_bindings)} role bindings")

    print("  → Fetching ClusterRoleBindings...")
    cluster_role_bindings = _fetch_resource("clusterrolebindings")
    print(f"    Found {len(cluster_role_bindings)} cluster role bindings")

    print("  → Fetching Secrets...")
    secrets = _fetch_resource("secrets")
    print(f"    Found {len(secrets)} secrets")

    print("  → Fetching ConfigMaps...")
    configmaps = _fetch_resource("configmaps")
    print(f"    Found {len(configmaps)} configmaps")

    # Build nodes and populate resolver map
    print("\n🔨 Building graph nodes...")
    nodes = []
    all_node_ids = set()
    resource_resolver = {} # (kind, namespace, name) -> uid

    def add_to_resolver(items, kind):
        for item in items:
            m = item.get("metadata", {})
            ns = m.get("namespace", "default") if kind not in ["clusterrole", "clusterrolebinding"] else "cluster-wide"
            name = m.get("name", "")
            uid = m.get("uid", name)
            resource_resolver[(kind, ns, name)] = uid

    add_to_resolver(pods, "pod")
    add_to_resolver(service_accounts, "serviceaccount")
    add_to_resolver(roles, "role")
    add_to_resolver(cluster_roles, "clusterrole")
    add_to_resolver(secrets, "secret")
    add_to_resolver(configmaps, "configmap")
    add_to_resolver(role_bindings, "rolebinding")
    add_to_resolver(cluster_role_bindings, "clusterrolebinding")

    # Add internet entry point
    nodes.append({
        "id": "internet",
        "label": "Internet",
        "type": "internet",
        "namespace": "external",
        "risk_level": "entry-point",
        "metadata": {"description": "External internet traffic entry point", "icon": "globe"},
    })
    all_node_ids.add("internet")

    for pod in pods:
        node = _pod_to_node(pod)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for sa in service_accounts:
        node = _sa_to_node(sa)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for role in roles:
        node = _role_to_node(role, is_cluster=False)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for cr in cluster_roles:
        node = _role_to_node(cr, is_cluster=True)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for secret in secrets:
        node = _secret_to_node(secret)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    for cm in configmaps:
        node = _configmap_to_node(cm)
        if node and node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])

    # Build edges
    print("🔗 Building graph edges...")
    edges = []

    # Pod → ServiceAccount edges
    edges.extend(_build_pod_sa_edges(pods, resource_resolver))

    # RoleBinding / ClusterRoleBinding → node + edge extraction
    for rb in role_bindings:
        node, binding_edges = _binding_to_node_and_edges(rb, resource_resolver, is_cluster=False)
        if node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])
        edges.extend(binding_edges)

    for crb in cluster_role_bindings:
        node, binding_edges = _binding_to_node_and_edges(crb, resource_resolver, is_cluster=True)
        if node["id"] not in all_node_ids:
            nodes.append(node)
            all_node_ids.add(node["id"])
        edges.extend(binding_edges)

    # Role → Secret edges
    all_roles = roles + cluster_roles
    edges.extend(_build_role_secret_edges(all_roles, secrets, resource_resolver))

    # Filter edges to only reference existing nodes
    edges = [e for e in edges if e["source"] in all_node_ids and e["target"] in all_node_ids]

    # Annotate CVEs using the scorer
    print("🛡️  Scoring CVEs...")
    for node in nodes:
        if node["type"] == "pod" and "containers" in node.get("metadata", {}):
            pod_cves = set()
            container_scores = []
            
            for container in node["metadata"]["containers"]:
                c_cves = container.get("cves", [])
                if c_cves:
                    cve_scores = [score_cve(cve, live=live_cve)["cvss"] for cve in c_cves]
                    c_risk = max(cve_scores) if cve_scores else 0.0
                    container["score"] = c_risk
                    container_scores.append(c_risk)
                    pod_cves.update(c_cves)
            
            if container_scores:
                container_scores.sort(reverse=True)
                # Compound Risk Formula: Highest container score + 10% of sum of other container scores
                pod_risk = container_scores[0] + 0.1 * sum(container_scores[1:])
                node["metadata"]["pod_risk_score"] = round(pod_risk, 2)
                
                # Top-level CVEs
                node["metadata"]["cves"] = list(pod_cves)
                node["metadata"]["cvss_scores"] = [score_cve(cve, live=live_cve)["cvss"] for cve in node["metadata"]["cves"]]
                
                if pod_risk > 8.0 and node["risk_level"] not in ("crown-jewel", "entry-point"):
                    node["risk_level"] = "critical"
                elif pod_risk > 6.0 and node["risk_level"] not in ("crown-jewel", "entry-point", "critical"):
                    node["risk_level"] = "high"
        else:
            cves = node.get("metadata", {}).get("cves", [])
            if cves:
                node["metadata"]["cvss_scores"] = [
                    score_cve(cve, live=live_cve)["cvss"] for cve in cves
                ]
                risk = compute_node_risk_score(cves, live=live_cve)
                node["metadata"]["pod_risk_score"] = risk
                if risk > 8.0 and node["risk_level"] not in ("crown-jewel", "entry-point"):
                    node["risk_level"] = "critical"

    # Build the final graph document
    graph_data = {
        "metadata": {
            "cluster_name": _get_cluster_name(),
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario": "Live Cluster Scan",
            "description": f"Auto-ingested from live cluster. {len(nodes)} entities, {len(edges)} relationships.",
        },
        "nodes": nodes,
        "edges": edges,
    }

    # Write to file
    output = Path(output_path)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)

    print(f"\n✅ Cluster graph exported to: {output.resolve()}")
    print(f"   Nodes: {len(nodes)} | Edges: {len(edges)}")

    return graph_data


def _get_cluster_name() -> str:
    """Get the current Kubernetes cluster name from kubectl config."""
    try:
        result = subprocess.run(
            ["kubectl", "config", "current-context"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "unknown-cluster"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest Kubernetes cluster state into a graph JSON file.")
    parser.add_argument("-o", "--output", default="cluster-graph.json", help="Output JSON file path")
    parser.add_argument("--live-cve", action="store_true", help="Enable live NVD API CVE lookups")
    args = parser.parse_args()

    ingest_cluster(output_path=args.output, live_cve=args.live_cve)
```

## backend\kill-chain-report.pdf

*(Could not read file: 'utf-8' codec can't decode byte 0x93 in position 10: invalid start byte)*

## backend\main.py

```python
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
    title="KubeInsights API",
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
            # Allow pure comment objects used in the rubric dataset
            if "comment" in edge or "_comment" in edge:
                continue
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
```

## backend\mock-cluster-graph.json

```json
{
  "metadata": {
    "cluster": "mock-prod-cluster",
    "generated": "2026-04-03",
    "node_count": 40,
    "edge_count": 58,
    "pre_planted_paths": 6,
    "description": "Synthetic Kubernetes cluster for hackathon testing"
  },
  "nodes": [
    {"id": "internet",           "type": "ExternalActor",    "name": "internet",              "namespace": "external",  "risk_score": 10.0, "is_source": true,  "is_sink": false, "cves": []},
    {"id": "user-dev1",          "type": "User",             "name": "dev-1",                 "namespace": "default",   "risk_score": 5.0,  "is_source": true,  "is_sink": false, "cves": []},
    {"id": "user-dev2",          "type": "User",             "name": "dev-2",                 "namespace": "default",   "risk_score": 5.0,  "is_source": true,  "is_sink": false, "cves": []},
    {"id": "user-cicd",          "type": "User",             "name": "cicd-bot",              "namespace": "ci",        "risk_score": 6.0,  "is_source": true,  "is_sink": false, "cves": []},
    {"id": "pod-webfront",       "type": "Pod",              "name": "web-frontend",          "namespace": "default",   "risk_score": 7.5,  "is_source": false, "is_sink": false, "cves": ["CVE-2024-1234"]},
    {"id": "pod-api",            "type": "Pod",              "name": "api-server",            "namespace": "default",   "risk_score": 6.0,  "is_source": false, "is_sink": false, "cves": ["CVE-2023-4567"]},
    {"id": "pod-worker",         "type": "Pod",              "name": "background-worker",     "namespace": "default",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "pod-metrics",        "type": "Pod",              "name": "metrics-collector",     "namespace": "monitoring","risk_score": 3.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "pod-logger",         "type": "Pod",              "name": "log-aggregator",        "namespace": "logging",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": ["CVE-2024-9999"]},
    {"id": "pod-admission",      "type": "Pod",              "name": "admission-webhook",     "namespace": "kube-system","risk_score": 8.5, "is_source": false, "is_sink": false, "cves": []},
    {"id": "pod-sidecar",        "type": "Pod",              "name": "sidecar-proxy",         "namespace": "default",   "risk_score": 5.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-webapp",          "type": "ServiceAccount",  "name": "sa-webapp",             "namespace": "default",   "risk_score": 5.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-worker",          "type": "ServiceAccount",  "name": "sa-worker",             "namespace": "default",   "risk_score": 4.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-monitor",         "type": "ServiceAccount",  "name": "sa-monitor",            "namespace": "monitoring","risk_score": 3.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-cicd",            "type": "ServiceAccount",  "name": "sa-cicd",               "namespace": "ci",        "risk_score": 8.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-logger",          "type": "ServiceAccount",  "name": "sa-logger",             "namespace": "logging",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-default",         "type": "ServiceAccount",  "name": "default",               "namespace": "default",   "risk_score": 6.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "role-secret-reader", "type": "Role",            "name": "secret-reader",         "namespace": "default",   "risk_score": 7.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "role-pod-exec",      "type": "Role",            "name": "pod-exec",              "namespace": "default",   "risk_score": 8.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "role-node-reader",   "type": "Role",            "name": "node-reader",           "namespace": "default",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "clusterrole-admin",  "type": "ClusterRole",     "name": "cluster-admin",         "namespace": "cluster",   "risk_score": 10.0, "is_source": false, "is_sink": false, "cves": []},
    {"id": "clusterrole-view",   "type": "ClusterRole",     "name": "cluster-viewer",        "namespace": "cluster",   "risk_score": 2.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "clusterrole-deploy", "type": "ClusterRole",     "name": "deployer",              "namespace": "cluster",   "risk_score": 7.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-db-creds",    "type": "Secret",          "name": "db-credentials",        "namespace": "default",   "risk_score": 9.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-api-key",     "type": "Secret",          "name": "api-key",               "namespace": "default",   "risk_score": 8.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-tls",         "type": "Secret",          "name": "tls-cert",              "namespace": "default",   "risk_score": 6.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-admin-token", "type": "Secret",          "name": "admin-token",           "namespace": "kube-system","risk_score": 10.0, "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-cicd-token",  "type": "Secret",          "name": "cicd-deploy-token",     "namespace": "ci",        "risk_score": 8.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "configmap-env",      "type": "ConfigMap",       "name": "app-env-config",        "namespace": "default",   "risk_score": 3.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "configmap-dburl",    "type": "ConfigMap",       "name": "db-url-config",         "namespace": "default",   "risk_score": 5.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "db-production",      "type": "Database",        "name": "production-db",         "namespace": "data",      "risk_score": 10.0, "is_source": false, "is_sink": true,  "cves": []},
    {"id": "db-analytics",       "type": "Database",        "name": "analytics-db",          "namespace": "data",      "risk_score": 7.0,  "is_source": false, "is_sink": true,  "cves": []},
    {"id": "node-worker-1",      "type": "Node",            "name": "worker-node-1",         "namespace": "cluster",   "risk_score": 9.0,  "is_source": false, "is_sink": true,  "cves": ["CVE-2024-3116"]},
    {"id": "node-worker-2",      "type": "Node",            "name": "worker-node-2",         "namespace": "cluster",   "risk_score": 9.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "lb-service",         "type": "Service",         "name": "loadbalancer-svc",      "namespace": "default",   "risk_score": 6.5,  "is_source": true,  "is_sink": false, "cves": []},
    {"id": "svc-internal-api",   "type": "Service",         "name": "internal-api-svc",      "namespace": "default",   "risk_score": 5.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "ns-default",         "type": "Namespace",       "name": "default",               "namespace": "cluster",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "ns-kube-system",     "type": "Namespace",       "name": "kube-system",           "namespace": "cluster",   "risk_score": 9.0,  "is_source": false, "is_sink": true,  "cves": []},
    {"id": "pvc-data",           "type": "PersistentVolume","name": "data-pvc",              "namespace": "data",      "risk_score": 7.0,  "is_source": false, "is_sink": true,  "cves": []},
    {"id": "svc-service-a",      "type": "Service",         "name": "service-a",             "namespace": "default",   "risk_score": 5.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "svc-service-b",      "type": "Service",         "name": "service-b",             "namespace": "default",   "risk_score": 5.0,  "is_source": false, "is_sink": false, "cves": []}
  ],
  "edges": [
    {"comment": "=== PATH 1: dev-1 -> web-frontend -> sa-webapp -> role-secret-reader -> secret-db-creds -> production-db ==="},
    {"source": "user-dev1",        "target": "pod-webfront",      "relationship": "can-exec",        "weight": 5.0,  "cve": "CVE-2024-1234", "cvss": 8.1},
    {"source": "pod-webfront",     "target": "sa-webapp",         "relationship": "uses",            "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "sa-webapp",        "target": "role-secret-reader","relationship": "bound-to",        "weight": 4.0,  "cve": null,            "cvss": null},
    {"source": "role-secret-reader","target": "secret-db-creds",  "relationship": "can-read",        "weight": 5.5,  "cve": null,            "cvss": null},
    {"source": "secret-db-creds",  "target": "db-production",     "relationship": "grants-access-to","weight": 6.6,  "cve": null,            "cvss": null},

    {"comment": "=== PATH 2: internet -> lb-service -> pod-api -> sa-worker -> role-pod-exec -> node-worker-1 ==="},
    {"source": "internet",         "target": "lb-service",        "relationship": "reaches",         "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "lb-service",       "target": "pod-api",           "relationship": "routes-to",       "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "pod-api",          "target": "sa-worker",         "relationship": "uses",            "weight": 3.5,  "cve": "CVE-2023-4567", "cvss": 7.2},
    {"source": "sa-worker",        "target": "role-pod-exec",     "relationship": "bound-to",        "weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "role-pod-exec",    "target": "node-worker-1",     "relationship": "can-exec-on",     "weight": 7.0,  "cve": "CVE-2024-3116", "cvss": 9.0},

    {"comment": "=== PATH 3: cicd-bot -> sa-cicd -> clusterrole-deploy -> secret-cicd-token -> production-db ==="},
    {"source": "user-cicd",        "target": "sa-cicd",           "relationship": "impersonates",    "weight": 4.0,  "cve": null,            "cvss": null},
    {"source": "sa-cicd",          "target": "clusterrole-deploy","relationship": "bound-to",        "weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "clusterrole-deploy","target": "secret-cicd-token","relationship": "can-read",        "weight": 4.5,  "cve": null,            "cvss": null},
    {"source": "secret-cicd-token","target": "db-production",     "relationship": "grants-access-to","weight": 7.0,  "cve": null,            "cvss": null},

    {"comment": "=== PATH 4: internet -> lb-service -> pod-webfront -> sa-default -> clusterrole-admin -> secret-admin-token -> kube-system ==="},
    {"source": "pod-webfront",     "target": "sa-default",        "relationship": "falls-back-to",   "weight": 6.0,  "cve": null,            "cvss": null},
    {"source": "sa-default",       "target": "clusterrole-admin", "relationship": "bound-to",        "weight": 8.0,  "cve": null,            "cvss": null},
    {"source": "clusterrole-admin","target": "secret-admin-token","relationship": "can-read",        "weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "secret-admin-token","target": "ns-kube-system",   "relationship": "grants-access-to","weight": 9.0,  "cve": null,            "cvss": null},

    {"comment": "=== PATH 5: dev-2 -> pod-logger -> sa-logger -> role-node-reader -> node-worker-1 -> pvc-data ==="},
    {"source": "user-dev2",        "target": "pod-logger",        "relationship": "can-exec",        "weight": 4.0,  "cve": "CVE-2024-9999", "cvss": 6.5},
    {"source": "pod-logger",       "target": "sa-logger",         "relationship": "uses",            "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "sa-logger",        "target": "role-node-reader",  "relationship": "bound-to",        "weight": 3.5,  "cve": null,            "cvss": null},
    {"source": "role-node-reader", "target": "node-worker-1",     "relationship": "can-read",        "weight": 4.5,  "cve": null,            "cvss": null},
    {"source": "node-worker-1",    "target": "pvc-data",          "relationship": "mounts",          "weight": 5.0,  "cve": null,            "cvss": null},

    {"comment": "=== PATH 6: internet -> lb-service -> pod-api -> configmap-dburl -> db-analytics ==="},
    {"source": "pod-api",          "target": "configmap-dburl",   "relationship": "reads",           "weight": 2.5,  "cve": null,            "cvss": null},
    {"source": "configmap-dburl",  "target": "db-analytics",      "relationship": "exposes-endpoint","weight": 4.0,  "cve": null,            "cvss": null},

    {"comment": "=== CYCLE: service-a <-> service-b mutual admin grant (DFS cycle detection) ==="},
    {"source": "svc-service-a",    "target": "svc-service-b",     "relationship": "admin-grant",     "weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "svc-service-b",    "target": "svc-service-a",     "relationship": "admin-grant",     "weight": 5.0,  "cve": null,            "cvss": null},

    {"comment": "=== ADDITIONAL EDGES (non-attack-path, realistic cluster noise) ==="},
    {"source": "pod-metrics",      "target": "sa-monitor",        "relationship": "uses",            "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "sa-monitor",       "target": "clusterrole-view",  "relationship": "bound-to",        "weight": 1.5,  "cve": null,            "cvss": null},
    {"source": "clusterrole-view", "target": "configmap-env",     "relationship": "can-read",        "weight": 1.0,  "cve": null,            "cvss": null},
    {"source": "pod-worker",       "target": "sa-worker",         "relationship": "uses",            "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "pod-sidecar",      "target": "sa-webapp",         "relationship": "uses",            "weight": 2.5,  "cve": null,            "cvss": null},
    {"source": "sa-webapp",        "target": "secret-tls",        "relationship": "can-read",        "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "sa-webapp",        "target": "secret-api-key",    "relationship": "can-read",        "weight": 4.0,  "cve": null,            "cvss": null},
    {"source": "secret-api-key",   "target": "db-analytics",      "relationship": "grants-access-to","weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "pod-admission",    "target": "ns-kube-system",    "relationship": "deployed-in",     "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "pod-webfront",     "target": "svc-internal-api",  "relationship": "calls",           "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "svc-internal-api", "target": "pod-api",           "relationship": "routes-to",       "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "user-dev1",        "target": "pod-worker",        "relationship": "can-exec",        "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "node-worker-2",    "target": "ns-default",        "relationship": "hosts",           "weight": 1.0,  "cve": null,            "cvss": null},
    {"source": "pod-api",          "target": "secret-api-key",    "relationship": "mounts",          "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "sa-cicd",          "target": "secret-cicd-token", "relationship": "can-read",        "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "clusterrole-admin","target": "ns-default",        "relationship": "admin-over",      "weight": 6.0,  "cve": null,            "cvss": null},
    {"source": "role-pod-exec",    "target": "node-worker-2",     "relationship": "can-exec-on",     "weight": 7.0,  "cve": null,            "cvss": null},
    {"source": "pod-logger",       "target": "configmap-env",     "relationship": "reads",           "weight": 1.5,  "cve": null,            "cvss": null},
    {"source": "internet",         "target": "pod-webfront",      "relationship": "reaches",         "weight": 4.0,  "cve": "CVE-2024-1234", "cvss": 8.1},
    {"source": "lb-service",       "target": "pod-webfront",      "relationship": "routes-to",       "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "sa-default",       "target": "secret-db-creds",   "relationship": "can-read",        "weight": 7.0,  "cve": null,            "cvss": null}
  ]
}
```

## backend\requirements.txt

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
networkx==3.3
pydantic==2.9.0
python-multipart==0.0.9
reportlab==4.2.5
```

## backend\run_test.py

```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

exec(open("test_rubric.py", encoding="utf-8").read())
```

## backend\temporal.py

```python
"""
KubeInsights Temporal Analysis — Snapshot storage, retrieval, and comparison.
Enables diffing graph state over time to detect security regressions.
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
```

## backend\test_e2e.py

```python
"""End-to-end CLI test — run the full report and save to file."""
import subprocess, sys

tests = [
    ("Full Report", ["python", "cli.py", "analyze", "--input", "mock-cluster-graph.json"]),
    ("Blast Radius", ["python", "cli.py", "blast-radius", "--source", "pod-webfront", "--hops", "3", "--input", "mock-cluster-graph.json"]),
    ("Shortest Path", ["python", "cli.py", "shortest-path", "--source", "user-dev1", "--target", "db-production", "--input", "mock-cluster-graph.json"]),
    ("No Path", ["python", "cli.py", "shortest-path", "--source", "svc-service-a", "--target", "db-analytics", "--input", "mock-cluster-graph.json"]),
    ("Cycles", ["python", "cli.py", "detect-cycles", "--input", "mock-cluster-graph.json"]),
    ("Help", ["python", "cli.py", "--help"]),
]

with open("e2e_results.txt", "w", encoding="utf-8") as f:
    for name, cmd in tests:
        f.write(f"\n{'='*60}\n  TEST: {name}\n  CMD: {' '.join(cmd)}\n{'='*60}\n")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            f.write(result.stdout)
            if result.stderr:
                f.write(f"\nSTDERR:\n{result.stderr}")
            f.write(f"\nEXIT CODE: {result.returncode}\n")
        except Exception as ex:
            f.write(f"\nERROR: {ex}\n")

print("Done! Results in e2e_results.txt")
```

## backend\test_output.txt

```
﻿Nodes: 41, Edges: 48

=== BFS-1: pod-webfront, hops=3 ===
Total reachable: 15
  Hop 1: ['default', 'internal-api-svc', 'sa-webapp']
  Hop 2: ['api-key', 'api-server', 'cluster-admin', 'db-credentials', 'secret-reader', 'tls-cert']
  Hop 3: ['admin-token', 'analytics-db', 'db-url-config', 'default', 'production-db', 'sa-worker']

=== BFS-2: user-cicd (cicd-bot), hops=2 ===
Total reachable: 3
  Hop 1: ['sa-cicd']
  Hop 2: ['cicd-deploy-token', 'deployer']

=== DIJK-1: user-dev1 -> db-production ===
Path: dev-1 -> web-frontend -> sa-webapp -> secret-reader -> db-credentials -> production-db
Cost: 24.1, Hops: 5

=== DIJK-2: internet -> ns-kube-system ===
Path: internet -> web-frontend -> default -> cluster-admin -> admin-token -> kube-system
Cost: 32.0, Hops: 5

=== DFS-1: Cycle Detection ===
Cycles found: 1
python : Traceback (most 
recent call last):
At line:1 char:1
+ python test_rubric.py 
2>&1 | Out-File -FilePath 
"test_output.txt" -En ...
+ 
~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo        
      : NotSpecified: (T  
  raceback (most recent   
  call last)::String)     
[], RemoteException
    + FullyQualifiedError 
   Id : NativeCommandErr  
  or
 
  File "C:\Users\akars\One
Drive\Desktop\kuber 
attack path visualizer\bac
kend\test_rubric.py", 
line 44, in <module>
    print(f"  
{c['description']}")
    ~~~~~^^^^^^^^^^^^^^^^^
^^^^^^^^
  File "C:\Users\akars\App
Data\Local\Programs\Python
\Python313\Lib\encodings\c
p1252.py", line 19, in 
encode
    return codecs.charmap_
encode(input,self.errors,e
ncoding_table)[0]
           ~~~~~~~~~~~~~~~
~~~~~~^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^
UnicodeEncodeError: 
'charmap' codec can't 
encode character '\u2194' 
in position 12: character 
maps to <undefined>
```

## backend\test_results.txt

```
Nodes: 41, Edges: 48

=== BFS-1: pod-webfront, hops=3 ===
Total reachable: 15
  Hop 1: ['default', 'internal-api-svc', 'sa-webapp']
  Hop 2: ['api-key', 'api-server', 'cluster-admin', 'db-credentials', 'secret-reader', 'tls-cert']
  Hop 3: ['admin-token', 'analytics-db', 'db-url-config', 'default', 'production-db', 'sa-worker']

=== BFS-2: user-cicd, hops=2 ===
Total reachable: 3
  Hop 1: ['sa-cicd']
  Hop 2: ['cicd-deploy-token', 'deployer']

=== DIJK-1: user-dev1 -> db-production ===
Path: dev-1 -> web-frontend -> sa-webapp -> secret-reader -> db-credentials -> production-db
Cost: 24.1, Hops: 5

=== DIJK-2: internet -> ns-kube-system ===
Path: internet -> web-frontend -> default -> cluster-admin -> admin-token -> kube-system
Cost: 32.0, Hops: 5

=== DIJK-3: no-path test ===
Path exists: False
Error: No path found from 'svc-service-a' to 'db-analytics'

=== DFS-1: Cycle Detection ===
Cycles found: 1
  service-b ↔ service-a ↔ service-b

=== CNA-1: Critical Node ===
Baseline paths: 46
Critical: web-frontend (Pod), broken: 32
Top 5:
  web-frontend                   (Pod            ) -32 paths
  api-server                     (Pod            ) -24 paths
  internal-api-svc               (Service        ) -16 paths
  sa-worker                      (ServiceAccount ) -14 paths
  pod-exec                       (Role           ) -14 paths

=== All Attack Paths: 18 ===
  #1: loadbalancer-svc -> analytics-db | 3 hops | cost=9.5
  #2: internet -> analytics-db | 4 hops | cost=11.5
  #3: cicd-bot -> production-db | 3 hops | cost=14.0
  #4: dev-2 -> worker-node-1 | 4 hops | cost=15.0
  #5: dev-1 -> analytics-db | 5 hops | cost=15.5
  #6: dev-1 -> worker-node-1 | 4 hops | cost=17.0
  #7: loadbalancer-svc -> worker-node-1 | 4 hops | cost=18.5
  #8: dev-2 -> data-pvc | 5 hops | cost=20.0
  #9: internet -> worker-node-1 | 5 hops | cost=20.5
  #10: dev-1 -> data-pvc | 5 hops | cost=22.0
  #11: loadbalancer-svc -> production-db | 5 hops | cost=22.1
  #12: internet -> production-db | 5 hops | cost=23.1
  #13: loadbalancer-svc -> data-pvc | 5 hops | cost=23.5
  #14: dev-1 -> production-db | 5 hops | cost=24.1
  #15: internet -> data-pvc | 6 hops | cost=25.5
  #16: loadbalancer-svc -> kube-system | 5 hops | cost=31.0
  #17: internet -> kube-system | 5 hops | cost=32.0
  #18: dev-1 -> kube-system | 5 hops | cost=33.0
```

## backend\test_rubric.py

```python
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
```

## backend\checklist\mock-cluster-graphnew.json

```json
{
  "metadata": {
    "cluster": "mock-prod-cluster",
    "generated": "2026-04-03",
    "node_count": 40,
    "edge_count": 58,
    "pre_planted_paths": 6,
    "description": "Synthetic Kubernetes cluster for hackathon testing"
  },
  "nodes": [
    {"id": "internet",           "type": "ExternalActor",    "name": "internet",              "namespace": "external",  "risk_score": 10.0, "is_source": true,  "is_sink": false, "cves": []},
    {"id": "user-dev1",          "type": "User",             "name": "dev-1",                 "namespace": "default",   "risk_score": 5.0,  "is_source": true,  "is_sink": false, "cves": []},
    {"id": "user-dev2",          "type": "User",             "name": "dev-2",                 "namespace": "default",   "risk_score": 5.0,  "is_source": true,  "is_sink": false, "cves": []},
    {"id": "user-cicd",          "type": "User",             "name": "cicd-bot",              "namespace": "ci",        "risk_score": 6.0,  "is_source": true,  "is_sink": false, "cves": []},
    {"id": "pod-webfront",       "type": "Pod",              "name": "web-frontend",          "namespace": "default",   "risk_score": 7.5,  "is_source": false, "is_sink": false, "cves": ["CVE-2024-1234"]},
    {"id": "pod-api",            "type": "Pod",              "name": "api-server",            "namespace": "default",   "risk_score": 6.0,  "is_source": false, "is_sink": false, "cves": ["CVE-2023-4567"]},
    {"id": "pod-worker",         "type": "Pod",              "name": "background-worker",     "namespace": "default",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "pod-metrics",        "type": "Pod",              "name": "metrics-collector",     "namespace": "monitoring","risk_score": 3.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "pod-logger",         "type": "Pod",              "name": "log-aggregator",        "namespace": "logging",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": ["CVE-2024-9999"]},
    {"id": "pod-admission",      "type": "Pod",              "name": "admission-webhook",     "namespace": "kube-system","risk_score": 8.5, "is_source": false, "is_sink": false, "cves": []},
    {"id": "pod-sidecar",        "type": "Pod",              "name": "sidecar-proxy",         "namespace": "default",   "risk_score": 5.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-webapp",          "type": "ServiceAccount",  "name": "sa-webapp",             "namespace": "default",   "risk_score": 5.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-worker",          "type": "ServiceAccount",  "name": "sa-worker",             "namespace": "default",   "risk_score": 4.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-monitor",         "type": "ServiceAccount",  "name": "sa-monitor",            "namespace": "monitoring","risk_score": 3.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-cicd",            "type": "ServiceAccount",  "name": "sa-cicd",               "namespace": "ci",        "risk_score": 8.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-logger",          "type": "ServiceAccount",  "name": "sa-logger",             "namespace": "logging",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "sa-default",         "type": "ServiceAccount",  "name": "default",               "namespace": "default",   "risk_score": 6.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "role-secret-reader", "type": "Role",            "name": "secret-reader",         "namespace": "default",   "risk_score": 7.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "role-pod-exec",      "type": "Role",            "name": "pod-exec",              "namespace": "default",   "risk_score": 8.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "role-node-reader",   "type": "Role",            "name": "node-reader",           "namespace": "default",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "clusterrole-admin",  "type": "ClusterRole",     "name": "cluster-admin",         "namespace": "cluster",   "risk_score": 10.0, "is_source": false, "is_sink": false, "cves": []},
    {"id": "clusterrole-view",   "type": "ClusterRole",     "name": "cluster-viewer",        "namespace": "cluster",   "risk_score": 2.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "clusterrole-deploy", "type": "ClusterRole",     "name": "deployer",              "namespace": "cluster",   "risk_score": 7.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-db-creds",    "type": "Secret",          "name": "db-credentials",        "namespace": "default",   "risk_score": 9.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-api-key",     "type": "Secret",          "name": "api-key",               "namespace": "default",   "risk_score": 8.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-tls",         "type": "Secret",          "name": "tls-cert",              "namespace": "default",   "risk_score": 6.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-admin-token", "type": "Secret",          "name": "admin-token",           "namespace": "kube-system","risk_score": 10.0, "is_source": false, "is_sink": false, "cves": []},
    {"id": "secret-cicd-token",  "type": "Secret",          "name": "cicd-deploy-token",     "namespace": "ci",        "risk_score": 8.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "configmap-env",      "type": "ConfigMap",       "name": "app-env-config",        "namespace": "default",   "risk_score": 3.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "configmap-dburl",    "type": "ConfigMap",       "name": "db-url-config",         "namespace": "default",   "risk_score": 5.5,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "db-production",      "type": "Database",        "name": "production-db",         "namespace": "data",      "risk_score": 10.0, "is_source": false, "is_sink": true,  "cves": []},
    {"id": "db-analytics",       "type": "Database",        "name": "analytics-db",          "namespace": "data",      "risk_score": 7.0,  "is_source": false, "is_sink": true,  "cves": []},
    {"id": "node-worker-1",      "type": "Node",            "name": "worker-node-1",         "namespace": "cluster",   "risk_score": 9.0,  "is_source": false, "is_sink": true,  "cves": ["CVE-2024-3116"]},
    {"id": "node-worker-2",      "type": "Node",            "name": "worker-node-2",         "namespace": "cluster",   "risk_score": 9.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "lb-service",         "type": "Service",         "name": "loadbalancer-svc",      "namespace": "default",   "risk_score": 6.5,  "is_source": true,  "is_sink": false, "cves": []},
    {"id": "svc-internal-api",   "type": "Service",         "name": "internal-api-svc",      "namespace": "default",   "risk_score": 5.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "ns-default",         "type": "Namespace",       "name": "default",               "namespace": "cluster",   "risk_score": 4.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "ns-kube-system",     "type": "Namespace",       "name": "kube-system",           "namespace": "cluster",   "risk_score": 9.0,  "is_source": false, "is_sink": true,  "cves": []},
    {"id": "pvc-data",           "type": "PersistentVolume","name": "data-pvc",              "namespace": "data",      "risk_score": 7.0,  "is_source": false, "is_sink": true,  "cves": []},
    {"id": "svc-service-a",      "type": "Service",         "name": "service-a",             "namespace": "default",   "risk_score": 5.0,  "is_source": false, "is_sink": false, "cves": []},
    {"id": "svc-service-b",      "type": "Service",         "name": "service-b",             "namespace": "default",   "risk_score": 5.0,  "is_source": false, "is_sink": false, "cves": []}
  ],
  "edges": [
    {"comment": "=== PATH 1: dev-1 -> web-frontend -> sa-webapp -> role-secret-reader -> secret-db-creds -> production-db ==="},
    {"source": "user-dev1",        "target": "pod-webfront",      "relationship": "can-exec",        "weight": 5.0,  "cve": "CVE-2024-1234", "cvss": 8.1},
    {"source": "pod-webfront",     "target": "sa-webapp",         "relationship": "uses",            "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "sa-webapp",        "target": "role-secret-reader","relationship": "bound-to",        "weight": 4.0,  "cve": null,            "cvss": null},
    {"source": "role-secret-reader","target": "secret-db-creds",  "relationship": "can-read",        "weight": 5.5,  "cve": null,            "cvss": null},
    {"source": "secret-db-creds",  "target": "db-production",     "relationship": "grants-access-to","weight": 6.6,  "cve": null,            "cvss": null},

    {"comment": "=== PATH 2: internet -> lb-service -> pod-api -> sa-worker -> role-pod-exec -> node-worker-1 ==="},
    {"source": "internet",         "target": "lb-service",        "relationship": "reaches",         "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "lb-service",       "target": "pod-api",           "relationship": "routes-to",       "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "pod-api",          "target": "sa-worker",         "relationship": "uses",            "weight": 3.5,  "cve": "CVE-2023-4567", "cvss": 7.2},
    {"source": "sa-worker",        "target": "role-pod-exec",     "relationship": "bound-to",        "weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "role-pod-exec",    "target": "node-worker-1",     "relationship": "can-exec-on",     "weight": 7.0,  "cve": "CVE-2024-3116", "cvss": 9.0},

    {"comment": "=== PATH 3: cicd-bot -> sa-cicd -> clusterrole-deploy -> secret-cicd-token -> production-db ==="},
    {"source": "user-cicd",        "target": "sa-cicd",           "relationship": "impersonates",    "weight": 4.0,  "cve": null,            "cvss": null},
    {"source": "sa-cicd",          "target": "clusterrole-deploy","relationship": "bound-to",        "weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "clusterrole-deploy","target": "secret-cicd-token","relationship": "can-read",        "weight": 4.5,  "cve": null,            "cvss": null},
    {"source": "secret-cicd-token","target": "db-production",     "relationship": "grants-access-to","weight": 7.0,  "cve": null,            "cvss": null},

    {"comment": "=== PATH 4: internet -> lb-service -> pod-webfront -> sa-default -> clusterrole-admin -> secret-admin-token -> kube-system ==="},
    {"source": "pod-webfront",     "target": "sa-default",        "relationship": "falls-back-to",   "weight": 6.0,  "cve": null,            "cvss": null},
    {"source": "sa-default",       "target": "clusterrole-admin", "relationship": "bound-to",        "weight": 8.0,  "cve": null,            "cvss": null},
    {"source": "clusterrole-admin","target": "secret-admin-token","relationship": "can-read",        "weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "secret-admin-token","target": "ns-kube-system",   "relationship": "grants-access-to","weight": 9.0,  "cve": null,            "cvss": null},

    {"comment": "=== PATH 5: dev-2 -> pod-logger -> sa-logger -> role-node-reader -> node-worker-1 -> pvc-data ==="},
    {"source": "user-dev2",        "target": "pod-logger",        "relationship": "can-exec",        "weight": 4.0,  "cve": "CVE-2024-9999", "cvss": 6.5},
    {"source": "pod-logger",       "target": "sa-logger",         "relationship": "uses",            "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "sa-logger",        "target": "role-node-reader",  "relationship": "bound-to",        "weight": 3.5,  "cve": null,            "cvss": null},
    {"source": "role-node-reader", "target": "node-worker-1",     "relationship": "can-read",        "weight": 4.5,  "cve": null,            "cvss": null},
    {"source": "node-worker-1",    "target": "pvc-data",          "relationship": "mounts",          "weight": 5.0,  "cve": null,            "cvss": null},

    {"comment": "=== PATH 6: internet -> lb-service -> pod-api -> configmap-dburl -> db-analytics ==="},
    {"source": "pod-api",          "target": "configmap-dburl",   "relationship": "reads",           "weight": 2.5,  "cve": null,            "cvss": null},
    {"source": "configmap-dburl",  "target": "db-analytics",      "relationship": "exposes-endpoint","weight": 4.0,  "cve": null,            "cvss": null},

    {"comment": "=== CYCLE: service-a <-> service-b mutual admin grant (DFS cycle detection) ==="},
    {"source": "svc-service-a",    "target": "svc-service-b",     "relationship": "admin-grant",     "weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "svc-service-b",    "target": "svc-service-a",     "relationship": "admin-grant",     "weight": 5.0,  "cve": null,            "cvss": null},

    {"comment": "=== ADDITIONAL EDGES (non-attack-path, realistic cluster noise) ==="},
    {"source": "pod-metrics",      "target": "sa-monitor",        "relationship": "uses",            "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "sa-monitor",       "target": "clusterrole-view",  "relationship": "bound-to",        "weight": 1.5,  "cve": null,            "cvss": null},
    {"source": "clusterrole-view", "target": "configmap-env",     "relationship": "can-read",        "weight": 1.0,  "cve": null,            "cvss": null},
    {"source": "pod-worker",       "target": "sa-worker",         "relationship": "uses",            "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "pod-sidecar",      "target": "sa-webapp",         "relationship": "uses",            "weight": 2.5,  "cve": null,            "cvss": null},
    {"source": "sa-webapp",        "target": "secret-tls",        "relationship": "can-read",        "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "sa-webapp",        "target": "secret-api-key",    "relationship": "can-read",        "weight": 4.0,  "cve": null,            "cvss": null},
    {"source": "secret-api-key",   "target": "db-analytics",      "relationship": "grants-access-to","weight": 5.0,  "cve": null,            "cvss": null},
    {"source": "pod-admission",    "target": "ns-kube-system",    "relationship": "deployed-in",     "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "pod-webfront",     "target": "svc-internal-api",  "relationship": "calls",           "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "svc-internal-api", "target": "pod-api",           "relationship": "routes-to",       "weight": 2.0,  "cve": null,            "cvss": null},
    {"source": "user-dev1",        "target": "pod-worker",        "relationship": "can-exec",        "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "node-worker-2",    "target": "ns-default",        "relationship": "hosts",           "weight": 1.0,  "cve": null,            "cvss": null},
    {"source": "pod-api",          "target": "secret-api-key",    "relationship": "mounts",          "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "sa-cicd",          "target": "secret-cicd-token", "relationship": "can-read",        "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "clusterrole-admin","target": "ns-default",        "relationship": "admin-over",      "weight": 6.0,  "cve": null,            "cvss": null},
    {"source": "role-pod-exec",    "target": "node-worker-2",     "relationship": "can-exec-on",     "weight": 7.0,  "cve": null,            "cvss": null},
    {"source": "pod-logger",       "target": "configmap-env",     "relationship": "reads",           "weight": 1.5,  "cve": null,            "cvss": null},
    {"source": "internet",         "target": "pod-webfront",      "relationship": "reaches",         "weight": 4.0,  "cve": "CVE-2024-1234", "cvss": 8.1},
    {"source": "lb-service",       "target": "pod-webfront",      "relationship": "routes-to",       "weight": 3.0,  "cve": null,            "cvss": null},
    {"source": "sa-default",       "target": "secret-db-creds",   "relationship": "can-read",        "weight": 7.0,  "cve": null,            "cvss": null}
  ]
}
```

## backend\checklist\read_pdf.py

```python
import sys
import subprocess

try:
    import PyPDF2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2

def read_pdf(file_path, out_path):
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write(text)

read_pdf(
    r"c:\Users\akars\OneDrive\Desktop\kuber attack path visualizer\backend\checklist\scoring-rubric.pdf",
    r"c:\Users\akars\OneDrive\Desktop\kuber attack path visualizer\backend\checklist\rubric.txt"
)
```

## backend\checklist\rubric.txt

```
HACKATHON SCORING RUBRIC
 Kubernetes Attack Path Visualizer
 Graph-Based Security Analysis for Cloud-Native Infrastructure
 Track: Cloud Security / Infrastructure · Difficulty: Advanced · Total Marks: 100
 Domains: Graph Theory · Kubernetes · Cybersecurity
 
Overview
This rubric defines the detailed scoring breakdown for each deliverable. Judges will evaluate submissions against
each test case independently. Partial credit is awarded where a component is attempted but incomplete or incorrect.
All five deliverables are mandatory; bonus challenges do not substitute for core marks.
Deliverable
Algorithm / Method
Weight
Max Marks
1. Working CLI Tool
All algorithms + ingestion
30%
30
2. Kill Chain Report
Dijkstra output + formatting
25%
25
3. Algorithm Correctness
BFS / Dijkstra / DFS unit tests
20%
20
4. Critical Node Analysis
Graph surgery / node removal
15%
15
5. Code Quality & Docs
README, schema, readability
10%
10
TOTAL
100%
100
Deliverable 1 — Working CLI Tool [30 marks]
1.1 Data Ingestion & Graph Construction (10 marks)
The tool must correctly parse cluster-graph.json (or live kubectl output) into an in-memory directed graph. All node
attributes and edge weights must be preserved and accessible during traversal.
Score Band
 Criteria
 Points
Full Marks
cluster-graph.json parsed without errors. All 40+ nodes and edges
loaded. Node attributes (type, namespace, risk_score, is_source,
is_sink, cves) and edge attributes (relationship, weight, cve, cvss)
are accessible. Graph reports correct node/edge count.
10
Strong
Graph loads correctly. Minor attribute missing (e.g. cves not stored
per node) or one node type not handled. All edges present.
8
Good
Graph loads but 10-20% of edges or nodes missing due to parsing
logic errors. Core source/sink nodes present.
6
Partial
Graph partially constructed. Schema not fully followed. Fewer than
30 nodes loaded. Some edges missing.
4
Minimal
JSON parsed but graph library not used (e.g. stored as raw dict). No
proper node/edge model.
2
Not Attempted
No graph construction. Data not loaded or tool crashes on ingestion.
0
1.2 CLI Interface & Usability (10 marks)

The tool must expose all algorithms via a clean command-line interface with named flags. Help text, error messages,
and exit codes must be appropriate.
Score Band
 Criteria
 Points
Full Marks
All algorithms accessible via distinct CLI flags (--blast-radius,
--source/--target, --cycles, --critical-node, --full-report). --help works.
Unknown nodes produce clear error. Exit code 0 on success,
non-zero on failure.
10
Strong
All algorithms reachable. Minor usability gap (e.g. no --help, or error
message unclear for missing node).
8
Good
3 or 4 of 5 algorithm modes exposed. Positional args used instead of
flags.
6
Partial
Hardcoded source/target nodes. Algorithm selected by editing code,
not CLI.
3
Not Attempted
No CLI. Script runs with no arguments or only via interactive prompt.
0
1.3 End-to-End Integration Test (10 marks)
Judges will run the tool against the provided mock-cluster-graph.json and verify the combined full-report output
matches expected values (see Section 6 — Test Cases).
Score Band
 Criteria
 Points
Full Marks
All 6 pre-planted attack paths detected. Cycle detected. Critical node
identified. Report generated without exceptions. Runtime under 60
seconds on mock data.
10
Strong
5 of 6 paths detected. Cycle found. Minor formatting issue in output.
8
Good
3-4 paths detected. One algorithm produces incorrect results. No
crash.
5
Partial
Tool runs but only 1-2 paths found. One or more algorithm sections
missing from output.
3
Not Attempted
Tool crashes or produces no output on mock data.
0

Deliverable 2 — Kill Chain Report [25 marks]
2.1 Attack Path Accuracy (10 marks)
Each detected path must list the correct sequence of nodes, the correct hop count, and an accurate total risk score
(sum of edge weights along the path). CVE annotations must appear on edges where present in the data.
Expected output for Path #1 (mock dataset):
dev-1 → web-frontend [CVE-2024-1234, CVSS 8.1] → sa-webapp → secret-reader → db-credentials
→ production-db | 5 hops | Risk Score: 24.2
Score Band
 Criteria
 Points
Full Marks
All detected paths show: correct node sequence, correct hop count,
correct cumulative risk score (±0.1), CVE annotations on correct
edges. Paths sorted by risk score ascending.
10
Strong
Correct paths. Risk scores off by > 0.1 due to rounding, or CVE not
shown on one edge. Sort order wrong.
8
Good
Correct node sequences but hop count miscalculated (off-by-one) or
risk scores computed incorrectly for 2+ paths.
5
Partial
Paths shown but node IDs used instead of names, or paths
truncated. No risk score.
3
Not Attempted
No path output, or paths are fabricated/incorrect.
0
2.2 Report Readability & Structure (8 marks)
The report must be clearly structured with labelled sections, risk severity labels (CRITICAL / HIGH / MEDIUM / LOW),
and actionable remediation language.
Score Band
 Criteria
 Points
Full Marks
Report has clearly labelled sections (Attack Paths, Blast Radius,
Cycles, Critical Node, Summary). Risk severity labels applied
correctly based on score thresholds. Each path includes source,
target, hops, score, severity. Summary section present.
8
Good
Most sections present. Severity label missing or threshold wrong on
1-2 paths. Summary absent.
6
Partial
Report is a raw list with no section structure. No severity labels.
Paths printed without hop count.
3
Not Attempted
No report output.
0
2.3 Remediation Advice (7 marks)
The report must include actionable remediation recommendations for each identified risk, not just a description of the
problem.
Score Band
 Criteria
 Points

Full Marks
Each attack path includes specific remediation (e.g. 'Remove
RoleBinding secret-reader from sa-webapp', 'Patch CVE-2024-1234
on web-frontend', 'Break cycle: revoke admin-grant from service-b to
service-a'). Critical node recommendation includes estimated impact
(N paths eliminated).
7
Good
Generic remediation advice present (e.g. 'reduce privileges') but not
specific to each path or node.
5
Partial
Remediation section exists but is placeholder text or duplicated for all
paths.
2
Not Attempted
No remediation advice.
0

Deliverable 3 — Algorithm Correctness [20 marks]
Judges will run each algorithm against the mock dataset and three additional hidden test graphs. Correct output on the
mock dataset earns base marks; correct output on hidden tests earns full marks.
3.1 Algorithm 1 — Blast Radius (BFS) [7 marks]
Test Case BFS-1: Source = pod-webfront, hops = 3
Expected: Hop 1 = {sa-webapp, sa-default, internal-api-svc, sidecar-proxy} | Hop 2 =
{secret-reader, tls-cert, api-key, cluster-admin, api-server} | Hop 3 = {db-credentials,
secret-admin-token, sa-worker, db-url-config}
Test Case BFS-2: Source = cicd-bot, hops = 2
Expected: Hop 1 = {sa-cicd} | Hop 2 = {deployer, cicd-deploy-token}
Test Case BFS-3 (hidden): Single-node source with no outbound edges.
Expected: Empty blast radius (0 reachable nodes).
Score Band
 Criteria
 Points
Full Marks
BFS-1 and BFS-2 exact match. BFS-3 (hidden) handled correctly
(empty result, no crash). Layer assignments (hop number) correct.
Nodes not double-counted across layers.
7
Strong
BFS-1 correct. BFS-2 off by one node. BFS-3 not tested.
5
Good
BFS runs. Hop layers merged into flat list (layering not implemented).
Node set correct.
4
Partial
BFS implemented but visits nodes in wrong order or revisits nodes
(no visited set). Incorrect node counts.
2
Not Attempted
BFS not implemented. DFS or random walk used instead.
0
3.2 Algorithm 2 — Dijkstra's Shortest Path [7 marks]
Test Case DIJK-1: Source = user-dev1, Target = db-production
Expected path: user-dev1 → pod-webfront → sa-webapp → role-secret-reader → secret-db-creds
→ db-production | Cost = 24.1
Test Case DIJK-2: Source = internet, Target = ns-kube-system
Expected path: internet → web-frontend → sa-default → cluster-admin → secret-admin-token →
ns-kube-system | Cost = 32.0
Test Case DIJK-3 (hidden): Source and target with no connecting path.
Expected: Clear 'No path found' message. No exception raised.
Score Band
 Criteria
 Points
Full Marks
DIJK-1 and DIJK-2 return correct path and cost (±0.05). DIJK-3
handled gracefully with informative message. Uses edge weight
correctly (not hop count).
7
Strong
DIJK-1 correct. DIJK-2 finds a valid path but not the shortest. DIJK-3
not crash.
5
Good
Shortest path found by hop count (unweighted BFS) instead of
Dijkstra. Results differ from expected.
3
Partial
Path returned but incorrect. Cost not calculated or always 0.
1

Not Attempted
Algorithm not implemented or always returns empty.
0
3.3 Algorithm 3 — Cycle Detection (DFS) [6 marks]
Test Case DFS-1: Full graph — mock dataset
Expected: Exactly 1 cycle detected: [svc-service-a, svc-service-b] (mutual admin-grant). No
false positives.
Test Case DFS-2 (hidden): Graph with 3 planted cycles.
Expected: All 3 cycles returned. No duplicate reporting of the same cycle.
Score Band
 Criteria
 Points
Full Marks
DFS-1: exactly 1 cycle found, correct nodes. DFS-2 (hidden): all 3
cycles found, no duplicates. Cycle reported as ordered node list.
6
Strong
DFS-1 correct. DFS-2: 2 of 3 cycles found.
4
Good
Cycle detection works but reports duplicates (e.g. A→B→A and
B→A→B counted separately).
3
Partial
Cycle detection attempted. Returns True/False (cycle exists) but not
the cycle nodes.
1
Not Attempted
No cycle detection.
0

Deliverable 4 — Critical Node Analysis [15 marks]
4.1 Correct Critical Node Identification (8 marks)
The algorithm must correctly identify the single non-source, non-sink node whose removal from the graph eliminates
the greatest number of source-to-sink paths. Judges will verify by independently running nx.all_simple_paths on the
modified graph.
Expected result (mock dataset):
Critical node: web-frontend (Pod) | Paths eliminated: 32 of 46 | Runner-up: api-server (Pod),
-24 paths
Score Band
 Criteria
 Points
Full Marks
Correct critical node identified (web-frontend). Correct elimination
count (32). Top-5 ranking output matches expected ranking. Source
and sink nodes correctly excluded from candidates.
8
Strong
Correct critical node. Elimination count off by ±2 (path counting
method differs slightly). Ranking mostly correct.
6
Good
Second-ranked node (api-server) returned as critical node.
Methodology correct but tie-breaking logic differs.
4
Partial
Algorithm runs and returns a node, but node is clearly wrong (e.g. a
source or sink node returned). No ranking.
2
Not Attempted
Analysis not implemented or crashes.
0
4.2 Methodology Correctness (7 marks)
The removal-and-recount methodology must be correctly applied: the original graph must be unmodified after each
test removal, and path counting must use all simple paths (not just shortest paths).
Score Band
 Criteria
 Points
Full Marks
Graph copied (not mutated) before each node removal. All simple
paths counted (not just shortest). Cutoff depth applied consistently.
Baseline path count correct. Graph restored to original state after
analysis.
7
Strong
Correct methodology. Minor issue: cutoff not applied (performance
risk on large graphs) or baseline not reported.
5
Good
Graph mutated in-place (original graph corrupted after analysis).
Results still numerically correct on mock data but would fail on
sequential calls.
3
Partial
Only shortest path counted (not all paths). Node betweenness
centrality used as a proxy (valid approach but not
specification-compliant).
2
Not Attempted
No methodology. Random node returned.
0

Deliverable 5 — Code Quality & Documentation [10 marks]
5.1 Code Readability (4 marks)
Score Band
 Criteria
 Points
Full Marks
Functions have docstrings. Variables clearly named. Algorithms
separated into distinct functions. No magic numbers. PEP-8
compliant (or equivalent for Go/Java). No dead code.
4
Good
Mostly readable. A few long functions. Some magic numbers. Minor
style inconsistencies.
3
Partial
Code works but is in one long main() block. No functions. Hardcoded
values throughout.
1
Not Attempted
Unreadable / obfuscated.
0
5.2 Schema Documentation (3 marks)
The cluster-graph.json schema must be documented so that a new team member could extend it without reading the
source code.
Score Band
 Criteria
 Points
Full Marks
README or separate schema doc explains all node types, all edge
relationship types, weight semantics, is_source/is_sink flags, and
CVE field format. Example node and edge JSON included.
3
Good
Schema documented but missing 1-2 field explanations (e.g. weight
semantics not defined, or node types not enumerated).
2
Partial
Schema mentioned but not documented. Reader must infer from
JSON.
1
Not Attempted
No schema documentation.
0
5.3 README & Setup Instructions (3 marks)
Score Band
 Criteria
 Points
Full Marks
README includes: installation steps (pip install), all CLI usage
examples with expected output snippets, description of all 4
algorithms, project structure overview. New user can run the tool
within 5 minutes.
3
Good
README present with install and basic usage. Missing algorithm
descriptions or project structure.
2
Partial
README is a stub with title only, or only lists file names.
1
Not Attempted
No README.
0

Bonus Challenges [up to +15 marks, non-substitutable]
Bonus marks are awarded in addition to core marks. They cannot substitute for missing core deliverables. Maximum
score including bonuses is capped at 100.
Bonus
Description
Marks
Evaluation Criteria
B1 Interactive
Graph
Visualisation
Render the attack graph in a
browser using D3.js or
Cytoscape.js. Critical path
highlighted in red, safe nodes in
green.
+5
Graph renders without error. Attack
path nodes visually distinct. Zoom/pan
functional. Node tooltip shows name,
type, risk score.
B2 Live CVE
Scoring
Integrate with NIST NVD API to
auto-assign CVSS scores to Pod
nodes based on container image
version.
+5
API called successfully. CVSS score
fetched and applied to at least one
real CVE. Fallback to mock data if API
unavailable. Rate limiting handled.
B3 Temporal
Analysis
Store graph snapshots over time.
Alert when a new attack path
appears between two consecutive
scans (graph diff).
+5
Two snapshots loadable. Diff
identifies new nodes, new edges, and
new attack paths. Alert output clearly
describes what changed and the risk
delta.
Section 6 — Test Case Reference Summary
ID
Algorithm
Input
Expected Output
Marks
BFS-1
Blast Radius
source=pod-webfront,
hops=3
13 reachable nodes across 3
layers
3
BFS-2
Blast Radius
source=cicd-bot, hops=2
4 nodes: sa-cicd, deployer,
cicd-deploy-token + 1
2
BFS-3*
Blast Radius
source=isolated-node,
hops=3
0 reachable nodes, no crash
2
DIJK-1
Dijkstra
user-dev1 →
db-production
5 hops, cost=24.1,
CVE-2024-1234 on first edge
3
DIJK-2
Dijkstra
internet →
ns-kube-system
5 hops, cost=32.0, via sa-default
→ cluster-admin
2
DIJK-3*
Dijkstra
no-path-src →
no-path-dst
'No path found' message, exit 0
2
DFS-1
Cycle Detection
Full mock graph
1 cycle: [svc-service-a,
svc-service-b]
3
DFS-2*
Cycle Detection
Hidden 3-cycle graph
Exactly 3 cycles, no duplicates
3
CNA-1
Critical Node
Full mock graph
web-frontend, 32/46 paths
eliminated
5
CNA-2*
Critical Node
Hidden graph
Correct node, correct count
5
* Hidden test cases not present in mock-cluster-graph.json. Tested separately by judges.

Penalties & Disqualification Criteria
Condition
 Penalty
 
Tool crashes or raises unhandled exception on mock data
 -5 marks
 
Tool mutates the input cluster-graph.json file
 -3 marks
 
Algorithm output hardcoded to match mock data (not computed)
Disqualification of that
deliverable (0 marks for
section)
Runtime exceeds 5 minutes on mock-cluster-graph.json (40 nodes)
 -5 marks
 
Plagiarism or use of a pre-existing K8s security scanner as the submission
Full disqualification
Submission does not run on Python 3.10+ / Go 1.21+ without modification
 -5 marks
 
This rubric is a synthetic reference document generated to support hackathon preparation. The official scoring rubric is distributed
by the hackathon organizers. Expected outputs are derived from mock-cluster-graph.json using the reference implementation.

```

## backend\checklist\sample-output.txt

```
══════════════════════════════════════════════════════════════════
  KILL CHAIN REPORT  —  2026-04-03 02:25:35
  Cluster : mock-prod-cluster
  Nodes   : 41  |  Edges: 48
══════════════════════════════════════════════════════════════════

[ SECTION 1 — ATTACK PATH DETECTION (Dijkstra) ]
  ⚠  18 attack path(s) detected

  Path #1  |  3 hops  |  Risk Score: 9.5  [MEDIUM]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[reads]-->  db-url-config (ConfigMap)
  db-url-config (ConfigMap)  --[exposes-endpoint]-->  analytics-db (Database)

  Path #2  |  4 hops  |  Risk Score: 11.5  [HIGH]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  loadbalancer-svc (Service)
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[reads]-->  db-url-config (ConfigMap)
  db-url-config (ConfigMap)  --[exposes-endpoint]-->  analytics-db (Database)

  Path #3  |  3 hops  |  Risk Score: 14.0  [HIGH]
  ────────────────────────────────────────────────────────────
  cicd-bot (User)  --[impersonates]-->  sa-cicd (ServiceAccount)
  sa-cicd (ServiceAccount)  --[can-read]-->  cicd-deploy-token (Secret)
  cicd-deploy-token (Secret)  --[grants-access-to]-->  production-db (Database)

  Path #4  |  4 hops  |  Risk Score: 15.0  [HIGH]
  ────────────────────────────────────────────────────────────
  dev-2 (User)  --[can-exec]-->  log-aggregator (Pod)  [CVE-2024-9999, CVSS 6.5]
  log-aggregator (Pod)  --[uses]-->  sa-logger (ServiceAccount)
  sa-logger (ServiceAccount)  --[bound-to]-->  node-reader (Role)
  node-reader (Role)  --[can-read]-->  worker-node-1 (Node)

  Path #5  |  5 hops  |  Risk Score: 15.5  [HIGH]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[calls]-->  internal-api-svc (Service)
  internal-api-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[reads]-->  db-url-config (ConfigMap)
  db-url-config (ConfigMap)  --[exposes-endpoint]-->  analytics-db (Database)

  Path #6  |  4 hops  |  Risk Score: 17.0  [HIGH]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  background-worker (Pod)
  background-worker (Pod)  --[uses]-->  sa-worker (ServiceAccount)
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]

  Path #7  |  4 hops  |  Risk Score: 18.5  [HIGH]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[uses]-->  sa-worker (ServiceAccount)  [CVE-2023-4567, CVSS 7.2]
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]

  Path #8  |  5 hops  |  Risk Score: 20.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  dev-2 (User)  --[can-exec]-->  log-aggregator (Pod)  [CVE-2024-9999, CVSS 6.5]
  log-aggregator (Pod)  --[uses]-->  sa-logger (ServiceAccount)
  sa-logger (ServiceAccount)  --[bound-to]-->  node-reader (Role)
  node-reader (Role)  --[can-read]-->  worker-node-1 (Node)
  worker-node-1 (Node)  --[mounts]-->  data-pvc (PersistentVolume)

  Path #9  |  5 hops  |  Risk Score: 20.5  [CRITICAL]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  loadbalancer-svc (Service)
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[uses]-->  sa-worker (ServiceAccount)  [CVE-2023-4567, CVSS 7.2]
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]

  Path #10  |  5 hops  |  Risk Score: 22.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  background-worker (Pod)
  background-worker (Pod)  --[uses]-->  sa-worker (ServiceAccount)
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]
  worker-node-1 (Node)  --[mounts]-->  data-pvc (PersistentVolume)

  Path #11  |  5 hops  |  Risk Score: 22.1  [CRITICAL]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  web-frontend (Pod)
  web-frontend (Pod)  --[uses]-->  sa-webapp (ServiceAccount)
  sa-webapp (ServiceAccount)  --[bound-to]-->  secret-reader (Role)
  secret-reader (Role)  --[can-read]-->  db-credentials (Secret)
  db-credentials (Secret)  --[grants-access-to]-->  production-db (Database)

  Path #12  |  5 hops  |  Risk Score: 23.1  [CRITICAL]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[uses]-->  sa-webapp (ServiceAccount)
  sa-webapp (ServiceAccount)  --[bound-to]-->  secret-reader (Role)
  secret-reader (Role)  --[can-read]-->  db-credentials (Secret)
  db-credentials (Secret)  --[grants-access-to]-->  production-db (Database)

  Path #13  |  5 hops  |  Risk Score: 23.5  [CRITICAL]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[uses]-->  sa-worker (ServiceAccount)  [CVE-2023-4567, CVSS 7.2]
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]
  worker-node-1 (Node)  --[mounts]-->  data-pvc (PersistentVolume)

  Path #14  |  5 hops  |  Risk Score: 24.1  [CRITICAL]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[uses]-->  sa-webapp (ServiceAccount)
  sa-webapp (ServiceAccount)  --[bound-to]-->  secret-reader (Role)
  secret-reader (Role)  --[can-read]-->  db-credentials (Secret)
  db-credentials (Secret)  --[grants-access-to]-->  production-db (Database)

  Path #15  |  6 hops  |  Risk Score: 25.5  [CRITICAL]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  loadbalancer-svc (Service)
  loadbalancer-svc (Service)  --[routes-to]-->  api-server (Pod)
  api-server (Pod)  --[uses]-->  sa-worker (ServiceAccount)  [CVE-2023-4567, CVSS 7.2]
  sa-worker (ServiceAccount)  --[bound-to]-->  pod-exec (Role)
  pod-exec (Role)  --[can-exec-on]-->  worker-node-1 (Node)  [CVE-2024-3116, CVSS 9.0]
  worker-node-1 (Node)  --[mounts]-->  data-pvc (PersistentVolume)

  Path #16  |  5 hops  |  Risk Score: 31.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  loadbalancer-svc (Service)  --[routes-to]-->  web-frontend (Pod)
  web-frontend (Pod)  --[falls-back-to]-->  default (ServiceAccount)
  default (ServiceAccount)  --[bound-to]-->  cluster-admin (ClusterRole)
  cluster-admin (ClusterRole)  --[can-read]-->  admin-token (Secret)
  admin-token (Secret)  --[grants-access-to]-->  kube-system (Namespace)

  Path #17  |  5 hops  |  Risk Score: 32.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  internet (ExternalActor)  --[reaches]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[falls-back-to]-->  default (ServiceAccount)
  default (ServiceAccount)  --[bound-to]-->  cluster-admin (ClusterRole)
  cluster-admin (ClusterRole)  --[can-read]-->  admin-token (Secret)
  admin-token (Secret)  --[grants-access-to]-->  kube-system (Namespace)

  Path #18  |  5 hops  |  Risk Score: 33.0  [CRITICAL]
  ────────────────────────────────────────────────────────────
  dev-1 (User)  --[can-exec]-->  web-frontend (Pod)  [CVE-2024-1234, CVSS 8.1]
  web-frontend (Pod)  --[falls-back-to]-->  default (ServiceAccount)
  default (ServiceAccount)  --[bound-to]-->  cluster-admin (ClusterRole)
  cluster-admin (ClusterRole)  --[can-read]-->  admin-token (Secret)
  admin-token (Secret)  --[grants-access-to]-->  kube-system (Namespace)


[ SECTION 2 — BLAST RADIUS ANALYSIS (BFS, depth=3) ]

  Source: internet  →  13 reachable resource(s) within 3 hops
    Hop 1: loadbalancer-svc, web-frontend
    Hop 2: api-server, sa-webapp, default, internal-api-svc
    Hop 3: sa-worker, db-url-config, api-key, secret-reader, tls-cert, cluster-admin, db-credentials

  Source: dev-1  →  13 reachable resource(s) within 3 hops
    Hop 1: web-frontend, background-worker
    Hop 2: sa-webapp, default, internal-api-svc, sa-worker
    Hop 3: secret-reader, tls-cert, api-key, cluster-admin, db-credentials, api-server, pod-exec

  Source: dev-2  →  4 reachable resource(s) within 3 hops
    Hop 1: log-aggregator
    Hop 2: sa-logger, app-env-config
    Hop 3: node-reader

  Source: cicd-bot  →  4 reachable resource(s) within 3 hops
    Hop 1: sa-cicd
    Hop 2: deployer, cicd-deploy-token
    Hop 3: production-db

  Source: loadbalancer-svc  →  14 reachable resource(s) within 3 hops
    Hop 1: api-server, web-frontend
    Hop 2: sa-worker, db-url-config, api-key, sa-webapp, default, internal-api-svc
    Hop 3: pod-exec, analytics-db, secret-reader, tls-cert, cluster-admin, db-credentials

[ SECTION 3 — CIRCULAR PERMISSION DETECTION (DFS) ]
  ⚠  1 cycle(s) detected

  Cycle #1: service-a ↔ service-b ↔ service-a

[ SECTION 4 — CRITICAL NODE ANALYSIS ]
  Computing... (removing each node and recounting paths)

  Baseline attack paths : 46

  ★  RECOMMENDATION:
     Remove permission binding 'web-frontend' (Pod) to eliminate 32 of 46 attack paths.

  Top 5 highest-impact nodes to remove:
    web-frontend                   (Pod            )  -32 paths  ████████████████████
    api-server                     (Pod            )  -24 paths  ████████████████████
    internal-api-svc               (Service        )  -16 paths  ████████████████
    sa-worker                      (ServiceAccount )  -14 paths  ██████████████
    pod-exec                       (Role           )  -14 paths  ██████████████

══════════════════════════════════════════════════════════════════
  SUMMARY
  Attack paths found   : 18
  Circular permissions : 1
  Total blast-radius nodes exposed : 48
  Critical node to remove : web-frontend
══════════════════════════════════════════════════════════════════
```

## backend\checklist\scoring-rubric.pdf

*(Could not read file: 'utf-8' codec can't decode byte 0x93 in position 10: invalid start byte)*

## backend\snapshots\snapshot_20260402_044827_baseline.json

```json
{
  "snapshot_metadata": {
    "timestamp": "2026-04-02T04:48:27.421727+00:00",
    "label": "baseline",
    "node_count": 24,
    "edge_count": 28
  },
  "nodes": [
    {
      "id": "internet",
      "label": "Internet",
      "type": "internet",
      "namespace": "external",
      "risk_level": "entry-point",
      "metadata": {
        "description": "External internet traffic entry point",
        "icon": "globe"
      }
    },
    {
      "id": "ingress-nginx",
      "label": "Ingress Controller",
      "type": "ingress",
      "namespace": "ingress-nginx",
      "risk_level": "medium",
      "metadata": {
        "description": "NGINX Ingress Controller",
        "version": "1.9.4",
        "cves": [
          "CVE-2024-7646"
        ],
        "cvss_scores": [
          8.8
        ],
        "ports": [
          80,
          443
        ],
        "icon": "network"
      }
    },
    {
      "id": "tesla-dashboard-pod",
      "label": "Tesla Dashboard",
      "type": "pod",
      "namespace": "monitoring",
      "risk_level": "critical",
      "metadata": {
        "description": "Internet-facing Kubernetes Dashboard \u2014 misconfigured with no authentication",
        "image": "kubernetesui/dashboard:v2.7.0",
        "cves": [
          "CVE-2018-18264",
          "CVE-2023-49797"
        ],
        "cvss_scores": [
          7.5,
          8.1
        ],
        "ports": [
          8443
        ],
        "labels": {
          "app": "kubernetes-dashboard",
          "exposed": "true"
        },
        "icon": "monitor"
      }
    },
    {
      "id": "dashboard-sa",
      "label": "dashboard-admin-sa",
      "type": "serviceaccount",
      "namespace": "monitoring",
      "risk_level": "critical",
      "metadata": {
        "description": "ServiceAccount with cluster-admin privileges mounted to the dashboard pod",
        "automount_token": true,
        "icon": "user-check"
      }
    },
    {
      "id": "cluster-admin-binding",
      "label": "dashboard-cluster-admin",
      "type": "rolebinding",
      "namespace": "cluster-wide",
      "risk_level": "critical",
      "metadata": {
        "description": "ClusterRoleBinding granting cluster-admin to dashboard-admin-sa",
        "binding_type": "ClusterRoleBinding",
        "icon": "link"
      }
    },
    {
      "id": "cluster-admin-role",
      "label": "cluster-admin",
      "type": "clusterrole",
      "namespace": "cluster-wide",
      "risk_level": "critical",
      "metadata": {
        "description": "ClusterRole with full access to all resources: *.* (verbs: *)",
        "rules": [
          "*.*:*"
        ],
        "icon": "shield-alert"
      }
    },
    {
      "id": "aws-cred-secret",
      "label": "aws-credentials",
      "type": "secret",
      "namespace": "production",
      "risk_level": "crown-jewel",
      "metadata": {
        "description": "AWS IAM access keys stored as Kubernetes Secret",
        "secret_type": "Opaque",
        "keys": [
          "AWS_ACCESS_KEY_ID",
          "AWS_SECRET_ACCESS_KEY"
        ],
        "icon": "key"
      }
    },
    {
      "id": "prod-database",
      "label": "Production PostgreSQL",
      "type": "database",
      "namespace": "production",
      "risk_level": "crown-jewel",
      "metadata": {
        "description": "Production PostgreSQL database containing customer PII and financial data",
        "engine": "PostgreSQL 15.2",
        "data_classification": "PII + Financial",
        "records": "2.4M customer records",
        "icon": "database"
      }
    },
    {
      "id": "db-credentials-secret",
      "label": "db-credentials",
      "type": "secret",
      "namespace": "production",
      "risk_level": "crown-jewel",
      "metadata": {
        "description": "Database connection string and credentials",
        "secret_type": "Opaque",
        "keys": [
          "DB_HOST",
          "DB_USER",
          "DB_PASSWORD",
          "DB_NAME"
        ],
        "icon": "key"
      }
    },
    {
      "id": "api-server-pod",
      "label": "API Server Pod",
      "type": "pod",
      "namespace": "production",
      "risk_level": "high",
      "metadata": {
        "description": "Main application API server",
        "image": "company/api-server:3.1.2",
        "cves": [
          "CVE-2023-44487"
        ],
        "cvss_scores": [
          7.5
        ],
        "ports": [
          8080
        ],
        "labels": {
          "app": "api-server",
          "tier": "backend"
        },
        "icon": "server"
      }
    },
    {
      "id": "api-server-sa",
      "label": "api-server-sa",
      "type": "serviceaccount",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "ServiceAccount for the API server pod",
        "automount_token": true,
        "icon": "user"
      }
    },
    {
      "id": "api-role-binding",
      "label": "api-server-rb",
      "type": "rolebinding",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "RoleBinding for api-server to access production secrets",
        "binding_type": "RoleBinding",
        "icon": "link"
      }
    },
    {
      "id": "api-role",
      "label": "api-server-role",
      "type": "role",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "Role granting read access to specific secrets in production namespace",
        "rules": [
          "secrets:get,list (production)"
        ],
        "icon": "shield"
      }
    },
    {
      "id": "worker-pod-1",
      "label": "Worker Pod 1",
      "type": "pod",
      "namespace": "production",
      "risk_level": "low",
      "metadata": {
        "description": "Background job worker processing queue messages",
        "image": "company/worker:2.8.0",
        "cves": [],
        "cvss_scores": [],
        "ports": [
          9090
        ],
        "labels": {
          "app": "worker",
          "tier": "backend"
        },
        "icon": "cpu"
      }
    },
    {
      "id": "worker-pod-2",
      "label": "Worker Pod 2",
      "type": "pod",
      "namespace": "production",
      "risk_level": "low",
      "metadata": {
        "description": "Background job worker processing queue messages",
        "image": "company/worker:2.8.0",
        "cves": [],
        "cvss_scores": [],
        "ports": [
          9090
        ],
        "labels": {
          "app": "worker",
          "tier": "backend"
        },
        "icon": "cpu"
      }
    },
    {
      "id": "monitoring-pod",
      "label": "Prometheus",
      "type": "pod",
      "namespace": "monitoring",
      "risk_level": "medium",
      "metadata": {
        "description": "Prometheus monitoring stack",
        "image": "prom/prometheus:v2.48.0",
        "cves": [
          "CVE-2024-6837"
        ],
        "cvss_scores": [
          5.4
        ],
        "ports": [
          9090
        ],
        "labels": {
          "app": "prometheus"
        },
        "icon": "activity"
      }
    },
    {
      "id": "monitoring-sa",
      "label": "prometheus-sa",
      "type": "serviceaccount",
      "namespace": "monitoring",
      "risk_level": "low",
      "metadata": {
        "description": "ServiceAccount for Prometheus with read-only metrics access",
        "automount_token": true,
        "icon": "user"
      }
    },
    {
      "id": "monitoring-role-binding",
      "label": "prometheus-rb",
      "type": "rolebinding",
      "namespace": "monitoring",
      "risk_level": "low",
      "metadata": {
        "description": "ClusterRoleBinding for Prometheus metrics collection",
        "binding_type": "ClusterRoleBinding",
        "icon": "link"
      }
    },
    {
      "id": "monitoring-role",
      "label": "prometheus-reader",
      "type": "clusterrole",
      "namespace": "cluster-wide",
      "risk_level": "low",
      "metadata": {
        "description": "ClusterRole with read-only access to metrics endpoints",
        "rules": [
          "pods:get,list,watch",
          "nodes:get,list,watch",
          "metrics.k8s.io:get,list"
        ],
        "icon": "shield"
      }
    },
    {
      "id": "etcd-pod",
      "label": "etcd",
      "type": "pod",
      "namespace": "kube-system",
      "risk_level": "critical",
      "metadata": {
        "description": "etcd key-value store \u2014 backbone of the cluster",
        "image": "registry.k8s.io/etcd:3.5.10",
        "cves": [
          "CVE-2023-47108"
        ],
        "cvss_scores": [
          7.5
        ],
        "ports": [
          2379,
          2380
        ],
        "icon": "hard-drive"
      }
    },
    {
      "id": "kube-apiserver",
      "label": "kube-apiserver",
      "type": "pod",
      "namespace": "kube-system",
      "risk_level": "critical",
      "metadata": {
        "description": "Kubernetes API Server \u2014 control plane component",
        "image": "registry.k8s.io/kube-apiserver:v1.28.4",
        "cves": [],
        "cvss_scores": [],
        "ports": [
          6443
        ],
        "icon": "server"
      }
    },
    {
      "id": "configmap-app-config",
      "label": "app-config",
      "type": "configmap",
      "namespace": "production",
      "risk_level": "low",
      "metadata": {
        "description": "Application configuration (non-sensitive)",
        "keys": [
          "LOG_LEVEL",
          "FEATURE_FLAGS",
          "API_TIMEOUT"
        ],
        "icon": "file-text"
      }
    },
    {
      "id": "network-policy-default",
      "label": "default-deny",
      "type": "networkpolicy",
      "namespace": "production",
      "risk_level": "info",
      "metadata": {
        "description": "Default deny network policy (not enforced on monitoring namespace!)",
        "enforcement": "partial",
        "icon": "shield-off"
      }
    },
    {
      "id": "svc-api-loadbalancer",
      "label": "api-service (LB)",
      "type": "service",
      "namespace": "production",
      "risk_level": "medium",
      "metadata": {
        "description": "LoadBalancer service exposing the API server externally",
        "service_type": "LoadBalancer",
        "ports": [
          443
        ],
        "icon": "globe"
      }
    }
  ],
  "edges": [
    {
      "source": "internet",
      "target": "ingress-nginx",
      "relationship": "routes_to",
      "weight": 1.0,
      "metadata": {
        "description": "External traffic hits ingress controller",
        "protocol": "HTTPS"
      }
    },
    {
      "source": "ingress-nginx",
      "target": "tesla-dashboard-pod",
      "relationship": "forwards_to",
      "weight": 1.5,
      "metadata": {
        "description": "Ingress routes /dashboard to Tesla Dashboard pod (no auth!)",
        "protocol": "HTTPS",
        "auth": "none"
      }
    },
    {
      "source": "tesla-dashboard-pod",
      "target": "dashboard-sa",
      "relationship": "uses_service_account",
      "weight": 0.5,
      "metadata": {
        "description": "Dashboard pod auto-mounts privileged ServiceAccount token"
      }
    },
    {
      "source": "dashboard-sa",
      "target": "cluster-admin-binding",
      "relationship": "bound_by",
      "weight": 0.5,
      "metadata": {
        "description": "SA is bound to cluster-admin via ClusterRoleBinding"
      }
    },
    {
      "source": "cluster-admin-binding",
      "target": "cluster-admin-role",
      "relationship": "grants",
      "weight": 0.5,
      "metadata": {
        "description": "Binding grants cluster-admin ClusterRole"
      }
    },
    {
      "source": "cluster-admin-role",
      "target": "aws-cred-secret",
      "relationship": "can_access",
      "weight": 1.0,
      "metadata": {
        "description": "cluster-admin can read all secrets including AWS credentials"
      }
    },
    {
      "source": "cluster-admin-role",
      "target": "db-credentials-secret",
      "relationship": "can_access",
      "weight": 1.0,
      "metadata": {
        "description": "cluster-admin can read database credentials"
      }
    },
    {
      "source": "db-credentials-secret",
      "target": "prod-database",
      "relationship": "authenticates_to",
      "weight": 0.5,
      "metadata": {
        "description": "DB credentials used to connect to production database"
      }
    },
    {
      "source": "aws-cred-secret",
      "target": "prod-database",
      "relationship": "provides_access",
      "weight": 1.5,
      "metadata": {
        "description": "AWS credentials can be used to access RDS instance directly"
      }
    },
    {
      "source": "internet",
      "target": "svc-api-loadbalancer",
      "relationship": "routes_to",
      "weight": 2.0,
      "metadata": {
        "description": "External traffic to API LoadBalancer service",
        "protocol": "HTTPS"
      }
    },
    {
      "source": "svc-api-loadbalancer",
      "target": "api-server-pod",
      "relationship": "forwards_to",
      "weight": 2.0,
      "metadata": {
        "description": "LoadBalancer routes to API server pod",
        "protocol": "HTTPS",
        "auth": "JWT"
      }
    },
    {
      "source": "api-server-pod",
      "target": "api-server-sa",
      "relationship": "uses_service_account",
      "weight": 1.0,
      "metadata": {
        "description": "API server pod uses its service account"
      }
    },
    {
      "source": "api-server-sa",
      "target": "api-role-binding",
      "relationship": "bound_by",
      "weight": 1.0,
      "metadata": {
        "description": "SA bound via RoleBinding"
      }
    },
    {
      "source": "api-role-binding",
      "target": "api-role",
      "relationship": "grants",
      "weight": 1.0,
      "metadata": {
        "description": "Binding grants api-server-role"
      }
    },
    {
      "source": "api-role",
      "target": "db-credentials-secret",
      "relationship": "can_access",
      "weight": 2.0,
      "metadata": {
        "description": "Role grants read access to db-credentials secret"
      }
    },
    {
      "source": "api-server-pod",
      "target": "prod-database",
      "relationship": "connects_to",
      "weight": 1.5,
      "metadata": {
        "description": "API server connects to production database",
        "protocol": "TCP:5432"
      }
    },
    {
      "source": "api-server-pod",
      "target": "configmap-app-config",
      "relationship": "mounts",
      "weight": 3.0,
      "metadata": {
        "description": "API server mounts application config"
      }
    },
    {
      "source": "api-server-pod",
      "target": "worker-pod-1",
      "relationship": "sends_jobs_to",
      "weight": 2.5,
      "metadata": {
        "description": "API server dispatches background jobs",
        "protocol": "AMQP"
      }
    },
    {
      "source": "api-server-pod",
      "target": "worker-pod-2",
      "relationship": "sends_jobs_to",
      "weight": 2.5,
      "metadata": {
        "description": "API server dispatches background jobs",
        "protocol": "AMQP"
      }
    },
    {
      "source": "monitoring-pod",
      "target": "monitoring-sa",
      "relationship": "uses_service_account",
      "weight": 2.0,
      "metadata": {
        "description": "Prometheus uses its service account for API discovery"
      }
    },
    {
      "source": "monitoring-sa",
      "target": "monitoring-role-binding",
      "relationship": "bound_by",
      "weight": 2.0,
      "metadata": {
        "description": "SA bound via ClusterRoleBinding"
      }
    },
    {
      "source": "monitoring-role-binding",
      "target": "monitoring-role",
      "relationship": "grants",
      "weight": 2.0,
      "metadata": {
        "description": "Binding grants prometheus-reader ClusterRole"
      }
    },
    {
      "source": "monitoring-pod",
      "target": "api-server-pod",
      "relationship": "scrapes_metrics",
      "weight": 3.0,
      "metadata": {
        "description": "Prometheus scrapes metrics from API server",
        "protocol": "HTTP:8080/metrics"
      }
    },
    {
      "source": "monitoring-pod",
      "target": "worker-pod-1",
      "relationship": "scrapes_metrics",
      "weight": 3.0,
      "metadata": {
        "description": "Prometheus scrapes metrics from worker",
        "protocol": "HTTP:9090/metrics"
      }
    },
    {
      "source": "kube-apiserver",
      "target": "etcd-pod",
      "relationship": "reads_writes",
      "weight": 1.0,
      "metadata": {
        "description": "API server reads/writes cluster state to etcd",
        "protocol": "gRPC:2379"
      }
    },
    {
      "source": "cluster-admin-role",
      "target": "kube-apiserver",
      "relationship": "full_access",
      "weight": 0.5,
      "metadata": {
        "description": "cluster-admin has full access to the Kubernetes API"
      }
    },
    {
      "source": "tesla-dashboard-pod",
      "target": "monitoring-pod",
      "relationship": "network_access",
      "weight": 2.5,
      "metadata": {
        "description": "Dashboard can reach monitoring namespace (no NetworkPolicy!)"
      }
    },
    {
      "source": "monitoring-pod",
      "target": "tesla-dashboard-pod",
      "relationship": "network_access",
      "weight": 2.5,
      "metadata": {
        "description": "Bidirectional access in monitoring namespace"
      }
    }
  ],
  "metadata": {
    "cluster_name": "prod-eks-cluster-01",
    "scan_timestamp": "2026-03-30T12:00:00Z",
    "scenario": "Tesla Breach Simulation",
    "description": "An internet-facing Kubernetes dashboard with excessive RBAC permissions leads to credential theft and database compromise."
  }
}
```

## frontend\.gitignore

```
# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
```

## frontend\eslint.config.js

```javascript
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
  },
])
```

## frontend\index.html

```html
<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="KubeInsights — Kubernetes Security Analysis Dashboard. Visualize attack paths, analyze blast radius, and identify critical nodes in your K8s cluster." />
    <title>KubeInsights - Kubernetes Attack Path Visualizer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

## frontend\package.json

```json
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
  "dependencies": {
    "@radix-ui/react-dialog": "^1.1.15",
    "@radix-ui/react-dropdown-menu": "^2.1.16",
    "@radix-ui/react-scroll-area": "^1.2.10",
    "@radix-ui/react-select": "^2.2.6",
    "@radix-ui/react-separator": "^1.1.8",
    "@radix-ui/react-slider": "^1.3.6",
    "@radix-ui/react-slot": "^1.2.4",
    "@radix-ui/react-switch": "^1.2.6",
    "@radix-ui/react-tabs": "^1.1.13",
    "@radix-ui/react-tooltip": "^1.2.8",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "framer-motion": "^12.38.0",
    "html2pdf.js": "^0.14.0",
    "lucide-react": "^1.7.0",
    "react": "^19.2.4",
    "react-dom": "^19.2.4",
    "react-force-graph-2d": "^1.29.1",
    "tailwind-merge": "^3.5.0"
  },
  "devDependencies": {
    "@eslint/js": "^9.39.4",
    "@tailwindcss/vite": "^4.2.2",
    "@types/node": "^24.12.0",
    "@types/react": "^19.2.14",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^6.0.1",
    "eslint": "^9.39.4",
    "eslint-plugin-react-hooks": "^7.0.1",
    "eslint-plugin-react-refresh": "^0.5.2",
    "globals": "^17.4.0",
    "tailwindcss": "^4.2.2",
    "typescript": "~5.9.3",
    "typescript-eslint": "^8.57.0",
    "vite": "^8.0.1"
  }
}
```

## frontend\README.md

```markdown
# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
```

## frontend\tsconfig.app.json

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "ES2023",
    "useDefineForClassFields": true,
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "types": ["vite/client"],
    "skipLibCheck": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    },

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["src"]
}
```

## frontend\tsconfig.json

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

## frontend\tsconfig.node.json

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "ES2023",
    "lib": ["ES2023"],
    "module": "ESNext",
    "types": ["node"],
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "erasableSyntaxOnly": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["vite.config.ts"]
}
```

## frontend\vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

## frontend\src\App.tsx

```typescript
import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, Moon, Sun, AlertTriangle, Activity, Database, Server,
  Lock, Wifi, WifiOff, Loader2, BarChart3, GitBranch, Search
} from 'lucide-react';
import GraphCanvas from './components/GraphCanvas';
import SecuritySidebar from './components/SecuritySidebar';
import ControlPanel from './components/ControlPanel';
import KillChainReport from './components/KillChainReport';
import { api } from './lib/api';
import type {
  GraphNode, GraphEdge, GraphData, HighlightState,
  BlastRadiusResult, ShortestPathResult, CycleResult, CriticalNodeResult,
  TopCriticalPathResult, TopCriticalPath,
} from './lib/types';

function App() {
  // ── Theme ────────────────────────────────
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('kubepathaudit-theme');
    return saved ? saved === 'dark' : true;
  });
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('kubepathaudit-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  // ── Graph State ──────────────────────────
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiLoading, setApiLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

  // ── UI State ─────────────────────────────
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);
  const [selectedCriticalPath, setSelectedCriticalPath] = useState<TopCriticalPath | null>(null);
  const [highlight, setHighlight] = useState<HighlightState>({
    nodes: new Set(), edges: new Set(), path: [], mode: 'none',
  });
  const [showKillChain, setShowKillChain] = useState(false);

  // ── Analysis Results ─────────────────────
  const [blastResult, setBlastResult] = useState<BlastRadiusResult | null>(null);
  const [pathResult, setPathResult] = useState<ShortestPathResult | null>(null);
  const [cycleResult, setCycleResult] = useState<CycleResult | null>(null);
  const [criticalResult, setCriticalResult] = useState<CriticalNodeResult | null>(null);
  const [topCriticalResult, setTopCriticalResult] = useState<TopCriticalPathResult | null>(null);

  // ── Graph container sizing ───────────────
  const graphContainerRef = useRef<HTMLDivElement>(null);
  // ── Load Graph ───────────────────────────
  const loadGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getGraph();
      setGraphData(data);
      setNodes(data.nodes);
      setLinks(data.links);
      setConnected(true);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend');
      setConnected(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  // ── Auto-analyze critical paths on graph load ─
  useEffect(() => {
    if (graphData && !topCriticalResult) {
      // Auto-analyze with a default count to discover total paths
      (async () => {
        try {
          const result = await api.topCriticalPaths(3);
          setTopCriticalResult(result);
        } catch (err) {
          // Silent fail - user can still manually trigger analysis
        }
      })();
    }
  }, [graphData, topCriticalResult]);

  // ── Flash status ─────────────────────────
  const flash = (text: string, type: 'success' | 'error' | 'info') => {
    setStatusMessage({ text, type });
    setTimeout(() => setStatusMessage(null), 4000);
  };

  // ── Clear Highlights ─────────────────────
  const clearHighlight = () => {
    setHighlight({ nodes: new Set(), edges: new Set(), path: [], mode: 'none' });
    setBlastResult(null);
    setPathResult(null);
    setCycleResult(null);
    setCriticalResult(null);
    setSelectedEdge(null);
    setTopCriticalResult(null);
    setSelectedCriticalPath(null);
  };

  // ── Algorithm Handlers ───────────────────
  const handleBlastRadius = async (source: string, hops: number) => {
    setApiLoading(true);
    try {
      const result = await api.blastRadius(source, hops);
      setBlastResult(result);

      const nodeIds = new Set(result.affected_nodes.map(n => n.id));
      const edgeIds = new Set(result.affected_edges.map(e => `${e.source}->${e.target}`));
      setHighlight({ nodes: nodeIds, edges: edgeIds, path: [], mode: 'blast-radius' });
      flash(`Blast radius: ${result.total_affected} nodes in danger zone`, result.risk_summary === 'CRITICAL' ? 'error' : 'info');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleShortestPath = async (source: string, target: string) => {
    setApiLoading(true);
    try {
      const result = await api.shortestPath(source, target);
      setPathResult(result);

      if (result.path_exists) {
        const nodeIds = new Set(result.path);
        const edgeIds = new Set<string>();
        for (let i = 0; i < result.path.length - 1; i++) {
          edgeIds.add(`${result.path[i]}->${result.path[i + 1]}`);
        }
        setHighlight({ nodes: nodeIds, edges: edgeIds, path: result.path, mode: 'shortest-path' });
        flash(`${result.difficulty} attack path found: ${result.hop_count} hops, weight ${result.total_weight}`,
          result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY' ? 'error' : 'info');
      } else {
        clearHighlight();
        flash('No attack path exists between these nodes ✓', 'success');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleDetectCycles = async () => {
    setApiLoading(true);
    try {
      const result = await api.detectCycles();
      setCycleResult(result);

      if (result.has_cycles) {
        const nodeIds = new Set<string>();
        const edgeIds = new Set<string>();
        result.cycles.forEach(c => {
          c.cycle.forEach(n => nodeIds.add(n));
          for (let i = 0; i < c.cycle.length; i++) {
            const next = c.cycle[(i + 1) % c.cycle.length];
            edgeIds.add(`${c.cycle[i]}->${next}`);
          }
        });
        setHighlight({ nodes: nodeIds, edges: edgeIds, path: [], mode: 'cycles' });
        flash(`${result.total_cycles} circular permission loop(s) detected`, 'error');
      } else {
        clearHighlight();
        flash('No circular permission loops found ✓', 'success');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleCriticalNode = async () => {
    setApiLoading(true);
    try {
      const result = await api.criticalNode();
      setCriticalResult(result);
      setTopCriticalResult(null);

      if (result.critical_node) {
        const nodeIds = new Set([result.critical_node.node_id]);
        setHighlight({ nodes: nodeIds, edges: new Set(), path: [], mode: 'critical-node' });
        flash(`Critical node: ${result.critical_node.label} (${result.critical_node.impact_percentage}% impact)`, 'info');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleTopCriticalPaths = async (count: number) => {
    setApiLoading(true);
    try {
      const result = await api.topCriticalPaths(count);
      setTopCriticalResult(result);
      setCriticalResult(null);
      setBlastResult(null);
      setPathResult(null);
      setCycleResult(null);

      if (result?.top_critical_paths?.[0]) {
        const path = result.top_critical_paths[0].path;
        const nodeIds = new Set(path);
        const edgeIds = new Set<string>();
        for (let i = 0; i < path.length - 1; i++) {
          edgeIds.add(`${path[i]}->${path[i + 1]}`);
        }
        setHighlight({ nodes: nodeIds, edges: edgeIds, path, mode: 'top-critical-paths' });
        flash(`Top critical path loaded: ${result.top_critical_paths[0].difficulty} (${result.top_critical_paths[0].total_weight} weight)`, 'info');
      } else {
        setHighlight({ nodes: new Set(), edges: new Set(), path: [], mode: 'none' });
        flash('No critical attack paths found', 'success');
      }
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleSelectCriticalPath = (path: TopCriticalPath) => {
    setSelectedCriticalPath(path);
    setSelectedNode(null);

    // Highlight the path on the graph
    const nodeIds = new Set(path.path);
    const edgeIds = new Set<string>();
    for (let i = 0; i < path.path.length - 1; i++) {
      edgeIds.add(`${path.path[i]}->${path.path[i + 1]}`);
    }
    setHighlight({ nodes: nodeIds, edges: edgeIds, path: path.path, mode: 'top-critical-paths' });
    flash(`Critical path selected: ${path.rank} (${path.difficulty})`, 'info');
  };

  const handleRemediate = async (nodeId: string) => {
    setApiLoading(true);
    try {
      const result = await api.remediate(nodeId);
      const newGraph = result.updated_graph;
      setGraphData(newGraph);
      setNodes(newGraph.nodes);
      setLinks(newGraph.links);
      clearHighlight();
      setSelectedNode(null);
      setSelectedEdge(null);
      setTopCriticalResult(null);
      setSelectedCriticalPath(null);
      setCriticalResult(null);
      flash(result.message, 'success');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleReset = async () => {
    setApiLoading(true);
    try {
      const result = await api.reset();
      setGraphData(result.graph);
      setNodes(result.graph.nodes);
      setLinks(result.graph.links);
      clearHighlight();
      setSelectedNode(null);
      setSelectedEdge(null);
      setSelectedCriticalPath(null);
      flash('Graph reset to original state', 'success');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleUpload = async (file: File) => {
    setApiLoading(true);
    try {
      const result = await api.uploadGraph(file);
      setGraphData(result.graph);
      setNodes(result.graph.nodes);
      setLinks(result.graph.links);
      clearHighlight();
      setSelectedNode(null);
      setSelectedNode(null);
      setSelectedEdge(null);
      setTopCriticalResult(null);
      setSelectedCriticalPath(null);
      flash(result.message, 'success');
    } catch (err: any) {
      flash(err.message, 'error');
    }
    setApiLoading(false);
  };

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
    setSelectedEdge(null);
  };

  const handleLinkClick = (link: GraphEdge) => {
    setSelectedEdge(link);
    setSelectedNode(null);
  };

  const handleFindPathToNode = (targetId: string) => {
    handleShortestPath('internet', targetId);
  };

  // ── Loading Screen ───────────────────────
  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-[#0a0f1e]' : 'bg-slate-50'}`}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center space-y-4"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          >
            <Shield className={`w-16 h-16 mx-auto ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
          </motion.div>
          <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>KubePathAudit</h1>
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Connecting to analysis engine...</p>
          <Loader2 className={`w-5 h-5 mx-auto animate-spin ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
        </motion.div>
      </div>
    );
  }

  // ── Error Screen ─────────────────────────
  if (error && !graphData) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDark ? 'bg-[#0a0f1e]' : 'bg-slate-50'}`}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4 max-w-md px-6"
        >
          <WifiOff className="w-16 h-16 mx-auto text-red-400" />
          <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Connection Failed</h1>
          <p className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{error}</p>
          <div className={`text-xs p-4 rounded-xl ${isDark ? 'bg-slate-800/50 text-slate-400' : 'bg-slate-100 text-slate-500'}`}>
            <p className="font-mono mb-2">Make sure the backend is running:</p>
            <code className={`block p-2 rounded ${isDark ? 'bg-slate-900' : 'bg-white'}`}>
              cd backend && uvicorn main:app --reload
            </code>
          </div>
          <button
            onClick={loadGraph}
            className="px-6 py-2.5 rounded-xl text-sm font-medium bg-gradient-to-r from-blue-600 to-cyan-600 text-white
              hover:from-blue-500 hover:to-cyan-500 transition-all hover:shadow-lg hover:shadow-blue-500/20"
          >
            Retry Connection
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-[#0a0f1e]' : 'bg-slate-50'}`}>

      {/* ─── Header ─────────────────────────── */}
      <header className={`shrink-0 flex items-center justify-between px-5 py-3 border-b z-40
        ${isDark ? 'bg-slate-900/80 border-slate-700/50' : 'bg-white/80 border-slate-200'}
        backdrop-blur-xl`}>
        <div className="flex items-center gap-3">
          <motion.div
            whileHover={{ rotate: 15, scale: 1.1 }}
            className="p-2 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 shadow-lg shadow-blue-500/20"
          >
            <Shield className="w-5 h-5 text-white" />
          </motion.div>
          <div>
            <h1 className={`text-lg font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
              KubeInsights
            </h1>
            <p className={`text-[11px] ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              Kubernetes Security Analysis Dashboard
            </p>
          </div>
        </div>

        {/* Center - Stats */}
        {graphData && (
          <div className="hidden md:flex items-center gap-6">
            <div className="flex items-center gap-2 px-2 py-1 rounded-lg">
              <Server className={`w-3.5 h-3.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
              <span className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                {graphData.stats.total_nodes} Nodes
              </span>
            </div>
            <div className="flex items-center gap-2 px-2 py-1 rounded-lg">
              <GitBranch className={`w-3.5 h-3.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`} />
              <span className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                {graphData.stats.total_edges} Edges
              </span>
            </div>
            <button 
              onClick={() => {
                const criticalNodes = new Set(nodes.filter(n => n.risk_level === 'critical').map(n => n.id));
                setHighlight({
                  nodes: criticalNodes,
                  edges: new Set(),
                  path: [],
                  mode: 'group-critical'
                });
                setSelectedNode(null); // Clear active sidebar to focus on the group
              }}
              className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-red-500/10 cursor-pointer transition-colors"
              title="Highlight all Critical Risk nodes"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
              <span className="text-xs font-medium text-red-400">
                {graphData.stats.critical_nodes} Critical
              </span>
            </button>
            <button 
              onClick={() => {
                const jewelNodes = new Set(nodes.filter(n => n.risk_level === 'crown-jewel').map(n => n.id));
                setHighlight({
                  nodes: jewelNodes,
                  edges: new Set(),
                  path: [],
                  mode: 'group-crown-jewel'
                });
                setSelectedNode(null); // Clear active sidebar to focus on the group
              }}
              className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-yellow-500/10 cursor-pointer transition-colors"
              title="Highlight all Crown Jewel nodes"
            >
              <Database className="w-3.5 h-3.5 text-yellow-400" />
              <span className="text-xs font-medium text-yellow-400">
                {graphData.stats.crown_jewels} Crown Jewels
              </span>
            </button>
          </div>
        )}

        {/* Right */}
        <div className="flex items-center gap-3">
          {/* Connection status */}
          <div className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full status-dot ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
              {connected ? 'Connected' : 'Offline'}
            </span>
          </div>

          {/* Cluster name */}
          {graphData?.metadata?.cluster_name && (
            <span className={`text-xs px-2.5 py-1 rounded-full font-mono
              ${isDark ? 'bg-slate-800 text-cyan-400 border border-slate-700' : 'bg-slate-100 text-blue-600 border border-slate-200'}`}>
              {graphData.metadata.cluster_name}
            </span>
          )}

          {/* Theme toggle */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsDark(!isDark)}
            className={`p-2 rounded-xl transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-yellow-400' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}`}
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </motion.button>
        </div>
      </header>

      {/* ─── Status Message ─────────────────── */}
      <AnimatePresence>
        {statusMessage && (
          <motion.div
            initial={{ y: -40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -40, opacity: 0 }}
            className={`absolute top-[60px] left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl shadow-lg text-xs font-medium flex items-center gap-2
              ${statusMessage.type === 'error' ? 'bg-red-500/90 text-white' :
                statusMessage.type === 'success' ? 'bg-green-500/90 text-white' :
                  'bg-blue-500/90 text-white'}
              backdrop-blur-sm`}
          >
            {statusMessage.type === 'error' && <AlertTriangle className="w-3.5 h-3.5" />}
            {statusMessage.type === 'success' && <Lock className="w-3.5 h-3.5" />}
            {statusMessage.type === 'info' && <Activity className="w-3.5 h-3.5" />}
            {statusMessage.text}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ─── Main Layout ────────────────────── */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Panel: Controls */}
        <div className={`shrink-0 w-[320px] border-r overflow-hidden flex flex-col
          ${isDark ? 'bg-slate-900/50 border-slate-700/50' : 'bg-white border-slate-200'}`}>
          {/* Scenario Badge */}
          {graphData?.metadata?.scenario && (
            <div className={`mx-4 mt-3 px-3 py-2 rounded-xl text-xs border animate-border-pulse
              ${isDark ? 'bg-red-950/30 border-red-900/40 text-red-300' : 'bg-red-50 border-red-200 text-red-700'}`}>
              <span className="font-semibold">🎯 Active Scenario:</span> {graphData.metadata.scenario}
            </div>
          )}

          {/* Node Search Map */}
          <div className="px-4 mt-4">
            <div className="relative group">
              <Search className={`w-4 h-4 absolute left-3 top-2.5 transition-colors ${isDark ? 'text-slate-500 group-focus-within:text-blue-400' : 'text-slate-400 group-focus-within:text-blue-500'}`} />
              <input
                type="text"
                list="node-search-list"
                placeholder="Search to locate node..."
                onChange={(e) => {
                  const val = e.target.value;
                  if (!val) return;
                  const found = nodes.find(n => n.id === val || n.label === val);
                  if (found) {
                    handleNodeClick(found);
                    setTimeout(() => { e.target.value = ''; }, 100);
                  }
                }}
                className={`w-full pl-9 pr-3 py-2 text-sm rounded-xl border outline-none transition-all
                  ${isDark 
                    ? 'bg-slate-800/40 border-slate-700/50 text-slate-200 focus:bg-slate-800/80 focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 placeholder:text-slate-500' 
                    : 'bg-white border-slate-200 text-slate-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder:text-slate-400'}`}
              />
              <datalist id="node-search-list">
                {nodes.map(n => (
                  <option key={n.id} value={n.label || n.id} />
                ))}
              </datalist>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto">
            <ControlPanel
              nodes={nodes}
              onBlastRadius={handleBlastRadius}
              onShortestPath={handleShortestPath}
              onDetectCycles={handleDetectCycles}
              onCriticalNode={handleCriticalNode}
              onTopCriticalPaths={handleTopCriticalPaths}
              onSelectCriticalPath={handleSelectCriticalPath}
              onRemediate={handleRemediate}
              onReset={handleReset}
              onUpload={handleUpload}
              onShowKillChain={() => setShowKillChain(true)}
              criticalNodeResult={criticalResult}
              topCriticalResult={topCriticalResult}
              cycleResult={cycleResult}
              blastResult={blastResult}
              pathResult={pathResult}
              loading={apiLoading}
              isDark={isDark}
              selectedNode={selectedNode}
            />
          </div>
        </div>

        {/* Center: Graph Canvas */}
        <div
          ref={graphContainerRef}
          className={`flex-1 relative overflow-hidden cyber-grid ${isDark ? '' : ''}`}
        >
          {/* Clear highlight button */}
          <AnimatePresence>
            {highlight.mode !== 'none' && (
              <motion.button
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: -20, opacity: 0 }}
                onClick={clearHighlight}
                className={`absolute top-3 left-3 z-20 px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5 transition-all
                  ${isDark ? 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 border border-slate-700' : 'bg-white/80 text-slate-600 hover:bg-white border border-slate-200'}
                  backdrop-blur-sm`}
              >
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                {highlight.mode === 'blast-radius' && 'Blast Radius Active'}
                {highlight.mode === 'shortest-path' && 'Attack Path Active'}
                {highlight.mode === 'cycles' && 'Cycles Highlighted'}
                {highlight.mode === 'critical-node' && 'Critical Node Highlighted'}
                <span className="ml-1">✕</span>
              </motion.button>
            )}
          </AnimatePresence>

          {/* Legend */}
          <div className={`absolute bottom-3 left-3 z-20 p-3 rounded-xl text-[10px] space-y-1.5
            ${isDark ? 'bg-slate-900/80 border border-slate-700/50' : 'bg-white/80 border border-slate-200'}
            backdrop-blur-sm`}>
            <button
              onClick={() => {
                const filtered = new Set(nodes.filter(n => n.type === 'internet' || n.risk_level === 'entry-point').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-entry-point' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-green-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Internet / Entry Point</span>
            </button>
            <button
              onClick={() => {
                const filtered = new Set(nodes.filter(n => n.risk_level === 'critical').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-critical' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-red-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Critical Risk</span>
            </button>
            <button
              onClick={() => {
                const filtered = new Set(nodes.filter(n => n.risk_level === 'crown-jewel').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-crown-jewel' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-yellow-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Crown Jewel</span>
            </button>
            <button
              onClick={() => {
                // Info or medium risks, or typical pods
                const filtered = new Set(nodes.filter(n => n.risk_level === 'info' || n.risk_level === 'medium' || n.type === 'pod' || n.type === 'service').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-standard' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-indigo-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Standard Entity</span>
            </button>
            <button
              onClick={() => {
                const filtered = new Set(nodes.filter(n => n.risk_level === 'low').map(n => n.id));
                setHighlight({ nodes: filtered, edges: new Set(), path: [], mode: 'group-low' });
                setSelectedNode(null);
              }}
              className="flex items-center gap-2 w-full hover:bg-slate-500/10 px-2 py-1 -mx-2 rounded transition-colors text-left"
            >
              <span className="w-3 h-3 rounded-full bg-slate-500 shrink-0" />
              <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Low Risk / Utility</span>
            </button>
          </div>

          <GraphCanvas
            nodes={nodes}
            links={links}
            highlight={highlight}
            onNodeClick={handleNodeClick}
            onLinkClick={handleLinkClick}
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
            isDark={isDark}
          />

          {/* Security Sidebar (overlays right side of graph) */}
          <SecuritySidebar
            node={selectedNode}
            edge={selectedEdge}
            criticalPath={selectedCriticalPath}
            onClose={() => {
              setSelectedNode(null);
              setSelectedEdge(null);
              setSelectedCriticalPath(null);
            }}
            onBlastRadius={(nodeId) => handleBlastRadius(nodeId, 3)}
            onFindPath={handleFindPathToNode}
            isDark={isDark}
          />
        </div>
      </div>

      {/* ─── Kill Chain Report Modal ────────── */}
      <KillChainReport
        result={pathResult}
        isOpen={showKillChain}
        onClose={() => setShowKillChain(false)}
        isDark={isDark}
      />
    </div>
  );
}

export default App;
```

## frontend\src\index.css

```css
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));

@theme {
  --color-border: hsl(220 13% 91%);
  --color-input: hsl(220 13% 91%);
  --color-ring: hsl(224 76% 48%);
  --color-background: hsl(0 0% 100%);
  --color-foreground: hsl(224 71% 4%);
  --color-primary: hsl(224 76% 48%);
  --color-primary-foreground: hsl(0 0% 100%);
  --color-secondary: hsl(220 14% 96%);
  --color-secondary-foreground: hsl(224 71% 4%);
  --color-destructive: hsl(0 84% 60%);
  --color-destructive-foreground: hsl(0 0% 100%);
  --color-muted: hsl(220 14% 96%);
  --color-muted-foreground: hsl(220 9% 46%);
  --color-accent: hsl(220 14% 96%);
  --color-accent-foreground: hsl(224 71% 4%);
  --color-popover: hsl(0 0% 100%);
  --color-popover-foreground: hsl(224 71% 4%);
  --color-card: hsl(0 0% 100%);
  --color-card-foreground: hsl(224 71% 4%);
  --color-sidebar: hsl(0 0% 98%);
  --color-sidebar-foreground: hsl(240 5% 26%);
  --color-chart-1: hsl(12 76% 61%);
  --color-chart-2: hsl(173 58% 39%);
  --color-chart-3: hsl(197 37% 24%);
  --color-chart-4: hsl(43 74% 66%);
  --color-chart-5: hsl(27 87% 67%);
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;

  --color-cyber-red: hsl(0 90% 55%);
  --color-cyber-gold: hsl(45 100% 50%);
  --color-cyber-blue: hsl(210 100% 60%);
  --color-cyber-green: hsl(145 80% 45%);
  --color-cyber-purple: hsl(270 80% 60%);
  --color-cyber-cyan: hsl(185 100% 50%);
  --color-cyber-orange: hsl(25 100% 55%);
}

.dark {
  --color-border: hsl(215 20% 17%);
  --color-input: hsl(215 20% 17%);
  --color-ring: hsl(216 90% 58%);
  --color-background: hsl(222 47% 6%);
  --color-foreground: hsl(210 40% 98%);
  --color-primary: hsl(216 90% 58%);
  --color-primary-foreground: hsl(0 0% 100%);
  --color-secondary: hsl(215 20% 12%);
  --color-secondary-foreground: hsl(210 40% 98%);
  --color-destructive: hsl(0 84% 60%);
  --color-destructive-foreground: hsl(0 0% 100%);
  --color-muted: hsl(215 20% 12%);
  --color-muted-foreground: hsl(215 16% 57%);
  --color-accent: hsl(215 20% 15%);
  --color-accent-foreground: hsl(210 40% 98%);
  --color-popover: hsl(222 47% 8%);
  --color-popover-foreground: hsl(210 40% 98%);
  --color-card: hsl(222 47% 8%);
  --color-card-foreground: hsl(210 40% 98%);
  --color-sidebar: hsl(222 47% 7%);
  --color-sidebar-foreground: hsl(215 16% 70%);
}

/* ─── Base Styles ───────────────────────────── */
@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground antialiased;
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  }
}

/* ─── Scrollbar Styles ──────────────────────── */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: hsl(215 20% 30%);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: hsl(215 20% 40%);
}

/* ─── Cyber Glow Effects ────────────────────── */
.glow-blue {
  box-shadow: 0 0 15px hsl(216 90% 58% / 0.3), 0 0 45px hsl(216 90% 58% / 0.1);
}

.glow-red {
  box-shadow: 0 0 15px hsl(0 90% 55% / 0.3), 0 0 45px hsl(0 90% 55% / 0.1);
}

.glow-gold {
  box-shadow: 0 0 15px hsl(45 100% 50% / 0.3), 0 0 45px hsl(45 100% 50% / 0.1);
}

.glow-green {
  box-shadow: 0 0 15px hsl(145 80% 45% / 0.3), 0 0 45px hsl(145 80% 45% / 0.1);
}

.glow-cyan {
  box-shadow: 0 0 15px hsl(185 100% 50% / 0.3), 0 0 45px hsl(185 100% 50% / 0.1);
}

/* ─── Pulse Animation ───────────────────────── */
@keyframes pulse-glow {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }
}

.animate-pulse-glow {
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes scan-line {
  0% {
    transform: translateY(-100%);
  }

  100% {
    transform: translateY(100vh);
  }
}

.scan-line {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, hsl(216 90% 58% / 0.4), transparent);
  animation: scan-line 4s linear infinite;
  pointer-events: none;
  z-index: 9999;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out forwards;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }

  100% {
    background-position: 200% 0;
  }
}

.animate-shimmer {
  background: linear-gradient(90deg, transparent 0%, hsl(216 90% 58% / 0.08) 50%, transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes border-pulse {

  0%,
  100% {
    border-color: hsl(216 90% 58% / 0.3);
  }

  50% {
    border-color: hsl(216 90% 58% / 0.7);
  }
}

.animate-border-pulse {
  animation: border-pulse 2s ease-in-out infinite;
}

/* ─── Glassmorphism ─────────────────────────── */
.glass {
  background: hsl(222 47% 8% / 0.6);
  backdrop-filter: blur(16px);
  border: 1px solid hsl(215 20% 17% / 0.5);
}

:where(:not(.dark)) .glass {
  background: hsl(0 0% 100% / 0.7);
  border: 1px solid hsl(220 13% 91% / 0.8);
}

/* ─── Grid Background ──────────────────────── */
.cyber-grid {
  background-image:
    linear-gradient(hsl(216 90% 58% / 0.03) 1px, transparent 1px),
    linear-gradient(90deg, hsl(216 90% 58% / 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
}

:where(:not(.dark)) .cyber-grid {
  background-image:
    linear-gradient(hsl(224 76% 48% / 0.05) 1px, transparent 1px),
    linear-gradient(90deg, hsl(224 76% 48% / 0.05) 1px, transparent 1px);
}

/* ─── Graph Canvas ──────────────────────────── */
.graph-container {
  width: 100%;
  height: 100%;
}
.graph-container canvas {
  display: block;
  border-radius: 0.75rem;
}


/* ─── Kill chain step connector ─────────────── */
.kill-chain-step::after {
  content: '';
  position: absolute;
  left: 1.25rem;
  bottom: -1.5rem;
  width: 2px;
  height: 1.5rem;
  background: linear-gradient(to bottom, hsl(0 90% 55%), transparent);
}

.kill-chain-step:last-child::after {
  display: none;
}

/* ─── Status dot animation ──────────────────── */
@keyframes dot-blink {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.3;
  }
}

.status-dot {
  animation: dot-blink 1.5s ease-in-out infinite;
}

/* ─── Tooltip ───────────────────────────────── */
.cyber-tooltip {
  background: hsl(222 47% 10%);
  color: hsl(210 40% 98%);
  border: 1px solid hsl(216 90% 58% / 0.3);
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  box-shadow: 0 4px 20px hsl(0 0% 0% / 0.3);
}

/* ─── Loading skeleton ──────────────────────── */
@keyframes skeleton-loading {
  0% {
    background-position: -200% 0;
  }

  100% {
    background-position: 200% 0;
  }
}

.skeleton {
  background: linear-gradient(90deg, hsl(215 20% 12%) 0%, hsl(215 20% 18%) 50%, hsl(215 20% 12%) 100%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
  border-radius: 0.375rem;
}

/* ─── Print Styles for PDF Export ───────────── */
@media print {
  @page {
    margin: 10mm;
    size: auto;
  }

  body * {
    visibility: hidden;
  }

  .printable-report,
  .printable-report * {
    visibility: visible;
  }

  .printable-report {
    position: absolute;
    left: 0;
    top: 0;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }

  .no-print,
  .no-print * {
    display: none !important;
  }

  /* Force background colors to print */
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
```

## frontend\src\main.tsx

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

## frontend\src\types.d.ts

```typescript
declare module 'html2pdf.js' {
  interface Html2PdfOptions {
    margin?: number | number[];
    filename?: string;
    image?: { type?: string; quality?: number };
    html2canvas?: { scale?: number; backgroundColor?: string };
    jsPDF?: { unit?: string; format?: string; orientation?: string };
  }

  interface Html2PdfInstance {
    set(options: Html2PdfOptions): Html2PdfInstance;
    from(element: HTMLElement): Html2PdfInstance;
    save(): Promise<void>;
  }

  function html2pdf(): Html2PdfInstance;
  export default html2pdf;
}

declare module 'react-force-graph-2d' {
  import { Component, RefObject } from 'react';
  
  export interface ForceGraphMethods {
    d3Force(forceName: string, force?: any): any;
    centerAt(x?: number, y?: number, ms?: number): void;
    zoom(amount: number, ms?: number): void;
    zoomToFit(ms?: number, padding?: number): void;
    screen2GraphCoords(x: number, y: number): { x: number; y: number };
    graph2ScreenCoords(x: number, y: number): { x: number; y: number };
  }
  
  const ForceGraph2D: React.ForwardRefExoticComponent<any & React.RefAttributes<ForceGraphMethods>>;
  export default ForceGraph2D;
  export type { ForceGraphMethods };
}
```

## frontend\src\components\ControlPanel.tsx

```typescript
import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crosshair, Route, RefreshCcw, AlertTriangle, Search, Trash2,
  Upload, Zap, RotateCcw, ChevronDown, ChevronUp, Loader2, Shield,
  TrendingUp, Target, Info
} from 'lucide-react';
import type { GraphNode, CriticalNodeResult, TopCriticalPathResult, TopCriticalPath, CycleResult, BlastRadiusResult, ShortestPathResult } from '@/lib/types';

interface Props {
  nodes: GraphNode[];
  onBlastRadius: (source: string, hops: number) => Promise<void>;
  onShortestPath: (source: string, target: string) => Promise<void>;
  onDetectCycles: () => Promise<void>;
  onCriticalNode: () => Promise<void>;
  onTopCriticalPaths: (count: number) => Promise<void>;
  onSelectCriticalPath: (path: TopCriticalPath) => void;
  onRemediate: (nodeId: string) => void;
  onReset: () => void;
  onUpload: (file: File) => void;
  onShowKillChain: () => void;
  criticalNodeResult: CriticalNodeResult | null;
  topCriticalResult: TopCriticalPathResult | null;
  cycleResult: CycleResult | null;
  blastResult: BlastRadiusResult | null;
  pathResult: ShortestPathResult | null;
  loading: boolean;
  isDark: boolean;
  selectedNode?: GraphNode | null;
}

export default function ControlPanel({
  nodes, onBlastRadius, onShortestPath, onDetectCycles, onCriticalNode,
  onTopCriticalPaths, onSelectCriticalPath, onRemediate, onReset, onUpload, onShowKillChain,
  criticalNodeResult, topCriticalResult, cycleResult, blastResult, pathResult,
  loading, isDark, selectedNode
}: Props) {
  const [blastSource, setBlastSource] = useState('');
  const [blastHops, setBlastHops] = useState(3);
  const [pathSource, setPathSource] = useState('internet');
  const [pathTarget, setPathTarget] = useState('prod-database');
  const [topCount, setTopCount] = useState(3);
  const [expanded, setExpanded] = useState<string | null>('blast');
  const [pickingFor, setPickingFor] = useState<'blastSource' | 'pathSource' | 'pathTarget' | null>(null);
  const nodeAtPickStartRef = useRef<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Sync selected node from canvas to active picker slot
  useEffect(() => {
    if (pickingFor && selectedNode) {
      if (selectedNode.id !== nodeAtPickStartRef.current) {
        if (pickingFor === 'blastSource') setBlastSource(selectedNode.id);
        if (pickingFor === 'pathSource') setPathSource(selectedNode.id);
        if (pickingFor === 'pathTarget') setPathTarget(selectedNode.id);
        setPickingFor(null);
        nodeAtPickStartRef.current = null;
      }
    } else if (!pickingFor) {
      nodeAtPickStartRef.current = null;
    }
  }, [selectedNode, pickingFor]);

  const sectionClass = `rounded-xl border transition-all duration-300 overflow-hidden
    ${isDark ? 'bg-slate-900/50 border-slate-700/50 hover:border-slate-600/50' : 'bg-white border-slate-200 hover:border-slate-300'}`;
  const headerClass = `flex items-center justify-between w-full px-4 py-3 cursor-pointer transition-colors
    ${isDark ? 'hover:bg-slate-800/50' : 'hover:bg-slate-50'}`;
  const labelClass = `text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-500'}`;
  const selectClass = `w-full px-3 py-2 rounded-lg text-sm border transition-colors
    ${isDark
      ? 'bg-slate-800 border-slate-700 text-slate-200 focus:border-blue-500'
      : 'bg-white border-slate-200 text-slate-700 focus:border-blue-500'} 
    outline-none focus:ring-1 focus:ring-blue-500/30`;

  const toggle = (id: string) => {
    setExpanded(prev => prev === id ? null : id);
    setPickingFor(null);
  };

  const renderPicker = (type: 'blastSource' | 'pathSource' | 'pathTarget', currentValue: string, labelText: string) => {
    const isPicking = pickingFor === type;
    const nodeLabel = nodes.find(n => n.id === currentValue)?.label || currentValue;
    
    return (
      <div className="mb-3 mt-3">
        <label className={labelClass + ' mb-2 block'}>{labelText}</label>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              if (isPicking) {
                setPickingFor(null);
                nodeAtPickStartRef.current = null;
              } else {
                setPickingFor(type);
                nodeAtPickStartRef.current = selectedNode?.id || null;
              }
            }}
            className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium border border-dashed transition-all text-left truncate
              ${isPicking 
                ? 'bg-blue-500/10 border-blue-400 text-blue-500 animate-pulse ring-2 ring-blue-500/20' 
                : (currentValue 
                  ? (isDark ? 'bg-slate-800 border-slate-600 text-slate-200' : 'bg-slate-100 border-slate-300 text-slate-700')
                  : (isDark ? 'bg-slate-900 border-slate-700 text-slate-500 hover:border-slate-500 hover:text-slate-400' : 'bg-white border-slate-300 text-slate-400 hover:border-slate-400 hover:text-slate-500'))}`}
          >
            {isPicking ? '🎯 Click a node on map...' : 
              (currentValue ? `✅ ${nodeLabel}` : '👉 Select node on map')}
          </button>
          
          {currentValue && (
            <button 
              onClick={() => {
                if (type === 'blastSource') setBlastSource('');
                if (type === 'pathSource') setPathSource('');
                if (type === 'pathTarget') setPathTarget('');
              }}
              className="p-1.5 hover:bg-red-500/10 text-slate-400 hover:text-red-500 rounded-md transition-colors border border-transparent hover:border-red-500/20"
              title="Clear selection"
            >
              ✕
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-3 p-4 overflow-y-auto h-full">
      {/* Title */}
      <div className="flex items-center justify-between mb-2">
        <h2 className={`text-sm font-bold uppercase tracking-wider ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
          ⚡ Analysis Tools
        </h2>
        <div className="flex gap-1.5">
          <button
            onClick={() => fileInputRef.current?.click()}
            className={`p-2 rounded-lg text-xs transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}`}
            title="Upload Custom Graph"
          >
            <Upload className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onReset}
            className={`p-2 rounded-lg text-xs transition-colors ${isDark ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}`}
            title="Reset Graph"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onUpload(f);
            e.target.value = '';
          }}
        />
      </div>

      {/* 1. Blast Radius */}
      <div className={sectionClass}>
        <button onClick={() => toggle('blast')} className={headerClass}>
          <span className="flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-red-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Blast Radius (BFS)</span>
          </span>
          {expanded === 'blast' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'blast' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Find all nodes reachable within N hops from a compromised node.
              </p>
              {renderPicker('blastSource', blastSource, 'Source Node')}
              <div>
                <label className={labelClass}>Max Hops: {blastHops}</label>
                <input
                  type="range"
                  min={1}
                  max={8}
                  value={blastHops}
                  onChange={e => setBlastHops(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-slate-700 accent-red-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
                  <span>1</span><span>4</span><span>8</span>
                </div>
              </div>
              <button
                disabled={!blastSource || loading}
                onClick={() => onBlastRadius(blastSource, blastHops)}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-red-600 to-orange-600 text-white
                  hover:from-red-500 hover:to-orange-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-red-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Analyze Blast Radius'}
              </button>
              {/* Result */}
              {blastResult && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2
                    ${blastResult.risk_summary === 'CRITICAL' ? (isDark ? 'bg-red-950/30 border-red-900/40' : 'bg-red-50 border-red-200') : (isDark ? 'bg-amber-950/30 border-amber-900/40' : 'bg-amber-50 border-amber-200')}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-bold ${blastResult.risk_summary === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}`}>
                      {blastResult.risk_summary} RISK
                    </span>
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>{blastResult.total_affected} nodes affected</span>
                  </div>
                  {blastResult.crown_jewels_reached > 0 && (
                    <p className="text-red-400">
                      ⚠️ {blastResult.crown_jewels_reached} Crown Jewel(s) reachable: {blastResult.crown_jewel_names.join(', ')}
                    </p>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 2. Shortest Attack Path */}
      <div className={sectionClass}>
        <button onClick={() => toggle('path')} className={headerClass}>
          <span className="flex items-center gap-2">
            <Route className="w-4 h-4 text-blue-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Attack Path (Dijkstra)</span>
          </span>
          {expanded === 'path' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'path' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Find the easiest attack path using CVSS-weighted edges.
              </p>
              {renderPicker('pathSource', pathSource, 'Source (Attacker Entry)')}
              {renderPicker('pathTarget', pathTarget, 'Target (Crown Jewel)')}
              <button
                disabled={!pathSource || !pathTarget || loading}
                onClick={() => onShortestPath(pathSource, pathTarget)}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-blue-600 to-cyan-600 text-white
                  hover:from-blue-500 hover:to-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-blue-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Find Shortest Path'}
              </button>
              {pathResult && pathResult.path_exists && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2 ${isDark ? 'bg-blue-950/30 border-blue-900/40' : 'bg-blue-50 border-blue-200'}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`font-bold ${pathResult.difficulty === 'TRIVIAL' || pathResult.difficulty === 'EASY' ? 'text-red-400' : 'text-blue-400'}`}>
                      {pathResult.difficulty} Attack
                    </span>
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>
                      {pathResult.hop_count} hops • Weight: {pathResult.total_weight}
                    </span>
                  </div>
                  <div className={`flex flex-wrap items-center gap-1 ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                    {pathResult.path.map((p, i) => (
                      <span key={p} className="flex items-center gap-1">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`}>{p}</span>
                        {i < pathResult.path.length - 1 && <span className="text-red-400">→</span>}
                      </span>
                    ))}
                  </div>
                  <button
                    onClick={onShowKillChain}
                    className="w-full mt-2 py-2 rounded-lg text-xs font-medium transition-all
                      bg-gradient-to-r from-purple-600 to-pink-600 text-white
                      hover:from-purple-500 hover:to-pink-500 hover:shadow-lg hover:shadow-purple-500/20"
                  >
                    📋 View Kill Chain Report
                  </button>
                </motion.div>
              )}
              {pathResult && !pathResult.path_exists && (
                <motion.div initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs ${isDark ? 'bg-green-950/30 border-green-900/40 text-green-400' : 'bg-green-50 border-green-200 text-green-700'}`}>
                  ✅ No attack path exists between these nodes.
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 3. Cycle Detection */}
      <div className={sectionClass}>
        <button onClick={() => toggle('cycles')} className={headerClass}>
          <span className="flex items-center gap-2">
            <RefreshCcw className="w-4 h-4 text-amber-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Cycle Detection (DFS)</span>
          </span>
          {expanded === 'cycles' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'cycles' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Detect circular permission loops in the RBAC graph.
              </p>
              <button
                disabled={loading}
                onClick={onDetectCycles}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-amber-600 to-yellow-600 text-white
                  hover:from-amber-500 hover:to-yellow-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-amber-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Detect Cycles'}
              </button>
              {cycleResult && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2 ${cycleResult.has_cycles ? (isDark ? 'bg-amber-950/30 border-amber-900/40' : 'bg-amber-50 border-amber-200') : (isDark ? 'bg-green-950/30 border-green-900/40' : 'bg-green-50 border-green-200')}`}
                >
                  {cycleResult.has_cycles ? (
                    <>
                      <span className="font-bold text-amber-400">⚠️ {cycleResult.total_cycles} cycle(s) found</span>
                      {cycleResult.cycles.map((c, i) => (
                        <div key={i} className={`p-2 rounded text-[11px] ${isDark ? 'bg-slate-800/50' : 'bg-slate-100'}`}>
                          <span className={`font-medium ${c.risk === 'CRITICAL' ? 'text-red-400' : 'text-amber-400'}`}>[{c.risk}]</span>{' '}
                          <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>{c.description}</span>
                        </div>
                      ))}
                    </>
                  ) : (
                    <span className="text-green-400">✅ No circular permission loops detected.</span>
                  )}
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 4. Top Critical Attack Paths */}
      <div className={sectionClass}>
        <button onClick={() => toggle('topCritical')} className={headerClass}>
          <span className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-red-500" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Top Critical Paths</span>
          </span>
          {expanded === 'topCritical' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'topCritical' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Identify and analyze the most critical attack paths with mitigation suggestions.
              </p>
              <div>
                <label className={labelClass}>Number of Paths: {topCount}</label>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={topCount > 10 ? 10 : topCount}
                  onChange={e => setTopCount(Number(e.target.value))}
                  className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-slate-700 accent-red-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-0.5">
                  <span>1</span><span>5</span><span>10 MAX</span>
                </div>
              </div>
              <button
                disabled={loading}
                onClick={() => onTopCriticalPaths(topCount)}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-red-600 to-pink-600 text-white
                  hover:from-red-500 hover:to-pink-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-red-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Analyze Critical Paths'}
              </button>
              {topCriticalResult && topCriticalResult.top_critical_paths.length > 0 && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs space-y-2 ${isDark ? 'bg-red-950/30 border-red-900/40' : 'bg-red-50 border-red-200'}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-red-400">🚨 {topCriticalResult.top_critical_paths.length} Critical Path(s)</span>
                    <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Total: {topCriticalResult.total_paths_found}</span>
                  </div>
                  {topCriticalResult.top_critical_paths.map((path, i) => (
                    <motion.div
                      key={i}
                      onClick={() => onSelectCriticalPath(path)}
                      whileHover={{ scale: 1.02 }}
                      className={`p-2 rounded text-[10px] space-y-1 cursor-pointer transition-all ${
                        isDark
                          ? 'bg-slate-800/50 hover:bg-slate-700/70 border border-slate-700/30 hover:border-red-500/50'
                          : 'bg-slate-100 hover:bg-slate-200 border border-slate-300/30 hover:border-red-400/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-red-400">#{path.rank}: {path.difficulty}</span>
                        <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Weight: {path.total_weight}</span>
                      </div>
                      <p className={isDark ? 'text-slate-300' : 'text-slate-600'} style={{ wordBreak: 'break-word' }}>
                        {path.description.substring(0, 120)}...
                      </p>
                      {path.mitigation_suggestions.length > 0 && (
                        <div className={`mt-1 pt-1 border-t ${isDark ? 'border-slate-700' : 'border-slate-200'}`}>
                          <span className={`font-semibold ${isDark ? 'text-green-400' : 'text-green-600'}`}>💡 Mitigation:</span>
                          <p className={isDark ? 'text-slate-400' : 'text-slate-500'} style={{ wordBreak: 'break-word' }}>
                            {path.mitigation_suggestions[0]}
                          </p>
                        </div>
                      )}
                    </motion.div>
                  ))}
                </motion.div>
              )}
              {topCriticalResult && topCriticalResult.top_critical_paths.length === 0 && (
                <motion.div initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
                  className={`p-3 rounded-lg border text-xs ${isDark ? 'bg-green-950/30 border-green-900/40 text-green-400' : 'bg-green-50 border-green-200 text-green-700'}`}>
                  ✅ No critical attack paths found from entry points to crown jewels.
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 5. Critical Node */}
      <div className={sectionClass}>
        <button onClick={() => toggle('critical')} className={headerClass}>
          <span className="flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-400" />
            <span className={`text-sm font-semibold ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>Critical Node Analysis</span>
          </span>
          {expanded === 'critical' ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </button>
        <AnimatePresence>
          {expanded === 'critical' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="px-4 pb-4 space-y-3"
            >
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Find the single node whose removal breaks the most attack paths.
              </p>
              <button
                disabled={loading}
                onClick={onCriticalNode}
                className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                  bg-gradient-to-r from-purple-600 to-violet-600 text-white
                  hover:from-purple-500 hover:to-violet-500 disabled:opacity-40 disabled:cursor-not-allowed
                  hover:shadow-lg hover:shadow-purple-500/20 active:scale-[0.98]"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Identify Critical Node'}
              </button>
              {criticalNodeResult?.critical_node && (
                <motion.div
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className={`space-y-3`}
                >
                  <div className={`p-3 rounded-lg border text-xs space-y-2 ${isDark ? 'bg-purple-950/30 border-purple-900/40' : 'bg-purple-50 border-purple-200'}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-purple-400">🎯 {criticalNodeResult.critical_node.label}</span>
                      <span className={`font-bold ${criticalNodeResult.critical_node.impact_percentage > 50 ? 'text-red-400' : 'text-amber-400'}`}>
                        {criticalNodeResult.critical_node.impact_percentage}% Impact
                      </span>
                    </div>
                    <p className={isDark ? 'text-slate-400' : 'text-slate-500'}>
                      Removing this node breaks {criticalNodeResult.critical_node.paths_broken}/{criticalNodeResult.baseline_paths} attack paths
                    </p>
                    <p className={isDark ? 'text-slate-300' : 'text-slate-600'}>
                      💡 {criticalNodeResult.recommendation}
                    </p>
                  </div>

                  {/* Top 5 */}
                  <div className={`p-3 rounded-lg ${isDark ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
                    <span className={`text-xs font-semibold ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Top Remediation Targets</span>
                    {criticalNodeResult.top_5_nodes.map((n, i) => (
                      <div key={n.node_id} className={`flex items-center justify-between py-1.5 text-xs ${i > 0 ? (isDark ? 'border-t border-slate-700/50' : 'border-t border-slate-200') : 'mt-1'}`}>
                        <span className={isDark ? 'text-slate-300' : 'text-slate-600'}>
                          {i + 1}. {n.label}
                        </span>
                        <div className="flex items-center gap-2">
                          <div className={`w-16 h-1.5 rounded-full overflow-hidden ${isDark ? 'bg-slate-700' : 'bg-slate-200'}`}>
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-purple-500 to-red-500"
                              style={{ width: `${n.impact_percentage}%` }}
                            />
                          </div>
                          <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>{n.impact_percentage}%</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Remediate Button */}
                  <button
                    onClick={() => onRemediate(criticalNodeResult.critical_node!.node_id)}
                    className="w-full py-2.5 rounded-lg text-sm font-medium transition-all
                      bg-gradient-to-r from-green-600 to-emerald-600 text-white
                      hover:from-green-500 hover:to-emerald-500
                      hover:shadow-lg hover:shadow-green-500/20 active:scale-[0.98]
                      flex items-center justify-center gap-2"
                  >
                    <Shield className="w-4 h-4" />
                    Remediate: Remove {criticalNodeResult.critical_node.label}
                  </button>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
```

## frontend\src\components\GraphCanvas.tsx

```typescript
import { useCallback, useRef, useEffect, useMemo } from 'react';
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d';
import type { GraphNode, GraphEdge, HighlightState } from '@/lib/types';

interface Props {
  nodes: GraphNode[];
  links: GraphEdge[];
  highlight: HighlightState;
  onNodeClick: (node: GraphNode) => void;
  onLinkClick: (link: GraphEdge) => void;
  selectedNode?: GraphNode | null;
  selectedEdge?: GraphEdge | null;
  isDark: boolean;
}

const NODE_COLORS: Record<string, string> = {
  internet: '#22c55e',
  ingress: '#3b82f6',
  pod: '#6366f1',
  service: '#8b5cf6',
  serviceaccount: '#06b6d4',
  rolebinding: '#f59e0b',
  role: '#f59e0b',
  clusterrole: '#ef4444',
  secret: '#eab308',
  database: '#eab308',
  configmap: '#64748b',
  networkpolicy: '#64748b',
  namespace: '#94a3b8',
};

const RISK_COLORS: Record<string, string> = {
  'crown-jewel': '#eab308',   // Yellow (Crown Jewel)
  'critical': '#ef4444',     // Red (Critical Risk)
  'high': '#f97316',         // Orange
  'medium': '#f59e0b',       // Amber
  'low': '#64748b',          // Slate/Grey (Low Risk / Utility)
  'entry-point': '#22c55e',  // Green (Internet / Entry Point)
  'info': '#6366f1',         // Indigo (Standard Entity)
};

const NODE_ICONS: Record<string, string> = {
  internet: '🌐',
  ingress: '🔀',
  pod: '📦',
  service: '🔌',
  serviceaccount: '👤',
  rolebinding: '🔗',
  role: '🛡️',
  clusterrole: '⚔️',
  secret: '🔑',
  database: '🗄️',
  configmap: '📋',
  networkpolicy: '🚧',
};

export default function GraphCanvas({ nodes, links, highlight, onNodeClick, onLinkClick, selectedNode, selectedEdge, isDark }: Props) {
  const fgRef = useRef<ForceGraphMethods | null>(null);

  const graphData = useMemo(() => {
    return {
      nodes: nodes.map(n => ({ ...n })),
      links: links.map(l => ({ ...l })),
    };
  }, [nodes, links]);

  // Tune layout forces
  useEffect(() => {
    const fg = fgRef.current;
    if (fg) {
      // Increase negative charge so nodes repel each other horizontally
      fg.d3Force('charge')?.strength(-400);
      // Let the link distances be flexible
      fg.d3Force('link')?.distance(60);
      
      (fg as any).d3ReheatSimulation?.();
    }
  }, [graphData]);

  const getNodeColor = useCallback((node: GraphNode) => {
    if (highlight.nodes.size > 0) {
      if (highlight.nodes.has(node.id)) {
        if (highlight.path.includes(node.id)) {
          return '#ef4444';
        }
        return RISK_COLORS[node.risk_level] || NODE_COLORS[node.type] || '#6366f1';
      }
      return isDark ? '#1e293b' : '#cbd5e1';
    }
    return RISK_COLORS[node.risk_level] || NODE_COLORS[node.type] || '#6366f1';
  }, [highlight, isDark]);

  const getNodeSize = useCallback((node: GraphNode) => {
    const baseSize = node.type === 'internet' ? 10 :
      node.risk_level === 'crown-jewel' ? 9 :
        node.risk_level === 'critical' ? 8 :
          node.type === 'pod' ? 7 : 6;

    if (highlight.nodes.size > 0 && highlight.nodes.has(node.id)) {
      return baseSize * 1.4;
    }
    if (highlight.nodes.size > 0 && !highlight.nodes.has(node.id)) {
      return baseSize * 0.6;
    }
    return baseSize;
  }, [highlight]);

  const paintNode = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const size = getNodeSize(node);
    const color = getNodeColor(node);
    const x = node.x ?? 0;
    const y = node.y ?? 0;
    const isHighlighted = highlight.nodes.size === 0 || highlight.nodes.has(node.id);
    const isOnPath = highlight.path.includes(node.id);
    const isSelected = selectedNode?.id === node.id;
    const isLinkSelected = selectedEdge && (
      (typeof selectedEdge.source === 'string' ? selectedEdge.source : (selectedEdge.source as any).id) === node.id ||
      (typeof selectedEdge.target === 'string' ? selectedEdge.target : (selectedEdge.target as any).id) === node.id
    );
    const isGroupGlow = 
      (highlight.mode === 'group-critical' && node.risk_level === 'critical') || 
      (highlight.mode === 'group-crown-jewel' && node.risk_level === 'crown-jewel') ||
      (highlight.mode === 'group-entry-point' && (node.type === 'internet' || node.risk_level === 'entry-point')) ||
      (highlight.mode === 'group-standard' && (node.risk_level === 'info' || node.risk_level === 'medium' || node.type === 'pod' || node.type === 'service')) ||
      (highlight.mode === 'group-low' && node.risk_level === 'low');

    // Draw native-colored glowing halo for selected node or filtered group
    if (isSelected || isGroupGlow || isLinkSelected) {
      ctx.beginPath();
      ctx.arc(x, y, size + (isSelected || isGroupGlow ? 6 : 4), 0, 2 * Math.PI);
      
      // Use standard transparent base mapping matching the node's true color natively!
      ctx.globalAlpha = isDark ? (isLinkSelected && !isSelected ? 0.2 : 0.35) : (isLinkSelected && !isSelected ? 0.15 : 0.25);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.globalAlpha = 1.0;
      
      // Add glowing shadow effect tied to the node's specific color
      if (isSelected || isGroupGlow) {
        ctx.shadowColor = color;
        ctx.shadowBlur = 20;
      }
      
      // Apply exact border
      ctx.strokeStyle = color;
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();
      
      // Reset shadow so it doesn't affect other elements
      ctx.shadowBlur = 0;
    }

    // Outer faint glow for generic highlighted nodes
    if (isHighlighted && (node.risk_level === 'critical' || node.risk_level === 'crown-jewel' || isOnPath)) {
      const glowSize = size + 4;
      const gradient = ctx.createRadialGradient(x, y, size * 0.5, x, y, glowSize);
      gradient.addColorStop(0, color + '60');
      gradient.addColorStop(1, color + '00');
      ctx.beginPath();
      ctx.arc(x, y, glowSize, 0, 2 * Math.PI);
      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // Main node circle
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI);
    ctx.fillStyle = isHighlighted ? color : (isDark ? '#1e293b' : '#e2e8f0');
    ctx.fill();

    // Border
    ctx.strokeStyle = isHighlighted ? color : (isDark ? '#334155' : '#94a3b8');
    ctx.lineWidth = isOnPath ? 2 : 1;
    ctx.stroke();

    // Icon (if zoomed in enough)
    if (globalScale > 0.8) {
      const icon = NODE_ICONS[node.type] || '⚪';
      ctx.font = `${Math.max(size * 0.9, 6)}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(icon, x, y);
    }

    // Label (if zoomed in)
    if (globalScale > 1.2) {
      ctx.font = `${Math.max(11 / globalScale, 3)}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = isHighlighted
        ? (isDark ? '#f1f5f9' : '#1e293b')
        : (isDark ? '#475569' : '#94a3b8');
      ctx.fillText(node.label || node.id, x, y + size + 3);
    }
  }, [getNodeColor, getNodeSize, highlight, isDark, selectedNode, selectedEdge]);

  const getLinkColor = useCallback((link: { source: GraphNode | string; target: GraphNode | string }) => {
    const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
    const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
    const edgeKey = `${sourceId}->${targetId}`;

    const isSelected = selectedEdge && (
      (typeof selectedEdge.source === 'string' ? selectedEdge.source : (selectedEdge.source as any).id) === sourceId &&
      (typeof selectedEdge.target === 'string' ? selectedEdge.target : (selectedEdge.target as any).id) === targetId
    );

    if (isSelected) return '#ef4444';

    if (highlight.edges.size > 0 && highlight.edges.has(edgeKey)) {
      return '#ef4444';
    }
    if (highlight.nodes.size > 0) {
      if (highlight.nodes.has(sourceId) && highlight.nodes.has(targetId)) {
        return isDark ? 'rgba(99,102,241,0.8)' : 'rgba(99,102,241,0.7)';
      }
      return isDark ? 'rgba(15,23,42,0.6)' : 'rgba(203,213,225,0.4)';
    }
    // High contrast professional lines (slate-400 equivalent for dark, slate-600 equivalent for light)
    return isDark ? 'rgba(148,163,184,0.75)' : 'rgba(71,85,105,0.8)';
  }, [highlight, isDark, selectedEdge]);

  const getLinkWidth = useCallback((link: { source: GraphNode | string; target: GraphNode | string }) => {
    const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
    const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
    const edgeKey = `${sourceId}->${targetId}`;

    const isSelected = selectedEdge && (
      (typeof selectedEdge.source === 'string' ? selectedEdge.source : (selectedEdge.source as any).id) === sourceId &&
      (typeof selectedEdge.target === 'string' ? selectedEdge.target : (selectedEdge.target as any).id) === targetId
    );

    if (isSelected) return 4;

    if (highlight.edges.size > 0 && highlight.edges.has(edgeKey)) {
      return 3;
    }
    return 1;
  }, [highlight, selectedEdge]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    onNodeClick(node);
    const fg = fgRef.current;
    if (fg) {
      fg.centerAt(node.x, node.y, 600);
      fg.zoom(2.5, 600);
    }
  }, [onNodeClick]);

  const handleLinkClick = useCallback((link: any) => {
    onLinkClick(link as GraphEdge);
  }, [onLinkClick]);

  return (
    <div className="graph-container relative w-full h-full">
      <ForceGraph2D
        ref={fgRef as any}
        graphData={graphData}
        nodeCanvasObject={paintNode as any}
        nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
          const size = getNodeSize(node);
          ctx.beginPath();
          ctx.arc(node.x ?? 0, node.y ?? 0, size + 2, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }}
        dagMode="td"
        dagLevelDistance={120}
        d3VelocityDecay={0.3}
        linkColor={getLinkColor as any}
        linkWidth={getLinkWidth as any}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={0.85}
        linkDirectionalParticles={(link: any) => {
          const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
          const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
          const edgeKey = `${sourceId}->${targetId}`;

          const isSelected = selectedEdge && (
            (typeof selectedEdge.source === 'string' ? selectedEdge.source : (selectedEdge.source as any).id) === sourceId &&
            (typeof selectedEdge.target === 'string' ? selectedEdge.target : (selectedEdge.target as any).id) === targetId
          );

          return (highlight.edges.has(edgeKey) || isSelected) ? 3 : 0;
        }}
        linkDirectionalParticleSpeed={0.006}
        linkDirectionalParticleWidth={3}
        linkDirectionalParticleColor={() => '#ef4444'}
        linkCurvature={0.25}
        onNodeClick={handleNodeClick as any}
        onLinkClick={handleLinkClick as any}
        backgroundColor={isDark ? '#0a0f1e' : '#f8fafc'}
        cooldownTicks={100}
        onEngineStop={() => fgRef.current?.zoomToFit(400, 40)}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        minZoom={0.3}
        maxZoom={8}
      />
      {/* Zoom hints */}
      <div className={`absolute bottom-3 right-3 text-xs px-3 py-1.5 rounded-full
        ${isDark ? 'bg-slate-800/80 text-slate-400' : 'bg-white/80 text-slate-500'} 
        backdrop-blur-sm border ${isDark ? 'border-slate-700/50' : 'border-slate-200'}`}>
        Scroll to zoom • Drag to pan • Click nodes
      </div>
    </div>
  );
}
```

## frontend\src\components\KillChainReport.tsx

```typescript
import { useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, FileText, AlertTriangle, ArrowRight, Shield, ChevronRight } from 'lucide-react';
import type { ShortestPathResult } from '@/lib/types';

interface Props {
  result: ShortestPathResult | null;
  isOpen: boolean;
  onClose: () => void;
  isDark: boolean;
}

const STEP_COLORS: Record<string, string> = {
  'crown-jewel': 'from-yellow-500 to-amber-600',
  'critical': 'from-red-500 to-rose-600',
  'high': 'from-orange-500 to-red-500',
  'medium': 'from-amber-500 to-orange-500',
  'low': 'from-green-500 to-emerald-500',
  'entry-point': 'from-green-500 to-teal-500',
  'info': 'from-slate-500 to-slate-600',
};

export default function KillChainReport({ result, isOpen, onClose, isDark }: Props) {
  const reportRef = useRef<HTMLDivElement>(null);

  if (!result || !isOpen) return null;

  const handleExportPDF = async () => {
    try {
      const res = await fetch('/api/export-pdf', { method: 'POST' });
      if (!res.ok) throw new Error('PDF generation failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `KubePathAudit_KillChain_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('PDF export failed:', err);
      alert('Failed to generate PDF. Make sure the backend is running.');
    }
  };

  const chain = result.kill_chain_summary || [];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ y: 40, opacity: 0, scale: 0.95 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: 40, opacity: 0, scale: 0.95 }}
          transition={{ type: 'spring', damping: 25 }}
          className={`relative z-10 flex flex-col w-full max-w-2xl max-h-[85vh] rounded-2xl shadow-2xl
            ${isDark ? 'bg-slate-900 border border-slate-700/50' : 'bg-white border border-slate-200'}
            shadow-black/30`}
        >
          {/* Header */}
          <div className={`shrink-0 z-20 flex items-center justify-between px-6 py-4 border-b rounded-t-2xl
            ${isDark ? 'bg-slate-900/95 border-slate-700/50' : 'bg-white/95 border-slate-200'}`}>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-red-500 to-orange-500">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>Kill Chain Report</h2>
                <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Attack Path Analysis — {new Date().toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 no-print">
              <button
                onClick={handleExportPDF}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                  bg-gradient-to-r from-blue-600 to-cyan-600 text-white
                  hover:from-blue-500 hover:to-cyan-500 hover:shadow-lg hover:shadow-blue-500/20"
              >
                <Download className="w-3.5 h-3.5" />
                Export PDF
              </button>
              <button
                onClick={onClose}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Report Content - Scrolling Area */}
          <div className="flex-1 overflow-y-auto printable-report">
            <div ref={reportRef} className="p-6">
            {/* Summary Banner */}
            <div className={`p-4 rounded-xl mb-6 border
              ${result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY'
                ? (isDark ? 'bg-red-950/40 border-red-900/50' : 'bg-red-50 border-red-200')
                : (isDark ? 'bg-amber-950/40 border-amber-900/50' : 'bg-amber-50 border-amber-200')
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className={`w-5 h-5 ${result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY' ? 'text-red-400' : 'text-amber-400'}`} />
                <span className={`text-sm font-bold ${result.difficulty === 'TRIVIAL' || result.difficulty === 'EASY' ? 'text-red-400' : 'text-amber-400'}`}>
                  {result.difficulty} Attack Path Detected
                </span>
              </div>
              <div className={`grid grid-cols-3 gap-4 mt-3 text-center`}>
                <div>
                  <p className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{result.hop_count}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Total Hops</p>
                </div>
                <div>
                  <p className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{result.total_weight}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>CVSS Weight</p>
                </div>
                <div>
                  <p className={`text-2xl font-bold ${
                    result.difficulty === 'TRIVIAL' ? 'text-red-400' :
                    result.difficulty === 'EASY' ? 'text-orange-400' :
                    result.difficulty === 'MODERATE' ? 'text-amber-400' : 'text-green-400'
                  }`}>{result.difficulty}</p>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Difficulty</p>
                </div>
              </div>
            </div>

            {/* Path Overview */}
            <div className="mb-6">
              <h3 className={`text-sm font-bold mb-3 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Attack Path Overview
              </h3>
              <div className="flex flex-wrap items-center gap-1.5">
                {result.path.map((nodeId, i) => (
                  <span key={nodeId} className="flex items-center gap-1.5">
                    <span className={`px-2 py-1 rounded-md text-xs font-mono font-medium
                      ${isDark ? 'bg-slate-800 text-slate-200 border border-slate-700' : 'bg-slate-100 text-slate-700 border border-slate-200'}`}>
                      {nodeId}
                    </span>
                    {i < result.path.length - 1 && (
                      <ArrowRight className="w-3.5 h-3.5 text-red-400 shrink-0" />
                    )}
                  </span>
                ))}
              </div>
            </div>

            {/* Kill Chain Steps */}
            <div>
              <h3 className={`text-sm font-bold mb-4 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Detailed Kill Chain
              </h3>
              <div className="space-y-4">
                {chain.map((step, i) => {
                  const gradient = STEP_COLORS[step.risk_level] || STEP_COLORS.info;
                  return (
                    <motion.div
                      key={step.step}
                      initial={{ x: -30, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: i * 0.08 }}
                      className="relative"
                    >
                      <div className={`flex gap-4 p-4 rounded-xl border transition-all
                        ${isDark ? 'bg-slate-800/50 border-slate-700/50 hover:bg-slate-800' : 'bg-slate-50 border-slate-200 hover:bg-white'}`}>
                        {/* Step Number */}
                        <div className={`shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br ${gradient}
                          flex items-center justify-center text-white font-bold text-sm shadow-lg`}>
                          {step.step}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-slate-900'}`}>
                              {step.node}
                            </span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium uppercase
                              ${isDark ? 'bg-slate-700 text-slate-300' : 'bg-slate-200 text-slate-600'}`}>
                              {step.node_type}
                            </span>
                          </div>
                          <p className={`text-xs mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                            {step.action}
                          </p>
                          <div className="flex flex-wrap items-center gap-2">
                            {step.cves_exploited.length > 0 && step.cves_exploited.map(cve => (
                              <span key={cve} className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-red-500/20 text-red-400">
                                {cve}
                              </span>
                            ))}
                            {step.edge_info && step.edge_info !== '—' && (
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${isDark ? 'bg-slate-700 text-slate-400' : 'bg-slate-200 text-slate-500'}`}>
                                → {step.edge_info}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Connector */}
                      {i < chain.length - 1 && (
                        <div className="absolute left-[2.15rem] top-[3.5rem] w-0.5 h-4 bg-gradient-to-b from-red-500/50 to-transparent" />
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Footer */}
            <div className={`mt-6 pt-4 border-t text-center ${isDark ? 'border-slate-700/50' : 'border-slate-200'}`}>
              <p className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                Generated by KubePathAudit • {new Date().toLocaleString()} • Confidential
              </p>
            </div>
          </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
```

## frontend\src\components\SecuritySidebar.tsx

```typescript
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield, AlertTriangle, Database, Key, Server, Globe, Link2, User,
  Cpu, Activity, HardDrive, FileText, ShieldOff, ShieldAlert, Network, Monitor,
  X, Crosshair, Route, ChevronRight, Zap
} from 'lucide-react';
import type { GraphNode, GraphEdge, TopCriticalPath } from '@/lib/types';

interface Props {
  node: GraphNode | null;
  edge: GraphEdge | null;
  criticalPath: TopCriticalPath | null;
  onClose: () => void;
  onBlastRadius: (nodeId: string) => void;
  onFindPath: (target: string) => void;
  isDark: boolean;
}

const ICON_MAP: Record<string, React.ReactNode> = {
  globe: <Globe className="w-5 h-5" />,
  network: <Network className="w-5 h-5" />,
  monitor: <Monitor className="w-5 h-5" />,
  server: <Server className="w-5 h-5" />,
  'user-check': <User className="w-5 h-5" />,
  user: <User className="w-5 h-5" />,
  link: <Link2 className="w-5 h-5" />,
  shield: <Shield className="w-5 h-5" />,
  'shield-alert': <ShieldAlert className="w-5 h-5" />,
  'shield-off': <ShieldOff className="w-5 h-5" />,
  key: <Key className="w-5 h-5" />,
  database: <Database className="w-5 h-5" />,
  cpu: <Cpu className="w-5 h-5" />,
  activity: <Activity className="w-5 h-5" />,
  'hard-drive': <HardDrive className="w-5 h-5" />,
  'file-text': <FileText className="w-5 h-5" />,
};

const RISK_BADGE: Record<string, { bg: string; text: string; label: string }> = {
  'crown-jewel': { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: '👑 Crown Jewel' },
  'critical': { bg: 'bg-red-500/20', text: 'text-red-400', label: '🔴 Critical' },
  'high': { bg: 'bg-orange-500/20', text: 'text-orange-400', label: '🟠 High' },
  'medium': { bg: 'bg-amber-500/20', text: 'text-amber-400', label: '🟡 Medium' },
  'low': { bg: 'bg-green-500/20', text: 'text-green-400', label: '🟢 Low' },
  'entry-point': { bg: 'bg-green-500/20', text: 'text-green-400', label: '🌐 Entry Point' },
  'info': { bg: 'bg-slate-500/20', text: 'text-slate-400', label: 'ℹ️ Info' },
};

export default function SecuritySidebar({ node, edge, criticalPath, onClose, onBlastRadius, onFindPath, isDark }: Props) {
  if (!node && !edge && !criticalPath) return null;

  // If showing critical path
  if (criticalPath) {
    return (
      <AnimatePresence>
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={`absolute top-0 right-0 w-[380px] h-full z-30 overflow-y-auto
            ${isDark 
              ? 'bg-slate-900/95 border-l border-slate-700/50' 
              : 'bg-white/95 border-l border-slate-200'}
            backdrop-blur-xl`}
        >
          {/* Header */}
          <div className={`sticky top-0 z-10 px-5 py-4 border-b backdrop-blur-xl
            ${isDark ? 'border-slate-700/50 bg-slate-900/90' : 'border-slate-200 bg-white/90'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isDark ? 'bg-slate-800' : 'bg-slate-100'} glow-red`}>
                  <Route className="w-5 h-5 text-red-400" />
                </div>
                <div>
                  <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    Attack Path #{criticalPath.rank}
                  </h3>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                    {criticalPath.difficulty} Risk
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="px-5 py-4 space-y-5">
            {/* Difficulty Badge */}
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              className={`inline-flex px-3 py-1.5 rounded-full text-xs font-medium
                ${criticalPath.difficulty === 'HARD' ? 'bg-red-500/20 text-red-400' :
                  criticalPath.difficulty === 'MODERATE' ? 'bg-orange-500/20 text-orange-400' :
                  'bg-yellow-500/20 text-yellow-400'}`}
            >
              📊 {criticalPath.difficulty} Difficulty
            </motion.div>

            {/* Path Stats */}
            <div className={`grid grid-cols-2 gap-3 p-3 rounded-xl ${isDark ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Hop Count</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{criticalPath.hop_count}</p>
              </div>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Total Weight</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{criticalPath.total_weight.toFixed(2)}</p>
              </div>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Vulnerabilities</span>
                <p className="text-sm font-medium text-red-400">⚠️ {criticalPath.vulnerabilities_found}</p>
              </div>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Criticality</span>
                <p className="text-sm font-medium text-amber-400">🎯 {criticalPath.criticality_score.toFixed(1)}</p>
              </div>
            </div>

            {/* Full Description */}
            <div>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Attack Description
              </h4>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                {criticalPath.description}
              </p>
            </div>

            {/* Attack Path */}
            <div>
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-3 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                📍 Attack Path ({criticalPath.path.length} nodes)
              </h4>
              <div className="space-y-2">
                {criticalPath.path.map((nodeId, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className={`px-2 py-1 rounded text-xs font-mono font-medium
                      ${idx === 0 ? 'bg-green-500/20 text-green-400' :
                        idx === criticalPath.path.length - 1 ? 'bg-yellow-500/20 text-yellow-400' :
                        isDark ? 'bg-slate-800 text-cyan-400' : 'bg-slate-100 text-blue-600'}`}>
                      {nodeId}
                    </div>
                    {idx < criticalPath.path.length - 1 && (
                      <ChevronRight className={`w-4 h-4 ${isDark ? 'text-slate-600' : 'text-slate-300'}`} />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Factors */}
            {criticalPath.risk_factors.length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                  Risk Factors
                </h4>
                <div className="space-y-1">
                  {criticalPath.risk_factors.map((factor, i) => (
                    <div key={i} className={`text-xs p-2 rounded ${isDark ? 'bg-red-950/30 text-red-300' : 'bg-red-50 text-red-700'}`}>
                      • {factor}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Mitigation Suggestions */}
            {criticalPath.mitigation_suggestions.length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  <Zap className="w-3.5 h-3.5 text-green-400" />
                  Mitigation Suggestions
                </h4>
                <div className="space-y-2">
                  {criticalPath.mitigation_suggestions.map((suggestion, i) => (
                    <motion.div
                      key={i}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: i * 0.1 }}
                      className={`flex gap-2 p-2.5 rounded-lg text-xs ${isDark ? 'bg-green-950/30 border border-green-900/30 text-green-300' : 'bg-green-50 border border-green-200 text-green-700'}`}
                    >
                      <span className="font-bold shrink-0">{i + 1}.</span>
                      <span>{suggestion}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    );
  }

  // Original node display logic
  if (node) {
    const risk = RISK_BADGE[node.risk_level] || RISK_BADGE.info;
    const icon = ICON_MAP[node.metadata?.icon || ''] || <Server className="w-5 h-5" />;
    const cves = node.metadata?.cves || [];
    const cvssScores = node.metadata?.cvss_scores || [];

    return (
      <AnimatePresence>
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={`absolute top-0 right-0 w-[380px] h-full z-30 overflow-y-auto
            ${isDark 
              ? 'bg-slate-900/95 border-l border-slate-700/50' 
              : 'bg-white/95 border-l border-slate-200'}
            backdrop-blur-xl`}
        >
          {/* Header */}
          <div className={`sticky top-0 z-10 px-5 py-4 border-b backdrop-blur-xl
            ${isDark ? 'border-slate-700/50 bg-slate-900/90' : 'border-slate-200 bg-white/90'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isDark ? 'bg-slate-800' : 'bg-slate-100'}
                  ${node.risk_level === 'critical' ? 'glow-red' : node.risk_level === 'crown-jewel' ? 'glow-gold' : ''}`}>
                  {icon}
                </div>
                <div>
                  <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    {node.label}
                  </h3>
                  <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                    {node.type.toUpperCase()}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="px-5 py-4 space-y-5">
            {/* Risk Badge */}
            <motion.div initial={{ scale: 0.9 }} animate={{ scale: 1 }} className={`inline-flex px-3 py-1.5 rounded-full text-xs font-medium ${risk.bg} ${risk.text}`}>
              {risk.label}
            </motion.div>

            {/* Description */}
            {node.metadata?.description && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Description
                </h4>
                <p className={`text-sm leading-relaxed ${isDark ? 'text-slate-300' : 'text-slate-600'}`}>
                  {node.metadata.description}
                </p>
              </div>
            )}

            {/* Properties */}
            <div className={`grid grid-cols-2 gap-3 p-3 rounded-xl ${isDark ? 'bg-slate-800/50' : 'bg-slate-50'}`}>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Namespace</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.namespace}</p>
              </div>
              <div>
                <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Type</span>
                <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.type}</p>
              </div>
              {!node.metadata?.containers && node.metadata?.image && (
                <div className="col-span-2">
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Image</span>
                  <p className={`text-xs font-mono break-all ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>{node.metadata.image}</p>
                </div>
              )}
              {node.metadata?.version && (
                <div>
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Version</span>
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.metadata.version}</p>
                </div>
              )}
              {!node.metadata?.containers && node.metadata?.ports && node.metadata.ports.length > 0 && (
                <div>
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Ports</span>
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.metadata.ports.join(', ')}</p>
                </div>
              )}
              {node.metadata?.engine && (
                <div className="col-span-2">
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Engine</span>
                  <p className={`text-sm font-medium ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{node.metadata.engine}</p>
                </div>
              )}
              {node.metadata?.records && (
                <div className="col-span-2">
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Data Volume</span>
                  <p className={`text-sm font-medium text-amber-400`}>{node.metadata.records}</p>
                </div>
              )}
              {node.metadata?.data_classification && (
                <div className="col-span-2">
                  <span className={`text-xs ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Classification</span>
                  <p className="text-sm font-medium text-red-400">⚠️ {node.metadata.data_classification}</p>
                </div>
              )}
            </div>

            {/* Detailed Containers */}
            {node.metadata?.containers && (node.metadata.containers as any[]).length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  <Cpu className="w-3.5 h-3.5" />
                  Containers ({(node.metadata.containers as any[]).length})
                </h4>
                <div className="space-y-2">
                  {(node.metadata.containers as any[]).map((c, i) => (
                    <div key={i} className={`p-3 rounded-xl border ${isDark ? 'bg-slate-800/80 border-slate-700/50' : 'bg-white border-slate-200'} shadow-sm`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-bold ${isDark ? 'text-cyan-400' : 'text-blue-600'}`}>{c.name}</span>
                        {c.score !== undefined && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 font-bold">
                            Risk: {c.score}
                          </span>
                        )}
                      </div>
                      <p className={`text-[10px] font-mono break-all mb-1 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>{c.image}</p>
                      {c.ports && c.ports.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {c.ports.map((p: number) => (
                            <span key={p} className={`text-[9px] px-1.5 py-0.5 rounded ${isDark ? 'bg-slate-700 text-slate-300' : 'bg-slate-100 text-slate-600'}`}>
                              Port {p}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CVEs */}
            {cves.length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                  Vulnerabilities ({cves.length})
                </h4>
                <div className="space-y-2">
                  {cves.map((cve, i) => (
                    <motion.div
                      key={cve}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: i * 0.1 }}
                      className={`flex items-center justify-between p-2.5 rounded-lg ${isDark ? 'bg-red-950/30 border border-red-900/30' : 'bg-red-50 border border-red-200'}`}
                    >
                      <span className={`text-xs font-mono font-medium ${isDark ? 'text-red-300' : 'text-red-700'}`}>{cve}</span>
                      {cvssScores[i] !== undefined && (
                        <span className={`text-xs font-bold px-2 py-0.5 rounded ${cvssScores[i]! >= 7 ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
                          CVSS {cvssScores[i]}
                        </span>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* RBAC Rules */}
            {node.metadata?.rules && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  RBAC Rules
                </h4>
                <div className="space-y-1">
                  {(node.metadata.rules as string[]).map((rule, i) => (
                    <div key={i} className={`text-xs font-mono p-2 rounded ${isDark ? 'bg-slate-800 text-cyan-400' : 'bg-slate-100 text-blue-600'}`}>
                      {rule}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Secret Keys */}
            {node.metadata?.keys && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Secret Keys
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {(node.metadata.keys as string[]).map((key) => (
                    <span key={key} className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'bg-amber-900/30 text-amber-300 border border-amber-800/30' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>
                      {key}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Labels */}
            {node.metadata?.labels && Object.keys(node.metadata.labels).length > 0 && (
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Labels
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(node.metadata.labels).map(([k, v]) => (
                    <span key={k} className={`text-xs font-mono px-2 py-1 rounded ${isDark ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'}`}>
                      {k}={v}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2 pt-2">
              <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                Analysis Actions
              </h4>
              <button
                onClick={() => onBlastRadius(node.id)}
                className="w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all
                  bg-gradient-to-r from-red-600 to-orange-600 text-white hover:from-red-500 hover:to-orange-500
                  hover:shadow-lg hover:shadow-red-500/20 active:scale-[0.98]"
              >
                <span className="flex items-center gap-2">
                  <Crosshair className="w-4 h-4" />
                  Run Blast Radius
                </span>
                <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => onFindPath(node.id)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all
                  ${isDark 
                    ? 'bg-slate-800 text-slate-200 hover:bg-slate-700 border border-slate-700' 
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200'}
                  hover:shadow-lg active:scale-[0.98]`}
              >
                <span className="flex items-center gap-2">
                  <Route className="w-4 h-4" />
                  Find Attack Path to This Node
                </span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    );
  }

  // ── Edge Rendering Logic ────────────────
  if (edge) {
    const sourceLabel = typeof edge.source === 'string' ? edge.source : (edge.source as any).label || (edge.source as any).id;
    const targetLabel = typeof edge.target === 'string' ? edge.target : (edge.target as any).label || (edge.target as any).id;

    return (
      <AnimatePresence>
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className={`absolute top-0 right-0 w-[380px] h-full z-30 overflow-y-auto
            ${isDark 
              ? 'bg-slate-900/95 border-l border-slate-700/50' 
              : 'bg-white/95 border-l border-slate-200'}
            backdrop-blur-xl`}
        >
          {/* Header */}
          <div className={`sticky top-0 z-10 px-5 py-4 border-b backdrop-blur-xl
            ${isDark ? 'border-slate-700/50 bg-slate-900/90' : 'border-slate-200 bg-white/90'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${isDark ? 'bg-slate-800' : 'bg-slate-100'} glow-blue`}>
                  <Link2 className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <h3 className={`font-semibold text-sm ${isDark ? 'text-slate-100' : 'text-slate-900'}`}>
                    Relationship
                  </h3>
                  <p className={`text-[10px] font-mono tracking-wider ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>
                    {edge.relationship.toUpperCase()}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-slate-800 text-slate-400' : 'hover:bg-slate-100 text-slate-500'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="px-5 py-6 space-y-6">
            {/* Connection Visualizer */}
            <div className="flex items-center justify-between gap-4 p-4 rounded-2xl bg-gradient-to-br from-slate-800/30 to-slate-900/30 border border-slate-700/30">
              <div className="text-center flex-1 min-w-0">
                <p className={`text-[10px] mb-1 uppercase tracking-tighter ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Source</p>
                <p className={`text-xs font-bold truncate ${isDark ? 'text-white' : 'text-slate-900'}`}>{sourceLabel}</p>
              </div>
              <div className="flex flex-col items-center gap-1">
                <div className="w-12 h-px bg-slate-700 mt-2 relative">
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 border-y-4 border-y-transparent border-l-4 border-l-slate-700" />
                </div>
              </div>
              <div className="text-center flex-1 min-w-0">
                <p className={`text-[10px] mb-1 uppercase tracking-tighter ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>Target</p>
                <p className={`text-xs font-bold truncate ${isDark ? 'text-white' : 'text-slate-900'}`}>{targetLabel}</p>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-4">
              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Relationship Type
                </h4>
                <div className={`p-3 rounded-xl text-sm font-mono ${isDark ? 'bg-slate-800 text-blue-400' : 'bg-slate-100 text-blue-600'}`}>
                  {edge.relationship}
                </div>
              </div>

              <div>
                <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  Difficulty Weight
                </h4>
                <div className="flex items-center gap-3">
                  <div className={`flex-1 h-2 rounded-full ${isDark ? 'bg-slate-800' : 'bg-slate-200'} overflow-hidden`}>
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${(1 - edge.weight / 5) * 100}%` }}
                      className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                    />
                  </div>
                  <span className={`text-xs font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                    {edge.weight}
                  </span>
                </div>
                <p className={`text-[10px] mt-1.5 ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                  Lower weight represents an easier attack path/permission grant.
                </p>
              </div>

              {/* Edge Metadata */}
              {edge.metadata && Object.keys(edge.metadata).length > 0 && (
                <div>
                  <h4 className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                    Metadata
                  </h4>
                  <div className={`divide-y ${isDark ? 'divide-slate-700/50 bg-slate-800/40' : 'divide-slate-200 bg-slate-50'} rounded-xl border border-transparent overflow-hidden`}>
                    {Object.entries(edge.metadata).map(([k, v]) => (
                      <div key={k} className="p-3">
                        <span className={`text-[10px] uppercase tracking-wider ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>{k.replace(/_/g, ' ')}</span>
                        <p className={`text-sm ${isDark ? 'text-slate-200' : 'text-slate-700'}`}>{String(v)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Analysis Note */}
            <div className={`p-4 rounded-2xl border ${isDark ? 'bg-blue-900/10 border-blue-800/30 text-blue-300' : 'bg-blue-50 border-blue-200 text-blue-700'}`}>
              <div className="flex gap-3">
                <Activity className="w-4 h-4 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-xs font-bold leading-none">Permission Trace</p>
                  <p className="text-[10px] leading-relaxed opacity-80">
                    This edge represents a {edge.relationship} relationship between {sourceLabel} and {targetLabel}. 
                    Attackers can leverage this path to traverse the cluster.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    );
  }

  return null;
}
```

## frontend\src\lib\api.ts

```typescript
import type {
  GraphData,
  BlastRadiusResult,
  ShortestPathResult,
  CycleResult,
  CriticalNodeResult,
  TopCriticalPathResult,
} from './types';

const BASE_URL = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Health check
  health: () => fetchJSON<{ status: string }>('/health'),

  // Get full graph
  getGraph: () => fetchJSON<GraphData>('/graph'),

  // BFS Blast Radius
  blastRadius: (source: string, maxHops: number = 3) =>
    fetchJSON<BlastRadiusResult>('/blast-radius', {
      method: 'POST',
      body: JSON.stringify({ source, max_hops: maxHops }),
    }),

  // Dijkstra Shortest Path
  shortestPath: (source: string, target: string) =>
    fetchJSON<ShortestPathResult>('/shortest-path', {
      method: 'POST',
      body: JSON.stringify({ source, target }),
    }),

  // DFS Cycle Detection
  detectCycles: () => fetchJSON<CycleResult>('/cycles'),

  // Critical Node Analysis
  criticalNode: () => fetchJSON<CriticalNodeResult>('/critical-node'),

  // Top Critical Attack Paths
  topCriticalPaths: (count: number = 3) =>
    fetchJSON<TopCriticalPathResult>(`/top-critical-paths?max_paths=${count}`),

  // Remediate (remove node)
  remediate: (nodeId: string) =>
    fetchJSON<{ removed_node: unknown; updated_graph: GraphData; message: string }>('/remediate', {
      method: 'POST',
      body: JSON.stringify({ node_id: nodeId }),
    }),

  // Reset graph
  reset: () =>
    fetchJSON<{ message: string; graph: GraphData }>('/reset', {
      method: 'POST',
    }),

  // Upload custom graph
  uploadGraph: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Upload error: ${res.status}`);
    }
    return res.json() as Promise<{ message: string; graph: GraphData }>;
  },
};
```

## frontend\src\lib\types.ts

```typescript
// ─── Node Types ───────────────────────────────
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  namespace: string;
  risk_level: string;
  metadata: NodeMetadata;
  // Force graph properties
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface ContainerInfo {
  name: string;
  image: string;
  ports: number[];
  cves: string[];
  score?: number;
}

export interface NodeMetadata {
  description?: string;
  image?: string;
  cves?: string[];
  cvss_scores?: number[];
  ports?: number[];
  labels?: Record<string, string>;
  icon?: string;
  version?: string;
  secret_type?: string;
  keys?: string[];
  engine?: string;
  data_classification?: string;
  records?: string;
  automount_token?: boolean;
  binding_type?: string;
  rules?: string[];
  service_type?: string;
  enforcement?: string;
  containers?: ContainerInfo[];
  uid?: string;
  name?: string;
  [key: string]: unknown;
}

// ─── Edge Types ───────────────────────────────
export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  weight: number;
  metadata: Record<string, unknown>;
}

// ─── Graph Data ───────────────────────────────
export interface GraphData {
  nodes: GraphNode[];
  links: GraphEdge[];
  metadata: {
    cluster_name?: string;
    scan_timestamp?: string;
    scenario?: string;
    description?: string;
  };
  stats: {
    total_nodes: number;
    total_edges: number;
    crown_jewels: number;
    critical_nodes: number;
  };
}

// ─── Algorithm Results ────────────────────────
export interface BlastRadiusResult {
  source: string;
  max_hops: number;
  affected_nodes: (GraphNode & { hop_distance: number })[];
  affected_edges: GraphEdge[];
  total_affected: number;
  crown_jewels_reached: number;
  crown_jewel_names: string[];
  risk_summary: string;
}

export interface ShortestPathResult {
  source: string;
  target: string;
  path: string[];
  path_details: PathStep[];
  total_weight: number;
  hop_count: number;
  difficulty: string;
  path_exists: boolean;
  kill_chain_summary: KillChainStep[];
  error?: string;
}

export interface PathStep {
  step: number;
  node_id: string;
  label: string;
  type: string;
  namespace: string;
  risk_level: string;
  metadata: NodeMetadata;
  edge_to_next?: {
    target: string;
    relationship: string;
    weight: number;
    metadata: Record<string, unknown>;
  };
}

export interface KillChainStep {
  step: number;
  action: string;
  node: string;
  node_type: string;
  risk_level: string;
  cves_exploited: string[];
  edge_info: string;
}

export interface CycleResult {
  total_cycles: number;
  cycles: CycleDetail[];
  has_cycles: boolean;
  risk_summary: string;
}

export interface CycleDetail {
  cycle: string[];
  cycle_nodes: GraphNode[];
  length: number;
  total_weight: number;
  risk: string;
  description: string;
}

export interface TopCriticalPath {
  rank: number;
  source: string;
  target: string;
  path: string[];
  path_details: PathStep[];
  total_weight: number;
  hop_count: number;
  difficulty: string;
  description: string;
  mitigation_suggestions: string[];
  vulnerabilities_found: number;
  risk_factors: string[];
  criticality_score: number;
}

export interface TopCriticalPathResult {
  total_paths_found: number;
  top_critical_paths: TopCriticalPath[];
  entry_points_count: number;
  crown_jewels_count: number;
  summary: string;
  error?: string;
}

export interface CriticalNodeResult {
  critical_node: CriticalNodeInfo | null;
  top_5_nodes: CriticalNodeInfo[];
  baseline_paths: number;
  entry_points: string[];
  crown_jewels: string[];
  betweenness_centrality: Record<string, number>;
  recommendation: string;
}

export interface CriticalNodeInfo {
  node_id: string;
  label: string;
  type: string;
  namespace: string;
  risk_level: string;
  paths_broken: number;
  paths_remaining: number;
  impact_percentage: number;
  metadata: NodeMetadata;
}

// ─── UI State ─────────────────────────────────
export type AnalysisMode = 
  | 'none' 
  | 'blast-radius' 
  | 'shortest-path' 
  | 'cycles' 
  | 'critical-node' 
  | 'top-critical-paths'
  | 'group-critical' 
  | 'group-crown-jewel' 
  | 'group-entry-point' 
  | 'group-standard' 
  | 'group-low';

export interface HighlightState {
  nodes: Set<string>;
  edges: Set<string>;
  path: string[];
  mode: AnalysisMode;
}
```

## frontend\src\lib\utils.ts

```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

