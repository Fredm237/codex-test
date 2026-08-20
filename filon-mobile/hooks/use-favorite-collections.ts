import { useCallback, useEffect, useState } from "react";

import { collectionsForFavorite, createFavoriteCollection, deleteFavoriteCollection, emptyFavoriteCollectionState, markFavoriteCollectionsPending, markFavoriteCollectionsReconciled, mergeRemoteFavoriteCollections, readFavoriteCollections, renameFavoriteCollection, saveFavoriteCollections, toggleFavoriteCollectionMembership, type FavoriteCollectionState, type RemoteFavoriteCollection } from "@/lib/favorite-collections";

export function useFavoriteCollections() {
  const [state, setState] = useState<FavoriteCollectionState>(emptyFavoriteCollectionState);
  const [ready, setReady] = useState(false);
  const refresh = useCallback(async () => { setState(await readFavoriteCollections()); setReady(true); }, []);
  useEffect(() => { void refresh(); }, [refresh]);
  const commit = useCallback(async (next: FavoriteCollectionState, reconciliationAt?: string) => { if (next === state) return next; const persisted = reconciliationAt ? markFavoriteCollectionsReconciled(next, reconciliationAt) : markFavoriteCollectionsPending(next); await saveFavoriteCollections(persisted); setState(persisted); return persisted; }, [state]);
  const create = useCallback((name: string) => commit(createFavoriteCollection(state, name, `collection:${Date.now()}`, new Date().toISOString())), [commit, state]);
  const toggle = useCallback((offerId: number, collectionId: string) => commit(toggleFavoriteCollectionMembership(state, offerId, collectionId)), [commit, state]);
  const rename = useCallback((collectionId: string, name: string) => commit(renameFavoriteCollection(state, collectionId, name, new Date().toISOString())), [commit, state]);
  const remove = useCallback((collectionId: string) => commit(deleteFavoriteCollection(state, collectionId, new Date().toISOString())), [commit, state]);
  const mergeRemote = useCallback((remote: RemoteFavoriteCollection[]) => commit(mergeRemoteFavoriteCollections(state, remote), new Date().toISOString()), [commit, state]);
  const syncPayload = useCallback(() => [...state.collections.map((collection) => ({ clientId: collection.id, name: collection.name, createdAt: collection.createdAt, updatedAt: collection.updatedAt, deletedAt: null, offerIds: Object.entries(state.memberships).filter(([, ids]) => ids.includes(collection.id)).map(([offerId]) => Number(offerId)).filter((offerId) => Number.isInteger(offerId) && offerId > 0) })), ...Object.entries(state.tombstones).map(([clientId, value]) => ({ clientId, name: value.name, createdAt: value.createdAt, updatedAt: value.deletedAt, deletedAt: value.deletedAt, offerIds: [] }))], [state]);
  return { ...state, ready, refresh, create, toggle, rename, remove, mergeRemote, syncPayload, forOffer: (offerId: number) => collectionsForFavorite(state, offerId) };
}
