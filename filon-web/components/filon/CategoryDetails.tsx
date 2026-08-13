"use client";

import { ProductCard } from "@/components/filon/ProductCard";
import { useLocale, type Locale } from "@/lib/i18n";

type Subcategory = { name: string; count: number };
type Category = { name: string; slug: string; count: number; subcategories?: Subcategory[] };
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

const COPY: Record<Locale, {
  back: string;
  compared: (count: string) => string;
  subs: string;
  other: string;
  all: string;
  empty: string;
  browse: (count: string) => string;
}> = {
  fr: {
    back: "← Tout le catalogue",
    compared: (count) => `${count} produits comparés chez nos marchands partenaires.`,
    subs: "Sous-rayons",
    other: "Autres rayons",
    all: "Tout",
    empty: "Aucun produit disponible dans ce rayon pour le moment.",
    browse: (count) => `Parcourir les ${count} produits`,
  },
  nl: {
    back: "← Volledige catalogus",
    compared: (count) => `${count} producten vergeleken bij onze partnerwinkels.`,
    subs: "Subcategorieën",
    other: "Andere categorieën",
    all: "Alles",
    empty: "Er zijn momenteel geen producten beschikbaar in deze categorie.",
    browse: (count) => `${count} producten bekijken`,
  },
  en: {
    back: "← Full catalogue",
    compared: (count) => `${count} products compared across our partner merchants.`,
    subs: "Subcategories",
    other: "Other categories",
    all: "All",
    empty: "No products are available in this category at the moment.",
    browse: (count) => `Browse ${count} products`,
  },
};

export function CategoryDetails({
  category,
  active,
  total,
  items,
  others,
}: {
  category: Category;
  active?: string;
  total: number;
  items: Offer[];
  others: Category[];
}) {
  const { locale } = useLocale();
  const copy = COPY[locale];
  const numberLocale = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  const formatNumber = (value: number) => value.toLocaleString(numberLocale);
  const subs = category.subcategories ?? [];

  return (
    <section className="ed-band" style={{ paddingTop: "clamp(90px, 12vw, 130px)" }}>
      <div className="ed-wrap">
        <p style={{ marginBottom: 18 }}><a href="/catalogue" style={{ fontSize: 13.5, color: "var(--ink-3)" }}>{copy.back}</a></p>
        <h1 className="cat-rail-title" style={{ fontSize: "clamp(26px, 4vw, 36px)" }}>{category.name}</h1>
        <p className="cat-rail-sub" style={{ marginBottom: 24 }}>{copy.compared(formatNumber(total))}</p>

        {subs.length > 0 && (
          <nav className="cat-chips" aria-label={copy.subs}>
            <a className={`cat-chip${active ? "" : " on"}`} href={`/categorie/${category.slug}/`}>{copy.all}</a>
            {subs.map((sub) => (
              <a key={sub.name} className={`cat-chip${active === sub.name ? " on" : ""}`} href={`/categorie/${category.slug}/?sub=${encodeURIComponent(sub.name)}`}>
                {sub.name} <span>{formatNumber(sub.count)}</span>
              </a>
            ))}
          </nav>
        )}

        {others.length > 0 && (
          <nav className="cat-chips" aria-label={copy.other}>
            {others.map((other) => <a key={other.slug} className="cat-chip" href={`/categorie/${other.slug}/`}>{other.name} <span>{formatNumber(other.count)}</span></a>)}
          </nav>
        )}

        {items.length === 0 ? (
          <p style={{ color: "var(--ink-3)", fontSize: 14.5, marginTop: 24 }}>{copy.empty}</p>
        ) : (
          <>
            <div className="fx-product-grid" style={{ marginTop: 28 }}>{items.map((offer) => <ProductCard key={offer.id} offer={offer} />)}</div>
            {total > items.length && <p style={{ marginTop: 30, textAlign: "center" }}><a className="ed-btn ghost" href="/catalogue/" style={{ textDecoration: "none" }}>{copy.browse(formatNumber(total))}</a></p>}
          </>
        )}
      </div>
    </section>
  );
}
