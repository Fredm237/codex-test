import AsyncStorage from "@react-native-async-storage/async-storage";

import { isFilonOfferActionable, isFilonObservationFresh, normalizeFilonCurrency, normalizeFilonObservedAt } from "./filon-api";
import { isSafePartnerOfferUrl } from "./partner-offer";

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
  observedAt: string | null;
  evidenceCurrent: boolean;
  linkedAt: string;
};

export function linkOfferEvidence(current: IntentOfferEvidence[], evidence: IntentOfferEvidence) {
  return [evidence, ...current.filter((item) => item.intentId !== evidence.intentId)];
}

export function unlinkOfferEvidence(current: IntentOfferEvidence[], intentId: string) {
  return current.filter((item) => item.intentId !== intentId);
}

function nonEmptyText(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

export function normalizeIntentOfferEvidence(value: unknown, now: number | Date = Date.now()): IntentOfferEvidence | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Record<string, unknown>;
  const intentId = nonEmptyText(candidate.intentId);
  const offerId = candidate.offerId;
  const name = nonEmptyText(candidate.name);
  const price = candidate.price;
  const currency = normalizeFilonCurrency(candidate.currency);
  const merchantName = nonEmptyText(candidate.merchantName);
  const link = nonEmptyText(candidate.link);
  const linkedAt = normalizeFilonObservedAt(candidate.linkedAt);
  if (
    intentId === null
    || typeof offerId !== "number"
    || !Number.isInteger(offerId)
    || offerId <= 0
    || name === null
    || typeof price !== "number"
    || !Number.isFinite(price)
    || price <= 0
    || currency === null
    || merchantName === null
    || link === null
    || !isSafePartnerOfferUrl(link)
    || linkedAt === null
  ) return null;

  const observedAt = normalizeFilonObservedAt(candidate.observedAt);
  const evidenceCurrent = candidate.evidenceCurrent === true;
  const observationIsFresh = evidenceCurrent && isFilonObservationFresh(observedAt, now);
  return {
    intentId,
    offerId,
    name,
    price,
    currency,
    merchantName,
    link,
    imageUrl: nonEmptyText(candidate.imageUrl),
    inStock: observationIsFresh && candidate.inStock === true ? true : observationIsFresh && candidate.inStock === false ? false : null,
    // Les anciennes liaisons restent visibles, mais sans date/snapshot elles
    // ne peuvent plus ouvrir la création d'une alerte.
    observedAt,
    evidenceCurrent,
    linkedAt,
  };
}

export function normalizeIntentOfferEvidenceList(value: unknown, now: number | Date = Date.now()) {
  if (!Array.isArray(value)) return [];
  return value.reduce<IntentOfferEvidence[]>((items, candidate) => {
    const normalized = normalizeIntentOfferEvidence(candidate, now);
    if (normalized && !items.some((item) => item.intentId === normalized.intentId)) items.push(normalized);
    return items;
  }, []);
}

export function isIntentOfferEvidenceCurrent(evidence: IntentOfferEvidence, now: number | Date = Date.now()) {
  return isSafePartnerOfferUrl(evidence.link) && isFilonOfferActionable({
    price: evidence.price,
    currency: evidence.currency,
    inStock: evidence.inStock,
    observedAt: evidence.observedAt,
    evidenceCurrent: evidence.evidenceCurrent,
  }, now);
}

export async function readIntentOfferEvidence(): Promise<IntentOfferEvidence[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try {
    return normalizeIntentOfferEvidenceList(JSON.parse(raw));
  } catch {
    return [];
  }
}

export async function saveIntentOfferEvidence(evidence: IntentOfferEvidence) {
  const normalized = normalizeIntentOfferEvidence(evidence);
  if (!normalized) throw new TypeError("Offre liée incomplète ou non sûre");
  const next = linkOfferEvidence(await readIntentOfferEvidence(), normalized);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export async function removeIntentOfferEvidence(intentId: string) {
  const next = unlinkOfferEvidence(await readIntentOfferEvidence(), intentId);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}
