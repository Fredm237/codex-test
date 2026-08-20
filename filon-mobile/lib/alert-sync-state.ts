export type AlertSyncState = "local" | "needs-account" | "syncing" | "synced" | "failed";

export function resolveAlertSyncState(input: { hasAccount: boolean; hasAlerts: boolean; isSyncing: boolean; hasSucceeded: boolean; hasFailed: boolean }): AlertSyncState {
  if (!input.hasAlerts) return "local";
  if (!input.hasAccount) return "needs-account";
  if (input.isSyncing) return "syncing";
  if (input.hasSucceeded) return "synced";
  if (input.hasFailed) return "failed";
  return "local";
}
