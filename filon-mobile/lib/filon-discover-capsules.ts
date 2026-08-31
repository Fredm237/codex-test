import type { StyleDirectionId, StyleDna } from "./style-dna";
import type { FilonOutfitLocale } from "./filon-outfit-i18n";

export type DiscoverCapsuleId = "minimal-work" | "minimal-evening" | "classic-wedding" | "classic-work" | "bold-evening" | "bold-wedding";

export type DiscoverCapsule = {
  id: DiscoverCapsuleId;
  style: StyleDirectionId;
  title: string;
  description: string;
  occasion: "work" | "wedding" | "evening" | null;
};

const CAPSULES: DiscoverCapsule[] = [
  { id: "minimal-work", style: "minimal", title: "Lignes claires", description: "Une base nette pour une journée de travail, sans surcharge visuelle.", occasion: "work" },
  { id: "minimal-evening", style: "minimal", title: "Soirée épurée", description: "Quelques pièces cohérentes, laissées respirer.", occasion: "evening" },
  { id: "classic-wedding", style: "classic", title: "Cérémonie intemporelle", description: "Des repères structurés pour une occasion formelle.", occasion: "wedding" },
  { id: "classic-work", style: "classic", title: "Bureau réemployable", description: "Une tenue ancrée, pensée pour être portée à nouveau.", occasion: "work" },
  { id: "bold-evening", style: "bold", title: "Accent assumé", description: "Une base lisible et une pièce plus expressive.", occasion: "evening" },
  { id: "bold-wedding", style: "bold", title: "Célébration vivante", description: "Une direction festive sans compromis sur la cohérence.", occasion: "wedding" },
];

const CAPSULE_QUERIES: Record<FilonOutfitLocale, Record<DiscoverCapsuleId, string>> = {
  fr: {
    "minimal-work": "chemise blanche pantalon droit chaussures cuir",
    "minimal-evening": "robe noire simple chaussures élégantes",
    "classic-wedding": "blazer robe midi chaussures cuir",
    "classic-work": "blazer pantalon droit chemise mocassins",
    "bold-evening": "robe colorée veste simple chaussures",
    "bold-wedding": "combinaison colorée blazer chaussures",
  },
  nl: {
    "minimal-work": "wit overhemd rechte broek leren schoenen",
    "minimal-evening": "eenvoudige zwarte jurk elegante schoenen",
    "classic-wedding": "blazer midi-jurk leren schoenen",
    "classic-work": "blazer rechte broek overhemd loafers",
    "bold-evening": "gekleurde jurk eenvoudige jas schoenen",
    "bold-wedding": "gekleurde jumpsuit blazer schoenen",
  },
  en: {
    "minimal-work": "white shirt straight trousers leather shoes",
    "minimal-evening": "simple black dress elegant shoes",
    "classic-wedding": "blazer midi dress leather shoes",
    "classic-work": "blazer straight trousers shirt loafers",
    "bold-evening": "colourful dress simple jacket shoes",
    "bold-wedding": "colourful jumpsuit blazer shoes",
  },
};

/** Les capsules sont des briefs de départ, jamais des offres, des prix ou une promesse de disponibilité. */
export function selectDiscoverCapsules(dna: StyleDna, limit = 3): DiscoverCapsule[] {
  const prioritized = dna.primary ? [...CAPSULES.filter((capsule) => capsule.style === dna.primary), ...CAPSULES.filter((capsule) => capsule.style !== dna.primary)] : CAPSULES;
  return prioritized.slice(0, Math.max(1, Math.min(limit, CAPSULES.length)));
}

export function findDiscoverCapsule(id: string): DiscoverCapsule | null {
  return CAPSULES.find((capsule) => capsule.id === id) ?? null;
}

export function localizedDiscoverCapsuleQuery(id: DiscoverCapsuleId, locale: FilonOutfitLocale) {
  return CAPSULE_QUERIES[locale][id];
}
