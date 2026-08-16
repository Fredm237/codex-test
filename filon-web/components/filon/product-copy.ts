// Libellés et formatage de la carte produit.
//
// Séparés de ProductCard.tsx à dessein : ce dernier porte « use client », et
// une valeur exportée depuis un module client devient une *référence* client
// quand un composant serveur l'importe — pas l'objet lui-même. La page
// catalogue recevait donc `copy` indéfini et rendait une 500.
//
// Un module neutre s'importe correctement des deux côtés.

export type CardLocale = "fr" | "nl" | "en";

export type CardCopy = {
  see: string;
  at: string;
  lowest: string;
  noImage: string;
  available: string;
  unavailable: string;
  availabilityUnknown: string;
};

export const CARD_COPY: Record<CardLocale, CardCopy> = {
  fr: {
    see: "Voir l'offre", at: "chez", lowest: "Au plus bas", noImage: "Visuel indisponible",
    available: "En stock dans le dernier flux", unavailable: "Indisponible dans le dernier flux", availabilityUnknown: "Disponibilité non renseignée",
  },
  nl: {
    see: "Bekijk aanbod", at: "bij", lowest: "Laagste ooit", noImage: "Geen afbeelding",
    available: "Op voorraad in de laatste feed", unavailable: "Niet beschikbaar in de laatste feed", availabilityUnknown: "Beschikbaarheid niet vermeld",
  },
  en: {
    see: "See offer", at: "at", lowest: "Lowest ever", noImage: "No image",
    available: "In stock in the latest feed", unavailable: "Unavailable in the latest feed", availabilityUnknown: "Availability not provided",
  },
};

export function money(
  price: number | null | undefined,
  currency: string | null | undefined,
  locale: CardLocale = "fr"
): string {
  if (price == null) return "—";
  const numberLocale = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  const symbol = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString(numberLocale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${symbol}`;
}
