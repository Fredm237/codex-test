export type RecreateConfidence = "certain" | "probable" | "unknown";
export type RecreateObservation = {
  label: string;
  confidence: RecreateConfidence;
  explanation: string;
};

export type RecreateAnalysis = {
  summary: string;
  silhouette: RecreateObservation[];
  palette: RecreateObservation[];
  visiblePieces: RecreateObservation[];
  limits: string[];
};

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
export function explanationForConfidence(confidence: RecreateConfidence) {
  if (confidence === "certain") return "Élément clairement observable sur l’inspiration fournie.";
  if (confidence === "probable") return "Interprétation visuelle plausible ; à confirmer dans une pièce réelle.";
  return "Élément insuffisamment visible ou ambigu ; FILON ne l’utilise pas comme contrainte forte.";
}
