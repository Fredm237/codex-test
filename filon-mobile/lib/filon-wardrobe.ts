import AsyncStorage from "@react-native-async-storage/async-storage";

import type { OutfitRole } from "./filon-intelligence";

export type WardrobeAttributes = {
  color: string | null;
  size: string | null;
  material: string | null;
};

export type WardrobeItem = {
  schemaVersion: 2;
  id: string;
  label: string;
  role: OutfitRole;
  attributes: WardrobeAttributes;
  provenance: "user_declared";
  storageScope: "local_device";
  createdAt: string;
  updatedAt: string;
};

export type WardrobeItemInput = {
  label: string;
  role: OutfitRole;
  attributes?: Partial<WardrobeAttributes>;
};

const STORAGE_KEY = "filon.intelligence.wardrobe.v2";
const LEGACY_STORAGE_KEY = "filon.intelligence.wardrobe.v1";
const LIMIT = 40;
let wardrobeMutationTail: Promise<void> = Promise.resolve();

function isRole(value: unknown): value is OutfitRole {
  return value === "base" || value === "structure" || value === "footwear" || value === "accessory";
}

function canonical(value: string) {
  return value.trim().toLocaleLowerCase().replace(/\s+/g, " ");
}

function boundedText(value: unknown, limit: number) {
  if (typeof value !== "string") return null;
  const normalized = value.trim().replace(/\s+/g, " ");
  return normalized.length > 0 ? normalized.slice(0, limit) : null;
}

function normalizedTimestamp(value: unknown) {
  if (typeof value !== "string") return null;
  const milliseconds = Date.parse(value);
  return Number.isFinite(milliseconds) ? new Date(milliseconds).toISOString() : null;
}

function normalizeAttributes(value: unknown): WardrobeAttributes {
  const attributes = value && typeof value === "object" ? value as Record<string, unknown> : {};
  return {
    color: boundedText(attributes.color, 64),
    size: boundedText(attributes.size, 64),
    material: boundedText(attributes.material, 64),
  };
}

export function normalizeWardrobeItem(value: unknown): WardrobeItem | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Record<string, unknown>;
  const id = boundedText(candidate.id, 96);
  const label = boundedText(candidate.label, 120);
  const createdAt = normalizedTimestamp(candidate.createdAt);
  const updatedAt = normalizedTimestamp(candidate.updatedAt);
  if (
    id === null
    || label === null
    || !isRole(candidate.role)
    || createdAt === null
    || updatedAt === null
    || Date.parse(createdAt) > Date.parse(updatedAt)
  ) return null;
  return {
    schemaVersion: 2,
    id,
    label,
    role: candidate.role,
    attributes: normalizeAttributes(candidate.attributes),
    provenance: "user_declared",
    storageScope: "local_device",
    createdAt,
    updatedAt,
  };
}

export function sanitizeWardrobe(raw: unknown): WardrobeItem[] {
  if (!Array.isArray(raw)) return [];
  const items: WardrobeItem[] = [];
  for (const candidate of raw) {
    const normalized = normalizeWardrobeItem(candidate);
    if (!normalized) continue;
    if (items.some((item) => item.id === normalized.id)) continue;
    if (items.some((item) => item.role === normalized.role && canonical(item.label) === canonical(normalized.label))) continue;
    items.push(normalized);
    if (items.length === LIMIT) break;
  }
  return items;
}

export function createWardrobeItem(input: WardrobeItemInput, id: string, at: string): WardrobeItem | null {
  return normalizeWardrobeItem({
    schemaVersion: 2,
    id,
    label: input.label,
    role: input.role,
    attributes: input.attributes,
    provenance: "user_declared",
    storageScope: "local_device",
    createdAt: at,
    updatedAt: at,
  });
}

export function mergeWardrobeItems(items: WardrobeItem[], next: WardrobeItem): WardrobeItem[] {
  const duplicate = items.find((item) => item.role === next.role && canonical(item.label) === canonical(next.label));
  if (duplicate) {
    return [{ ...next, id: duplicate.id, createdAt: duplicate.createdAt }, ...items.filter((item) => item.id !== duplicate.id)].slice(0, LIMIT);
  }
  return [next, ...items.filter((item) => item.id !== next.id)].slice(0, LIMIT);
}

export function wardrobeCoverage(items: WardrobeItem[]) {
  const sanitized = sanitizeWardrobe(items);
  const roles = new Set(sanitized.map((item) => item.role));
  return {
    itemCount: sanitized.length,
    representedRoles: [...roles].sort(),
    missingRoles: (["base", "structure", "footwear", "accessory"] as OutfitRole[]).filter((role) => !roles.has(role)),
    score: null,
    measurementStatus: "not_calibrated" as const,
  };
}

async function readStoredWardrobe(): Promise<WardrobeItem[]> {
  const current = await AsyncStorage.getItem(STORAGE_KEY);
  if (current) {
    try { return sanitizeWardrobe(JSON.parse(current)); } catch { return []; }
  }
  const legacy = await AsyncStorage.getItem(LEGACY_STORAGE_KEY);
  if (!legacy) return [];
  try {
    const migrated = sanitizeWardrobe(JSON.parse(legacy));
    if (migrated.length > 0) await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(migrated));
    await AsyncStorage.removeItem(LEGACY_STORAGE_KEY);
    return migrated;
  } catch {
    return [];
  }
}

export async function readWardrobe(): Promise<WardrobeItem[]> {
  return readStoredWardrobe();
}

function updateWardrobe(transition: (current: WardrobeItem[]) => WardrobeItem[]) {
  const operation = wardrobeMutationTail.then(async () => {
    const current = await readStoredWardrobe();
    const next = transition(current);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    return next;
  });
  wardrobeMutationTail = operation.then(() => undefined, () => undefined);
  return operation;
}

export async function saveWardrobeItem(input: WardrobeItemInput): Promise<WardrobeItem[]> {
  const now = new Date().toISOString();
  const item = createWardrobeItem(input, `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`, now);
  if (!item) return readStoredWardrobe();
  return updateWardrobe((current) => mergeWardrobeItems(current, item));
}

export function removeWardrobeItem(id: string): Promise<WardrobeItem[]> {
  return updateWardrobe((current) => current.filter((item) => item.id !== id));
}

/** Erasure removes both the current store and any unmigrated legacy copy. */
export async function clearWardrobe(): Promise<WardrobeItem[]> {
  const operation = wardrobeMutationTail.then(async () => {
    await AsyncStorage.multiRemove([STORAGE_KEY, LEGACY_STORAGE_KEY]);
    return [] as WardrobeItem[];
  });
  wardrobeMutationTail = operation.then(() => undefined, () => undefined);
  return operation;
}
