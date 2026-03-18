/**
 * Code retrieval — tokenisation + cosine-similarity search over ICD-10/CPT databases.
 * Pure TypeScript, no Python/scikit-learn dependency needed on Vercel.
 */

import icd10Raw from "@/data/icd10_codes.json";
import cptRaw   from "@/data/cpt_codes.json";

interface CodeEntry {
  code:        string;
  description: string;
  keywords:    string[];
  category:    string;
}

export interface RetrievedCode extends CodeEntry {
  retrieval_score: number;
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length > 1);
}

function cosineSim(queryTokens: string[], doc: string): number {
  const docSet   = new Set(tokenize(doc));
  const querySet = new Set(queryTokens);
  let matches    = 0;
  for (const t of querySet) if (docSet.has(t)) matches++;
  if (matches === 0) return 0;
  return matches / Math.sqrt(querySet.size * docSet.size);
}

function buildDoc(c: CodeEntry): string {
  return `${c.code} ${c.description} ${c.keywords.join(" ")} ${c.category}`;
}

function search(query: string, codes: CodeEntry[], topK = 10): RetrievedCode[] {
  if (!query.trim()) return [];
  const qTokens = tokenize(query);
  return codes
    .map((c) => ({ ...c, retrieval_score: parseFloat(cosineSim(qTokens, buildDoc(c)).toFixed(4)) }))
    .filter((c) => c.retrieval_score > 0.02)
    .sort((a, b) => b.retrieval_score - a.retrieval_score)
    .slice(0, topK);
}

function bulkSearch(queries: string[], codes: CodeEntry[], topK = 10): RetrievedCode[] {
  const seen   = new Set<string>();
  const result: RetrievedCode[] = [];
  for (const q of queries) {
    for (const item of search(q, codes, topK)) {
      if (!seen.has(item.code)) {
        seen.add(item.code);
        result.push(item);
      }
    }
  }
  return result.sort((a, b) => b.retrieval_score - a.retrieval_score);
}

export const searchIcd10 = (queries: string[]) => bulkSearch(queries, icd10Raw as CodeEntry[]);
export const searchCpt   = (queries: string[]) => bulkSearch(queries, cptRaw   as CodeEntry[]);
