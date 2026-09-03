import { isFreshObservation, positiveFinitePrice } from "@/components/filon/product-copy";
import { API } from "@/lib/api";
import { normalizeSupportedCurrency } from "@/lib/currency";

export type ImmersiveOfferProof = {
  id: number;
  merchant: string;
  region: string | null;
  price: number;
  currency: string;
  observedAt: string;
};

export type ImmersiveExactProductProof = {
  ean: string;
  name: string;
  brand: string | null;
  category: string | null;
  image: string | null;
  priceMin: number;
  priceMax: number;
  currency: string;
  offers: ImmersiveOfferProof[];
  merchants: number;
  latestObservedAt: string;
  historySamples: number | null;
  historyTrackedDays: number | null;
  historyHeadline: string | null;
};

const TIMEOUT_MS = 8_000;
const CANDIDATE_LIMIT = 6;

async function getJson(path: string): Promise<any | null> {
  try {
    const response = await fetch(`${API}${path}`, {
      next: { revalidate: 600 },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

function qualifyProduct(product: any): ImmersiveExactProductProof | null {
  if (!product || !Array.isArray(product.offers)) return null;

  const offers: ImmersiveOfferProof[] = [];
  for (const offer of product.offers) {
    const currency = normalizeSupportedCurrency(offer?.currency);
    if (
      offer?.evidence_current !== true
      || !positiveFinitePrice(offer?.price)
      || currency === null
      || !isFreshObservation(offer?.observed_at)
      || typeof offer?.merchant?.name !== "string"
      || !offer.merchant.name.trim()
    ) continue;

    offers.push({
      id: Number(offer.id),
      merchant: offer.merchant.name.trim(),
      region: typeof offer.merchant.region === "string" ? offer.merchant.region : null,
      price: offer.price,
      currency,
      observedAt: offer.observed_at,
    });
  }

  const currencies = new Set(offers.map((offer) => offer.currency));
  const merchants = new Set(offers.map((offer) => offer.merchant));
  if (offers.length < 2 || merchants.size < 2 || currencies.size !== 1) return null;

  const currency = offers[0].currency;
  const sorted = offers
    .filter((offer) => offer.currency === currency)
    .sort((a, b) => a.price - b.price || a.id - b.id);
  const priceMin = sorted[0]?.price;
  const priceMax = sorted.at(-1)?.price;
  if (!positiveFinitePrice(priceMin) || !positiveFinitePrice(priceMax) || priceMax <= priceMin) return null;

  const latestObservedAt = sorted
    .map((offer) => offer.observedAt)
    .sort((a, b) => Date.parse(b) - Date.parse(a))[0];
  const history = product?.decision?.price_verdict ?? product?.verdict ?? null;

  return {
    ean: String(product.ean),
    name: String(product.name),
    brand: typeof product.brand === "string" ? product.brand : null,
    category: typeof product.category === "string" ? product.category : null,
    image: typeof product.image === "string" ? product.image : null,
    priceMin,
    priceMax,
    currency,
    offers: sorted,
    merchants: merchants.size,
    latestObservedAt,
    historySamples: Number.isFinite(history?.samples) ? Number(history.samples) : null,
    historyTrackedDays: Number.isFinite(history?.tracked_days) ? Number(history.tracked_days) : null,
    historyHeadline: typeof history?.headline === "string" ? history.headline : null,
  };
}

/**
 * Trouve une preuve produit exacte pour le laboratoire, sans élargir le contrat
 * de la home. La liste ne vaut que comme index de candidats : seule la fiche
 * détaillée, avec offres courantes et horodatées, peut franchir cette frontière.
 */
export async function getImmersiveExactProductProof(): Promise<ImmersiveExactProductProof | null> {
  const listing = await getJson(`/api/catalog/products?multi_merchant=true&limit=${CANDIDATE_LIMIT}`);
  const candidates = Array.isArray(listing?.items) ? listing.items : [];

  for (const candidate of candidates) {
    const ean = typeof candidate?.ean === "string" ? candidate.ean.trim() : "";
    if (!ean) continue;
    const detail = await getJson(`/api/catalog/product/${encodeURIComponent(ean)}`);
    const qualified = qualifyProduct(detail);
    if (qualified !== null) return qualified;
  }
  return null;
}
