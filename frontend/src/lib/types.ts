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