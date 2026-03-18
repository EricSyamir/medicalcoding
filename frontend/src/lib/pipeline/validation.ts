import type {
  DiagnosisCode,
  ProcedureCode,
  CodingWarning,
  ReviewPriority,
} from "@/types/review";

export interface ValidationResult {
  warnings:             CodingWarning[];
  requiresHumanReview:  boolean;
  reviewPriority:       ReviewPriority;
}

const HIGH_RISK_PREFIXES = ["C", "I2", "I6", "J96", "N17", "K57", "S", "T"];

function isHighRisk(code: string): boolean {
  return HIGH_RISK_PREFIXES.some((p) => code.startsWith(p));
}

export function validate(
  diagnosisCodes: DiagnosisCode[],
  procedureCodes: ProcedureCode[],
): ValidationResult {
  const warnings: CodingWarning[] = [];

  // 1. No primary diagnosis
  if (!diagnosisCodes.some((d) => d.is_primary)) {
    warnings.push({
      type:          "missing_info",
      severity:      "error",
      message:       "No primary diagnosis code assigned. A principal diagnosis is required.",
      related_codes: [],
    });
  }

  // 2. Multiple primary diagnoses
  const primaries = diagnosisCodes.filter((d) => d.is_primary);
  if (primaries.length > 1) {
    warnings.push({
      type:          "conflict",
      severity:      "error",
      message:       `Multiple primary diagnoses flagged: ${primaries.map((d) => d.code).join(", ")}. Only one is allowed.`,
      related_codes: primaries.map((d) => d.code),
    });
  }

  // 3. Low-confidence codes
  const lowDx  = diagnosisCodes.filter((d) => d.confidence_score < 0.5);
  const lowCpt = procedureCodes.filter( (p) => p.confidence_score < 0.5);
  if (lowDx.length > 0) {
    warnings.push({
      type:          "ambiguity",
      severity:      "warning",
      message:       `Low-confidence diagnosis codes require verification: ${lowDx.map((d) => d.code).join(", ")}`,
      related_codes: lowDx.map((d) => d.code),
    });
  }
  if (lowCpt.length > 0) {
    warnings.push({
      type:          "ambiguity",
      severity:      "warning",
      message:       `Low-confidence procedure codes require verification: ${lowCpt.map((p) => p.code).join(", ")}`,
      related_codes: lowCpt.map((p) => p.code),
    });
  }

  // 4. No procedures when diagnoses suggest active treatment
  if (diagnosisCodes.length > 0 && procedureCodes.length === 0) {
    warnings.push({
      type:          "missing_info",
      severity:      "info",
      message:       "No procedure codes identified. Verify that all performed procedures are documented.",
      related_codes: [],
    });
  }

  // 5. High-risk codes
  const riskyCodes = [...diagnosisCodes, ...procedureCodes].filter((c) => isHighRisk(c.code));
  if (riskyCodes.length > 0) {
    warnings.push({
      type:          "documentation_gap",
      severity:      "warning",
      message:       `High-risk codes detected — ensure documentation is complete and specificity is maximised: ${riskyCodes.map((c) => c.code).join(", ")}`,
      related_codes: riskyCodes.map((c) => c.code),
    });
  }

  // 6. Empty evidence
  const noEvidence = [
    ...diagnosisCodes.filter((d) => d.evidence.length === 0),
    ...procedureCodes.filter( (p) => p.evidence.length === 0),
  ];
  if (noEvidence.length > 0) {
    warnings.push({
      type:          "documentation_gap",
      severity:      "info",
      message:       `Codes with no supporting evidence: ${noEvidence.map((c) => c.code).join(", ")}`,
      related_codes: noEvidence.map((c) => c.code),
    });
  }

  // Determine priority
  const hasErrors   = warnings.some((w) => w.severity === "error");
  const hasWarnings = warnings.some((w) => w.severity === "warning");

  const requiresHumanReview = warnings.length > 0;
  const reviewPriority: ReviewPriority =
    hasErrors   ? "urgent" :
    hasWarnings ? "normal" : "low";

  return { warnings, requiresHumanReview, reviewPriority };
}
