import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "filon.intent-offer-evidence.v1";

export type IntentOfferEvidence = {
  intentId: string;
  offerId: number;
  name: string;
  price: number;
  currency: string;
  merchantName: string;
  link: string;
  imageUrl: string | null;
  inStock: boolean | null;
  linkedAt: string;
};

export function linkOfferEvidence(current: IntentOfferEvidence[], evidence: IntentOfferEvidence) {
  return [evidence, ...current.filter((item) => item.intentId !== evidence.intentId)];
}

export function unlinkOfferEvidence(current: IntentOfferEvidence[], intentId: string) {
  return current.filter((item) => item.intentId !== intentId);
}

function isIntentOfferEvidence(value: unknown): value is IntentOfferEvidence {
  if (!value || typeof value !== "object") return false;
  const evidence = value as IntentOfferEvidence;
  return typeof evidence.intentId === "string" && typeof evidence.offerId === "number" && typeof evidence.name === "string" && typeof evidence.price === "number" && typeof evidence.currency === "string" && typeof evidence.merchantName === "string" && typeof evidence.link === "string" && (typeof evidence.imageUrl === "string" || evidence.imageUrl === null) && (typeof evidence.inStock === "boolean" || evidence.inStock === null) && typeof evidence.linkedAt === "string";
}

export async function readIntentOfferEvidence(): Promise<IntentOfferEvidence[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter(isIntentOfferEvidence) : [];
  } catch {
    return [];
  }
}

export async function saveIntentOfferEvidence(evidence: IntentOfferEvidence) {
  const next = linkOfferEvidence(await readIntentOfferEvidence(), evidence);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export async function removeIntentOfferEvidence(intentId: string) {
  const next = unlinkOfferEvidence(await readIntentOfferEvidence(), intentId);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
