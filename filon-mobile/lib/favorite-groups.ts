import type { FavoriteOffer } from "./favorites";

export type FavoriteListRow = { type: "heading"; key: string; category: string } | { type: "offer"; key: string; offer: FavoriteOffer };

export function groupFavoriteRows(items: FavoriteOffer[], uncategorizedLabel: string): FavoriteListRow[] {
  const groups = new Map<string, FavoriteOffer[]>();
  for (const item of items) {
    const category = item.category?.split(">")[0]?.trim() || uncategorizedLabel;
    groups.set(category, [...(groups.get(category) ?? []), item]);
  }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b)).flatMap(([category, offers]) => [{ type: "heading" as const, key: `heading:${category}`, category }, ...offers.map((offer) => ({ type: "offer" as const, key: `offer:${offer.id}`, offer }))]);
}
