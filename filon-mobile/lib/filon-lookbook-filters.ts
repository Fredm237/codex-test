import type { LookbookPlan, LookbookSummary } from "./filon-lookbook";
import type { SavedOutfit } from "./filon-outfit-journal";

export type LookbookFilter = "all" | "planned" | "unplanned" | "orphaned";
export type FilteredLookbook = { plans: LookbookPlan[]; outfits: SavedOutfit[]; count: number };

/** Les filtres réorganisent l’état local ; ils ne déduisent pas de disponibilité, de port réel ou de préférence. */
export function filterLookbook(summary: LookbookSummary, filter: LookbookFilter): FilteredLookbook {
  if (filter === "planned") { const plans = summary.planned.filter((item) => item.outfit !== null); return { plans, outfits: [], count: plans.length }; }
  if (filter === "orphaned") { const plans = summary.planned.filter((item) => item.outfit === null); return { plans, outfits: [], count: plans.length }; }
  if (filter === "unplanned") return { plans: [], outfits: summary.unplanned, count: summary.unplanned.length };
  return { plans: summary.planned, outfits: summary.unplanned, count: summary.planned.length + summary.unplanned.length };
}

export function lookbookFilterCounts(summary: LookbookSummary): Record<LookbookFilter, number> {
  return { all: summary.planned.length + summary.unplanned.length, planned: summary.planned.filter((item) => item.outfit !== null).length, unplanned: summary.unplanned.length, orphaned: summary.planned.filter((item) => item.outfit === null).length };
}
