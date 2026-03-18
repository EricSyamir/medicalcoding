import { generateJSON } from "./llm";
import type { ExtractedFacts } from "@/types/review";

const SYSTEM_PROMPT = `You are a senior clinical documentation specialist with expertise in medical
coding (CPC-certified). Your task is to read a clinical note and extract
structured medical facts that will be used to assign ICD-10-CM and CPT codes.

Return ONLY valid JSON matching the schema below. Do not add commentary.

Schema:
{
  "chief_complaint": "<string or null>",
  "diagnoses_mentioned": ["<list of explicit and implied diagnoses>"],
  "symptoms_signs": ["<list of symptoms, signs, physical exam findings>"],
  "procedures_mentioned": ["<list of procedures performed or ordered>"],
  "medications": ["<list of medications with doses if mentioned>"],
  "lab_imaging_results": ["<list of lab/imaging results with values>"],
  "relevant_history": ["<past medical history, surgical history, family history>"],
  "supporting_quotes": ["<verbatim short excerpts (<=20 words each) that strongly support coding>"]
}

Rules:
- Be specific: include qualifiers (laterality, acuity, severity, stage).
- Include both confirmed and probable diagnoses (note uncertainty).
- Do not fabricate information not in the note.
- Keep each list item concise (one concept per item).`;

export async function extractFacts(
  noteText: string,
  provider: string,
  apiKey:   string,
  model:    string,
): Promise<ExtractedFacts> {
  const data = await generateJSON(
    provider, apiKey, model,
    SYSTEM_PROMPT,
    `Clinical Note:\n\n${noteText}`,
  );
  return data as unknown as ExtractedFacts;
}
