export const FILON_API_BASE_URL = "https://web-production-c6842.up.railway.app";

type RawOffer = {
  id: number;
  name: string;
  brand?: string | null;
  category?: string | null;
  price: number;
  currency?: string | null;
  in_stock?: boolean | null;
  image?: string | null;
  link: string;
  merchant?: { name?: string | null; slug?: string | null } | null;
};

export type FilonOffer = {
  id: number;
  name: string;
  brand: string | null;
  category: string | null;
  price: number;
  currency: string;
  /** `null` signifie que le marchand n’a pas fourni de disponibilité. */
  inStock: boolean | null;
  imageUrl: string | null;
  merchantName: string;
  merchantSlug: string | null;
  link: string;
};

type RawCategory = { name?: string | null; slug?: string | null; count?: number | null };
export type FilonCategoryCoverage = { name: string; slug: string; count: number };
type RawTaxonomyNode = RawCategory & { categories?: RawTaxonomyNode[]; subcategories?: RawTaxonomyNode[]; children?: RawTaxonomyNode[] };
type RawCategoryNode = RawTaxonomyNode;
type RawDepartment = RawTaxonomyNode;
export type FilonSubcategory = { name: string; count: number; slug?: string };
export type FilonCategoryNode = FilonCategoryCoverage & { subcategories: FilonSubcategory[] };
export type FilonDepartment = FilonCategoryCoverage & { categories: FilonCategoryNode[] };
export type FilonCatalogueNavigation = { categories: FilonCategoryCoverage[]; departments: FilonDepartment[] };
export type FilonOfferSort = "relevance" | "price_asc" | "price_desc" | "name";
export type FilonOfferSearch = {
  query?: string;
  merchant?: string | null;
  department?: string | null;
  category?: string | null;
  subcategory?: string | null;
  brand?: string | null;
  priceMin?: number | null;
  priceMax?: number | null;
  sort?: FilonOfferSort;
  limit?: number;
  offset?: number;
};
export type FilonFacet = { value: string; count: number };
export type FilonCatalogueFacets = { categories: FilonFacet[]; brands: FilonFacet[] };
export type FilonMerchant = { mid: number; name: string; slug: string; domain: string | null; region: string | null; sector: string | null; logoUrl: string | null };
export type FilonCataloguePulse = { live: boolean; lastReading: string | null; readings24h: number | null; drops24h: number | null; syncStatus: string | null; lastSuccess: string | null; ageHours: number | null };
export type FilonPriceRelief = { id: number; name: string; brand: string | null; merchantName: string; category: string | null; price: number; currency: string; imageUrl: string | null; high: number; low: number; dropPercentage: number; trackedDays: number; samples: number; confidence: string | null };
export type FilonCatalogueRelief = { live: boolean; generatedAt: string | null; windowDays: number | null; items: FilonPriceRelief[] };

type RawProductOffer = Omit<RawOffer, "name" | "brand" | "category" | "image">;
type RawProduct = { ean: string; name: string; brand?: string | null; category?: string | null; image?: string | null; price_min: number; price_max: number; currency?: string | null; offers_count: number; merchants_count: number; offers?: RawProductOffer[] };
export type FilonProduct = { ean: string; name: string; brand: string | null; category: string | null; imageUrl: string | null; priceMin: number; priceMax: number; currency: string; offersCount: number; merchantsCount: number; offers: FilonOffer[] };
type RawPricePoint = { price?: number | null; at?: string | null };
type RawOfferDetail = RawOffer & { history?: RawPricePoint[]; price_min?: number | null; price_max?: number | null; verdict?: { level?: string | null; headline?: string | null } | null };
export type FilonOfferDetail = { offer: FilonOffer; history: { price: number; at: string | null }[]; priceMin: number | null; priceMax: number | null; verdict: { level: string | null; headline: string | null } | null };

export function getFirstImageUrl(value?: string | null) {
  if (!value) return null;
  const first = value.split(",").map((item) => item.trim()).find((item) => item.startsWith("https://") || item.startsWith("http://"));
  return first ?? null;
}

export function normalizeOffer(raw: RawOffer): FilonOffer {
  return {
    id: raw.id,
    name: raw.name,
    brand: raw.brand?.trim() || null,
    category: raw.category?.trim() || null,
    price: raw.price,
    currency: raw.currency || "EUR",
    // Ne jamais transformer une absence de donnée en promesse de stock.
    inStock: raw.in_stock ?? null,
    imageUrl: getFirstImageUrl(raw.image),
    merchantName: raw.merchant?.name?.trim() || "Marchand partenaire",
    merchantSlug: raw.merchant?.slug?.trim() || null,
    link: raw.link,
  };
}

export function normalizeProduct(raw: RawProduct): FilonProduct {
  const base = { name: raw.name, brand: raw.brand, category: raw.category, image: raw.image };
  return { ean: raw.ean, name: raw.name, brand: raw.brand?.trim() || null, category: raw.category?.trim() || null, imageUrl: getFirstImageUrl(raw.image), priceMin: raw.price_min, priceMax: raw.price_max, currency: raw.currency || "EUR", offersCount: raw.offers_count, merchantsCount: raw.merchants_count, offers: (raw.offers ?? []).map((offer) => normalizeOffer({ ...offer, ...base })) };
}

export function normalizeOfferDetail(raw: RawOfferDetail): FilonOfferDetail {
  return { offer: normalizeOffer(raw), history: (raw.history ?? []).filter((point): point is { price: number; at?: string | null } => typeof point.price === "number").map((point) => ({ price: point.price, at: point.at ?? null })), priceMin: typeof raw.price_min === "number" ? raw.price_min : null, priceMax: typeof raw.price_max === "number" ? raw.price_max : null, verdict: raw.verdict ? { level: raw.verdict.level ?? null, headline: raw.verdict.headline ?? null } : null };
}

export function buildFilonOfferSearchParams(input: string | FilonOfferSearch, legacyLimit = 24) {
  const criteria: FilonOfferSearch = typeof input === "string" ? { query: input, limit: legacyLimit } : input;
  const params = new URLSearchParams({ limit: String(Math.min(Math.max(criteria.limit ?? 24, 1), 200)), offset: String(Math.max(criteria.offset ?? 0, 0)) });
  const values: Record<string, string | null | undefined> = {
    q: criteria.query?.trim(), merchant: criteria.merchant, department: criteria.department, category: criteria.category,
    subcategory: criteria.subcategory, brand: criteria.brand,
    price_min: criteria.priceMin !== null && criteria.priceMin !== undefined ? String(criteria.priceMin) : undefined,
    price_max: criteria.priceMax !== null && criteria.priceMax !== undefined ? String(criteria.priceMax) : undefined,
    sort: criteria.sort && criteria.sort !== "relevance" ? criteria.sort : undefined,
  };
  for (const [key, value] of Object.entries(values)) if (value) params.set(key, value);
  return params;
}

export async function searchFilonOffers(input: string | FilonOfferSearch, legacyLimit = 24): Promise<{ total: number; items: FilonOffer[]; offset: number; limit: number }> {
  const params = buildFilonOfferSearchParams(input, legacyLimit);
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/offers?${params.toString()}`);
  if (!response.ok) throw new Error(`Catalogue indisponible (${response.status})`);
  const payload = (await response.json()) as { total?: number; items?: RawOffer[] };
  return { total: payload.total ?? 0, items: (payload.items ?? []).map(normalizeOffer), offset: Number(params.get("offset") ?? 0), limit: Number(params.get("limit") ?? 24) };
}

function normalizeCategory(item: RawCategory): FilonCategoryCoverage | null {
  if (typeof item.name !== "string" || typeof item.slug !== "string" || typeof item.count !== "number" || item.count <= 0) return null;
  return { name: item.name, slug: item.slug, count: item.count };
}

function childrenOf(node: RawTaxonomyNode): RawTaxonomyNode[] {
  return node.categories ?? node.children ?? node.subcategories ?? [];
}

export function normalizeFilonCatalogueNavigation(payload: { items?: RawCategory[]; departments?: RawDepartment[]; roots?: RawDepartment[]; children?: RawDepartment[] }): FilonCatalogueNavigation {
  // Le backend garde l'autorité de la taxonomie. Ces alias absorbent une
  // évolution de contrat (« roots »/« children ») sans nécessiter une nouvelle
  // app, tant que chaque branche fournit nom, slug et volume.
  const roots = payload.departments ?? payload.roots ?? payload.children ?? [];
  const categories = (payload.items ?? []).map(normalizeCategory).filter((item): item is FilonCategoryCoverage => item !== null);
  const departments: FilonDepartment[] = [];
  for (const department of roots) {
    const base = normalizeCategory(department);
    if (!base) continue;
    const children: FilonCategoryNode[] = [];
    for (const category of childrenOf(department)) {
      const normalized = normalizeCategory(category);
      if (!normalized) continue;
      const subcategories = childrenOf(category)
        .filter((sub): sub is RawTaxonomyNode & { name: string; count: number } => typeof sub.name === "string" && typeof sub.count === "number" && sub.count > 0)
        .map((sub) => ({ name: sub.name, count: sub.count, slug: typeof sub.slug === "string" ? sub.slug : undefined }));
      children.push({ ...normalized, subcategories });
    }
    departments.push({ ...base, categories: children });
  }
  return { categories, departments };
}

export async function getFilonCatalogueNavigation(): Promise<FilonCatalogueNavigation> {
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/categories`);
  if (!response.ok) throw new Error(`Catalogue indisponible (${response.status})`);
  return normalizeFilonCatalogueNavigation((await response.json()) as { items?: RawCategory[]; departments?: RawDepartment[]; roots?: RawDepartment[]; children?: RawDepartment[] });
}

export async function getFilonCategoryCoverage(): Promise<FilonCategoryCoverage[]> {
  return (await getFilonCatalogueNavigation()).categories;
}

export async function getFilonCatalogueFacets(limit = 24): Promise<FilonCatalogueFacets> {
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/facets?limit=${Math.min(Math.max(limit, 1), 200)}`);
  if (!response.ok) throw new Error(`Facettes indisponibles (${response.status})`);
  const payload = (await response.json()) as { categories?: Array<{ value?: string; count?: number }>; brands?: Array<{ value?: string; count?: number }> };
  const normalize = (items?: Array<{ value?: string; count?: number }>) => (items ?? []).filter((item): item is { value: string; count: number } => typeof item.value === "string" && item.value.trim().length > 0 && typeof item.count === "number" && item.count > 0).map((item) => ({ value: item.value, count: item.count }));
  return { categories: normalize(payload.categories), brands: normalize(payload.brands) };
}

export async function getFilonMerchants(limit = 300): Promise<FilonMerchant[]> {
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/merchants?limit=${Math.min(Math.max(limit, 1), 500)}`);
  if (!response.ok) throw new Error(`Marchands indisponibles (${response.status})`);
  const payload = (await response.json()) as { items?: Array<{ mid?: number; name?: string; slug?: string; domain?: string | null; region?: string | null; sector?: string | null; logo?: string | null }> };
  return (payload.items ?? []).filter((item): item is { mid: number; name: string; slug: string; domain?: string | null; region?: string | null; sector?: string | null; logo?: string | null } => typeof item.mid === "number" && typeof item.name === "string" && typeof item.slug === "string" && item.name.trim().length > 0 && item.slug.trim().length > 0).map((item) => ({ mid: item.mid, name: item.name, slug: item.slug, domain: item.domain ?? null, region: item.region ?? null, sector: item.sector ?? null, logoUrl: getFirstImageUrl(item.logo) }));
}

export function normalizeFilonCataloguePulse(raw: { live?: boolean; last_reading?: string | null; readings_24h?: number | null; drops_24h?: number | null; sync?: { status?: string | null; last_success?: string | null; age_hours?: number | null } | null }): FilonCataloguePulse {
  return { live: raw.live === true, lastReading: typeof raw.last_reading === "string" ? raw.last_reading : null, readings24h: typeof raw.readings_24h === "number" ? raw.readings_24h : null, drops24h: typeof raw.drops_24h === "number" ? raw.drops_24h : null, syncStatus: typeof raw.sync?.status === "string" ? raw.sync.status : null, lastSuccess: typeof raw.sync?.last_success === "string" ? raw.sync.last_success : null, ageHours: typeof raw.sync?.age_hours === "number" ? raw.sync.age_hours : null };
}

export async function getFilonCataloguePulse(): Promise<FilonCataloguePulse> {
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/pulse`);
  if (!response.ok) throw new Error(`État du catalogue indisponible (${response.status})`);
  return normalizeFilonCataloguePulse((await response.json()) as { live?: boolean; last_reading?: string | null; readings_24h?: number | null; drops_24h?: number | null; sync?: { status?: string | null; last_success?: string | null; age_hours?: number | null } | null });
}

export function normalizeFilonCatalogueRelief(raw: { live?: boolean; generated_at?: string | null; window_days?: number | null; columns?: Array<{ id?: number; name?: string; brand?: string | null; merchant?: string; category?: string | null; price?: number; currency?: string | null; image?: string | null; high?: number; low?: number; drop_pct?: number; tracked_days?: number; samples?: number; confidence?: string | null }> }): FilonCatalogueRelief {
  const items = (raw.columns ?? []).filter((item): item is { id: number; name: string; merchant: string; price: number; high: number; low: number; drop_pct: number; tracked_days: number; samples: number; brand?: string | null; category?: string | null; currency?: string | null; image?: string | null; confidence?: string | null } => typeof item.id === "number" && typeof item.name === "string" && typeof item.merchant === "string" && typeof item.price === "number" && typeof item.high === "number" && typeof item.low === "number" && typeof item.drop_pct === "number" && typeof item.tracked_days === "number" && typeof item.samples === "number" && item.high > item.price && item.samples > 0).map((item) => ({ id: item.id, name: item.name, brand: item.brand?.trim() || null, merchantName: item.merchant, category: item.category?.trim() || null, price: item.price, currency: item.currency || "EUR", imageUrl: getFirstImageUrl(item.image), high: item.high, low: item.low, dropPercentage: Math.abs(item.drop_pct), trackedDays: item.tracked_days, samples: item.samples, confidence: item.confidence?.trim() || null }));
  return { live: raw.live === true, generatedAt: typeof raw.generated_at === "string" ? raw.generated_at : null, windowDays: typeof raw.window_days === "number" ? raw.window_days : null, items };
}

export async function getFilonCatalogueRelief(): Promise<FilonCatalogueRelief> {
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/relief`);
  if (!response.ok) throw new Error(`Relief de prix indisponible (${response.status})`);
  return normalizeFilonCatalogueRelief((await response.json()) as { live?: boolean; generated_at?: string | null; window_days?: number | null; columns?: Array<{ id?: number; name?: string; brand?: string | null; merchant?: string; category?: string | null; price?: number; currency?: string | null; image?: string | null; high?: number; low?: number; drop_pct?: number; tracked_days?: number; samples?: number; confidence?: string | null }> });
}

export async function getFilonProductByEan(ean: string): Promise<FilonProduct | null> {
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/product/${encodeURIComponent(ean)}`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Catalogue indisponible (${response.status})`);
  return normalizeProduct((await response.json()) as RawProduct);
}

export async function getFilonOfferDetail(offerId: number): Promise<FilonOfferDetail> {
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/offer/${offerId}`);
  if (!response.ok) throw new Error(`Catalogue indisponible (${response.status})`);
  return normalizeOfferDetail((await response.json()) as RawOfferDetail);
}

export function formatFilonPrice(amount: number, locale: "fr" | "nl" | "en", currency = "EUR") {
  return new Intl.NumberFormat(locale === "en" ? "en-BE" : `${locale}-BE`, { style: "currency", currency, maximumFractionDigits: 2 }).format(amount);
}
