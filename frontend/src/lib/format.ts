import type { CaseStatus, DocType, Severity } from "../api/types";

export const STATUS_LABEL: Record<CaseStatus, string> = {
  received: "Received",
  processing: "Running checks",
  needs_review: "Needs review",
  clarification_requested: "Waiting on applicant",
  approved: "Approved",
  rejected: "Rejected",
  processing_failed: "Checks failed",
};

export const DOC_LABEL: Record<DocType, string> = {
  APPLICATION_FORM: "Application Form",
  INSTITUTION_AUTHORIZATION_LETTER: "Authorization Letter",
  ENROLMENT_OR_IDENTITY_PROOF: "Enrolment Proof",
  EOA_APPLICATION_FORM: "AICTE EoA Application Form",
  UNIVERSITY_AFFILIATION_ORDER: "University Affiliation Order",
  FIRE_SAFETY_CERTIFICATE: "Fire Safety Certificate",
  BUILDING_SAFETY_CERTIFICATE: "Building Safety Certificate",
  LAND_DOCUMENT_AND_USE_CERTIFICATE: "Land Document & Land Use Certificate",
  OCCUPANCY_CERTIFICATE: "Occupancy / Completion Certificate",
};

export const SEVERITY_ORDER: Severity[] = ["high", "medium", "low", "info"];

export function when(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function ago(iso: string): string {
  const s = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return `${Math.floor(s / 86400)} d ago`;
}

export function bytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export function humanize(code: string): string {
  const s = code.replace(/[_.]/g, " ").toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
}
