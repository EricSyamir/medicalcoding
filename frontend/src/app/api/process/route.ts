import { NextRequest, NextResponse } from "next/server";
import { MOCK_RESULT } from "@/lib/mock";
import { runPipeline } from "@/lib/pipeline/pipeline";

export const maxDuration = 120; // Vercel Pro allows up to 300s; free tier caps at 60s

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));

  // Demo mode: return mock data immediately
  const demoMode =
    body?.demo === true ||
    process.env.DEMO_MODE === "true";

  if (demoMode) {
    await new Promise((r) => setTimeout(r, 2500)); // simulate processing delay
    return NextResponse.json(MOCK_RESULT);
  }

  // Production: run the full pipeline in-process
  const noteText: string  = String(body?.note_text ?? "").trim();
  const provider: string  = String(body?.provider  ?? "gemini");
  const model:    string  = String(
    body?.model ??
    (provider === "gemini" ? "gemini-2.0-flash" : "gpt-4o"),
  );

  // API key resolution: request body → Vercel env vars
  const apiKey: string =
    String(body?.api_key ?? "") ||
    (provider === "gemini"
      ? (process.env.GOOGLE_API_KEY ?? process.env.GEMINI_API_KEY ?? "")
      : (process.env.OPENAI_API_KEY ?? ""));

  if (!noteText) {
    return NextResponse.json({ error: "note_text is required" }, { status: 400 });
  }

  if (!apiKey) {
    return NextResponse.json(
      {
        error:
          provider === "gemini"
            ? "No Gemini API key found. Enter your key in the UI, or set GOOGLE_API_KEY in Vercel environment variables."
            : "No OpenAI API key found. Enter your key in the UI, or set OPENAI_API_KEY in Vercel environment variables.",
      },
      { status: 401 },
    );
  }

  try {
    const result = await runPipeline({ noteText, provider, model, apiKey });
    return NextResponse.json(result);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);

    if (msg.includes("429") || /quota|rate.?limit/i.test(msg)) {
      return NextResponse.json(
        { error: "API quota exceeded. Check your plan at https://ai.dev/rate-limit or try again later." },
        { status: 429 },
      );
    }
    if (msg.includes("401") || msg.includes("403") || /invalid.{0,20}key|api.?key/i.test(msg)) {
      return NextResponse.json(
        { error: "Invalid API key. Please check it and try again." },
        { status: 401 },
      );
    }
    if (msg.includes("404") || /not.found|model/i.test(msg)) {
      return NextResponse.json(
        { error: `Model not found: ${model}. Try 'gemini-2.0-flash' or 'gpt-4o'.` },
        { status: 422 },
      );
    }

    console.error("[api/process] pipeline error:", msg);
    return NextResponse.json(
      { error: `Pipeline error: ${msg.slice(0, 300)}` },
      { status: 500 },
    );
  }
}
