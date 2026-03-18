import { generateJSON } from "./llm";
import type {
  DiagnosisCode,
  ProcedureCode,
  EvidenceReference,
  ConfidenceLevel,
} from "@/types/review";
import type { ExtractedFacts } from "@/types/review";
import type { RetrievedCode } from "./retrieval";

function toLevel(score: number): ConfidenceLevel {
  if (score >= 0.80) return "high";
  if (score >= 0.50) return "medium";
  return "low";
}

function coerce(raw: Record<string, unknown>): DiagnosisCode | ProcedureCode | null {
  const code  = String(raw.code  ?? "").trim();
  const desc  = String(raw.description ?? "").trim();
  const score = Math.min(1, Math.max(0, Number(raw.confidence_score ?? 0)));
  if (!code || !desc) return null;

  const evidence: EvidenceReference[] = ((raw.evidence ?? []) as Record<string, unknown>[]).map((e) => ({
    quote:     String(e.quote     ?? ""),
    rationale: String(e.rationale ?? ""),
  }));

  return {
    code,
    description: desc,
    confidence_score: parseFloat(score.toFixed(2)),
    confidence_level: toLevel(score),
    evidence,
    reviewer_override: null,
  } as DiagnosisCode;
}

const SYSTEM_PROMPT = `You are a certified medical coder (CPC) with deep ICD-10-CM and CPT expertise.

You will receive:
1. The original clinical note.
2. Extracted clinical facts.
3. Candidate ICD-10 diagnosis codes (pre-filtered by retrieval).
4. Candidate CPT procedure codes (pre-filtered by retrieval).

Your task: select the most appropriate codes and return a structured JSON response.

Return ONLY valid JSON in this exact shape:
{
  "diagnosis_codes": [
    {
      "code":             "<ICD-10-CM code from the candidate list>",
      "description":      "<exact description>",
      "confidence_score": <0.0–1.0>,
      "is_primary":       <true for the principal diagnosis, false otherwise>,
      "evidence": [
        { "quote": "<verbatim excerpt <=20 words>", "rationale": "<why this quote supports the code>" }
      ]
    }
  ],
  "procedure_codes": [
    {
      "code":             "<CPT code from the candidate list>",
      "description":      "<exact description>",
      "confidence_score": <0.0–1.0>,
      "evidence": [
        { "quote": "<verbatim excerpt <=20 words>", "rationale": "<why this quote supports the code>" }
      ]
    }
  ]
}

Rules:
- Only use codes from the provided candidate lists.
- Assign exactly ONE primary diagnosis (is_primary: true).
- Provide 1–3 evidence references per code.
- Confidence: 0.9+ = unambiguous documentation; 0.7–0.89 = clear but minor gaps; 0.5–0.69 = probable; <0.5 = uncertain.
- Omit codes with confidence < 0.40.
- Do not include commentary outside the JSON.`;

export async function assignCodes(
  noteText:       string,
  facts:          ExtractedFacts,
  icd10Candidates: RetrievedCode[],
  cptCandidates:   RetrievedCode[],
  provider: string,
  apiKey:   string,
  model:    string,
): Promise<{ diagnosisCodes: DiagnosisCode[]; procedureCodes: ProcedureCode[] }> {
  const userMessage = `Clinical Note:
${noteText}

Extracted Facts:
${JSON.stringify(facts, null, 2)}

ICD-10 Candidates:
${JSON.stringify(icd10Candidates.map((c) => ({ code: c.code, description: c.description, category: c.category })), null, 2)}

CPT Candidates:
${JSON.stringify(cptCandidates.map((c) => ({ code: c.code, description: c.description, category: c.category })), null, 2)}`;

  const data = await generateJSON(provider, apiKey, model, SYSTEM_PROMPT, userMessage);

  const rawDx  = (Array.isArray(data.diagnosis_codes)  ? data.diagnosis_codes  : []) as Record<string, unknown>[];
  const rawCpt = (Array.isArray(data.procedure_codes)   ? data.procedure_codes  : []) as Record<string, unknown>[];

  const diagnosisCodes = rawDx
    .map((r) => {
      const base = coerce(r);
      if (!base) return null;
      return { ...base, is_primary: Boolean(r.is_primary) } as DiagnosisCode;
    })
    .filter(Boolean) as DiagnosisCode[];

  // Ensure exactly one primary
  if (diagnosisCodes.length > 0 && !diagnosisCodes.some((d) => d.is_primary)) {
    diagnosisCodes[0].is_primary = true;
  }

  const procedureCodes = rawCpt
    .map((r) => coerce(r))
    .filter(Boolean) as ProcedureCode[];

  return { diagnosisCodes, procedureCodes };
}
