import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { buildMetadata } from "@/lib/seo";
import { API } from "@/lib/api";
import { ProductCard, CARD_COPY } from "@/components/filon/ProductCard";

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

async function getCategories(): Promise<Category[]> {
  try {
    const res = await fetch(`${API}/api/catalog/categories`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) return [];
    const data = await res.json();
    // On lit l'arborescence : elle porte les sous-rayons, pas la liste plate.
    return (data.departments || []).flatMap(
      (d: { categories: Category[] }) => d.categories
    ) as Category[];
  } catch {
    return [];
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

  return (
    <section className="ed-band" style={{ paddingTop: "clamp(90px, 12vw, 130px)" }}>
      <div className="ed-wrap">
        <p style={{ marginBottom: 18 }}>
          <a href="/catalogue" style={{ fontSize: 13.5, color: "var(--ink-3)" }}>← Tout le catalogue</a>
        </p>

        <h1 className="cat-rail-title" style={{ fontSize: "clamp(26px, 4vw, 36px)" }}>{category.name}</h1>
        <p className="cat-rail-sub" style={{ marginBottom: 24 }}>
          {total.toLocaleString("fr-FR")} produits comparés chez nos marchands partenaires.
        </p>

        {subs.length > 0 && (
          <nav className="cat-chips" aria-label="Sous-rayons">
            <a
              className={`cat-chip${active ? "" : " on"}`}
              href={`/categorie/${category.slug}/`}
            >
              Tout
            </a>
            {subs.map((s) => (
              <a
                key={s.name}
                className={`cat-chip${active === s.name ? " on" : ""}`}
                href={`/categorie/${category.slug}/?sub=${encodeURIComponent(s.name)}`}
              >
                {s.name} <span>{s.count.toLocaleString("fr-FR")}</span>
              </a>
            ))}
          </nav>
        )}

        {others.length > 0 && (
          <nav className="cat-chips" aria-label="Autres rayons">
            {others.map((c) => (
              <a key={c.slug} className="cat-chip" href={`/categorie/${c.slug}/`}>
                {c.name} <span>{c.count.toLocaleString("fr-FR")}</span>
              </a>
            ))}
          </nav>
        )}

        {items.length === 0 ? (
          <p style={{ color: "var(--ink-3)", fontSize: 14.5, marginTop: 24 }}>
            Aucun produit disponible dans ce rayon pour le moment.
          </p>
        ) : (
          <>
            <div className="fx-product-grid" style={{ marginTop: 28 }}>
              {items.map((o) => (
                <ProductCard key={o.id} offer={o} copy={CARD_COPY.fr} />
              ))}
            </div>

            {total > items.length && (
              <p style={{ marginTop: 30, textAlign: "center" }}>
                <a className="ed-btn ghost" href="/catalogue/" style={{ textDecoration: "none" }}>
                  Parcourir les {total.toLocaleString("fr-FR")} produits
                </a>
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
