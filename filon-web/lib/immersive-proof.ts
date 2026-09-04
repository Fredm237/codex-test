import { Buffer } from "node:buffer";

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
  textureImage: string | null;
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
const EDITORIAL_CANDIDATES_PER_FAMILY = 2;
const EDITORIAL_CANDIDATE_QUERIES = [
  "montre connectée",
  "chaussures",
  "casque à conduction osseuse",
] as const;
const IMMERSIVE_TEXTURE_MAX_BYTES = 512_000;
const IMMERSIVE_TEXTURE_HOSTS = new Set([
  "cdn.blazimg.com",
  "cdn.shopify.com",
  "objectstore.true.nl",
  "static.tyres.net",
]);
const IMMERSIVE_TEXTURE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);
const SECONDARY_PRODUCT_MARKERS = [
  "adaptateur",
  "bracelet",
  "câble",
  "cable",
  "chargeur",
  "coque",
  "couvre-chaussures",
  "étui",
  "housse",
  "protection",
  "support",
] as const;

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

/** Transforme uniquement les images de CDN publics explicitement admis en
 * texture locale. Une balise img accepte souvent une image sans CORS, WebGL
 * non : sans cette frontière, un produit éditorial valide ferait tomber la
 * scène entière. Un hôte inconnu, un type non-image ou un fichier trop lourd
 * conserve le produit dans le DOM mais n'entre jamais dans le canvas. */
export async function getImmersiveTextureDataUri(image: string | null): Promise<string | null> {
  if (!image) return null;
  let url: URL;
  try {
    url = new URL(image);
  } catch {
    return null;
  }
  if (url.protocol !== "https:" || !IMMERSIVE_TEXTURE_HOSTS.has(url.hostname.toLowerCase())) return null;

  try {
    const response = await fetch(url, {
      next: { revalidate: 21_600 },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    if (!response.ok) return null;
    const contentType = response.headers.get("content-type")?.split(";", 1)[0]?.trim().toLowerCase() ?? "";
    const contentLength = Number(response.headers.get("content-length") || 0);
    if (
      !IMMERSIVE_TEXTURE_TYPES.has(contentType)
      || (Number.isFinite(contentLength) && contentLength > IMMERSIVE_TEXTURE_MAX_BYTES)
    ) return null;
    const bytes = await response.arrayBuffer();
    if (!bytes.byteLength || bytes.byteLength > IMMERSIVE_TEXTURE_MAX_BYTES) return null;
    return `data:${contentType};base64,${Buffer.from(bytes).toString("base64")}`;
  } catch {
    return null;
  }
}

function qualifyProduct(product: any): ImmersiveExactProductProof | null {
  if (
    !product
    || !Array.isArray(product.offers)
    || typeof product.image !== "string"
    || !product.image.trim()
  ) return null;

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
    image: product.image.trim(),
    textureImage: null,
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

function isEditorialCandidate(candidate: any): boolean {
  const name = typeof candidate?.name === "string" ? candidate.name.trim() : "";
  const image = typeof candidate?.image === "string" ? candidate.image.trim() : "";
  const priceMin = positiveFinitePrice(candidate?.price_min) ? candidate.price_min : null;
  const priceMax = positiveFinitePrice(candidate?.price_max) ? candidate.price_max : null;
  const comparedMerchants = Number(candidate?.compared_merchants_count || 0);
  const normalizedName = name.toLocaleLowerCase("fr");

  return Boolean(
    typeof candidate?.ean === "string"
    && candidate.ean.trim()
    && name.length >= 8
    && name.length <= 110
    && image
    && priceMin !== null
    && priceMax !== null
    && priceMax > priceMin
    && comparedMerchants >= 2
    && !SECONDARY_PRODUCT_MARKERS.some((marker) => normalizedName.includes(marker))
  );
}

function dailyIndex(size: number): number {
  if (size <= 1) return 0;
  return Math.floor(Date.now() / 86_400_000) % size;
}

async function qualifyCandidates(eans: string[]): Promise<ImmersiveExactProductProof[]> {
  const unique = [...new Set(eans)].slice(0, CANDIDATE_LIMIT);
  const details = await Promise.all(
    unique.map((ean) => getJson(`/api/catalog/product/${encodeURIComponent(ean)}`)),
  );
  return details
    .map(qualifyProduct)
    .filter((candidate): candidate is ImmersiveExactProductProof => candidate !== null);
}

async function withImmersiveTexture(product: ImmersiveExactProductProof): Promise<ImmersiveExactProductProof> {
  return {
    ...product,
    textureImage: await getImmersiveTextureDataUri(product.image),
  };
}

/** La liste ne vaut que comme index de candidats : seule la fiche détaillée,
 * avec offres courantes et horodatées, peut franchir la frontière visuelle. */
export async function getImmersiveExactProductProof(): Promise<ImmersiveExactProductProof | null> {
  const editorialListings = await Promise.all(
    EDITORIAL_CANDIDATE_QUERIES.map((query) => getJson(
      `/api/catalog/products?q=${encodeURIComponent(query)}&multi_merchant=true&limit=12`,
    )),
  );
  const editorialEans = editorialListings.flatMap((listing) => (
    Array.isArray(listing?.items)
      ? listing.items
        .filter(isEditorialCandidate)
        .slice(0, EDITORIAL_CANDIDATES_PER_FAMILY)
        .map((candidate: any) => candidate.ean.trim())
      : []
  ));
  const editorialProducts = await qualifyCandidates(editorialEans);
  if (editorialProducts.length) {
    return withImmersiveTexture(editorialProducts[dailyIndex(editorialProducts.length)]);
  }

  // Si aucune famille éditoriale ne dispose d'une preuve suffisante, FILON
  // conserve le comportement général historique plutôt que de forcer un objet.
  const listing = await getJson(`/api/catalog/products?multi_merchant=true&limit=${CANDIDATE_LIMIT}`);
  const fallbackEans = (Array.isArray(listing?.items) ? listing.items : [])
    .map((candidate: any) => typeof candidate?.ean === "string" ? candidate.ean.trim() : "")
    .filter(Boolean);
  const fallback = (await qualifyCandidates(fallbackEans))[0] ?? null;
  return fallback ? withImmersiveTexture(fallback) : null;
}
