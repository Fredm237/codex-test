import type { FilonCategoryCoverage } from "./filon-api";

export function topCoveredCategories(items: FilonCategoryCoverage[], limit = 4) {
  return [...items].filter((item) => Number.isFinite(item.count) && item.count > 0).sort((a, b) => b.count - a.count || a.name.localeCompare(b.name)).slice(0, limit);
}

const labels: Record<string, Record<"fr" | "nl" | "en", string>> = {
  "auto-moto": { fr: "Auto & Moto", nl: "Auto & Motor", en: "Auto & Moto" },
  telephonie: { fr: "Téléphonie", nl: "Telefonie", en: "Phones" },
  "beaute-parfum": { fr: "Beauté & Parfum", nl: "Beauty & Parfum", en: "Beauty & Fragrance" },
  "maison-deco": { fr: "Maison & Déco", nl: "Huis & Interieur", en: "Home & Decor" },
  informatique: { fr: "Informatique", nl: "Computer", en: "Computers" },
  gaming: { fr: "Gaming", nl: "Gaming", en: "Gaming" },
  electromenager: { fr: "Électroménager", nl: "Huishoudtoestellen", en: "Appliances" },
  "tv-son": { fr: "TV & Son", nl: "TV & Audio", en: "TV & Audio" },
};

export function categoryCoverageLabel(item: FilonCategoryCoverage, locale: "fr" | "nl" | "en") { return labels[item.slug]?.[locale] ?? item.name; }
