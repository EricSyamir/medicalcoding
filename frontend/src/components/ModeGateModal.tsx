"use client";

import { useEffect, useState } from "react";
import { KeyRound, Sparkles, ShieldAlert } from "lucide-react";
import clsx from "clsx";

export type AppMode = "demo" | "production";

interface Props {
  open: boolean;
  onSelect: (mode: AppMode) => void;
  onClose?: () => void;
}

export default function ModeGateModal({ open, onSelect, onClose }: Props) {
  const [visible, setVisible] = useState(open);

  useEffect(() => setVisible(open), [open]);
  useEffect(() => {
    const onEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape" && onClose) onClose();
    };
    window.addEventListener("keydown", onEsc);
    return () => window.removeEventListener("keydown", onEsc);
  }, [onClose]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-lg rounded-2xl bg-white border border-slate-200 shadow-xl overflow-hidden animate-slide-up">
        <div className="p-6">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">
            Choose Mode
          </p>
          <h2 className="text-xl font-extrabold text-slate-900 leading-tight">
            Demo or Production?
          </h2>
          <p className="text-sm text-slate-500 mt-2 leading-relaxed">
            Demo mode uses a <span className="font-semibold">mock LLM</span> and returns a realistic example result
            instantly — no API key required. Production mode runs the real pipeline and requires an API key.
          </p>

          <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-3">
            <button
              onClick={() => onSelect("demo")}
              className={clsx(
                "rounded-2xl border p-4 text-left hover:shadow-sm transition-all",
                "border-navy-200 bg-navy-50"
              )}
            >
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-navy-800 text-white flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-cyan-300" />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-900">Demo</p>
                  <p className="text-xs text-slate-500">Mock LLM · No API key</p>
                </div>
              </div>
              <ul className="mt-3 text-xs text-slate-600 space-y-1">
                <li>- Great for Vercel preview links</li>
                <li>- Works even when quotas are exhausted</li>
                <li>- Shows full reviewer workflow</li>
              </ul>
            </button>

            <button
              onClick={() => onSelect("production")}
              className={clsx(
                "rounded-2xl border p-4 text-left hover:shadow-sm transition-all",
                "border-slate-200 bg-white"
              )}
            >
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-slate-900 text-white flex items-center justify-center">
                  <KeyRound className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-900">Production</p>
                  <p className="text-xs text-slate-500">Real LLM · Requires API key</p>
                </div>
              </div>
              <ul className="mt-3 text-xs text-slate-600 space-y-1">
                <li>- Uses your deployed backend</li>
                <li>- Runs extraction + coding live</li>
                <li>- Subject to provider quota</li>
              </ul>
            </button>
          </div>

          <div className="mt-4 flex items-start gap-2 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3">
            <ShieldAlert className="w-4 h-4 text-amber-700 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-amber-800 leading-relaxed">
              Do not paste real patient identifiers. For Production mode, the API key is used only for the request and
              is not stored by the UI.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

