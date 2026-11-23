export interface TicketInput {
  subject: string;
  body: string;
  account_id?: string;
}

export interface ClassificationResult {
  category: string;
  urgency: string;
  product_area: string;
  sentiment: string;
  confidence: number;
}

export interface GroundingChunk {
  doc_id: string;
  heading: string;
  similarity_score: number;
  content: string;
}

export interface TriageResult {
  ticket_id?: string;
  classification: ClassificationResult;
  grounding: {
    matched_articles: string[];
    retrieved_chunks: GroundingChunk[];
  };
  draft_response: {
    reply_text: string;
    confidence: number;
    hallucination_risk: string;
    citations: string[];
  };
  routing: {
    assigned_team: string;
    priority: "P1" | "P2" | "P3" | "P4";
    escalation_required: boolean;
    routing_reason: string;
  };
}

export interface ChurnSignal {
  name: string;
  severity: "low" | "medium" | "high" | "critical";
  metric_value: string | number;
  trigger_reason: string;
}

export interface AccountBrief {
  account_id: string;
  company_name: string;
  risk_level: "Healthy" | "Low" | "Medium" | "High" | "Critical";
  churn_signals: ChurnSignal[];
  executive_summary: string;
  recommended_actions: string[];
  linked_tickets_digest?: {
    total_tickets: number;
    open_tickets: number;
    p1_count: number;
  };
}

/** Read-only synthetic support records powering the operations console. */
export interface SupportTicket {
  ticket_id: string;
  account_id?: string;
  company: string;
  subject: string;
  body: string;
  product: string;
  product_area: string;
  category: string;
  urgency: "P1" | "P2" | "P3" | "P4";
  status: "Open" | "In Progress" | "Pending Customer" | "Resolved" | "Closed";
  assigned_agent: string;
  created_at: string;
  updated_at: string;
  channel: string;
  tags: string[];
  plan_tier: string;
}

export interface SupportAccount {
  account_id: string;
  company: string;
  tam: string;
  plan_tier: string;
  health_status: string;
  usage_trend: string;
  open_tickets: number;
  arr_usd: number;
  renewal_date: string;
  risk_level: "Low" | "Medium" | "High";
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface OperationsSummary {
  source: "synthetic_dataset";
  total_tickets: number;
  active_tickets: number;
  critical_active: number;
  total_accounts: number;
  high_risk_accounts: number;
  priority_counts: Record<"P1" | "P2" | "P3" | "P4", number>;
  status_counts: Record<string, number>;
  monthly_volume: Array<{ month: string; tickets: number }>;
}
