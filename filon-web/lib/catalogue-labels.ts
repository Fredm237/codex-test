import type { Locale } from "@/lib/i18n";

/**
 * Les flux partenaires conservent les noms de rayons en français. Cette couche
 * traduit l’interface de navigation sans altérer les slugs, les données SEO ou
 * les intitulés marchands.
 */
const LABELS: Record<string, Partial<Record<Locale, string>>> = {
  "Mode & Accessoires": { nl: "Mode & accessoires", en: "Fashion & accessories" },
  "Mode femme": { nl: "Damesmode", en: "Women's fashion" },
  "Mode homme": { nl: "Herenmode", en: "Men's fashion" },
  "Mode enfant": { nl: "Kindermode", en: "Children's fashion" },
  "Chaussures": { nl: "Schoenen", en: "Footwear" },
  "Accessoires": { nl: "Accessoires", en: "Accessories" },
  "Bagagerie": { nl: "Tassen & bagage", en: "Bags & luggage" },
  "Bijoux & Montres": { nl: "Sieraden & horloges", en: "Jewellery & watches" },
  "High-Tech": { nl: "High-tech", en: "Tech" },
  "Informatique": { nl: "Computers", en: "Computing" },
  "Téléphonie": { nl: "Telefonie", en: "Phones" },
  "TV & Son": { nl: "TV & audio", en: "TV & audio" },
  "Photo": { nl: "Fotografie", en: "Photography" },
  "Gaming": { nl: "Gaming", en: "Gaming" },
  "Maison & Déco": { nl: "Huis & decor", en: "Home & decor" },
  "Beauté & Parfum": { nl: "Beauty & parfum", en: "Beauty & fragrance" },
  "Auto & Moto": { nl: "Auto & motor", en: "Cars & motorbikes" },
  "Sport & Plein air": { nl: "Sport & outdoor", en: "Sports & outdoor" },
  "Animalerie": { nl: "Dieren", en: "Pets" },
  "Bébé & Santé": { nl: "Baby & gezondheid", en: "Baby & health" },
  "Famille & Quotidien": { nl: "Familie & dagelijks leven", en: "Family & everyday" },
  "Voyage & Loisirs": { nl: "Reizen & vrije tijd", en: "Travel & leisure" },
  "Jardin & Bricolage": { nl: "Tuin & klussen", en: "Garden & DIY" },
  "Électroménager": { nl: "Huishoudtoestellen", en: "Home appliances" },
  "Alimentation": { nl: "Voeding", en: "Food & drink" },
};

export function catalogueLabel(name: string, locale: Locale): string {
  return locale === "fr" ? name : LABELS[name]?.[locale] ?? name;
}
