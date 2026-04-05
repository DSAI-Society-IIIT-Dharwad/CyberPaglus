// ─── Node Types ───────────────────────────────
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  namespace: string;
  risk_level: string;
  mitre_tactics?: string[];
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
export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  crown_jewels: number;
  critical_nodes: number;
  security_score: number; // 0-100
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphEdge[];
  metadata: {
    cluster?: string;
    cluster_name?: string;
    version?: string;
    timestamp?: string;
    scenario?: string;
    description?: string;
  };
  stats: GraphStats;
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

export interface SnapshotMetadata {
  filename: string;
  filepath: string;
  timestamp: string;
  label: string;
  node_count: number;
  edge_count: number;
}

export interface DiffRiskChange {
  node_id: string;
  label: string;
  old_risk: string;
  new_risk: string;
  escalation: boolean;
}

export interface TemporalDiffResult {
  has_changes: boolean;
  has_new_threats: boolean;
  summary: {
    nodes_added: number;
    nodes_removed: number;
    edges_added: number;
    edges_removed: number;
    risk_changes: number;
    new_attack_paths: number;
  };
  added_nodes: GraphNode[];
  removed_nodes: GraphNode[];
  added_edges: GraphEdge[];
  removed_edges: GraphEdge[];
  risk_changes: DiffRiskChange[];
  new_attack_paths: TopCriticalPath[];
  old_timestamp: string;
  new_timestamp: string;
}
