import type { FilonOffer } from "./filon-api";
import type { OutfitRole } from "./filon-intelligence";
import type { SavedOutfit, SavedOutfitPiece } from "./filon-outfit-journal";
import { isSafePartnerOfferUrl } from "./partner-offer";

export type OutfitOptimizationReplacement = { previous: SavedOutfitPiece; next: FilonOffer; saving: number };
export type OutfitOptimization =
  | { status: "solution"; sourceOutfitId: string; checkedOffers: number; replacements: OutfitOptimizationReplacement[]; originalTotal: number; optimizedTotal: number; savings: number; constraints: string[] }
  | { status: "abstain"; sourceOutfitId: string; checkedOffers: number; reason: string };

function normalized(value: string | null | undefined) {
  return (value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
}

function roleFromOffer(offer: FilonOffer): OutfitRole | null {
  const text = normalized(`${offer.name} ${offer.category ?? ""}`);
  if (/\b(chaussures?|shoes?|sneakers?|baskets?|boots?|bottines?|escarpins?|mocassins?|sandals?|sandales?)\b/.test(text)) return "footwear";
  if (/\b(blazers?|vestes?|jackets?|manteaux?|coats?|surchemises?|vestons?|gilets?)\b/.test(text)) return "structure";
  if (/\b(sacs?|bags?|ceintures?|belts?|echarpes?|scarves|bijoux|jewellery|chapeaux|hats?|montres?|watches)\b/.test(text)) return "accessory";
  if (/\b(robes?|dresses?|chemises?|shirts?|pantalons?|trousers?|jeans?|jupes?|skirts?|tops?|pulls?|sweaters?|t-shirts?|tshirts?|combinaisons?)\b/.test(text)) return "base";
  return null;
}

/** Compare uniquement des snapshots locaux avec des offres catalogue actuelles vérifiées ; aucune disponibilité passée n’est supposée. */
export function optimizeSavedOutfit(outfit: SavedOutfit, offers: FilonOffer[]): OutfitOptimization {
  const eligible = offers.filter((offer) => offer.inStock === true && isSafePartnerOfferUrl(offer.link));
  const replacements: OutfitOptimizationReplacement[] = [];
  for (const previous of outfit.pieces) {
    const next = eligible.filter((offer) => roleFromOffer(offer) === previous.role && offer.price < previous.price).sort((left, right) => left.price - right.price)[0];
    if (next) replacements.push({ previous, next, saving: previous.price - next.price });
  }
  if (replacements.length === 0) return { status: "abstain", sourceOutfitId: outfit.id, checkedOffers: offers.length, reason: "Aucune offre partenaire actuellement disponible ne permet une amélioration de coût vérifiable pour cette tenue sauvegardée." };
  const savings = replacements.reduce((total, replacement) => total + replacement.saving, 0);
  return {
    status: "solution",
    sourceOutfitId: outfit.id,
    checkedOffers: offers.length,
    replacements,
    originalTotal: outfit.total,
    optimizedTotal: Math.max(0, outfit.total - savings),
    savings,
    constraints: ["Comparaison avec des offres partenaires actuellement disponibles uniquement", "Le prix sauvegardé reste un instantané historique", "Aucune livraison, promotion ou cashback n’est déduit lorsqu’il est inconnu"],
  };
}
