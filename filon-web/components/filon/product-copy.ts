// Libellés et formatage de la carte produit.
//
// Séparés de ProductCard.tsx à dessein : ce dernier porte « use client », et
// une valeur exportée depuis un module client devient une *référence* client
// quand un composant serveur l'importe — pas l'objet lui-même. La page
// catalogue recevait donc `copy` indéfini et rendait une 500.
//
// Un module neutre s'importe correctement des deux côtés.

export type CardCopy = {
  see: string;
  at: string;
  lowest: string;
  noImage: string;
};

export const CARD_COPY: Record<"fr" | "nl" | "en", CardCopy> = {
  fr: { see: "Voir l'offre", at: "chez", lowest: "Au plus bas", noImage: "Visuel indisponible" },
  nl: { see: "Bekijk aanbod", at: "bij", lowest: "Laagste ooit", noImage: "Geen afbeelding" },
  en: { see: "See offer", at: "at", lowest: "Lowest ever", noImage: "No image" },
};

export function money(
  price: number | null | undefined,
  currency: string | null | undefined
): string {
  if (price == null) return "—";
  const symbol = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString("fr-BE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${symbol}`;
}
