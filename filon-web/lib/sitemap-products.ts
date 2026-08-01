import { API } from "./api";

/** Nombre d'URL par fichier sitemap. Google en accepte 50 000 ; on garde de la
 *  marge pour ne pas frôler la limite quand le catalogue grossit. */
export const SITEMAP_CHUNK = 25_000;

export type SitemapProduct = { ean: string; updated: string | null };

type Payload = { total: number; items: SitemapProduct[] };

/** Récupère une tranche de produits indexables.
 *
 *  Ne remonte que les produits vendus par au moins deux marchands : c'est le
 *  filtre appliqué côté backend, et la seule population dont la fiche apporte
 *  un contenu que la fiche de l'offre ne dit pas déjà.
 */
export async function fetchSitemapProducts(
  offset: number,
  limit: number = SITEMAP_CHUNK
): Promise<Payload> {
  try {
    const res = await fetch(
      `${API}/api/catalog/sitemap/products?limit=${limit}&offset=${offset}`,
      { next: { revalidate: 86400 }, signal: AbortSignal.timeout(15000) }
    );
    if (!res.ok) return { total: 0, items: [] };
    const data = (await res.json()) as Payload;
    return { total: data.total ?? 0, items: data.items ?? [] };
  } catch {
    // Un backend indisponible ne doit pas faire échouer le build : on publie
    // alors un sitemap sans produits plutôt que rien du tout.
    return { total: 0, items: [] };
  }
}

/** Nombre de fichiers sitemap nécessaires (au moins un, même à vide). */
export async function countSitemapChunks(): Promise<number> {
  const { total } = await fetchSitemapProducts(0, 1);
  return Math.max(1, Math.ceil(total / SITEMAP_CHUNK));
}
