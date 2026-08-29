import type { SavedOutfit } from "./filon-outfit-journal";
import type { OutfitPublicMessage } from "./filon-outfit-i18n";

export type OutfitRotationSuggestion = { outfit: SavedOutfit; daysSinceSaved: number; reason: OutfitPublicMessage };

/** La rotation utilise uniquement la date de sauvegarde. Elle ne déduit jamais qu’une tenue a été portée ou non. */
export function buildOutfitRotation(items: SavedOutfit[], now = new Date()): OutfitRotationSuggestion[] {
  return items.slice().sort((left, right) => new Date(left.createdAt).getTime() - new Date(right.createdAt).getTime()).slice(0, 3).map((outfit) => {
    const daysSinceSaved = Math.max(0, Math.floor((now.getTime() - new Date(outfit.createdAt).getTime()) / 86_400_000));
    return { outfit, daysSinceSaved, reason: daysSinceSaved === 0 ? { code: "rotation.saved_today" } : { code: "rotation.saved_days_ago", days: daysSinceSaved } };
  });
}
