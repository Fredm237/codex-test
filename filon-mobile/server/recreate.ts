import { z } from "zod";

import type { RecreateAnalysis } from "../lib/recreate-contract";
import { isSafeRecreateImageUrl } from "../lib/recreate-contract";
import { invokeLLM } from "./_core/llm";

const observationSchema = z.object({ label: z.string().trim().min(1).max(120), confidence: z.enum(["certain", "probable", "unknown"]), explanation: z.string().trim().min(1).max(240) });
const analysisSchema = z.object({ summary: z.string().trim().min(1).max(420), silhouette: z.array(observationSchema).max(5), palette: z.array(observationSchema).max(5), visiblePieces: z.array(observationSchema).max(8), limits: z.array(z.string().trim().min(1).max(240)).max(5) });

export async function analyzeRecreateInspiration(imageUrl: string): Promise<RecreateAnalysis> {
  if (!isSafeRecreateImageUrl(imageUrl)) throw new Error("L’inspiration doit être une image HTTPS publique valide.");
  const response = await invokeLLM({
    model: "gemini-3-flash-preview",
    max_tokens: 1800,
    response_format: { type: "json_object" },
    messages: [
      { role: "system", content: "Tu analyses une inspiration mode pour FILON. Retourne UNIQUEMENT un objet JSON avec summary, silhouette, palette, visiblePieces et limits. Chaque observation doit avoir label, confidence (certain|probable|unknown) et explanation. Décris seulement ce qui est visuellement observable. N’invente jamais marque, prix, disponibilité, matière précise, identité, taille, genre, lieu ou saison. Quand l’image ne permet pas de conclure, indique unknown et ajoute une limite." },
      { role: "user", content: [{ type: "text", text: "Analyse cette inspiration de tenue. Distingue explicitement le certain, le probable et l’inconnu." }, { type: "image_url", image_url: { url: imageUrl, detail: "low" } }] },
    ],
  });
  const content = response.choices[0]?.message.content;
  if (typeof content !== "string") throw new Error("L’analyse visuelle n’a pas retourné de résultat structuré.");
  return analysisSchema.parse(JSON.parse(content));
}
