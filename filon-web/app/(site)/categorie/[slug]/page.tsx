import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { buildMetadata } from "@/lib/seo";
import { API } from "@/lib/api";
import { CategoryDetails } from "@/components/filon/CategoryDetails";

// Page d'un rayon FILON. Rendu serveur + ISR : indexable, et sans spinner.
export const revalidate = 1800;
export const dynamicParams = true;

type Subcategory = { name: string; count: number };
type Category = {
  name: string; slug: string; count: number;
  subcategories?: Subcategory[];
};

type Offer = {
  id: number;
  name: string;
  brand: string | null;
  price: number | null;
  currency: string | null;
  image: string | null;
  link: string | null;
  merchant: { name: string; slug: string };
};

/** Signale une indisponibilité passagère, distincte d'un rayon inexistant. */
class CatalogueIndisponible extends Error {
  constructor(cause: string) {
    super(`Catalogue indisponible : ${cause}`);
    this.name = "CatalogueIndisponible";
  }
}

/** Rend l'arborescence des rayons, ou LÈVE si le catalogue est injoignable.
 *
 *  Elle rendait une liste vide en cas de panne. L'appelant n'y retrouvait
 *  alors aucun rayon et appelait `notFound()` : une base muette suffisait à
 *  transformer TOUS les rayons en 404, alors que ce sont les pages qui
 *  portent le référencement. La Search Console a fini par le signaler.
 *
 *  Une liste vide et une panne ne veulent pas dire la même chose. La première
 *  est une réponse, la seconde une absence de réponse. */
async function getCategories(): Promise<Category[]> {
  let res: Response;
  try {
    res = await fetch(`${API}/api/catalog/categories`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(8000),
    });
  } catch (e) {
    throw new CatalogueIndisponible(e instanceof Error ? e.name : "réseau");
  }
  if (!res.ok) throw new CatalogueIndisponible(`HTTP ${res.status}`);
  try {
    const data = await res.json();
    // On lit l'arborescence : elle porte les sous-rayons, pas la liste plate.
    return (data.departments || []).flatMap(
      (d: { categories: Category[] }) => d.categories
    ) as Category[];
  } catch {
    throw new CatalogueIndisponible("réponse illisible");
  }
}

async function getOffers(
  category: string,
  sub?: string
): Promise<{ total: number; items: Offer[] }> {
  try {
    const params = new URLSearchParams({ category, limit: "48" });
    if (sub) params.set("subcategory", sub);
    const res = await fetch(
      `${API}/api/catalog/offers?${params.toString()}`,
      { next: { revalidate: 1800 }, signal: AbortSignal.timeout(8000) }
    );
    if (!res.ok) return { total: 0, items: [] };
    const data = await res.json();
    return { total: data.total || 0, items: (data.items || []) as Offer[] };
  } catch {
    return { total: 0, items: [] };
  }
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const category = (await getCategories()).find((c) => c.slug === slug);
  if (!category) {
    return buildMetadata({ path: `/categorie/${slug}`, title: "Rayon" });
  }
  return buildMetadata({
    path: `/categorie/${slug}`,
    title: category.name,
    description: `${category.count.toLocaleString("fr-FR")} produits en ${category.name}, comparés chez nos marchands partenaires. Prix, disponibilité et meilleure offre réunis par FILON.`,
  });
}

export default async function CategoriePage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ sub?: string }>;
}) {
  const { slug } = await params;
  const { sub } = await searchParams;
  const categories = await getCategories();
  const category = categories.find((c) => c.slug === slug);
  if (!category) notFound();

  // Un sous-rayon inconnu est ignoré plutôt que de vider la page.
  const subs = category.subcategories ?? [];
  const active = subs.some((s) => s.name === sub) ? sub : undefined;
  const { total, items } = await getOffers(category.name, active);
  const others = categories.filter((c) => c.slug !== slug).slice(0, 12);

  return <CategoryDetails category={category} active={active} total={total} items={items} others={others} />;
}
