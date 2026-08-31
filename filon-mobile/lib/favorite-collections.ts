import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "filon.favorite-collections.v1";
let favoriteCollectionMutationTail: Promise<void> = Promise.resolve();

export type FavoriteCollection = { id: string; name: string; createdAt: string; updatedAt: string };
export type CollectionTombstone = { name: string; createdAt: string; deletedAt: string };
export type FavoriteCollectionState = { collections: FavoriteCollection[]; memberships: Record<string, string[]>; tombstones: Record<string, CollectionTombstone>; lastSyncedAt: string | null; pendingSync: boolean };
export type RemoteFavoriteCollection = { clientId: string; name: string; createdAt: string; updatedAt: string; deletedAt: string | null; offerIds: number[] };
export const emptyFavoriteCollectionState: FavoriteCollectionState = { collections: [], memberships: {}, tombstones: {}, lastSyncedAt: null, pendingSync: false };

export function normalizeCollectionName(value: string) { return value.trim().replace(/\s+/g, " ").slice(0, 42); }

export function createFavoriteCollection(current: FavoriteCollectionState, name: string, id: string, createdAt: string): FavoriteCollectionState {
  const normalized = normalizeCollectionName(name);
  if (!normalized || current.collections.some((collection) => collection.name.toLocaleLowerCase() === normalized.toLocaleLowerCase())) return current;
  return { ...current, collections: [...current.collections, { id, name: normalized, createdAt, updatedAt: createdAt }] };
}

export function renameFavoriteCollection(current: FavoriteCollectionState, collectionId: string, name: string, updatedAt: string): FavoriteCollectionState {
  const normalized = normalizeCollectionName(name);
  if (!normalized || current.collections.some((item) => item.id !== collectionId && item.name.toLocaleLowerCase() === normalized.toLocaleLowerCase())) return current;
  return { ...current, collections: current.collections.map((item) => item.id === collectionId ? { ...item, name: normalized, updatedAt } : item) };
}

export function markFavoriteCollectionsPending(current: FavoriteCollectionState): FavoriteCollectionState {
  return { ...current, pendingSync: true };
}

export function markFavoriteCollectionsReconciled(current: FavoriteCollectionState, at: string): FavoriteCollectionState {
  return { ...current, pendingSync: false, lastSyncedAt: at };
}

export function toggleFavoriteCollectionMembership(current: FavoriteCollectionState, offerId: number, collectionId: string): FavoriteCollectionState {
  if (!current.collections.some((collection) => collection.id === collectionId)) return current;
  const key = String(offerId);
  const existing = current.memberships[key] ?? [];
  const next = existing.includes(collectionId) ? existing.filter((id) => id !== collectionId) : [...existing, collectionId];
  return { ...current, memberships: { ...current.memberships, [key]: next } };
}

export function deleteFavoriteCollection(current: FavoriteCollectionState, collectionId: string, deletedAt: string): FavoriteCollectionState {
  const collection = current.collections.find((item) => item.id === collectionId);
  if (!collection) return current;
  const memberships = Object.fromEntries(Object.entries(current.memberships).map(([offerId, ids]) => [offerId, ids.filter((id) => id !== collectionId)]));
  return { ...current, collections: current.collections.filter((item) => item.id !== collectionId), memberships, tombstones: { ...current.tombstones, [collectionId]: { name: collection.name, createdAt: collection.createdAt, deletedAt } } };
}

export function collectionsForFavorite(current: FavoriteCollectionState, offerId: number) {
  const membership = new Set(current.memberships[String(offerId)] ?? []);
  return current.collections.filter((collection) => membership.has(collection.id));
}

export function mergeRemoteFavoriteCollections(current: FavoriteCollectionState, remote: RemoteFavoriteCollection[]): FavoriteCollectionState {
  let next: FavoriteCollectionState = { ...current, collections: [...current.collections], memberships: { ...current.memberships }, tombstones: { ...current.tombstones } };
  for (const collection of remote) {
    if (collection.deletedAt) {
      const localTombstone = next.tombstones[collection.clientId];
      if (!localTombstone || Date.parse(collection.deletedAt) >= Date.parse(localTombstone.deletedAt)) {
        const localExists = next.collections.some((item) => item.id === collection.clientId);
        next = localExists ? deleteFavoriteCollection(next, collection.clientId, collection.deletedAt) : { ...next, tombstones: { ...next.tombstones, [collection.clientId]: { name: collection.name, createdAt: collection.createdAt, deletedAt: collection.deletedAt } } };
      }
      continue;
    }
    if (next.tombstones[collection.clientId]) continue;
    const local = next.collections.find((item) => item.id === collection.clientId);
    if (!local) next = createFavoriteCollection(next, collection.name, collection.clientId, collection.createdAt);
    else if (Date.parse(collection.updatedAt) > Date.parse(local.updatedAt)) next = { ...next, collections: next.collections.map((item) => item.id === collection.clientId ? { ...item, name: normalizeCollectionName(collection.name), updatedAt: collection.updatedAt } : item) };
    for (const offerId of collection.offerIds.filter((id) => Number.isInteger(id) && id > 0)) {
      const key = String(offerId);
      const memberships = next.memberships[key] ?? [];
      if (!memberships.includes(collection.clientId)) next = { ...next, memberships: { ...next.memberships, [key]: [...memberships, collection.clientId] } };
    }
  }
  return next;
}

export function buildFavoriteCollectionSyncPayload(state: FavoriteCollectionState): RemoteFavoriteCollection[] {
  return [
    ...state.collections.map((collection) => ({
      clientId: collection.id,
      name: collection.name,
      createdAt: collection.createdAt,
      updatedAt: collection.updatedAt,
      deletedAt: null,
      offerIds: Object.entries(state.memberships)
        .filter(([, ids]) => ids.includes(collection.id))
        .map(([offerId]) => Number(offerId))
        .filter((offerId) => Number.isInteger(offerId) && offerId > 0),
    })),
    ...Object.entries(state.tombstones).map(([clientId, value]) => ({
      clientId,
      name: value.name,
      createdAt: value.createdAt,
      updatedAt: value.deletedAt,
      deletedAt: value.deletedAt,
      offerIds: [],
    })),
  ];
}

function collectionSnapshot(items: RemoteFavoriteCollection[]) {
  return [...items]
    .map((item) => ({ ...item, offerIds: [...item.offerIds].sort((left, right) => left - right) }))
    .sort((left, right) => left.clientId.localeCompare(right.clientId));
}

export function reconcileFavoriteCollectionsAfterSync(current: FavoriteCollectionState, remote: RemoteFavoriteCollection[], syncedPayload: RemoteFavoriteCollection[], at: string): FavoriteCollectionState {
  const unchanged = JSON.stringify(collectionSnapshot(buildFavoriteCollectionSyncPayload(current))) === JSON.stringify(collectionSnapshot(syncedPayload));
  if (!unchanged) return markFavoriteCollectionsPending(current);
  return markFavoriteCollectionsReconciled(mergeRemoteFavoriteCollections(current, remote), at);
}

export async function readFavoriteCollections(): Promise<FavoriteCollectionState> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return emptyFavoriteCollectionState;
  try {
    const parsed = JSON.parse(raw) as Partial<FavoriteCollectionState>;
    return { collections: Array.isArray(parsed.collections) ? parsed.collections.filter((item): item is FavoriteCollection => Boolean(item && typeof item.id === "string" && typeof item.name === "string" && typeof item.createdAt === "string")).map((item) => ({ ...item, updatedAt: typeof item.updatedAt === "string" ? item.updatedAt : item.createdAt })) : [], memberships: parsed.memberships && typeof parsed.memberships === "object" ? parsed.memberships as Record<string, string[]> : {}, tombstones: parsed.tombstones && typeof parsed.tombstones === "object" ? parsed.tombstones as Record<string, CollectionTombstone> : {}, lastSyncedAt: typeof parsed.lastSyncedAt === "string" ? parsed.lastSyncedAt : null, pendingSync: parsed.pendingSync === true };
  } catch { return emptyFavoriteCollectionState; }
}

export async function saveFavoriteCollections(state: FavoriteCollectionState) { await AsyncStorage.setItem(KEY, JSON.stringify(state)); return state; }

export function updateFavoriteCollections(transition: (current: FavoriteCollectionState) => FavoriteCollectionState) {
  const operation = favoriteCollectionMutationTail.then(async () => {
    const current = await readFavoriteCollections();
    const next = transition(current);
    if (next !== current) await saveFavoriteCollections(next);
    return next;
  });
  favoriteCollectionMutationTail = operation.then(() => undefined, () => undefined);
  return operation;
}
