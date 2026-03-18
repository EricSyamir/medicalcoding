export type ConfidenceLevel = "high" | "medium" | "low";
export type WarningSeverity  = "error" | "warning" | "info";
export type WarningType =
  | "missing_info"
  | "ambiguity"
  | "conflict"
  | "documentation_gap"
  | "specificity";
export type ReviewPriority = "urgent" | "normal" | "low";

export interface EvidenceReference {
  quote:     string;
  rationale: string;
}

export interface DiagnosisCode {
  code:              string;
  description:       string;
  confidence_score:  number;
  confidence_level:  ConfidenceLevel;
  is_primary:        boolean;
  evidence:          EvidenceReference[];
  reviewer_override: string | null;
}

export interface ProcedureCode {
  code:              string;
  description:       string;
  confidence_score:  number;
  confidence_level:  ConfidenceLevel;
  evidence:          EvidenceReference[];
  reviewer_override: string | null;
}

export interface CodingWarning {
  type:          WarningType;
  severity:      WarningSeverity;
  message:       string;
  related_codes: string[];
}

export interface ExtractedFacts {
  chief_complaint:      string | null;
  diagnoses_mentioned:  string[];
  symptoms_signs:       string[];
  procedures_mentioned: string[];
  medications:          string[];
  lab_imaging_results:  string[];
  relevant_history:     string[];
  supporting_quotes:    string[];
}

export interface ReviewPayload {
  note_id:              string;
  processed_at:         string;
  note_word_count:      number;
  extracted_facts:      ExtractedFacts;
  diagnosis_codes:      DiagnosisCode[];
  procedure_codes:      ProcedureCode[];
  warnings:             CodingWarning[];
  requires_human_review: boolean;
  review_priority:      ReviewPriority;
  reviewer_notes:       string | null;
  reviewed_by:          string | null;
  reviewed_at:          string | null;
  pipeline_version:     string;
  model_used:           string;
  audit_trail:          string[];
}
