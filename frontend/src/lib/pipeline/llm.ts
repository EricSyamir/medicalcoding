/**
 * Unified LLM client — supports Gemini and OpenAI from a single interface.
 * Runs inside Next.js serverless functions (Node.js runtime).
 */

export async function generateJSON(
  provider: string,
  apiKey:   string,
  model:    string,
  systemPrompt: string,
  userMessage:  string,
): Promise<Record<string, unknown>> {
  if (provider === "gemini") {
    const { GoogleGenerativeAI } = await import("@google/generative-ai");
    const genai  = new GoogleGenerativeAI(apiKey);
    const m      = genai.getGenerativeModel({
      model,
      generationConfig: { responseMimeType: "application/json", temperature: 0 },
    });
    const result = await m.generateContent(`${systemPrompt}\n\n---\n\n${userMessage}`);
    const text   = result.response.text();
    if (!text) throw new Error("Gemini returned empty response");
    return JSON.parse(text);
  }

  // OpenAI
  const { default: OpenAI } = await import("openai");
  const client   = new OpenAI({ apiKey });
  const response = await client.chat.completions.create({
    model,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user",   content: userMessage  },
    ],
    response_format: { type: "json_object" },
    temperature: 0,
  });
  const text = response.choices[0].message.content ?? "{}";
  return JSON.parse(text);
}
