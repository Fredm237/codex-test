import type { PlannedOccasion } from "./filon-occasion-planner";
import type { SavedOutfit } from "./filon-outfit-journal";

export type LookbookPlan = { occasion: PlannedOccasion; outfit: SavedOutfit | null };
export type LookbookSummary = { planned: LookbookPlan[]; unplanned: SavedOutfit[]; totalOutfits: number; totalPlans: number };

/** Le Lookbook assemble uniquement les données sauvegardées localement ; une occasion orpheline reste explicitement signalée. */
export function buildLookbookSummary(outfits: SavedOutfit[], occasions: PlannedOccasion[]): LookbookSummary {
  const byId = new Map(outfits.map((outfit) => [outfit.id, outfit]));
  const planned = occasions.slice().sort((left, right) => left.date.localeCompare(right.date)).map((occasion) => ({ occasion, outfit: byId.get(occasion.outfitId) ?? null }));
  const plannedIds = new Set(occasions.map((occasion) => occasion.outfitId));
  return { planned, unplanned: outfits.filter((outfit) => !plannedIds.has(outfit.id)), totalOutfits: outfits.length, totalPlans: occasions.length };
}
