"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Quote, Pencil, Check, X } from "lucide-react";
import type { ProcedureCode } from "@/types/review";
import ConfidenceBadge from "./ConfidenceBadge";

interface Props {
  code: ProcedureCode;
  onOverride: (code: string, value: string | null) => void;
}

export default function ProcedureCard({ code, onOverride }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [editing,  setEditing]  = useState(false);
  const [draft,    setDraft]    = useState(code.reviewer_override ?? "");

  const confirmOverride = () => {
    onOverride(code.code, draft.trim() || null);
    setEditing(false);
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white hover:shadow-sm transition-shadow">
      <div className="p-4">
        <div className="flex items-start gap-3">
          <span className="flex-shrink-0 font-mono text-xs font-bold px-2.5 py-1 rounded-lg bg-cyan-700 text-white tracking-wide">
            {code.code}
          </span>
          <p className="flex-1 text-sm font-medium text-slate-800 leading-snug">
            {code.description}
          </p>
        </div>

        <div className="mt-3">
          <ConfidenceBadge level={code.confidence_level} score={code.confidence_score} />
        </div>

        {code.reviewer_override && !editing && (
          <div className="mt-2 flex items-center gap-2 text-xs text-violet-700 bg-violet-50 ring-1 ring-violet-200 px-3 py-1.5 rounded-lg">
            <Pencil className="w-3 h-3 flex-shrink-0" />
            <span className="font-medium">Override:</span>
            <span>{code.reviewer_override}</span>
            <button onClick={() => { setDraft(code.reviewer_override ?? ""); setEditing(true); }} className="ml-auto hover:text-violet-900">Edit</button>
          </div>
        )}

        {editing && (
          <div className="mt-2 flex items-center gap-2">
            <input
              className="flex-1 text-xs border border-violet-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-violet-300"
              placeholder="Enter corrected code or note…"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && confirmOverride()}
              autoFocus
            />
            <button onClick={confirmOverride} className="p-1.5 rounded-lg bg-violet-600 text-white hover:bg-violet-700">
              <Check className="w-3.5 h-3.5" />
            </button>
            <button onClick={() => setEditing(false)} className="p-1.5 rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        <div className="mt-3 flex items-center gap-3">
          {code.evidence.length > 0 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-slate-500 hover:text-cyan-700 transition-colors"
            >
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              {code.evidence.length} evidence {code.evidence.length === 1 ? "ref" : "refs"}
            </button>
          )}
          {!editing && (
            <button
              onClick={() => { setDraft(code.reviewer_override ?? ""); setEditing(true); }}
              className="ml-auto flex items-center gap-1 text-xs text-slate-400 hover:text-violet-600 transition-colors"
            >
              <Pencil className="w-3 h-3" /> Override
            </button>
          )}
        </div>
      </div>

      {expanded && (
        <div className="border-t border-slate-100 divide-y divide-slate-50">
          {code.evidence.map((ev, i) => (
            <div key={i} className="px-4 py-3 bg-slate-50/60">
              <div className="flex gap-2">
                <Quote className="w-3.5 h-3.5 text-slate-300 flex-shrink-0 mt-0.5" />
                <p className="text-xs italic text-slate-600">&ldquo;{ev.quote}&rdquo;</p>
              </div>
              <p className="mt-1.5 text-xs text-slate-500 pl-5">{ev.rationale}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
