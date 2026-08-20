import AsyncStorage from "@react-native-async-storage/async-storage";

export type StyleDirectionId = "minimal" | "classic" | "bold";
export type StyleSignal = { direction: StyleDirectionId; value: "affirmed" | "rejected"; at: string };
export type StyleDna = {
  primary: StyleDirectionId | null;
  confidence: "low" | "medium" | "high";
  evidenceCount: number;
  source: "declared" | "repeated_signals" | "unknown";
};

export type DiscoverDirection = { id: StyleDirectionId; title: string; description: string };
const STORAGE_KEY = "filon.intelligence.style-signals.v1";
const DIRECTIONS: StyleDirectionId[] = ["minimal", "classic", "bold"];

function isDirection(value: unknown): value is StyleDirectionId {
  return value === "minimal" || value === "classic" || value === "bold";
}

function recencyWeight(at: string, now: Date) {
  const days = Math.max(0, (now.getTime() - new Date(at).getTime()) / 86_400_000);
  if (days <= 14) return 1;
  if (days <= 60) return 0.7;
  return 0.35;
}

/** Ne promeut aucun signal isolé : deux signaux convergents minimum sont requis. */
export function resolveStyleDna(declaredStyle: StyleDirectionId | null, signals: StyleSignal[], now = new Date()): StyleDna {
  if (declaredStyle) return { primary: declaredStyle, confidence: "high", evidenceCount: 1, source: "declared" };
  const scores: Record<StyleDirectionId, number> = { minimal: 0, classic: 0, bold: 0 };
  const counts: Record<StyleDirectionId, number> = { minimal: 0, classic: 0, bold: 0 };
  for (const signal of signals) {
    if (!isDirection(signal.direction)) continue;
    const score = recencyWeight(signal.at, now) * (signal.value === "affirmed" ? 1 : -1);
    scores[signal.direction] += score;
    if (signal.value === "affirmed") counts[signal.direction] += 1;
  }
  let primary: StyleDirectionId | null = null;
  for (const direction of DIRECTIONS) if (counts[direction] >= 2 && scores[direction] >= 1.25 && (!primary || scores[direction] > scores[primary])) primary = direction;
  if (!primary) return { primary: null, confidence: "low", evidenceCount: signals.length, source: "unknown" };
  return { primary, confidence: counts[primary] >= 4 ? "high" : "medium", evidenceCount: counts[primary], source: "repeated_signals" };
}

export function getDiscoverDirections(dna: StyleDna): DiscoverDirection[] {
  const copy: Record<StyleDirectionId, Omit<DiscoverDirection, "id">> = {
    minimal: { title: "Minimal", description: "Des lignes nettes, peu de bruit visuel et des pièces polyvalentes." },
    classic: { title: "Classique", description: "Des repères intemporels, structurés et faciles à réemployer." },
    bold: { title: "Audacieux", description: "Un accent plus assumé, sans dégrader la lisibilité de la tenue." },
  };
  const ordered = dna.primary ? [dna.primary, ...DIRECTIONS.filter((direction) => direction !== dna.primary)] : DIRECTIONS;
  return ordered.map((id) => ({ id, ...copy[id] }));
}

export async function readStyleSignals(): Promise<StyleSignal[]> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is StyleSignal => typeof item === "object" && item !== null && isDirection((item as StyleSignal).direction) && ((item as StyleSignal).value === "affirmed" || (item as StyleSignal).value === "rejected") && typeof (item as StyleSignal).at === "string").slice(0, 80);
  } catch {
    return [];
  }
}

export async function appendStyleSignal(direction: StyleDirectionId, value: StyleSignal["value"]) {
  const existing = await readStyleSignals();
  const next = [{ direction, value, at: new Date().toISOString() }, ...existing].slice(0, 80);
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}
