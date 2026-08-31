import { z } from "zod";

import type { RecreateAnalysis, RecreateLocale } from "../lib/recreate-contract";
import { buildRecreatePrompt, isSafeRecreateImageUrl, recreateServerError } from "../lib/recreate-contract";
import { invokeLLM } from "./_core/llm";

const observationSchema = z.object({ label: z.string().trim().min(1).max(120), confidence: z.enum(["certain", "probable", "unknown"]), explanation: z.string().trim().min(1).max(240) });
const analysisSchema = z.object({ summary: z.string().trim().min(1).max(420), silhouette: z.array(observationSchema).max(5), palette: z.array(observationSchema).max(5), visiblePieces: z.array(observationSchema).max(8), limits: z.array(z.string().trim().min(1).max(240)).max(5) });

export async function analyzeRecreateInspiration(imageUrl: string, locale: RecreateLocale): Promise<RecreateAnalysis> {
  if (!isSafeRecreateImageUrl(imageUrl)) throw new Error(recreateServerError(locale, "invalidImage"));
  const response = await invokeLLM({
    model: "gemini-3-flash-preview",
    max_tokens: 1800,
    response_format: { type: "json_object" },
    messages: buildRecreatePrompt(imageUrl, locale),
  });
  const content = response.choices[0]?.message.content;
  if (typeof content !== "string") throw new Error(recreateServerError(locale, "invalidResponse"));
  return { ...analysisSchema.parse(JSON.parse(content)), locale };
}
