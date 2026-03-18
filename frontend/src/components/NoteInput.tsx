"use client";

import { useState, useRef } from "react";
import { Upload, FileText, Sparkles, ChevronDown, KeyRound } from "lucide-react";
import clsx from "clsx";

const SAMPLE_NOTE_SNIPPET = `PATIENT ENCOUNTER NOTE
Date of Service: 03/18/2026  |  Provider: Dr. Sarah Mitchell, MD, FACC

CHIEF COMPLAINT: Progressive shortness of breath and worsening leg swelling x2 weeks.

HISTORY: 73-year-old male with chronic systolic CHF (EF 35%), CAD s/p CABG x3 (2018), 
hypertension, T2DM on metformin + insulin glargine, hyperlipidemia, and CKD stage 3...`;

interface Props {
  onSubmit: (note: string, provider: string, model: string, apiKey?: string) => void;
  loading: boolean;
  mode: "demo" | "production";
}

const PROVIDERS = ["gemini", "openai"] as const;

const MODELS: Record<string, string[]> = {
  gemini: ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-pro"],
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
};

export default function NoteInput({ onSubmit, loading, mode }: Props) {
  const [note,     setNote]     = useState("");
  const [provider, setProvider] = useState<"gemini" | "openai">("gemini");
  const [model,    setModel]    = useState(MODELS.gemini[0]);
  const [apiKey,   setApiKey]   = useState("");
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleProviderChange = (p: "gemini" | "openai") => {
    setProvider(p);
    setModel(MODELS[p][0]);
  };

  const loadSample = async () => {
    try {
      const res = await fetch("/sample_note.txt");
      if (res.ok) { setNote(await res.text()); return; }
    } catch { /* fallback below */ }
    setNote(SAMPLE_NOTE_SNIPPET);
  };

  const handleFile = (file: File) => {
    if (!file.type.startsWith("text") && !file.name.endsWith(".txt")) return;
    const reader = new FileReader();
    reader.onload = (e) => setNote((e.target?.result as string) ?? "");
    reader.readAsText(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleSubmit = () => {
    if (note.trim().length < 20) return;
    onSubmit(note, provider, model, apiKey.trim() || undefined);
  };

  return (
    <div className="space-y-5 animate-fade-in">

      {/* Feature pills */}
      <div className="flex flex-wrap gap-2 justify-center">
        {["ICD-10-CM Diagnosis Codes", "CPT Procedure Codes", "Confidence Scores", "Evidence References", "Conflict Detection"].map((f) => (
          <span key={f} className="text-xs font-medium px-3 py-1 rounded-full bg-navy-100 text-navy-700 border border-navy-200">
            {f}
          </span>
        ))}
      </div>

      {/* Main card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

        {/* Textarea */}
        <div
          className={clsx(
            "relative border-b border-slate-100 transition-colors",
            dragging && "bg-blue-50"
          )}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Paste a clinical note here — or drag & drop a .txt file…"
            rows={12}
            className="w-full px-5 pt-4 pb-3 text-sm text-slate-700 placeholder-slate-300 resize-none focus:outline-none font-mono leading-relaxed"
          />
          {/* Drag overlay */}
          {dragging && (
            <div className="absolute inset-0 flex items-center justify-center bg-blue-50/80 pointer-events-none">
              <div className="flex flex-col items-center gap-2 text-blue-600">
                <Upload className="w-8 h-8" />
                <p className="text-sm font-semibold">Drop .txt file here</p>
              </div>
            </div>
          )}
        </div>

        {/* Toolbar */}
        <div className="px-5 py-3 flex flex-wrap items-center gap-3">
          {/* Word count */}
          <span className="text-xs text-slate-400 tabular-nums">
            {note.trim() ? `${note.trim().split(/\s+/).length} words` : "No note entered"}
          </span>

          {/* File upload */}
          <button
            onClick={() => fileRef.current?.click()}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-navy-700 transition-colors"
          >
            <Upload className="w-3.5 h-3.5" /> Upload .txt
          </button>
          <input ref={fileRef} type="file" accept=".txt,text/plain" className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />

          {/* Sample note */}
          <button
            onClick={loadSample}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-navy-700 transition-colors"
          >
            <FileText className="w-3.5 h-3.5" /> Load Sample
          </button>

          <div className="ml-auto flex items-center gap-2">
            {/* Provider selector */}
            <div className="relative">
              <select
                value={provider}
                onChange={(e) => handleProviderChange(e.target.value as "gemini" | "openai")}
                className="appearance-none text-xs font-medium pl-3 pr-7 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 focus:outline-none focus:ring-2 focus:ring-navy-200 cursor-pointer"
              >
                {PROVIDERS.map((p) => <option key={p} value={p}>{p === "gemini" ? "Gemini" : "OpenAI"}</option>)}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 pointer-events-none" />
            </div>

            {/* Model selector */}
            <div className="relative">
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="appearance-none text-xs font-medium pl-3 pr-7 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 focus:outline-none focus:ring-2 focus:ring-navy-200 cursor-pointer"
              >
                {MODELS[provider].map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 pointer-events-none" />
            </div>
          </div>
        </div>

        {/* Production key prompt */}
        {mode === "production" && (
          <div className="px-5 pb-0">
            <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 text-slate-600">
                <KeyRound className="w-4 h-4" />
                <p className="text-xs font-semibold">API key required for Production</p>
              </div>
              <input
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={provider === "gemini" ? "Paste Google API key (AIza…)" : "Paste OpenAI API key (sk-…)"}
                className="flex-1 min-w-[220px] text-xs border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-navy-200"
              />
              <p className="text-[11px] text-slate-400">
                Used for this request only.
              </p>
            </div>
          </div>
        )}

        {/* Submit */}
        <div className="px-5 pb-5">
          <button
            onClick={handleSubmit}
            disabled={note.trim().length < 20 || loading || (mode === "production" && apiKey.trim().length < 10)}
            className={clsx(
              "w-full flex items-center justify-center gap-2.5 py-3 rounded-xl text-sm font-bold transition-all",
              note.trim().length >= 20 && !loading && (mode !== "production" || apiKey.trim().length >= 10)
                ? "bg-navy-800 text-white hover:bg-navy-700 shadow-sm hover:shadow"
                : "bg-slate-100 text-slate-400 cursor-not-allowed"
            )}
          >
            <Sparkles className="w-4 h-4" />
            {loading ? "Processing…" : "Analyze Clinical Note"}
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-center text-xs text-slate-400">
        Do not submit notes containing real patient identifiers. For demo and evaluation purposes only.
      </p>
    </div>
  );
}
