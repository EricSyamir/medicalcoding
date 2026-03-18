/**
 * Orchestrates the full medical coding pipeline.
 * Runs in-process inside the Next.js API route — no separate backend required.
 */

import { createHash } from "crypto";
import { extractFacts }  from "./extraction";
import { assignCodes }   from "./coding";
import { validate }      from "./validation";
import { searchIcd10, searchCpt } from "./retrieval";
import type { ReviewPayload, ExtractedFacts } from "@/types/review";

const PIPELINE_VERSION = "1.1.0";
const TOP_K = 10;

interface PipelineInput {
  noteText: string;
  provider: string;
  model:    string;
  apiKey:   string;
}

function normalise(text: string): string {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/[ \t]+/g, " ")
    .trim();
}

function noteId(text: string): string {
  return `note_${createHash("sha256").update(text).digest("hex").slice(0, 12)}`;
}

function ts(): string {
  return new Date().toISOString();
}

function buildRetrievalQueries(facts: ExtractedFacts): string[] {
  return [
    ...(facts.diagnoses_mentioned  ?? []),
    ...(facts.symptoms_signs        ?? []),
    ...(facts.procedures_mentioned  ?? []),
    facts.chief_complaint ?? "",
  ].filter(Boolean);
}

export async function runPipeline(input: PipelineInput): Promise<ReviewPayload> {
  const { noteText, provider, model, apiKey } = input;
  const audit: string[] = [];
  const log = (msg: string) => audit.push(`[${ts()}] ${msg}`);

  const normalized   = normalise(noteText);
  const wordCount    = normalized.split(/\s+/).filter(Boolean).length;
  const id           = noteId(normalized);
  const processedAt  = ts();

  log(`Pipeline started: note_id=${id}, words=${wordCount}, provider=${provider}, model=${model}`);

  // Step 1: Extract clinical facts
  log("Step 1/4: Extracting clinical facts via LLM");
  const facts = await extractFacts(normalized, provider, apiKey, model);
  log(`Step 1/4 complete: ${facts.diagnoses_mentioned.length} diagnoses, ${facts.procedures_mentioned.length} procedures mentioned`);

  // Step 2: Retrieve candidate codes
  log("Step 2/4: Retrieving candidate codes (TF-IDF)");
  const queries        = buildRetrievalQueries(facts);
  const icd10Candidates = searchIcd10(queries).slice(0, TOP_K);
  const cptCandidates   = searchCpt(queries).slice(0, TOP_K);
  log(`Step 2/4 complete: ${icd10Candidates.length} ICD-10 candidates, ${cptCandidates.length} CPT candidates`);

  // Step 3: Assign codes
  log("Step 3/4: Assigning codes via LLM");
  const { diagnosisCodes, procedureCodes } = await assignCodes(
    normalized, facts, icd10Candidates, cptCandidates, provider, apiKey, model,
  );
  log(`Step 3/4 complete: ${diagnosisCodes.length} dx codes, ${procedureCodes.length} cpt codes assigned`);

  // Step 4: Validate
  log("Step 4/4: Running rule-based validation");
  const { warnings, requiresHumanReview, reviewPriority } = validate(diagnosisCodes, procedureCodes);
  log(`Step 4/4 complete: ${warnings.length} warnings, priority=${reviewPriority}`);

  log("Pipeline complete");

  return {
    note_id:              id,
    processed_at:         processedAt,
    note_word_count:      wordCount,
    extracted_facts:      facts,
    diagnosis_codes:      diagnosisCodes,
    procedure_codes:      procedureCodes,
    warnings,
    requires_human_review: requiresHumanReview,
    review_priority:      reviewPriority,
    reviewer_notes:       null,
    reviewed_by:          null,
    reviewed_at:          null,
    pipeline_version:     PIPELINE_VERSION,
    model_used:           `${provider}/${model}`,
    audit_trail:          audit,
  };
}
