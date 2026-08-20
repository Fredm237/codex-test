export type ScanLookupState = "idle" | "checking" | "invalid" | "unmatched" | "unavailable";

/** État visible après une recherche de code, sans confondre absence et panne. */
export function resolveScanLookupState(found: boolean, requestFailed: boolean): ScanLookupState {
  if (requestFailed) return "unavailable";
  return found ? "idle" : "unmatched";
}
