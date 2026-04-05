# Walkthrough: KubeInsights "Unbeatable" Features Guide

This guide covers the advanced features added to elevate KubeInsights into a comprehensive security product. Use this as a reference for your hackathon presentation.

---

## 🛡️ 1. Real-Time Security Health HUD
The header now tracks the global security posture of the cluster.
- **Where to find it**: The circular gauge in the dashboard header.
- **How to use**:
    1. Observe the current score (e.g., 5% "Critical" or 85% "Optimized").
    2. Perform a "Remediation" by clicking any node and selecting **Analyze Blast Radius**.
    3. Click **Remediate Risk** to simulate the removal of the threat.
    4. **Watch the score bounce back up** in real-time as the risk is removed.

---

## 🤖 2. AI Remediation & CLI Fixes
Get expert advice and the exact commands needed to fix vulnerabilities.
- **Where to find it**: Node Security Sidebar (right-hand side).
- **How to use**:
    1. Click on a **Critical Node** (Red icon) or a **Crown Jewel** (Blue Shield).
    2. Click the **Ask AI Advisor** button.
    3. The AI (Gemini 1.5 Flash) will generate a structured response:
        - **Risk Summary**: What's actually wrong.
        - **Remediation**: Strategic steps.
        - **CLI Fix**: The exact `kubectl` command to fix it.
    4. Click the **Copy CLI Fix Command** button to copy it instantly.

---

## 🕵️ 3. Advanced Attack Path Analysis
Identify how an attacker could move from a public entry point to your most sensitive data.
- **Where to find it**: Left-hand **ANALYSIS TOOLS** panel.
- **How to use**:
    1. **Attack Path (Dijkstra)**: Select a starting node (Source) and a target node (Sink). Click **Find Shortest Path**. The UI will draw the most efficient exploit path.
    2. **Cycle Detection (DFS)**: Click **Find Permission Cycles**. This identifies circular RBAC relationships (e.g., ServiceAccount A can manage B, which can manage A), which are high-risk loops for privilege escalation.

---

## ⏳ 4. Temporal Analysis (Infrastructure Drift)
Track how the security of your cluster has changed over time.
- **Where to find it**: The **Clock Icon** next to the "Analysis Tools" header.
- **How to use**:
    1. Click the clock icon to open the **Temporal Dashboard**.
    2. Click **Save New Snapshot**.
    3. Manually edit or upload a different cluster graph.
    4. Open the Temporal Dashboard again and select the old and new snapshots.
    5. Click **Compare Snapshots** to see exactly which risks were added or removed between versions.

---

## 💻 5. The Hardened CLI
A robust, Unicode-safe tool for security engineers.
- **Usage**:
    ```bash
    cd backend
    python cli.py analyze --input mock-cluster-graph.json --full-report
    ```
- **Key Feature**: I have implemented a `safe_print` and `io.TextIOWrapper` override. Even if the terminal doesn't support modern symbols, the CLI will **never crash** and will automatically fall back to ASCII characters.

---

## 💡 Hackathon Demo Script Tip:
> "We identified that visualizers often overwhelm users with data. That's why we added the **Actionable Intelligence Layer**. Notice how we don't just show a risk—we provide the exact `kubectl patch` command to fix it. Our **Security HUD** gives C-level executives a high-level view, while the **Temporal Dashboard** allows DevOps teams to detect 'Security Drift' during CI/CD."

**Good luck with your final demonstration!** 🏁
