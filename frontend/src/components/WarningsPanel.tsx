import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import clsx from "clsx";
import type { CodingWarning } from "@/types/review";

interface Props { warnings: CodingWarning[] }

const SEV = {
  error:   { icon: AlertCircle,   bg: "bg-red-50",    border: "border-red-200",   text: "text-red-700",   badge: "bg-red-100 text-red-700",    label: "Error"   },
  warning: { icon: AlertTriangle, bg: "bg-amber-50",  border: "border-amber-200", text: "text-amber-700", badge: "bg-amber-100 text-amber-700",  label: "Warning" },
  info:    { icon: Info,          bg: "bg-blue-50",   border: "border-blue-200",  text: "text-blue-700",  badge: "bg-blue-100 text-blue-700",    label: "Info"    },
} as const;

const TYPE_LABEL: Record<string, string> = {
  missing_info:       "Missing Info",
  ambiguity:          "Ambiguity",
  conflict:           "Conflict",
  documentation_gap:  "Documentation Gap",
  specificity:        "Specificity",
};

export default function WarningsPanel({ warnings }: Props) {
  if (warnings.length === 0) {
    return (
      <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-medium">
        <Info className="w-4 h-4 flex-shrink-0" />
        No warnings — coding looks clean.
      </div>
    );
  }

  const errors   = warnings.filter((w) => w.severity === "error");
  const warnOnly = warnings.filter((w) => w.severity === "warning");
  const infos    = warnings.filter((w) => w.severity === "info");

  return (
    <div className="space-y-2.5">
      {/* Summary chips */}
      <div className="flex flex-wrap gap-2">
        {errors.length   > 0 && <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-red-100   text-red-700">{errors.length}   error{errors.length > 1 ? "s" : ""}</span>}
        {warnOnly.length > 0 && <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-700">{warnOnly.length} warning{warnOnly.length > 1 ? "s" : ""}</span>}
        {infos.length    > 0 && <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-100  text-blue-700">{infos.length}    info</span>}
      </div>

      {/* Warning cards */}
      {warnings.map((w, i) => {
        const s = SEV[w.severity];
        const Icon = s.icon;
        return (
          <div key={i} className={clsx("flex gap-3 p-3.5 rounded-xl border", s.bg, s.border)}>
            <Icon className={clsx("w-4 h-4 flex-shrink-0 mt-0.5", s.text)} />
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-1.5 mb-1">
                <span className={clsx("text-xs font-semibold px-2 py-0.5 rounded-full", s.badge)}>
                  {s.label}
                </span>
                <span className="text-xs text-slate-500">
                  {TYPE_LABEL[w.type] ?? w.type}
                </span>
                {w.related_codes.length > 0 && (
                  <div className="flex gap-1">
                    {w.related_codes.map((c) => (
                      <span key={c} className="font-mono text-xs px-1.5 py-0.5 bg-white/60 rounded border border-slate-200 text-slate-600">
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <p className={clsx("text-xs leading-relaxed", s.text)}>{w.message}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
