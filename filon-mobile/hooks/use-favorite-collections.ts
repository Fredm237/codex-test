import { useFocusEffect } from "expo-router";
import { useCallback, useRef, useState } from "react";

import {
  buildFavoriteCollectionSyncPayload,
  collectionsForFavorite,
  createFavoriteCollection,
  deleteFavoriteCollection,
  emptyFavoriteCollectionState,
  markFavoriteCollectionsPending,
  reconcileFavoriteCollectionsAfterSync,
  renameFavoriteCollection,
  toggleFavoriteCollectionMembership,
  updateFavoriteCollections,
  type FavoriteCollectionState,
  type RemoteFavoriteCollection,
} from "@/lib/favorite-collections";

export function useFavoriteCollections() {
  const [state, setState] = useState<FavoriteCollectionState>(emptyFavoriteCollectionState);
  const [ready, setReady] = useState(false);
  const stateRef = useRef<FavoriteCollectionState>(emptyFavoriteCollectionState);

  const enqueue = useCallback((transition: (current: FavoriteCollectionState) => FavoriteCollectionState) => {
    return updateFavoriteCollections(transition).then((next) => {
      stateRef.current = next;
      setState(next);
      return next;
    });
  }, []);

  const refresh = useCallback(() => {
    return updateFavoriteCollections((current) => current).then((next) => {
      stateRef.current = next;
      setState(next);
      setReady(true);
      return next;
    });
  }, []);

  useFocusEffect(useCallback(() => { void refresh(); }, [refresh]));

  const commit = useCallback(
    (transition: (current: FavoriteCollectionState) => FavoriteCollectionState) =>
      enqueue((current) => {
        const next = transition(current);
        return next === current ? current : markFavoriteCollectionsPending(next);
      }),
    [enqueue],
  );
  const create = useCallback((name: string) => {
    const id = `collection:${Date.now()}`;
    const createdAt = new Date().toISOString();
    return commit((current) => createFavoriteCollection(current, name, id, createdAt));
  }, [commit]);
  const toggle = useCallback((offerId: number, collectionId: string) => commit((current) => toggleFavoriteCollectionMembership(current, offerId, collectionId)), [commit]);
  const rename = useCallback((collectionId: string, name: string) => {
    const updatedAt = new Date().toISOString();
    return commit((current) => renameFavoriteCollection(current, collectionId, name, updatedAt));
  }, [commit]);
  const remove = useCallback((collectionId: string) => {
    const deletedAt = new Date().toISOString();
    return commit((current) => deleteFavoriteCollection(current, collectionId, deletedAt));
  }, [commit]);
  const mergeRemote = useCallback(
    (remote: RemoteFavoriteCollection[], syncedPayload: RemoteFavoriteCollection[]) =>
      enqueue((current) => reconcileFavoriteCollectionsAfterSync(current, remote, syncedPayload, new Date().toISOString())),
    [enqueue],
  );
  const syncPayload = useCallback(() => buildFavoriteCollectionSyncPayload(stateRef.current), []);

  return {
    ...state,
    ready,
    refresh,
    create,
    toggle,
    rename,
    remove,
    mergeRemote,
    syncPayload,
    forOffer: (offerId: number) => collectionsForFavorite(state, offerId),
  };
}
