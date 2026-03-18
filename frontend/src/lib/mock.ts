import type { ReviewPayload } from "@/types/review";

/** Realistic demo result based on the bundled cardiology sample note. */
export const MOCK_RESULT: ReviewPayload = {
  note_id: "note_da99160e6c20",
  processed_at: "2026-03-18T18:26:41Z",
  note_word_count: 694,
  extracted_facts: {
    chief_complaint:
      "Progressive shortness of breath and bilateral lower extremity edema for 2 weeks",
    diagnoses_mentioned: [
      "Acute decompensated heart failure (chronic systolic CHF exacerbation)",
      "Acute-on-chronic kidney disease (cardiorenal syndrome)",
      "Hypertension, uncontrolled",
      "Type 2 diabetes mellitus with hyperglycemia",
      "Hyperlipidemia",
      "Chronic kidney disease stage 3",
      "History of coronary artery bypass graft x3",
      "Former smoker",
    ],
    symptoms_signs: [
      "Dyspnea on exertion, worsening over 2 weeks",
      "3-pillow orthopnea",
      "Paroxysmal nocturnal dyspnea",
      "Bilateral lower extremity pitting edema (2+ to knee)",
      "Weight gain 8 lbs over 10 days",
      "SpO2 91% on room air",
      "BP 152/94 mmHg",
      "JVD to 12 cm at 45 degrees",
      "S3 gallop present",
      "Bibasilar crackles to mid-lung fields",
    ],
    procedures_mentioned: [
      "12-lead ECG",
      "Chest X-ray (2 views)",
      "Basic Metabolic Panel (BMP)",
      "Complete Blood Count (CBC)",
      "BNP level",
      "HbA1c",
      "IV furosemide 80 mg BID",
      "Flu vaccine administered",
    ],
    medications: [
      "Carvedilol 12.5 mg BID",
      "Lisinopril 10 mg daily",
      "Furosemide 40 mg daily",
      "Spironolactone 25 mg daily",
      "Atorvastatin 40 mg nightly",
      "Metformin 1000 mg BID",
      "Insulin glargine 20 units SC nightly",
      "Aspirin 81 mg daily",
    ],
    lab_imaging_results: [
      "BNP 980 pg/mL (markedly elevated)",
      "Creatinine 2.1 mg/dL (baseline 1.8)",
      "Glucose 187 mg/dL",
      "HbA1c 8.2%",
      "Hemoglobin 11.4 g/dL",
      "Chest X-ray: cardiomegaly, bilateral interstitial pulmonary edema, small bilateral pleural effusions",
      "ECG: Normal sinus rhythm 88 bpm, LBBB (previously documented), no new ST changes",
    ],
    relevant_history: [
      "Coronary artery bypass graft x3 (2018)",
      "Chronic systolic CHF (EF 35%)",
      "CKD stage 3 (baseline creatinine 1.8)",
      "Former smoker (40 pack-years, quit 2010)",
    ],
    supporting_quotes: [
      "ACUTE DECOMPENSATED HEART FAILURE (chronic systolic CHF exacerbation) — primary diagnosis",
      "BP 152/94 mmHg, SpO2 91% on room air",
      "BNP: 980 pg/mL (markedly elevated)",
      "HbA1c: 8.2% (last result was 7.6% three months ago)",
      "creatinine 2.1 (baseline 1.8 — acute-on-chronic)",
    ],
  },
  diagnosis_codes: [
    {
      code: "I50.22",
      description: "Chronic systolic (congestive) heart failure",
      confidence_score: 0.96,
      confidence_level: "high",
      is_primary: true,
      evidence: [
        {
          quote:
            "ACUTE DECOMPENSATED HEART FAILURE (chronic systolic CHF exacerbation) — primary diagnosis",
          rationale:
            "Explicitly documented as primary diagnosis with systolic type specificity",
        },
        {
          quote: "last known EF 35% on echo 6 months ago",
          rationale: "EF 35% confirms systolic dysfunction (HFrEF)",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "I10",
      description: "Essential (primary) hypertension",
      confidence_score: 0.91,
      confidence_level: "high",
      is_primary: false,
      evidence: [
        {
          quote: "Essential hypertension — BP 152/94 mmHg",
          rationale:
            "Documented history of hypertension with elevated BP confirmed on exam",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "E11.65",
      description: "Type 2 diabetes mellitus with hyperglycemia",
      confidence_score: 0.88,
      confidence_level: "high",
      is_primary: false,
      evidence: [
        {
          quote: "glucose 187, HbA1c 8.2%",
          rationale:
            "T2DM with documented hyperglycemia — glucose 187 and HbA1c 8.2% both above target",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "N19",
      description: "Unspecified kidney failure",
      confidence_score: 0.82,
      confidence_level: "high",
      is_primary: false,
      evidence: [
        {
          quote: "creatinine elevated from baseline 1.8 to 2.1 — acute-on-chronic",
          rationale: "Acute-on-chronic kidney injury documented in assessment",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "N18.3",
      description: "Chronic kidney disease, stage 3 (moderate)",
      confidence_score: 0.85,
      confidence_level: "high",
      is_primary: false,
      evidence: [
        {
          quote: "Stage 3 chronic kidney disease (baseline creatinine 1.8 mg/dL)",
          rationale: "CKD stage 3 explicitly documented in past medical history",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "E78.5",
      description: "Hyperlipidemia, unspecified",
      confidence_score: 0.83,
      confidence_level: "high",
      is_primary: false,
      evidence: [
        {
          quote: "Hyperlipidemia — on atorvastatin 40 mg",
          rationale: "Documented hyperlipidemia with active statin therapy",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "Z95.1",
      description: "Presence of aortocoronary bypass graft",
      confidence_score: 0.92,
      confidence_level: "high",
      is_primary: false,
      evidence: [
        {
          quote: "status post coronary artery bypass graft x3 in 2018",
          rationale: "History of CABG documents presence of bypass grafts",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "Z87.891",
      description: "Personal history of nicotine dependence",
      confidence_score: 0.88,
      confidence_level: "high",
      is_primary: false,
      evidence: [
        {
          quote: "Former smoker — quit 2010 (40 pack-year history)",
          rationale: "Documents former tobacco use — personal history of nicotine dependence",
        },
      ],
      reviewer_override: null,
    },
  ],
  procedure_codes: [
    {
      code: "99223",
      description:
        "Initial hospital inpatient care, high level medical decision making",
      confidence_score: 0.92,
      confidence_level: "high",
      evidence: [
        {
          quote: "Admit to telemetry for IV diuresis — Disposition: inpatient cardiology",
          rationale:
            "High-complexity inpatient admission with multiple acute diagnoses and active management",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "93000",
      description:
        "Electrocardiogram, routine ECG with at least 12 leads; with interpretation and report",
      confidence_score: 0.93,
      confidence_level: "high",
      evidence: [
        {
          quote: "12-lead ECG: Normal sinus rhythm at 88 bpm; left bundle branch block",
          rationale: "12-lead ECG performed and interpreted with documented findings",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "71046",
      description: "Radiologic examination, chest; 2 views",
      confidence_score: 0.91,
      confidence_level: "high",
      evidence: [
        {
          quote: "Chest X-ray (2 views): Cardiomegaly with bilateral interstitial pulmonary edema",
          rationale: "Two-view chest radiograph performed and interpreted",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "80048",
      description: "Basic metabolic panel",
      confidence_score: 0.88,
      confidence_level: "high",
      evidence: [
        {
          quote: "BMP: Sodium 136, Potassium 4.2, BUN 28, Creatinine 2.1, Glucose 187",
          rationale: "Complete BMP ordered and resulted with values documented",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "85025",
      description: "Blood count; complete (CBC), automated and automated differential WBC count",
      confidence_score: 0.88,
      confidence_level: "high",
      evidence: [
        {
          quote: "CBC: WBC 7.2, Hgb 11.4, Hct 34%, Plt 210",
          rationale: "CBC with differential ordered and resulted",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "83036",
      description: "Hemoglobin; glycosylated (A1C)",
      confidence_score: 0.9,
      confidence_level: "high",
      evidence: [
        {
          quote: "HbA1c: 8.2% (last result was 7.6% three months ago)",
          rationale: "HbA1c ordered, resulted, and compared to prior values",
        },
      ],
      reviewer_override: null,
    },
    {
      code: "90686",
      description: "Influenza virus vaccine, quadrivalent (IIV4), intramuscular",
      confidence_score: 0.78,
      confidence_level: "medium",
      evidence: [
        {
          quote: "flu vaccine administered in clinic today",
          rationale: "Influenza vaccine administered during this encounter",
        },
      ],
      reviewer_override: null,
    },
  ],
  warnings: [
    {
      type: "documentation_gap",
      severity: "warning",
      message:
        "High-risk diagnosis I50.22 (Chronic systolic heart failure) detected. Ensure all supporting documentation, staging, and complications are fully coded.",
      related_codes: ["I50.22"],
    },
    {
      type: "specificity",
      severity: "info",
      message:
        "N19 (Unspecified kidney failure) coded — consider N17.9 (Acute kidney failure, unspecified) given the documented acute-on-chronic presentation.",
      related_codes: ["N19"],
    },
    {
      type: "documentation_gap",
      severity: "warning",
      message:
        "Acute decompensation qualifier noted — verify I50.22 captures the full acuity, or add an additional code for the acute exacerbation context.",
      related_codes: ["I50.22"],
    },
    {
      type: "missing_info",
      severity: "info",
      message:
        "Anemia (Hgb 11.4) documented but no anemia code assigned. Consider adding D64.9 (Anemia, unspecified).",
      related_codes: ["D64.9"],
    },
  ],
  requires_human_review: true,
  review_priority: "urgent",
  reviewer_notes: null,
  reviewed_by: null,
  reviewed_at: null,
  pipeline_version: "1.0.0",
  model_used: "gemini-2.0-flash (demo)",
  audit_trail: [
    "[2026-03-18T18:26:36Z] Pipeline started: note_id=note_da99160e6c20, words=694",
    "[2026-03-18T18:26:36Z] Step 1/4: Extracting clinical facts via LLM",
    "[2026-03-18T18:26:38Z] Extraction complete: 8 diagnoses, 10 symptoms, 8 procedures",
    "[2026-03-18T18:26:38Z] Step 2/4: Retrieving candidate codes via TF-IDF",
    "[2026-03-18T18:26:38Z] Retrieval complete: 45 ICD-10 candidates, 28 CPT candidates",
    "[2026-03-18T18:26:38Z] Step 3/4: Assigning and scoring codes via LLM",
    "[2026-03-18T18:26:41Z] Coding complete: 8 diagnosis codes, 7 procedure codes",
    "[2026-03-18T18:26:41Z] Step 4/4: Running rule-based validation",
    "[2026-03-18T18:26:41Z] Validation complete: 4 warnings (0 errors), review_priority=urgent",
    "[2026-03-18T18:26:41Z] Pipeline complete — note_da99160e6c20: 8 dx codes, 7 px codes, 4 warnings",
  ],
};
