export type HapticAction = "light" | "medium" | "success" | "error";

export function hapticActionFor(event: "primary" | "saved-change" | "scan-match" | "sync-success" | "failure"): HapticAction {
  if (event === "scan-match" || event === "sync-success") return "success";
  if (event === "saved-change") return "medium";
  if (event === "failure") return "error";
  return "light";
}
