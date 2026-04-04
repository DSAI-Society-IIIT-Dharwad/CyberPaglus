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
