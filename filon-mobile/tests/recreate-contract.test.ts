import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { buildRecreatePrompt, explanationForConfidence, isRecreateAnalysisForLocale, isSafeRecreateImageUrl, recreateServerError, type RecreateAnalysis } from "../lib/recreate-contract";
import { resolveOutfitPublicMessage } from "../lib/filon-outfit-i18n";

describe("Contrat Recreate", () => {
  it("n’accepte qu’une inspiration HTTPS publique", () => {
    expect(isSafeRecreateImageUrl("https://images.example.com/look.jpg")).toBe(true);
    expect(isSafeRecreateImageUrl("http://images.example.com/look.jpg")).toBe(false);
    expect(isSafeRecreateImageUrl("javascript:alert(1)")).toBe(false);
  });

  it("accepte une image locale encodée sous une limite stricte", () => {
    expect(isSafeRecreateImageUrl("data:image/jpeg;base64,aGVsbG8=")).toBe(true);
    expect(isSafeRecreateImageUrl("data:text/plain;base64,aGVsbG8=")).toBe(false);
  });

  it("conserve une explication calibrée par niveau de confiance", () => {
    expect(explanationForConfidence("certain")).toEqual({ code: "recreate.certain" });
    expect(explanationForConfidence("unknown")).toEqual({ code: "recreate.unknown" });
    expect(resolveOutfitPublicMessage(explanationForConfidence("certain"), "fr")).toContain("clairement observable");
    expect(resolveOutfitPublicMessage(explanationForConfidence("unknown"), "en")).toContain("ambiguous");
  });

  it.each([
    ["fr", "en français", "Réponds en français"],
    ["nl", "in het Nederlands", "Antwoord in het Nederlands"],
    ["en", "written in English", "Answer in English"],
  ] as const)("construit un prompt Recreate entièrement cohérent en %s", (locale, systemMarker, userMarker) => {
    const messages = buildRecreatePrompt("https://images.example.com/look.jpg", locale);
    expect(messages[0].content).toContain(systemMarker);
    expect(messages[0].content).toContain("summary");
    expect(messages[0].content).toContain("unknown");
    const user = messages[1];
    expect(typeof user.content).not.toBe("string");
    if (typeof user.content !== "string") {
      expect(user.content[0].text).toContain(userMarker);
      expect(user.content[1].image_url.url).toBe("https://images.example.com/look.jpg");
    }
  });

  it("associe chaque analyse dynamique à sa langue et masque un résultat conservé après changement", () => {
    const analysis: RecreateAnalysis = { locale: "fr", summary: "Silhouette droite", silhouette: [], palette: [], visiblePieces: [], limits: [] };
    expect(isRecreateAnalysisForLocale(analysis, "fr")).toBe(true);
    expect(isRecreateAnalysisForLocale(analysis, "nl")).toBe(false);
    expect(recreateServerError("nl", "invalidResponse")).toContain("gestructureerd");
    expect(recreateServerError("en", "invalidImage")).toContain("valid public HTTPS image");
  });

  it("rend aussi l’erreur Recreate dans la langue active", () => {
    const studio = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "..", "app", "outfit-studio.tsx"), "utf8");
    expect(studio).toContain('title={mode === "recreate" ? recreateText.error : text.error}');
  });
});
