// Lecture du catalogue côté serveur, et contrat d'URL des filtres.
//
// La grille était chargée depuis le navigateur : elle dépendait donc du réseau
// du visiteur, n'était pas indexable, et échouait sur une phrase sans issue
// (« Impossible de charger le catalogue pour le moment »). Les pages rayon,
// rendues côté serveur, ne connaissaient pas ce problème. Le catalogue passe
// sur le même modèle.
//
// Tout l'état des filtres vit dans l'URL. Une sélection se partage, se met en
// favori, et le bouton Précédent revient au résultat attendu — ce qu'aucun
// filtre en état React ne permet.

import { API } from "@/lib/api";

export type Subcategory = { name: string; count: number };
export type Category = {
  name: string;
  slug: string;
  count: number;
  subcategories?: Subcategory[];
};
export type Department = {
  name: string;
  slug: string;
  count: number;
  categories: Category[];
};

export type Offer = {
  id: number;
  name: string;
  brand: string | null;
  price: number | null;
  currency: string | null;
  image: string | null;
  link: string | null;
  /** Valeur observée dans le dernier flux marchand, éventuellement absente. */
  in_stock: boolean | null;
  /** Dernier relevé de prix Core, distinct d’une mise à jour interne. */
  observed_at: string | null;
  merchant: { name: string; slug: string };
};

// Les offres ci-dessous sont des accessoires ou des appareils secondaires dont le
// titre mentionne un smartphone pour la compatibilité. Elles ont été observées
// dans le sous-rayon public Smartphones le 18 août 2026. Ce filet de visibilité
// ne touche aucun autre rayon et sera redondant dès que le correctif backend
// fusionné sera enfin déployé par Railway.
const SMARTPHONE_DISPLAY_IMPOSTORS = [
  /\bsmarttag\d*\b/i,
  /\b(?:réalité\s+virtuelle|virtual\s+reality|vr\s+(?:glasses|headset|bril))\b/i,
  /\bsmartphone\s+ventilat(?:ion|or)\b/i,
  /\b(?:car|auto|dashboard|vent)\s+(?:mount|holder)\b/i,
  // Marqueurs d’accessoires déjà mesurés et employés dans le garde-fou
  // backend Smartphones : ils décrivent une protection, pas un appareil.
  /\b(?:coque|phone\s+cover|telefoonhoes|smartphonehoes|backcover|bookcase|screen\s+protector|screenprotector|tempered\s+glass|verre\s+tremp[ée]|protege[- ]?ecran|protège[- ]?écran|bescherm(?:ing|hoes)|cover|covr|prot(?:ection|ction))\b/i,
  // Intrus strictement observés : support de téléphone, bracelet ou imprimante
  // compatible avec un mobile, mais pas appareil principal.
  /\b(?:holder|phone\s+stand|finger\s+grip|bracket|socket|wrist\s+band|armband|fotoprinter|photo\s*printer|pocket\s*printer|mini\s*printer)\b/i,
  // Pièces détachées observées dans la vitrine Smartphones : elles peuvent
  // citer un modèle précis mais ne constituent jamais un téléphone achetable.
  /\b(?:circuit(?:\s+imprim[ée])?|pcb|capteur|empreintes?\s+digitales?|gabarit|isolation\s+des\s+pistes)\b/i,
  // Composants et protections relevés ensuite dans les premières cartes :
  // une référence de réparation ou un stylet ne prouve pas un téléphone complet.
  /\b(?:service\s+pack|gh\d{2}-\d+|haut[- ]?parleur|s[\s-]?pen|verre\s+(?:hybride|tremp[ée])|étui|etui|pochette|housse|husa)\b|tui\s+pour/i,
] as const;

// Un accessoire peut citer Apple, Samsung ou Huawei dans son titre. On exige
// donc une famille de téléphone concrète et on applique ensuite les exclusions
// ci-dessus. Quand la preuve manque, FILON préfère ne pas afficher l’offre.
const SMARTPHONE_PRIMARY_EVIDENCE = [
  /\biphone\s*(?:\d|se\b|pro\b|plus\b|mini\b|air\b)/i,
  /\bgalaxy\s+(?:s|a|z|note|m|xcover)\s*\d/i,
  /\b(?:google\s+)?pixel\s*\d/i,
  /\b(?:oneplus|xiaomi|redmi|poco|huawei|honor|oppo|realme|vivo|nokia|motorola|moto|asus|sony\s+xperia|nothing\s+phone)\s*[a-z0-9]/i,
] as const;

function isVisibleInSelectedSubcategory(offer: Offer, subcategory: string | null) {
  if (subcategory !== "Smartphones") return true;
  return SMARTPHONE_PRIMARY_EVIDENCE.some((pattern) => pattern.test(offer.name))
    && !SMARTPHONE_DISPLAY_IMPOSTORS.some((pattern) => pattern.test(offer.name));
}

export type CatalogueQuery = {
  q?: string;
  dept?: string;
  cat?: string;
  sub?: string;
  brand?: string;
  min?: string;
  max?: string;
  sort?: string;
  page?: string;
  per?: string;
};

// Clés de dictionnaire plutôt que libellés : le tri doit se lire en NL et en
// EN comme en FR.
export const SORTS = [
  { value: "relevance", labelKey: "cat.sortRelevance" },
  { value: "price_asc", labelKey: "cat.sortPriceAsc" },
  { value: "price_desc", labelKey: "cat.sortPriceDesc" },
  { value: "name", labelKey: "cat.sortName" },
] as const;

export const PER_PAGE = [24, 48, 96] as const;

const TIMEOUT = 8000;

async function getJson(path: string, revalidate: number, timeout = TIMEOUT): Promise<any | null> {
  try {
    const res = await fetch(`${API}${path}`, {
      next: { revalidate },
      signal: AbortSignal.timeout(timeout),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export type PulsePayload = {
  live: boolean;
  lastReading: string | null;
  readings24h: number;
  drops24h: number;
} | null;

/** Le battement du catalogue. Fenêtre de cache courte : c'est précisément ce
 *  chiffre qui doit paraître frais. */
export async function getPulse(): Promise<PulsePayload> {
  const data = await getJson("/api/catalog/pulse", 120);
  if (!data?.live) return null;
  return {
    live: true,
    lastReading: data.last_reading ?? null,
    readings24h: Number(data.readings_24h || 0),
    drops24h: Number(data.drops_24h || 0),
  };
}

/** Rangées thématiques — le contenu qui change tout seul d'un jour à l'autre. */
export async function getRails(): Promise<Array<{ key: string; items: any[] }>> {
  // Les rangées enrichissent la page, mais une requête lente ne doit jamais
  // retenir le premier produit ni la navigation. Elles sont diffusées sous
  // Suspense et abandonnées rapidement si le service n'est pas disponible.
  const data = await getJson("/api/catalog/highlights?limit=12", 300, 2500);
  return (data?.sections || []).filter(
    (s: { items?: unknown[] }) => (s.items || []).length > 0
  );
}

export async function getDepartments(): Promise<Department[]> {
  const data = await getJson("/api/catalog/categories", 3600);
  return (data?.departments || []) as Department[];
}

/** Retrouve le rayon et le département à partir des créneaux d'URL. */
export function resolve(departments: Department[], query: CatalogueQuery) {
  const department = departments.find((d) => d.slug === query.dept) || null;
  const pool = department ? department.categories : departments.flatMap((d) => d.categories);
  const category = pool.find((c) => c.slug === query.cat) || null;
  // Un sous-rayon n'a de sens que sous son rayon : hors contexte, il est ignoré
  // plutôt que de vider silencieusement la page.
  const subcategory =
    category && query.sub && (category.subcategories || []).some((s) => s.name === query.sub)
      ? query.sub
      : null;
  // Un rayon sélectionné sans département : on retrouve le sien pour le fil.
  const owningDepartment =
    department ||
    (category ? departments.find((d) => d.categories.some((c) => c.slug === category.slug)) || null : null);
  return { department: owningDepartment, category, subcategory };
}

export function pageSize(query: CatalogueQuery): number {
  const n = Number(query.per);
  return (PER_PAGE as readonly number[]).includes(n) ? n : 48;
}

export function pageNumber(query: CatalogueQuery): number {
  const n = Number(query.page);
  return Number.isFinite(n) && n >= 1 ? Math.floor(n) : 1;
}

export function sortValue(query: CatalogueQuery): string {
  return SORTS.some((s) => s.value === query.sort) ? (query.sort as string) : "relevance";
}

export async function getOffers(
  query: CatalogueQuery,
  resolved: ReturnType<typeof resolve>
): Promise<{ total: number; items: Offer[]; withheld_for_evidence: boolean } | null> {
  const per = pageSize(query);
  const page = pageNumber(query);
  const params = new URLSearchParams({
    limit: String(per),
    offset: String((page - 1) * per),
    sort: sortValue(query),
  });
  if (query.q) params.set("q", query.q);
  // Le département filtre tout seul quand aucun rayon n'est choisi. Sans lui,
  // sélectionner « Beauté & Santé » n'envoyait aucun critère et la page
  // renvoyait le catalogue entier — des pneus dans la beauté.
  if (resolved.department && !resolved.category) {
    params.set("department", resolved.department.slug);
  }
  if (resolved.category) params.set("category", resolved.category.name);
  if (resolved.subcategory) params.set("subcategory", resolved.subcategory);
  if (query.brand) params.set("brand", query.brand);
  if (query.min) params.set("price_min", query.min);
  if (query.max) params.set("price_max", query.max);

  const data = await getJson(`/api/catalog/offers?${params.toString()}`, 300);
  if (!data) return null;
  const items = (data.items || []) as Offer[];
  const visibleItems = items.filter((offer) => isVisibleInSelectedSubcategory(offer, resolved.subcategory));
  return {
    total: Number(data.total || 0),
    items: visibleItems,
    withheld_for_evidence: resolved.subcategory === "Smartphones" && items.length > 0 && visibleItems.length === 0,
  };
}

/** Construit une URL de catalogue en repartant des filtres courants.
 *  Une valeur `null` retire le paramètre ; changer un filtre remet page 1. */
export function href(query: CatalogueQuery, patch: Partial<CatalogueQuery>): string {
  const next: Record<string, string> = {};
  for (const [k, v] of Object.entries({ ...query, ...patch })) {
    if (v != null && v !== "") next[k] = String(v);
  }
  if (!("page" in patch)) delete next.page;
  const qs = new URLSearchParams(next).toString();
  return qs ? `/catalogue/?${qs}` : "/catalogue/";
}

/** Suite de pages avec ellipses : 1 … 4 5 [6] 7 8 … 250. */
export function pageWindow(page: number, last: number): Array<number | null> {
  if (last <= 7) return Array.from({ length: last }, (_, i) => i + 1);
  const out: Array<number | null> = [1];
  const from = Math.max(2, page - 2);
  const to = Math.min(last - 1, page + 2);
  if (from > 2) out.push(null);
  for (let p = from; p <= to; p++) out.push(p);
  if (to < last - 1) out.push(null);
  out.push(last);
  return out;
}
