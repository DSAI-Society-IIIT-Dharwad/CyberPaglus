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
