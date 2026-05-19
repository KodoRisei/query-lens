export type Severity = "critical" | "warning" | "info";
export type FindingCategory = "performance" | "correctness" | "security" | "style";
export type ReviewMode = "junior" | "senior" | "performance";

export interface StaticFinding {
  rule_id: string;
  severity: Severity;
  category: FindingCategory;
  title: string;
  message: string;
  suggestion: string | null;
  line: number | null;
  column: number | null;
}

export interface StaticAnalysis {
  findings: StaticFinding[];
  query_type: string;
  dialect: string;
  table_references: string[];
  critical_count: number;
  warning_count: number;
  info_count: number;
}

export interface PlanFinding {
  rule_id: string;
  node_type: string;
  severity: Severity;
  category: FindingCategory;
  title: string;
  message: string;
  suggestion: string | null;
  relation_name: string | null;
}

export interface ExecutionPlan {
  findings: PlanFinding[];
  execution_time_ms: number | null;
  planning_time_ms: number | null;
  has_analyze_data: boolean;
}

export interface AiFinding {
  rule_id: string;
  explanation: string;
  suggestion: string;
}

export interface AiReview {
  summary: string;
  findings: AiFinding[];
  improved_query: string | null;
  educational_note: string | null;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
}

export interface QueryReview {
  id: string;
  sql: string;
  dialect: string;
  review_mode: ReviewMode;
  static_analysis: StaticAnalysis;
  execution_plan: ExecutionPlan | null;
  ai_review: AiReview;
  created_at: string;
}

export interface ReviewRequest {
  sql: string;
  dialect?: string;
  review_mode?: ReviewMode;
  provider?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
}
