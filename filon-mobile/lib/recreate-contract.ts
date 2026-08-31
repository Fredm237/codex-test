import type { FilonOutfitLocale, OutfitPublicMessage } from "./filon-outfit-i18n";

export type RecreateLocale = FilonOutfitLocale;
export type RecreateConfidence = "certain" | "probable" | "unknown";
export type RecreateObservation = {
  label: string;
  confidence: RecreateConfidence;
  explanation: string;
};

export type RecreateAnalysis = {
  locale: RecreateLocale;
  summary: string;
  silhouette: RecreateObservation[];
  palette: RecreateObservation[];
  visiblePieces: RecreateObservation[];
  limits: string[];
};

export type RecreatePromptMessage =
  | { role: "system"; content: string }
  | { role: "user"; content: [{ type: "text"; text: string }, { type: "image_url"; image_url: { url: string; detail: "low" } }] };

const promptCopy: Record<RecreateLocale, { system: string; user: string; invalidImage: string; invalidResponse: string }> = {
  fr: {
    system: "Tu analyses une inspiration mode pour FILON. Retourne UNIQUEMENT un objet JSON avec summary, silhouette, palette, visiblePieces et limits. Tous les champs textuels (summary, label, explanation et limits) doivent être rédigés en français. Chaque observation doit avoir label, confidence (certain|probable|unknown) et explanation. Décris seulement ce qui est visuellement observable. N’invente jamais marque, prix, disponibilité, matière précise, identité, taille, genre, lieu ou saison. Quand l’image ne permet pas de conclure, indique unknown et ajoute une limite.",
    user: "Analyse cette inspiration de tenue. Distingue explicitement le certain, le probable et l’inconnu. Réponds en français.",
    invalidImage: "L’inspiration doit être une image HTTPS publique valide ou une image locale prise en charge.",
    invalidResponse: "L’analyse visuelle n’a pas retourné de résultat structuré.",
  },
  nl: {
    system: "Je analyseert mode-inspiratie voor FILON. Geef UITSLUITEND een JSON-object terug met summary, silhouette, palette, visiblePieces en limits. Alle tekstvelden (summary, label, explanation en limits) moeten in het Nederlands zijn geschreven. Elke observatie bevat label, confidence (certain|probable|unknown) en explanation. Beschrijf alleen wat visueel waarneembaar is. Verzin nooit merk, prijs, beschikbaarheid, exacte stof, identiteit, maat, gender, locatie of seizoen. Gebruik unknown en voeg een beperking toe wanneer het beeld geen conclusie toelaat.",
    user: "Analyseer deze outfitinspiratie. Maak expliciet onderscheid tussen zeker, waarschijnlijk en onbekend. Antwoord in het Nederlands.",
    invalidImage: "De inspiratie moet een geldige openbare HTTPS-afbeelding of een ondersteunde lokale afbeelding zijn.",
    invalidResponse: "De visuele analyse heeft geen gestructureerd resultaat opgeleverd.",
  },
  en: {
    system: "You analyse fashion inspiration for FILON. Return ONLY a JSON object with summary, silhouette, palette, visiblePieces and limits. Every text field (summary, label, explanation and limits) must be written in English. Each observation must contain label, confidence (certain|probable|unknown) and explanation. Describe only what is visually observable. Never invent a brand, price, availability, exact material, identity, size, gender, location or season. Use unknown and add a limitation whenever the image does not support a conclusion.",
    user: "Analyse this outfit inspiration. Explicitly distinguish what is certain, probable and unknown. Answer in English.",
    invalidImage: "The inspiration must be a valid public HTTPS image or a supported local image.",
    invalidResponse: "The visual analysis did not return a structured result.",
  },
};

export function buildRecreatePrompt(imageUrl: string, locale: RecreateLocale): RecreatePromptMessage[] {
  const text = promptCopy[locale];
  return [
    { role: "system", content: text.system },
    { role: "user", content: [{ type: "text", text: text.user }, { type: "image_url", image_url: { url: imageUrl, detail: "low" } }] },
  ];
}

export function recreateServerError(locale: RecreateLocale, code: "invalidImage" | "invalidResponse") {
  return promptCopy[locale][code];
}

export function isRecreateAnalysisForLocale(analysis: RecreateAnalysis, locale: RecreateLocale) {
  return analysis.locale === locale;
}

export function isSafeRecreateImageUrl(url: string) {
  if (/^data:image\/(jpeg|jpg|png|webp);base64,[a-z0-9+/=]+$/i.test(url)) return url.length <= 8_000_000;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" && parsed.hostname.length > 0 && url.length <= 2048;
  } catch {
    return false;
  }
}

/** Maintient le calibrage : la confiance exprime l’observabilité visuelle, jamais une vérité marchande. */
export function explanationForConfidence(confidence: RecreateConfidence): OutfitPublicMessage {
  if (confidence === "certain") return { code: "recreate.certain" };
  if (confidence === "probable") return { code: "recreate.probable" };
  return { code: "recreate.unknown" };
}
