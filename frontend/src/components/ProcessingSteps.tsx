"use client";

import { Check, Loader2 } from "lucide-react";
import clsx from "clsx";

const STEPS = [
  { id: 0, label: "Extracting clinical facts",      desc: "LLM reads the note and identifies diagnoses, procedures, and symptoms" },
  { id: 1, label: "Retrieving candidate codes",     desc: "TF-IDF search narrows 70k+ codes to relevant candidates"              },
  { id: 2, label: "Assigning & scoring codes",      desc: "LLM selects codes, scores confidence, and attaches evidence"           },
  { id: 3, label: "Validating & checking conflicts", desc: "Rule engine checks for conflicts, gaps, and warnings"                  },
];

export default function ProcessingSteps({ current }: { current: number }) {
  return (
    <div className="w-full max-w-xl mx-auto space-y-3">
      {STEPS.map((step) => {
        const done    = current > step.id;
        const active  = current === step.id;
        const pending = current < step.id;

        return (
          <div
            key={step.id}
            className={clsx(
              "flex items-start gap-4 p-4 rounded-xl border transition-all duration-300",
              done    && "bg-emerald-50  border-emerald-200",
              active  && "bg-blue-50    border-blue-200 shadow-sm",
              pending && "bg-white       border-slate-100 opacity-40"
            )}
          >
            {/* Icon */}
            <div
              className={clsx(
                "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center",
                done   && "bg-emerald-500",
                active && "bg-blue-500",
                pending && "bg-slate-200"
              )}
            >
              {done   && <Check   className="w-4 h-4 text-white" strokeWidth={2.5} />}
              {active && <Loader2 className="w-4 h-4 text-white animate-spin" />}
              {pending && <span className="w-2 h-2 rounded-full bg-slate-400" />}
            </div>

            {/* Text */}
            <div>
              <p className={clsx("text-sm font-semibold",
                done    && "text-emerald-700",
                active  && "text-blue-700",
                pending && "text-slate-400"
              )}>
                {step.label}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">{step.desc}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
