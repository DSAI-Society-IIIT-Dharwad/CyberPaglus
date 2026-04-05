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

  // ─── Temporal Analysis ────────────────────────

  saveSnapshot: (label: string = '') =>
    fetchJSON<{ message: string; filepath: string }>('/snapshots/save', {
      method: 'POST',
      body: JSON.stringify({ label }),
    }),

  listSnapshots: () =>
    fetchJSON<{ snapshots: import('./types').SnapshotMetadata[] }>('/snapshots'),

  diffSnapshot: (filepath: string) =>
    fetchJSON<import('./types').TemporalDiffResult>(`/snapshots/diff?filepath=${encodeURIComponent(filepath)}`),
};
