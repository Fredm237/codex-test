export const FILON_API_BASE_URL = "https://web-production-c6842.up.railway.app";

export const FILON_OFFER_MAX_AGE_HOURS = 72;
export const SUPPORTED_FILON_CURRENCIES = [
  "EUR", "CHF", "GBP", "DKK", "SEK", "NOK", "ISK", "PLN", "CZK", "HUF", "RON", "BGN", "ALL", "BAM", "MKD", "RSD", "MDL", "UAH", "TRY", "GEL", "AMD", "AZN",
  "USD", "CAD", "AUD", "NZD", "JPY", "CNY", "HKD", "SGD", "KRW", "INR", "AED", "SAR", "ILS", "ZAR",
] as const;

export type FilonCurrency = (typeof SUPPORTED_FILON_CURRENCIES)[number];

const SUPPORTED_FILON_CURRENCY_SET: ReadonlySet<string> = new Set(SUPPORTED_FILON_CURRENCIES);
const ISO_DATE_TIME = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?(Z|[+-]\d{2}:?\d{2})?$/i;

type RawOffer = {
  id: number;
  name: string;
  brand?: string | null;
  category?: string | null;
  price?: number | null;
  currency?: string | null;
  in_stock?: boolean | null;
  observed_at?: string | null;
  evidence_current?: boolean | null;
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
  /** Instant du relevé prix/stock. Absent ou périmé = offre non achetable. */
  observedAt?: string | null;
  /** Preuve explicite que prix, devise et stock appartiennent au même relevé. */
  evidenceCurrent?: boolean;
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
export type FilonOfferSort = "relevance" | "name";
export type FilonOfferSearch = {
  query?: string;
  merchant?: string | null;
  department?: string | null;
  category?: string | null;
  subcategory?: string | null;
  brand?: string | null;
  sort?: FilonOfferSort;
  limit?: number;
  offset?: number;
};
export type FilonFacet = { value: string; count: number };
export type FilonCatalogueFacets = { categories: FilonFacet[]; brands: FilonFacet[] };
export type FilonMerchant = { mid: number; name: string; slug: string; domain: string | null; region: string | null; sector: string | null; logoUrl: string | null };
export type FilonCataloguePulse = { live: boolean; lastReading: string | null; readings24h: number | null; drops24h: number | null; dropsComparable: boolean; syncStatus: string | null; lastSuccess: string | null; ageHours: number | null };
export type FilonPriceRelief = { id: number; name: string; brand: string | null; merchantName: string; category: string | null; price: number; currency: string; observedAt: string; imageUrl: string | null; high: number; low: number; dropPercentage: number; trackedDays: number; samples: number; confidence: string | null };
export type FilonCatalogueRelief = { live: boolean; generatedAt: string | null; windowDays: number | null; items: FilonPriceRelief[] };

type RawFilonPriceRelief = { id?: number; name?: string; brand?: string | null; merchant?: string; category?: string | null; price?: number; currency?: string | null; observed_at?: string | null; evidence_current?: boolean | null; history_currency?: string | null; image?: string | null; high?: number; low?: number; drop_pct?: number; tracked_days?: number; samples?: number; confidence?: string | null };

type RawProductOffer = Omit<RawOffer, "name" | "brand" | "category" | "image">;
type RawProduct = { ean: string; name: string; brand?: string | null; category?: string | null; image?: string | null; price_min: number; price_max: number; currency?: string | null; offers_count: number; merchants_count: number; offers?: RawProductOffer[] };
export type FilonProduct = { ean: string; name: string; brand: string | null; category: string | null; imageUrl: string | null; priceMin: number; priceMax: number; currency: string; offersCount: number; merchantsCount: number; offers: FilonOffer[] };
type RawPricePoint = { price?: number | null; currency?: string | null; at?: string | null; in_stock?: boolean | null };
type RawOfferDetail = RawOffer & { history?: RawPricePoint[]; price_min?: number | null; price_max?: number | null; verdict?: { level?: string | null; headline?: string | null } | null };
export type FilonOfferDetail = { offer: FilonOffer; history: { price: number; at: string | null }[]; priceMin: number | null; priceMax: number | null; verdict: { level: string | null; headline: string | null } | null };

export function getFirstImageUrl(value?: string | null) {
  if (!value) return null;
  const first = value.split(",").map((item) => item.trim()).find((item) => item.startsWith("https://") || item.startsWith("http://"));
  return first ?? null;
}

export function normalizeFilonCurrency(value: unknown): FilonCurrency | null {
  if (typeof value !== "string") return null;
  const code = value.trim().toUpperCase();
  return SUPPORTED_FILON_CURRENCY_SET.has(code) ? code as FilonCurrency : null;
}

export function normalizeFilonObservedAt(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const timestamp = value.trim();
  const parts = timestamp.match(ISO_DATE_TIME);
  if (!parts) return null;
  const [, yearText, monthText, dayText, hourText, minuteText, secondText = "0", fraction = ""] = parts;
  const [year, month, day, hour, minute, second] = [yearText, monthText, dayText, hourText, minuteText, secondText].map(Number);
  const millisecond = Number(`${fraction}000`.slice(0, 3));
  const calendar = new Date(0);
  calendar.setUTCFullYear(year, month - 1, day);
  calendar.setUTCHours(hour, minute, second, millisecond);
  if (
    calendar.getUTCFullYear() !== year
    || calendar.getUTCMonth() !== month - 1
    || calendar.getUTCDate() !== day
    || calendar.getUTCHours() !== hour
    || calendar.getUTCMinutes() !== minute
    || calendar.getUTCSeconds() !== second
  ) return null;
  // Les DateTime SQL historiques sont UTC mais peuvent sortir sans suffixe.
  const zoned = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(timestamp) ? timestamp : `${timestamp}Z`;
  const milliseconds = Date.parse(zoned);
  return Number.isFinite(milliseconds) ? new Date(milliseconds).toISOString() : null;
}

export function isFilonObservationFresh(observedAt: unknown, now: number | Date = Date.now()) {
  const normalized = normalizeFilonObservedAt(observedAt);
  const reference = now instanceof Date ? now.getTime() : now;
  if (!normalized || !Number.isFinite(reference)) return false;
  const age = reference - Date.parse(normalized);
  return age >= 0 && age <= FILON_OFFER_MAX_AGE_HOURS * 60 * 60 * 1000;
}

export function currentFilonStock(offer: Pick<FilonOffer, "inStock" | "observedAt" | "evidenceCurrent">, now: number | Date = Date.now()): boolean | null {
  if (offer.evidenceCurrent !== true || !isFilonObservationFresh(offer.observedAt, now)) return null;
  return offer.inStock === true ? true : offer.inStock === false ? false : null;
}

export function isFilonOfferPriceCurrent(offer: Pick<FilonOffer, "price" | "currency" | "observedAt" | "evidenceCurrent">, now: number | Date = Date.now()) {
  return Number.isFinite(offer.price)
    && offer.price > 0
    && normalizeFilonCurrency(offer.currency) !== null
    && offer.evidenceCurrent === true
    && isFilonObservationFresh(offer.observedAt, now);
}

export function isFilonOfferActionable(offer: Pick<FilonOffer, "price" | "currency" | "inStock" | "observedAt" | "evidenceCurrent">, now: number | Date = Date.now()) {
  return isFilonOfferPriceCurrent(offer, now)
    && currentFilonStock(offer, now) === true;
}

function positiveFinite(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : null;
}

function nonNegativeInteger(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 ? value : null;
}

function nonEmptyText(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

export function normalizeOffer(raw: RawOffer): FilonOffer {
  const price = positiveFinite(raw.price);
  const currency = normalizeFilonCurrency(raw.currency);
  const name = nonEmptyText(raw.name);
  const link = nonEmptyText(raw.link);
  const merchantName = nonEmptyText(raw.merchant?.name);
  if (!Number.isInteger(raw.id) || raw.id <= 0 || name === null || price === null || currency === null || merchantName === null || link === null || !/^https?:\/\//i.test(link)) {
    throw new TypeError("Offre catalogue incomplète : identité, prix, devise, marchand ou lien sans preuve explicite");
  }
  return {
    id: raw.id,
    name,
    brand: raw.brand?.trim() || null,
    category: raw.category?.trim() || null,
    price,
    currency,
    // Ne jamais transformer une absence de donnée en promesse de stock.
    inStock: raw.in_stock === true ? true : raw.in_stock === false ? false : null,
    observedAt: normalizeFilonObservedAt(raw.observed_at),
    evidenceCurrent: raw.evidence_current === true,
    imageUrl: getFirstImageUrl(raw.image),
    merchantName,
    merchantSlug: raw.merchant?.slug?.trim() || null,
    link,
  };
}

function normalizeOffers(rawOffers: RawOffer[]) {
  return rawOffers.reduce<FilonOffer[]>((offers, raw) => {
    try {
      offers.push(normalizeOffer(raw));
    } catch {
      // Une ligne incomplète reste absente au lieu de recevoir une devise ou un
      // marchand inventé. Les autres lignes de la page restent consultables.
    }
    return offers;
  }, []);
}

export function normalizeProduct(raw: RawProduct): FilonProduct {
  const priceMin = positiveFinite(raw.price_min);
  const priceMax = positiveFinite(raw.price_max);
  const currency = normalizeFilonCurrency(raw.currency);
  if (priceMin === null || priceMax === null || priceMin > priceMax || currency === null) {
    throw new TypeError("Produit groupé incomplet : prix ou devise sans preuve explicite");
  }
  const base = { name: raw.name, brand: raw.brand, category: raw.category, image: raw.image };
  const offers = (raw.offers ?? []).map((offer) => normalizeOffer({ ...offer, ...base }));
  if (offers.length === 0 || offers.some((offer) => offer.currency !== currency)) {
    throw new TypeError("Produit groupé non comparable : offres absentes ou multidevises");
  }
  const observedMin = Math.min(...offers.map((offer) => offer.price));
  const observedMax = Math.max(...offers.map((offer) => offer.price));
  if (Math.abs(observedMin - priceMin) > 0.005 || Math.abs(observedMax - priceMax) > 0.005) {
    throw new TypeError("Produit groupé incohérent : bornes de prix non prouvées par les offres");
  }
  return { ean: raw.ean, name: raw.name, brand: raw.brand?.trim() || null, category: raw.category?.trim() || null, imageUrl: getFirstImageUrl(raw.image), priceMin, priceMax, currency, offersCount: offers.length, merchantsCount: new Set(offers.map((offer) => offer.merchantName)).size, offers };
}

export function normalizeOfferDetail(raw: RawOfferDetail, now: number | Date = Date.now()): FilonOfferDetail {
  const offer = normalizeOffer(raw);
  const reference = now instanceof Date ? now.getTime() : now;
  const history = (raw.history ?? []).reduce<{ price: number; at: string; timestamp: number; sourceIndex: number }[]>((valid, point, sourceIndex) => {
    const price = positiveFinite(point.price);
    const at = normalizeFilonObservedAt(point.at);
    const timestamp = at === null ? Number.NaN : Date.parse(at);
    if (price === null || at === null || !Number.isFinite(reference) || timestamp > reference || normalizeFilonCurrency(point.currency) !== offer.currency || point.in_stock !== true) return valid;
    valid.push({ price, at, timestamp, sourceIndex });
    return valid;
  }, [])
    .sort((left, right) => left.timestamp - right.timestamp || left.sourceIndex - right.sourceIndex)
    .map(({ price, at }) => ({ price, at }));
  const prices = history.map((point) => point.price);
  return { offer, history, priceMin: prices.length > 0 ? Math.min(...prices) : null, priceMax: prices.length > 0 ? Math.max(...prices) : null, verdict: raw.verdict ? { level: raw.verdict.level ?? null, headline: raw.verdict.headline ?? null } : null };
}

export function buildFilonOfferSearchParams(input: string | FilonOfferSearch, legacyLimit = 24) {
  const criteria: FilonOfferSearch = typeof input === "string" ? { query: input, limit: legacyLimit } : input;
  const params = new URLSearchParams({ limit: String(Math.min(Math.max(criteria.limit ?? 24, 1), 200)), offset: String(Math.max(criteria.offset ?? 0, 0)) });
  const values: Record<string, string | null | undefined> = {
    q: criteria.query?.trim(), merchant: criteria.merchant, department: criteria.department, category: criteria.category,
    subcategory: criteria.subcategory, brand: criteria.brand,
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
  const rawItems = payload.items ?? [];
  const items = normalizeOffers(rawItems);
  // Le curseur doit avancer sur les lignes effectivement lues, y compris celles
  // fermées par la validation, sinon la page suivante répéterait des offres.
  const offset = Number(params.get("offset") ?? 0) + rawItems.length - items.length;
  return { total: payload.total ?? 0, items, offset, limit: Number(params.get("limit") ?? 24) };
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

export function normalizeFilonCataloguePulse(raw: { live?: boolean; last_reading?: string | null; readings_24h?: number | null; drops_24h?: number | null; drops_comparable?: boolean | null; sync?: { status?: string | null; last_success?: string | null; age_hours?: number | null } | null }): FilonCataloguePulse {
  const ageHours = typeof raw.sync?.age_hours === "number" && Number.isFinite(raw.sync.age_hours) && raw.sync.age_hours >= 0
    ? raw.sync.age_hours
    : null;
  return { live: raw.live === true, lastReading: normalizeFilonObservedAt(raw.last_reading), readings24h: nonNegativeInteger(raw.readings_24h), drops24h: nonNegativeInteger(raw.drops_24h), dropsComparable: raw.drops_comparable === true, syncStatus: typeof raw.sync?.status === "string" ? raw.sync.status : null, lastSuccess: normalizeFilonObservedAt(raw.sync?.last_success), ageHours };
}

export async function getFilonCataloguePulse(): Promise<FilonCataloguePulse> {
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/pulse`);
  if (!response.ok) throw new Error(`État du catalogue indisponible (${response.status})`);
  return normalizeFilonCataloguePulse((await response.json()) as { live?: boolean; last_reading?: string | null; readings_24h?: number | null; drops_24h?: number | null; drops_comparable?: boolean | null; sync?: { status?: string | null; last_success?: string | null; age_hours?: number | null } | null });
}

export function normalizeFilonCatalogueRelief(raw: { live?: boolean; generated_at?: string | null; window_days?: number | null; columns?: RawFilonPriceRelief[] }, now: number | Date = Date.now()): FilonCatalogueRelief {
  const items = (raw.columns ?? []).reduce<FilonPriceRelief[]>((valid, item) => {
    const currency = normalizeFilonCurrency(item.currency);
    const historyCurrency = normalizeFilonCurrency(item.history_currency);
    const observedAt = normalizeFilonObservedAt(item.observed_at);
    const merchantName = nonEmptyText(item.merchant);
    const price = positiveFinite(item.price);
    const high = positiveFinite(item.high);
    const low = positiveFinite(item.low);
    const dropPercentage = price !== null && high !== null && high > price
      ? ((high - price) / high) * 100
      : null;
    if (typeof item.id !== "number" || !Number.isInteger(item.id) || item.id <= 0 || typeof item.name !== "string" || !item.name.trim() || merchantName === null || price === null || currency === null || historyCurrency !== currency || observedAt === null || item.evidence_current !== true || !isFilonObservationFresh(observedAt, now) || high === null || low === null || dropPercentage === null || dropPercentage < 1 || dropPercentage > 100 || typeof item.tracked_days !== "number" || !Number.isFinite(item.tracked_days) || item.tracked_days < 0 || typeof item.samples !== "number" || !Number.isInteger(item.samples) || low > high || item.samples <= 0) return valid;
    valid.push({ id: item.id, name: item.name.trim(), brand: item.brand?.trim() || null, merchantName, category: item.category?.trim() || null, price, currency, observedAt, imageUrl: getFirstImageUrl(item.image), high, low, dropPercentage, trackedDays: item.tracked_days, samples: item.samples, confidence: item.confidence?.trim() || null });
    return valid;
  }, []);
  return { live: raw.live === true, generatedAt: typeof raw.generated_at === "string" ? raw.generated_at : null, windowDays: typeof raw.window_days === "number" ? raw.window_days : null, items };
}

export async function getFilonCatalogueRelief(): Promise<FilonCatalogueRelief> {
  const response = await fetch(`${FILON_API_BASE_URL}/api/catalog/relief`);
  if (!response.ok) throw new Error(`Relief de prix indisponible (${response.status})`);
  return normalizeFilonCatalogueRelief((await response.json()) as { live?: boolean; generated_at?: string | null; window_days?: number | null; columns?: RawFilonPriceRelief[] });
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

export function formatFilonPrice(amount: number, locale: "fr" | "nl" | "en", currency?: string | null) {
  const normalizedCurrency = normalizeFilonCurrency(currency);
  if (!Number.isFinite(amount) || normalizedCurrency === null) return "—";
  return new Intl.NumberFormat(locale === "en" ? "en-BE" : `${locale}-BE`, { style: "currency", currency: normalizedCurrency, maximumFractionDigits: 2 }).format(amount);
}
