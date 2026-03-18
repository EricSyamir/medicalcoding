import { NextRequest, NextResponse } from "next/server";
import { MOCK_RESULT } from "@/lib/mock";

export async function POST(req: NextRequest) {
  const body = await req.json();

  // Demo mode: return mock data without hitting the backend.
  // Enabled by:
  // - explicit client selection (body.demo === true), OR
  // - server config (DEMO_MODE=true), OR
  // - no BACKEND_URL configured
  const demoMode =
    body?.demo === true || process.env.DEMO_MODE === "true" || !process.env.BACKEND_URL;

  if (demoMode) {
    // Simulate realistic processing delay
    await new Promise((r) => setTimeout(r, 3500));
    return NextResponse.json(MOCK_RESULT);
  }

  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

  try {
    const upstream = await fetch(`${backendUrl}/api/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      // 120 s timeout for long notes
      signal: AbortSignal.timeout(120_000),
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      return NextResponse.json(
        { error: data.detail ?? "Backend error" },
        { status: upstream.status }
      );
    }

    return NextResponse.json(data);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { error: `Could not reach backend: ${msg}` },
      { status: 502 }
    );
  }
}
