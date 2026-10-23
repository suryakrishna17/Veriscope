export type Role = "applicant" | "reviewer" | "admin";
export type CaseStatus =
  | "received" | "processing" | "needs_review" | "clarification_requested"
  | "approved" | "rejected" | "processing_failed";
export type Severity = "high" | "medium" | "low" | "info";
export type TrustLabel = "ISSUER_VERIFIED" | "ANOMALY_DETECTED" | "NOT_VERIFIED";
export type DocType = "APPLICATION_FORM" | "INSTITUTION_AUTHORIZATION_LETTER" | "ENROLMENT_OR_IDENTITY_PROOF";
export type BBox = [number, number, number, number];

export interface User { id: string; email: string; name: string; role: Role }

export interface TriageComponent { label: string; points: number }

export interface CaseSummary {
  id: string;
  case_ref: string;
  application_type: string;
  application_type_label: string;
  applicant_ref: string;
  institution_ref: string;
  status: CaseStatus;
  triage_priority: number;
  triage_components: TriageComponent[];
  open_findings: Record<Severity, number>;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface PageInfo { page_number: number; width: number; height: number; text_source: "pdf_text" | "ocr"; mean_confidence: number | null }

export interface IssuerCheck { label: TrustLabel; issuer: string | null; response_id: string | null; checked_at: string; reason: string; simulated: boolean }

export interface DocumentInfo {
  id: string;
  doc_type: DocType;
  original_name: string;
  mime_type: string;
  size_bytes: number;
  sha256: string;
  uploaded_at: string;
  page_count: number;
  processing_status: "pending" | "processing" | "processed" | "failed";
  processing_error: string | null;
  trust_label: TrustLabel;
  issuer_check: IssuerCheck | null;
  signals: { quality?: { ocr_used?: boolean; min_ocr_confidence?: number | null }; metadata?: { notes?: string[] } };
  pages: PageInfo[];
}

export interface Field {
  id: string;
  document_id: string;
  doc_type: DocType;
  field_key: string;
  label: string;
  raw_value: string | null;
  normalized_value: string | null;
  effective_value: string | null;
  confidence: number;
  page_number: number | null;
  evidence_excerpt: string | null;
  bbox: BBox | null;
  source: "pdf_text" | "ocr" | "visual" | "llm_suggestion";
  corrected_value: string | null;
  corrected_by: string | null;
  corrected_at: string | null;
  correction_reason: string | null;
}

export interface EvidenceRef {
  document_id: string;
  doc_type?: DocType;
  field_key?: string;
  field_id?: string;
  page: number | null;
  bbox?: BBox | null;
  excerpt?: string | null;
  value?: string | null;
}

export interface Finding {
  id: string;
  rule_id: string;
  rule_version: string;
  category: string;
  severity: Severity;
  status: "open" | "resolved" | "waived";
  trust_label: TrustLabel;
  summary: string;
  detail: string;
  evidence_refs: EvidenceRef[];
  confidence: number;
  next_action: string | null;
  resolution_note: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface Decision { id: string; outcome: "approve" | "request_clarification" | "reject"; reason_code: string; note: string; reviewer: string; decided_at: string }

export interface AuditEvent { id: string; action: string; actor: string; actor_role: string; entity_type: string; entity_id: string | null; payload: Record<string, unknown>; created_at: string }

export interface Job { id: string; case_id: string; kind: string; status: "queued" | "running" | "succeeded" | "failed"; progress: number; error_code: string | null; error_message: string | null }

export interface CaseDetail extends CaseSummary {
  rule_set_version: string;
  documents: DocumentInfo[];
  fields: Field[];
  findings: Finding[];
  decisions: Decision[];
  summary: { kind: "template" | "llm"; text: string; missing_evidence: string[]; provider: string; generated_at: string } | null;
  audit: AuditEvent[];
  allowed_actions: string[];
  ruleset: { name: string; version: string; is_provisional: boolean };
  latest_job: Job | null;
}

export interface Meta {
  application_types: { id: string; label: string }[];
  doc_types: { id: DocType; label: string }[];
  reason_codes: Record<"approve" | "request_clarification" | "reject", string[]>;
  max_upload_mb: number;
  max_pages: number;
  ai_provider: string;
  issuer_verifier: string;
}

export interface Paged<T> { items: T[]; total: number; page: number; page_size: number }
