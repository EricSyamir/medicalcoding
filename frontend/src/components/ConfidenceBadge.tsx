import clsx from "clsx";
import type { ConfidenceLevel } from "@/types/review";

interface Props {
  level: ConfidenceLevel;
  score: number;
}

const config: Record<ConfidenceLevel, { bar: string; badge: string; label: string }> = {
  high:   { bar: "bg-emerald-500", badge: "bg-emerald-50 text-emerald-700 ring-emerald-200", label: "High"   },
  medium: { bar: "bg-amber-400",   badge: "bg-amber-50  text-amber-700  ring-amber-200",    label: "Medium" },
  low:    { bar: "bg-red-400",     badge: "bg-red-50    text-red-700    ring-red-200",       label: "Low"    },
};

export default function ConfidenceBadge({ level, score }: Props) {
  const c = config[level];
  return (
    <div className="flex items-center gap-2">
      {/* Progress bar */}
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={clsx("h-full rounded-full transition-all", c.bar)}
          style={{ width: `${Math.round(score * 100)}%` }}
        />
      </div>
      {/* Percentage */}
      <span className="text-xs font-semibold text-slate-500 w-9 text-right tabular-nums">
        {Math.round(score * 100)}%
      </span>
      {/* Level badge */}
      <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full ring-1", c.badge)}>
        {c.label}
      </span>
    </div>
  );
}
