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
  merchant: { name: string; slug: string };
};

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

async function getJson(path: string, revalidate: number): Promise<any | null> {
  try {
    const res = await fetch(`${API}${path}`, {
      next: { revalidate },
      signal: AbortSignal.timeout(TIMEOUT),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
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
): Promise<{ total: number; items: Offer[] } | null> {
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
  return { total: Number(data.total || 0), items: (data.items || []) as Offer[] };
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
