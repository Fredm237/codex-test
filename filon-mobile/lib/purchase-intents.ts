import AsyncStorage from "@react-native-async-storage/async-storage";

import type { FilonLocale } from "@/lib/locale";

const KEY = "filon.purchase-intents.v1";
const LIMIT = 10;

export type PurchaseIntentDraft = {
  need: string;
  maxBudget: number | null;
  deadline: string | null;
  preferences: string | null;
};

export type PurchaseIntent = PurchaseIntentDraft & {
  id: string;
  createdAt: string;
  updatedAt: string;
};

export function normalizeIntentText(value: string | null | undefined) {
  const normalized = value?.trim().replace(/\s+/g, " ") ?? "";
  return normalized || null;
}

export function normalizePurchaseIntentDraft(draft: PurchaseIntentDraft): PurchaseIntentDraft {
  const budget = typeof draft.maxBudget === "number" && Number.isFinite(draft.maxBudget) && draft.maxBudget >= 0
    ? Math.round(draft.maxBudget * 100) / 100
    : null;
  return {
    need: normalizeIntentText(draft.need) ?? "",
    maxBudget: budget,
    deadline: normalizeIntentText(draft.deadline),
    preferences: normalizeIntentText(draft.preferences),
  };
}

export function isPurchaseIntentValid(draft: PurchaseIntentDraft) {
  return normalizePurchaseIntentDraft(draft).need.length >= 2;
}

export function buildPurchaseIntent(draft: PurchaseIntentDraft, now = new Date().toISOString(), existing?: PurchaseIntent): PurchaseIntent {
  const normalized = normalizePurchaseIntentDraft(draft);
  const id = existing?.id ?? `intent-${now.replace(/[^0-9]/g, "").slice(0, 14)}-${normalized.need.toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, "-").replace(/(^-|-$)/g, "").slice(0, 32) || "filon"}`;
  return { ...normalized, id, createdAt: existing?.createdAt ?? now, updatedAt: now };
}

export function upsertPurchaseIntent(current: PurchaseIntent[], intent: PurchaseIntent) {
  return [intent, ...current.filter((item) => item.id !== intent.id)].slice(0, LIMIT);
}

function isPurchaseIntent(value: unknown): value is PurchaseIntent {
  if (!value || typeof value !== "object") return false;
  const intent = value as PurchaseIntent;
  return typeof intent.id === "string" && typeof intent.need === "string" && typeof intent.createdAt === "string" && typeof intent.updatedAt === "string" && (typeof intent.maxBudget === "number" || intent.maxBudget === null) && (typeof intent.deadline === "string" || intent.deadline === null) && (typeof intent.preferences === "string" || intent.preferences === null);
}

export async function readPurchaseIntents(): Promise<PurchaseIntent[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter(isPurchaseIntent).slice(0, LIMIT) : [];
  } catch {
    return [];
  }
}

export async function readPurchaseIntent(id: string) {
  return (await readPurchaseIntents()).find((item) => item.id === id) ?? null;
}

export async function savePurchaseIntent(draft: PurchaseIntentDraft, existing?: PurchaseIntent) {
  const current = await readPurchaseIntents();
  const intent = buildPurchaseIntent(draft, new Date().toISOString(), existing);
  const next = upsertPurchaseIntent(current, intent);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return intent;
}

export async function removePurchaseIntent(id: string) {
  const next = (await readPurchaseIntents()).filter((item) => item.id !== id);
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export function describePurchaseIntent(intent: PurchaseIntent, locale: FilonLocale) {
  const budget = intent.maxBudget === null ? null : `${intent.maxBudget.toLocaleString(locale === "nl" ? "nl-BE" : locale === "fr" ? "fr-BE" : "en-BE", { maximumFractionDigits: 2 })} EUR`;
  if (locale === "nl") return [
    `Ik zoek ${intent.need}.`,
    budget ? `Maximumbudget: ${budget}.` : null,
    intent.deadline ? `Tegen: ${intent.deadline}.` : null,
    intent.preferences ? `Voorkeuren: ${intent.preferences}.` : null,
  ].filter(Boolean).join(" ");
  if (locale === "en") return [
    `I am looking for ${intent.need}.`,
    budget ? `Maximum budget: ${budget}.` : null,
    intent.deadline ? `Needed by: ${intent.deadline}.` : null,
    intent.preferences ? `Preferences: ${intent.preferences}.` : null,
  ].filter(Boolean).join(" ");
  return [
    `Je cherche ${intent.need}.`,
    budget ? `Budget maximum : ${budget}.` : null,
    intent.deadline ? `À avoir avant : ${intent.deadline}.` : null,
    intent.preferences ? `Préférences : ${intent.preferences}.` : null,
  ].filter(Boolean).join(" ");
}

export function getPurchaseIntentCatalogueParams(intent: PurchaseIntent) {
  return { q: intent.need, max: intent.maxBudget === null ? "" : String(intent.maxBudget) };
}
