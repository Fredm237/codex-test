import { useQueryClient } from "@tanstack/react-query";
import * as Network from "expo-network";
import { AppState, type AppStateStatus } from "react-native";
import { useCallback, useEffect, useRef } from "react";

import {
  CATALOGUE_REFRESH_INTERVAL_MS,
  isLiveFilonQueryKey,
  shouldRefreshCatalogue,
  type CatalogueRefreshReason,
} from "@/lib/catalogue-refresh-policy";

/**
 * Keeps live FILON data current without requiring a pull gesture. The controller
 * only refetches active catalogue queries, preserves cached data offline and
 * avoids a burst of duplicate requests when the app regains focus repeatedly.
 */
export function CatalogueAutoRefresh() {
  const queryClient = useQueryClient();
  const lastRefreshAt = useRef<number | null>(null);
  const appState = useRef<AppStateStatus>(AppState.currentState);

  const refresh = useCallback(
    async (reason: CatalogueRefreshReason) => {
      const now = Date.now();
      if (!shouldRefreshCatalogue({ reason, now, lastRefreshAt: lastRefreshAt.current })) return;

      const network = await Network.getNetworkStateAsync().catch(() => null);
      if (network?.isInternetReachable === false) return;

      lastRefreshAt.current = now;
      await queryClient.invalidateQueries({
        predicate: (query) => isLiveFilonQueryKey(query.queryKey),
        refetchType: "active",
      });
    },
    [queryClient],
  );

  useEffect(() => {
    void refresh("launch");

    const appSubscription = AppState.addEventListener("change", (nextState) => {
      const returnedToForeground = appState.current.match(/inactive|background/) && nextState === "active";
      appState.current = nextState;
      if (returnedToForeground) void refresh("foreground");
    });
    const networkSubscription = Network.addNetworkStateListener((state) => {
      if (state.isInternetReachable) void refresh("network");
    });
    const interval = setInterval(() => {
      if (appState.current === "active") void refresh("interval");
    }, CATALOGUE_REFRESH_INTERVAL_MS);

    return () => {
      appSubscription.remove();
      networkSubscription.remove();
      clearInterval(interval);
    };
  }, [refresh]);

  return null;
}
