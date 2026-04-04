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
