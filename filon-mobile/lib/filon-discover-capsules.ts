import type { StyleDirectionId, StyleDna } from "./style-dna";

export type DiscoverCapsule = {
  id: string;
  style: StyleDirectionId;
  title: string;
  description: string;
  startQuery: string;
  occasion: "work" | "wedding" | "evening" | null;
};

const CAPSULES: DiscoverCapsule[] = [
  { id: "minimal-work", style: "minimal", title: "Lignes claires", description: "Une base nette pour une journée de travail, sans surcharge visuelle.", startQuery: "chemise blanche pantalon droit chaussures cuir", occasion: "work" },
  { id: "minimal-evening", style: "minimal", title: "Soirée épurée", description: "Quelques pièces cohérentes, laissées respirer.", startQuery: "robe noire simple chaussures élégantes", occasion: "evening" },
  { id: "classic-wedding", style: "classic", title: "Cérémonie intemporelle", description: "Des repères structurés pour une occasion formelle.", startQuery: "blazer robe midi chaussures cuir", occasion: "wedding" },
  { id: "classic-work", style: "classic", title: "Bureau réemployable", description: "Une tenue ancrée, pensée pour être portée à nouveau.", startQuery: "blazer pantalon droit chemise mocassins", occasion: "work" },
  { id: "bold-evening", style: "bold", title: "Accent assumé", description: "Une base lisible et une pièce plus expressive.", startQuery: "robe colorée veste simple chaussures", occasion: "evening" },
  { id: "bold-wedding", style: "bold", title: "Célébration vivante", description: "Une direction festive sans compromis sur la cohérence.", startQuery: "combinaison colorée blazer chaussures", occasion: "wedding" },
];

/** Les capsules sont des briefs de départ, jamais des offres, des prix ou une promesse de disponibilité. */
export function selectDiscoverCapsules(dna: StyleDna, limit = 3): DiscoverCapsule[] {
  const prioritized = dna.primary ? [...CAPSULES.filter((capsule) => capsule.style === dna.primary), ...CAPSULES.filter((capsule) => capsule.style !== dna.primary)] : CAPSULES;
  return prioritized.slice(0, Math.max(1, Math.min(limit, CAPSULES.length)));
}

export function findDiscoverCapsule(id: string): DiscoverCapsule | null {
  return CAPSULES.find((capsule) => capsule.id === id) ?? null;
}
