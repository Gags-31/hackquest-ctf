export interface EntityField {
  name: string;
  type: string;
  primary_key?: boolean;
  unique?: boolean;
  nullable?: boolean;
  ref?: string;
  ref_table?: string;
  default?: unknown;
}

export interface Entity {
  name: string;
  table: string;
  description: string;
  fields: EntityField[];
}

export interface Specification {
  name: string;
  app_type: string;
  domain: string;
  summary: string;
  users: string[];
  features: string[];
  entities: Entity[];
  security: {
    authentication: string;
    authorization: string;
    roles: string[];
    oauth_provider?: string;
  };
  non_functional: Record<string, string>;
}

export interface Architecture {
  style: string;
  rationale: string;
  components: { name: string; kind: string; description: string }[];
  layers: { name: string; technology: string; responsibility: string }[];
  communication: string;
  diagram: string;
  deployment_topology: string;
}

export interface DatabaseSchema {
  entities: Entity[];
  relationships: { from: string; to: string; type: string; field: string; description: string }[];
  sql: string;
  er_diagram: string;
  indexes: string[];
}

export interface ApiContract {
  openapi: Record<string, unknown>;
  endpoints: { method: string; path: string; summary: string; resource: string }[];
}

export interface UiDesign {
  pages: { name: string; path: string; public: boolean; description: string; components: string[] }[];
  shared_components: string[];
  navigation: string[];
  style: Record<string, string>;
}

export interface TestResult {
  ok: boolean | null;
  passed?: number;
  failed?: number;
  output?: string;
}

export interface Tests {
  files: string[];
  traceability: { requirement: string; test_file: string }[];
  result: TestResult;
  passed: boolean;
}

export interface SecurityReport {
  score: number;
  grade: string;
  checks_passed: string[];
  findings: { severity: string; category: string; detail: string; fix: string }[];
  summary: string;
}

export interface ValidationStage {
  status: string;
  detail: string;
}

export interface Validation {
  ok: boolean;
  iterations: number;
  history: {
    iteration: number;
    report: { ok: boolean; stages: Record<string, ValidationStage> };
  }[];
}

export interface ImpactAnalysis {
  change_request: string;
  intent: string;
  affected: Record<string, string[]>;
  risk: string;
  safe: boolean;
}

export interface Modification {
  instruction: string;
  analysis: { intent: string; new_entities: string[]; removed_entities: string[]; new_features: string[] };
  affected: Record<string, string[]>;
}

export interface Project {
  id: string;
  name: string;
  requirement: string;
  mode: string;
  status: string;
  created_at: number;
  specification: Specification;
  architecture: Architecture;
  tech_stack: Record<string, Record<string, string> | string>;
  database_schema: DatabaseSchema;
  api_contract: ApiContract;
  ui_design: UiDesign;
  file_structure: string[];
  dependencies: Record<string, string[]>;
  tests: Tests;
  validation: Validation;
  security: SecurityReport;
  documentation: Record<string, string>;
  deployment: { files: string[]; targets: string[]; status: string };
  known_issues: string[];
  modifications: Modification[];
  impact_analyses: ImpactAnalysis[];
}

export interface ProjectSummary {
  id: string;
  name: string;
  status: string;
  app_type: string;
  created_at: number;
  requirement: string;
}

export interface PipelineEvent {
  project_id: string;
  agent: string;
  stage: string;
  status: "started" | "thinking" | "finished" | "failed" | "info";
  message: string;
  detail: Record<string, unknown>;
  ts: number;
}

export interface ServerConfig {
  llm_provider: string;
  llm_model: string;
  llm_online: boolean;
  max_debug_iterations: number;
}

export interface PreviewInfo {
  running: boolean;
  url?: string;
  docs?: string;
  health?: string;
  port?: number;
  uptime_seconds?: number;
}
