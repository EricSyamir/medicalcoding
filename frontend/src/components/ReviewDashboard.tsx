"use client";

import { useState } from "react";
import {
  Download, RotateCcw, ChevronDown, ChevronUp,
  FileText, Stethoscope, FlaskConical, Clock,
  ShieldCheck, AlertTriangle
} from "lucide-react";
import clsx from "clsx";
import type { ReviewPayload, DiagnosisCode, ProcedureCode } from "@/types/review";
import DiagnosisCard  from "./DiagnosisCard";
import ProcedureCard  from "./ProcedureCard";
import WarningsPanel  from "./WarningsPanel";

interface Props {
  result: ReviewPayload;
  onReset: () => void;
}

const PRIORITY_STYLE: Record<string, string> = {
  urgent: "bg-red-600   text-white",
  normal: "bg-amber-500 text-white",
  low:    "bg-emerald-600 text-white",
};

export default function ReviewDashboard({ result, onReset }: Props) {
  const [codes, setCodes] = useState(result);
  const [showFacts,  setShowFacts]  = useState(false);
  const [showAudit,  setShowAudit]  = useState(false);

  const updateDxOverride = (code: string, value: string | null) => {
    setCodes((prev) => ({
      ...prev,
      diagnosis_codes: prev.diagnosis_codes.map((d) =>
        d.code === code ? { ...d, reviewer_override: value } : d
      ),
    }));
  };

  const updatePxOverride = (code: string, value: string | null) => {
    setCodes((prev) => ({
      ...prev,
      procedure_codes: prev.procedure_codes.map((p) =>
        p.code === code ? { ...p, reviewer_override: value } : p
      ),
    }));
  };

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(codes, null, 2)], { type: "application/json" });
    const a    = document.createElement("a");
    a.href     = URL.createObjectURL(blob);
    a.download = `${codes.note_id}_review.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const processedDate = new Date(codes.processed_at).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });

  const overrideCount =
    codes.diagnosis_codes.filter((d) => d.reviewer_override).length +
    codes.procedure_codes.filter((p) => p.reviewer_override).length;

  return (
    <div className="animate-fade-in space-y-6">

      {/* ── Summary Banner ────────────────────────────────────── */}
      <div className="rounded-2xl bg-navy-800 text-white p-5 flex flex-wrap items-center gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-navy-100/70 font-medium uppercase tracking-widest mb-1">Review Ready</p>
          <h2 className="text-lg font-bold truncate font-mono">{codes.note_id}</h2>
          <p className="text-xs text-navy-100/60 mt-0.5">{processedDate} · {codes.note_word_count} words · {codes.model_used}</p>
        </div>

        {/* Stats */}
        <div className="flex flex-wrap gap-3">
          <Stat icon={<Stethoscope className="w-4 h-4" />} value={codes.diagnosis_codes.length} label="Dx Codes" />
          <Stat icon={<FlaskConical className="w-4 h-4" />} value={codes.procedure_codes.length} label="CPT Codes" />
          <Stat icon={<AlertTriangle className="w-4 h-4" />} value={codes.warnings.length} label="Warnings" />
          {overrideCount > 0 && (
            <Stat icon={<ShieldCheck className="w-4 h-4" />} value={overrideCount} label="Overrides" highlight />
          )}
        </div>

        {/* Priority */}
        <span className={clsx("text-xs font-bold px-3 py-1.5 rounded-full uppercase tracking-wider",
          PRIORITY_STYLE[codes.review_priority])}>
          {codes.review_priority} priority
        </span>
      </div>

      {/* ── Warnings ──────────────────────────────────────────── */}
      <Section title="Warnings & Flags" icon={<AlertTriangle className="w-4 h-4" />} defaultOpen>
        <WarningsPanel warnings={codes.warnings} />
      </Section>

      {/* ── Codes (2-column on desktop) ────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Diagnosis codes */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Stethoscope className="w-4 h-4 text-navy-700" />
            <h3 className="text-sm font-bold text-slate-800">ICD-10-CM Diagnosis Codes</h3>
            <span className="ml-auto text-xs font-semibold px-2 py-0.5 rounded-full bg-navy-100 text-navy-700">
              {codes.diagnosis_codes.length}
            </span>
          </div>
          <div className="space-y-3">
            {codes.diagnosis_codes.map((d: DiagnosisCode) => (
              <DiagnosisCard key={d.code} code={d} onOverride={updateDxOverride} />
            ))}
          </div>
        </div>

        {/* Procedure codes */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <FlaskConical className="w-4 h-4 text-cyan-700" />
            <h3 className="text-sm font-bold text-slate-800">CPT Procedure Codes</h3>
            <span className="ml-auto text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-700">
              {codes.procedure_codes.length}
            </span>
          </div>
          <div className="space-y-3">
            {codes.procedure_codes.map((p: ProcedureCode) => (
              <ProcedureCard key={p.code} code={p} onOverride={updatePxOverride} />
            ))}
          </div>
        </div>
      </div>

      {/* ── Extracted Facts (collapsible) ──────────────────────── */}
      <Section
        title="Extracted Clinical Facts"
        icon={<FileText className="w-4 h-4" />}
        open={showFacts}
        onToggle={() => setShowFacts((v) => !v)}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FactGroup title="Chief Complaint"     items={codes.extracted_facts.chief_complaint ? [codes.extracted_facts.chief_complaint] : []} />
          <FactGroup title="Diagnoses Mentioned" items={codes.extracted_facts.diagnoses_mentioned} />
          <FactGroup title="Symptoms & Signs"    items={codes.extracted_facts.symptoms_signs} />
          <FactGroup title="Procedures"          items={codes.extracted_facts.procedures_mentioned} />
          <FactGroup title="Medications"         items={codes.extracted_facts.medications} />
          <FactGroup title="Labs & Imaging"      items={codes.extracted_facts.lab_imaging_results} />
          <FactGroup title="Relevant History"    items={codes.extracted_facts.relevant_history} />
        </div>
      </Section>

      {/* ── Audit Trail (collapsible) ──────────────────────────── */}
      <Section
        title="Audit Trail"
        icon={<Clock className="w-4 h-4" />}
        open={showAudit}
        onToggle={() => setShowAudit((v) => !v)}
      >
        <div className="space-y-1">
          {codes.audit_trail.map((entry, i) => (
            <p key={i} className="font-mono text-xs text-slate-500 leading-relaxed">{entry}</p>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-400">
          Pipeline v{codes.pipeline_version}
        </div>
      </Section>

      {/* ── Action Bar ────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3 justify-end pt-2">
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <RotateCcw className="w-4 h-4" /> New Note
        </button>
        <button
          onClick={exportJSON}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-navy-800 text-white text-sm font-medium hover:bg-navy-700 transition-colors"
        >
          <Download className="w-4 h-4" /> Export JSON
        </button>
      </div>
    </div>
  );
}

/* ── Small helpers ───────────────────────────────────────────── */

function Stat({ icon, value, label, highlight = false }: {
  icon: React.ReactNode; value: number; label: string; highlight?: boolean;
}) {
  return (
    <div className={clsx("flex items-center gap-2 px-3 py-2 rounded-xl",
      highlight ? "bg-violet-500/20" : "bg-white/10")}>
      <span className="opacity-70">{icon}</span>
      <span>
        <span className="text-base font-bold">{value}</span>
        <span className="text-xs text-white/60 ml-1">{label}</span>
      </span>
    </div>
  );
}

function Section({
  title, icon, children, defaultOpen, open, onToggle,
}: {
  title: string; icon: React.ReactNode; children: React.ReactNode;
  defaultOpen?: boolean; open?: boolean; onToggle?: () => void;
}) {
  const [localOpen, setLocalOpen] = useState(defaultOpen ?? false);
  const isOpen   = onToggle ? open : localOpen;
  const toggle   = onToggle ?? (() => setLocalOpen((v) => !v));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
      <button
        onClick={toggle}
        className="w-full flex items-center gap-2 px-5 py-4 text-left hover:bg-slate-50 transition-colors"
      >
        <span className="text-slate-500">{icon}</span>
        <span className="text-sm font-bold text-slate-800 flex-1">{title}</span>
        {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>
      {isOpen && <div className="px-5 pb-5">{children}</div>}
    </div>
  );
}

function FactGroup({ title, items }: { title: string; items: string[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">{title}</p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex gap-2 text-xs text-slate-700">
            <span className="text-slate-300 mt-0.5">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
