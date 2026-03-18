"use client";

import { useState } from "react";
import { Activity, Github, BookOpen, Loader2 } from "lucide-react";
import type { ReviewPayload } from "@/types/review";
import NoteInput        from "@/components/NoteInput";
import ReviewDashboard  from "@/components/ReviewDashboard";
import ProcessingSteps  from "@/components/ProcessingSteps";

type View = "input" | "processing" | "results";

export default function Home() {
  const [view,           setView]           = useState<View>("input");
  const [result,         setResult]         = useState<ReviewPayload | null>(null);
  const [error,          setError]          = useState<string | null>(null);
  const [processingStep, setProcessingStep] = useState(0);

  const handleSubmit = async (note: string, provider: string, model: string) => {
    setError(null);
    setProcessingStep(0);
    setView("processing");

    // Animate through pipeline steps
    const timers = [
      setTimeout(() => setProcessingStep(1), 1200),
      setTimeout(() => setProcessingStep(2), 2400),
      setTimeout(() => setProcessingStep(3), 3200),
    ];

    try {
      const res = await fetch("/api/process", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ note_text: note, provider, model }),
      });

      timers.forEach(clearTimeout);

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error ?? `Server error ${res.status}`);
      }

      const data: ReviewPayload = await res.json();
      setProcessingStep(4);
      setTimeout(() => {
        setResult(data);
        setView("results");
      }, 400);
    } catch (err: unknown) {
      timers.forEach(clearTimeout);
      setError(err instanceof Error ? err.message : "Unknown error");
      setView("input");
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setProcessingStep(0);
    setView("input");
  };

  return (
    <div className="min-h-screen flex flex-col">

      {/* ── Navigation ─────────────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-navy-800 border-b border-white/10 shadow-lg">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-3">
          <Activity className="w-5 h-5 text-cyan-400 flex-shrink-0" />
          <span className="text-white font-bold text-sm tracking-tight">
            Medical Coding Assistant
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-400/20 text-cyan-300 font-medium">
            AI-Powered
          </span>

          <div className="ml-auto flex items-center gap-4">
            <span className="hidden sm:block text-xs text-white/40">
              ICD-10-CM · CPT · Human Review
            </span>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-white/60 hover:text-white transition-colors"
            >
              <Github className="w-3.5 h-3.5" /> GitHub
            </a>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-white/60 hover:text-white transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5" /> Docs
            </a>
          </div>
        </div>
      </header>

      {/* ── Main Content ───────────────────────────────────── */}
      <main className="flex-1">
        <div className="max-w-6xl mx-auto px-4 py-8">

          {/* INPUT VIEW */}
          {view === "input" && (
            <div className="max-w-2xl mx-auto">
              {/* Hero */}
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-navy-800 shadow-lg mb-4">
                  <Activity className="w-7 h-7 text-cyan-400" />
                </div>
                <h1 className="text-2xl font-extrabold text-slate-900 mb-2">
                  AI Medical Coding Pipeline
                </h1>
                <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
                  Paste a clinical note to receive structured ICD-10-CM and CPT code
                  suggestions with confidence scores, evidence references, and reviewer
                  warnings — ready for human review and override.
                </p>
              </div>

              {/* Error */}
              {error && (
                <div className="mb-5 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm animate-fade-in">
                  <p className="font-semibold mb-1">Processing failed</p>
                  <p className="text-xs">{error}</p>
                </div>
              )}

              <NoteInput onSubmit={handleSubmit} loading={false} />
            </div>
          )}

          {/* PROCESSING VIEW */}
          {view === "processing" && (
            <div className="max-w-2xl mx-auto text-center animate-fade-in">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-navy-800 shadow-lg mb-6">
                <Loader2 className="w-7 h-7 text-cyan-400 animate-spin" />
              </div>
              <h2 className="text-xl font-bold text-slate-800 mb-2">Analyzing Note</h2>
              <p className="text-sm text-slate-500 mb-8">
                The pipeline is extracting facts, retrieving codes, and validating results…
              </p>
              <ProcessingSteps current={processingStep} />
            </div>
          )}

          {/* RESULTS VIEW */}
          {view === "results" && result && (
            <ReviewDashboard result={result} onReset={handleReset} />
          )}
        </div>
      </main>

      {/* ── Footer ─────────────────────────────────────────── */}
      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-4 py-4 flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-slate-400">
            Medical Coding Assistant v1.0.0 · Not for clinical use without human review
          </p>
          <p className="text-xs text-slate-400">
            Pipeline: ICD-10-CM + CPT · Powered by Gemini / OpenAI · MIT License
          </p>
        </div>
      </footer>
    </div>
  );
}
