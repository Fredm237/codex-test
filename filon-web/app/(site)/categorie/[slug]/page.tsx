import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { buildMetadata } from "@/lib/seo";
import { API } from "@/lib/api";

// Page d'un rayon FILON. Rendu serveur + ISR : indexable, et sans spinner.
export const revalidate = 1800;
export const dynamicParams = true;

type Category = { name: string; slug: string; count: number };

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
    return ((await res.json()).items || []) as Category[];
  } catch {
    return [];
  }
}

async function getOffers(category: string): Promise<{ total: number; items: Offer[] }> {
  try {
    const res = await fetch(
      `${API}/api/catalog/offers?category=${encodeURIComponent(category)}&limit=48`,
      { next: { revalidate: 1800 }, signal: AbortSignal.timeout(8000) }
    );
    if (!res.ok) return { total: 0, items: [] };
    const data = await res.json();
    return { total: data.total || 0, items: (data.items || []) as Offer[] };
  } catch {
    return { total: 0, items: [] };
  }
}

function money(price: number | null, currency: string | null): string {
  if (price == null) return "—";
  const sym = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
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

export default async function CategoriePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const categories = await getCategories();
  const category = categories.find((c) => c.slug === slug);
  if (!category) notFound();

  const { total, items } = await getOffers(category.name);
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
            <div
              style={{
                display: "grid",
                gap: 16,
                gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                marginTop: 28,
              }}
            >
              {items.map((o) => (
                <article className="cat-card" key={o.id}>
                  <a className="cat-card-media" href={`/produit/${o.id}/`} aria-label={o.name}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    {o.image ? <img src={o.image} alt="" loading="lazy" /> : <span aria-hidden="true">—</span>}
                  </a>
                  <div className="cat-card-body">
                    {o.brand && <span className="cat-card-brand">{o.brand}</span>}
                    <a className="cat-card-title" href={`/produit/${o.id}/`}>{o.name}</a>
                    <span className="cat-card-merchant">chez {o.merchant.name}</span>
                    <div className="cat-card-foot">
                      <span className="cat-card-prices">
                        <b>{money(o.price, o.currency)}</b>
                      </span>
                      {o.link && (
                        <a
                          className="cat-card-cta"
                          href={o.link}
                          target="_blank"
                          rel="noopener noreferrer sponsored"
                        >
                          Voir l&apos;offre
                        </a>
                      )}
                    </div>
                  </div>
                </article>
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
