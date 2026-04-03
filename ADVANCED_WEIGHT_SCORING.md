# Advanced Edge Weight Scoring Guide

## Overview

The new `AdvancedWeightScorer` replaces simple CVSS-based edge weights (0-10 scale) with a **5-parameter multi-factor** scoring system that provides more nuanced attack path difficulty calculations.

## The 5 Scoring Parameters

### 1. **Asset Criticality** (25% weight)
Measures the **target node's intrinsic security level** and CVE exposure.

**Factors:**
- Node risk level: `entry-point` (1.0) → `low` (2.0) → `medium` (4.0) → `high` (5.0) → `critical` (6.0) → `crown-jewel` (7.0)
- CVE presence: Higher CVSS scores make targets **easier** to compromise (score adjusted downward)

**Example:**
```json
{
  "id": "ingress-nginx",
  "risk_level": "medium",
  "metadata": {
    "cves": ["CVE-2024-7646"],
    "cvss_scores": [8.8]
  }
}
```
→ Easier to exploit (lower criticality score) due to CVE 8.8

---

### 2. **Privilege Escalation Potential** (25% weight)
Measures **how much access/privilege is gained** by traversing the edge.

**High Escalation Paths (scores 0.8-1.5):**
- Pod → ServiceAccount (token theft)
- Secret → Database (credential extraction)
- Secret → External system (AWS, cloud access)

**Medium Escalation (scores 2.0-2.5):**
- Pod → Pod (lateral movement)
- Service → Pod (sideband access)

**Low Escalation (scores 3.5+):**
- Pod ↔ Pod (same-privilege movement)

**Modifiers:**
- `can_access` relationship: ×0.7 (direct access = easier escalation)
- `bound_by` relationship: ×0.8 (RBAC binding = high escalation)
- Lateral movement: ×1.2 (harder)

**Example:**
```json
{
  "source": "tesla-dashboard-pod",
  "target": "dashboard-sa",
  "relationship": "uses_service_account",
  "description": "Pod mounts privileged token"
}
```
→ Score: 1.5 (HIGH escalation = easy path)

---

### 3. **Network Reachability** (20% weight)
Measures **how isolated the target is** and **network layer protection**.

**Isolation Levels (base scores):**
- Internet/Ingress: 0.5-1.0 (most reachable)
- Pod: 2.0 (container isolation)
- Service: 1.5 (load-balanced)
- Secret/ConfigMap: 2.5 (K8s API access)
- Database: 4.0 (external system)
- Role/ClusterRole: 3.0-3.5 (meta-layer)

**Network Policy Impact:**
- If `network_policy_enforced` = true → ×1.5 (harder to reach)
- Same namespace: ×0.8 (easier lateral movement)
- Cross-namespace: ×1.2 (harder)

**Example:**
```json
{
  "id": "api-server-pod",
  "namespace": "production",
  "metadata": {
    "network_policy_enforced": true
  }
}
```
→ With network policy = harder to reach

---

### 4. **RBAC Permission Restrictions** (20% weight)
Measures **how restrictive permissions need to be** to access this resource.

**Permission Restrictiveness (base scores):**
- Secret: 1.5 (high restriction)
- Role/ConfigMap: 1.5-2.0 (namespace scope)
- Pod: 2.0
- Service: 2.5
- ClusterRole: 1.2 (lower = more permissive patterns)

**Permission Modifiers:**
- Wildcard rules (`*`): ×0.7 (less restrictive = easier)
- `automount_token = true`: ×0.6 (automatic mounting = easier access)

**Example:**
```json
{
  "id": "cluster-admin-role",
  "metadata": {
    "rules": ["*.*:*"],  // Wildcard = very permissive
    "automount_token": true
  }
}
```
→ Much lower score (easier access due to wildcards and automounting)

---

### 5. **Blast Radius** (10% weight)
Measures **downstream impact** if this node is compromised.

**Direct Blast Radius (by risk level):**
- `entry-point`: 2.0 (reaches many nodes)
- `low`: 1.0 (limited impact)
- `medium`: 1.5
- `high`: 2.5 (critical impact)
- `critical`: 3.5
- `crown-jewel`: 4.0 (maximum impact)

**Downstream Bonus:**
- If graph context available: `+0.2 per outbound edge`

**Example:**
```json
{
  "id": "cluster-admin-role",
  "risk_level": "critical",
  "outbound_edges": ["aws-cred-secret", "db-credentials-secret", "api-server-pod"]
}
```
→ Higher blast radius due to multiple downstream targets

---

## Weight Scale (0.1 - 10.0)

**Difficulty Ratings:**
| Weight | Difficulty | Meaning |
|--------|------------|---------|
| < 1.0 | **TRIVIAL** | Extremely easy to exploit |
| 1.0-2.0 | **EASY** | Straightforward attack path |
| 2.0-4.0 | **MODERATE** | Requires multi-step exploitation |
| 4.0-6.0 | **HARD** | Significant security controls in place |
| > 6.0 | **VERY HARD** | Heavily protected, unlikely to succeed |

---

## Usage in Code

### 1. Automatic Recalculation (Python)
```python
from graph_engine import K8sGraphEngine

engine = K8sGraphEngine("mock-cluster-graph.json")

# Recalculate all edge weights
result = engine.recalculate_edge_weights_advanced(include_details=False)
print(f"Updated {result['edges_updated']} edges")

# Get detailed breakdown
detailed_result = engine.recalculate_edge_weights_advanced(include_details=True)
for report in detailed_result['weight_reports']:
    print(f"{report['edge']}: {report['final_weight']} ({report['difficulty_rating']})")
```

### 2. Via REST API
```bash
# Recalculate weights without details
POST /api/recalculate-weights

# Recalculate with detailed component breakdown
POST /api/recalculate-weights?include_details=true
```

**Response:**
```json
{
  "status": "success",
  "recalculation": {
    "edges_updated": 24,
    "factors": [
      "Asset Criticality (25%)",
      "Privilege Escalation (25%)",
      "Network Reachability (20%)",
      "RBAC Restrictions (20%)",
      "Blast Radius (10%)"
    ],
    "weight_reports": [
      {
        "edge": "ingress-nginx -> tesla-dashboard-pod",
        "relationship": "forwards_to",
        "component_scores": {
          "asset_criticality": 3.2,
          "privilege_escalation": 2.0,
          "network_reachability": 1.5,
          "rbac_restrictions": 1.8,
          "blast_radius": 2.5
        },
        "final_weight": 2.15,
        "difficulty_rating": "EASY"
      }
    ]
  },
  "graph": { /* full updated graph */ }
}
```

### 3. Single Edge Calculation (Python)
```python
from advanced_weight_scorer import AdvancedWeightScorer

source = engine.graph.nodes["tesla-dashboard-pod"]
target = engine.graph.nodes["dashboard-sa"]

weight = AdvancedWeightScorer.calculate_edge_weight(
    source, target, "uses_service_account"
)
print(f"Edge weight: {weight}")

# Detailed breakdown
report = AdvancedWeightScorer.generate_weight_report(
    source, target, "uses_service_account"
)
print(report)
```

---

## Example Scoring Scenarios

### Scenario A: Highly Protected Secret
```
Node: db-credentials-secret
- risk_level: crown-jewel
- namespace: production
- metadata.rules: ["secrets:get (production)"]  # Restricted to prod namespace
- metadata.network_policy_enforced: true

Asset Criticality: 7.0 (crown-jewel)
- CVSS impact: 0 (no CVEs)
- Final: 7.0

RBAC Restrictions: 1.5 (secrets are restricted)
- No wildcards (specific rules)
- automount: false
- Final: 1.5

Result: HIGH difficulty path (weight ~4.0-5.0)
```

### Scenario B: Vulnerable, Exposed Pod
```
Node: tesla-dashboard-pod
- risk_level: critical
- cves: [CVE-2018-18264, CVE-2023-49797]
- cvss_scores: [7.5, 8.1]  <- Average: 7.8
- exposed: true

Asset Criticality: 6.0 (critical)
- CVSS reduction: 6.0 × (1 - 7.8/20) = 3.66
- Final: 3.66 (MUCH LOWER due to CVEs)

Network Reachability: 1.5 (exposed, reachable)
- No network policy

Result: LOW difficulty path (weight ~2.0-2.5)
```

### Scenario C: Restrictive API Secret
```
Edge: api-server-pod -> db-credentials-secret
Relationship: can_access

Asset Criticality: 5.0 (high risk)
Privilege Escalation: 2.0 × 0.7 = 1.4 (direct access modifier)
Network Reachability: 2.5 (K8s secret API)
RBAC Restrictions: 2.0 × 0.9 = 1.8 (namespace-scoped, not wildcards)
Blast Radius: 2.0 (database impact)

Weighted Composite:
= 5.0 × 0.25 + 1.4 × 0.25 + 2.5 × 0.20 + 1.8 × 0.20 + 2.0 × 0.10
= 1.25 + 0.35 + 0.50 + 0.36 + 0.20
= 2.66 (MODERATE difficulty)
```

---

## Migration Strategy

### Step 1: Add Metadata to Your Nodes
Enhance nodes with fields the scorer uses:

```json
{
  "id": "my-pod",
  "type": "pod",
  "metadata": {
    "automount_token": true,
    "network_policy_enforced": false,
    "rules": ["secrets:get,list (namespace)"],
    "cves": ["CVE-2024-1234"],
    "cvss_scores": [7.5]
  }
}
```

### Step 2: Call Recalculation
```python
# On load or updates
engine.recalculate_edge_weights_advanced(include_details=True)
```

### Step 3: Review Changes
```python
# See detailed breakdown
result = engine.recalculate_edge_weights_advanced(include_details=True)
for report in result['weight_reports'][:5]:
    print(f"{report['edge']}: {report['old_weight']} → {report['new_weight']}")
```

---

## Customization

To customize the factor weights, edit `FACTOR_WEIGHTS` in `advanced_weight_scorer.py`:

```python
FACTOR_WEIGHTS = {
    "asset_criticality": 0.30,        # Increase criticality weight
    "privilege_escalation": 0.25,
    "network_reachability": 0.15,     # Decrease network weight
    "rbac_restrictions": 0.20,
    "blast_radius": 0.10,
}
```

To adjust specific scoring functions, override methods in `AdvancedWeightScorer`:

```python
@staticmethod
def _score_asset_criticality(node: Dict) -> float:
    # Your custom logic here
    pass
```

---

## Integration with Dijkstra's Shortest Path

The `dijkstra_shortest_path()` algorithm automatically uses the recalculated weights:

```python
# After recalculation
path_result = engine.dijkstra_shortest_path("internet", "prod-database")

# The path will follow the lowest-weight edges
# (considering all 5 parameters, not just CVSS)
print(f"Easiest attack path weight: {path_result['total_weight']}")
```

This means attack paths are now based on **real-world exploitation difficulty**, not just CVE scores!
