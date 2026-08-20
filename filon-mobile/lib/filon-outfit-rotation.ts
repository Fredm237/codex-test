import type { SavedOutfit } from "./filon-outfit-journal";

export type OutfitRotationSuggestion = { outfit: SavedOutfit; daysSinceSaved: number; reason: string };

/** La rotation utilise uniquement la date de sauvegarde. Elle ne déduit jamais qu’une tenue a été portée ou non. */
export function buildOutfitRotation(items: SavedOutfit[], now = new Date()): OutfitRotationSuggestion[] {
  return items.slice().sort((left, right) => new Date(left.createdAt).getTime() - new Date(right.createdAt).getTime()).slice(0, 3).map((outfit) => {
    const daysSinceSaved = Math.max(0, Math.floor((now.getTime() - new Date(outfit.createdAt).getTime()) / 86_400_000));
    return { outfit, daysSinceSaved, reason: daysSinceSaved === 0 ? "Sauvegardée aujourd’hui : à garder en repère." : `Sauvegardée il y a ${daysSinceSaved} jour${daysSinceSaved > 1 ? "s" : ""} : à reconsidérer pour une prochaine occasion.` };
  });
}
