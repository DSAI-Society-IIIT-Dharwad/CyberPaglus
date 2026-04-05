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
        req = urllib.request.Request(url, headers={"User-Agent": "KubeInsights/1.0"})
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
