// Preuves réelles de la home, lues dans le catalogue au moment du rendu (ISR).
//
// La bande « preuves » annonçait « 5+ marchands » et « chiffres réels à venir »
// alors que la base en compte 154 et près de 800 000 offres. Un partenaire qui
// lit cette page y voit un site qui s'annonce vide : on affiche donc ce qui
// existe vraiment, jamais un chiffre saisi à la main.
//
// Toute erreur rend `null` : la section retombe alors sur sa rédaction générique
// plutôt que d'afficher un zéro, qui mentirait dans l'autre sens.

import { API } from "@/lib/api";

export type ProofStats = {
  merchants: number;
  offers: number;
  products: number;
  multiMerchant: number;
  snapshots: number;
};

export type ProofProduct = {
  ean: string;
  name: string;
  brand: string | null;
  image: string | null;
  priceMin: number;
  priceMax: number;
  currency: string;
  merchants: number;
};

export type Proof = {
  stats: ProofStats;
  merchants: string[];
  product: ProofProduct | null;
};

const TIMEOUT_MS = 6000;

async function getJson(path: string, revalidate: number): Promise<any | null> {
  try {
    const res = await fetch(`${API}${path}`, {
      next: { revalidate },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Le produit vitrine : réellement vendu par le plus de marchands, et dont
 *  l'écart de prix est mesurable. Sans écart il ne prouve rien — on l'écarte. */
function pickProduct(items: any[]): ProofProduct | null {
  for (const p of items) {
    const min = typeof p.price_min === "number" ? p.price_min : null;
    const max = typeof p.price_max === "number" ? p.price_max : null;
    if (min === null || max === null || max <= min) continue;
    if ((p.merchants_count || 0) < 2) continue;
    return {
      ean: String(p.ean),
      name: String(p.name),
      brand: p.brand ?? null,
      image: p.image ?? null,
      priceMin: min,
      priceMax: max,
      currency: p.currency || "EUR",
      merchants: Number(p.merchants_count),
    };
  }
  return null;
}

export async function getProof(): Promise<Proof | null> {
  const [stats, merchants, products] = await Promise.all([
    getJson("/api/catalog/stats", 3600),
    getJson("/api/catalog/merchants?limit=40", 21600),
    getJson("/api/catalog/products?multi_merchant=true&limit=24", 3600),
  ]);

  if (!stats?.database || !stats.merchants || !stats.offers) return null;

  return {
    stats: {
      merchants: Number(stats.merchants || 0),
      offers: Number(stats.offers || 0),
      products: Number(stats.products || 0),
      multiMerchant: Number(stats.products_multi_merchant || 0),
      snapshots: Number(stats.snapshots || 0),
    },
    // Les vrais partenaires, tels que le réseau les nomme. Les logos des
    // enseignes que nous ne distribuons pas n'ont rien à faire ici.
    merchants: ((merchants?.items || []) as any[])
      .map((m) => String(m.name || "").trim())
      .filter(Boolean)
      .slice(0, 18),
    product: pickProduct((products?.items || []) as any[]),
  };
}
