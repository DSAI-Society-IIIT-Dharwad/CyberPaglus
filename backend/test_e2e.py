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
