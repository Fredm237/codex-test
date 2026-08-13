import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { buildMetadata, JsonLd } from "@/lib/seo";
import { API } from "@/lib/api";
import type { VerdictData } from "@/components/editorial/Verdict";
import { ProductDetails } from "@/components/filon/ProductDetails";
import { site } from "@/lib/site";

// Fiche d'un produit regroupé par EAN : le même article, comparé chez tous les
// marchands qui le vendent. Rendu serveur + ISR — indexable, et sans spinner.
export const revalidate = 1800;
export const dynamicParams = true;

type ProductOffer = {
  id: number;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  link: string | null;
  merchant: { name: string; slug: string; region: string | null };
};

type Product = {
  ean: string;
  name: string;
  brand: string | null;
  category: string | null;
  image: string | null;
  price_min: number | null;
  price_max: number | null;
  currency: string | null;
  offers_count: number;
  merchants_count: number;
  offers: ProductOffer[];
  verdict: VerdictData | null;
};

/** Signale une indisponibilité passagère, à ne surtout pas confondre avec une
 *  page absente. Voir `getProduct` pour la raison. */
class CatalogueIndisponible extends Error {
  constructor(cause: string) {
    super(`Catalogue indisponible : ${cause}`);
    this.name = "CatalogueIndisponible";
  }
}

/** Rend le produit, `null` s'il n'existe pas — et LÈVE si le catalogue est
 *  seulement injoignable.
 *
 *  La distinction est tout sauf cosmétique. Cette fonction rendait `null`
 *  dans les deux cas, et l'appelant faisait `notFound()` : une panne de base
 *  transformait donc toutes les fiches produit déjà indexées en 404, et la
 *  Search Console a fini par signaler leur désindexation.
 *
 *  Un 404 dit à un moteur « cette page n'existe pas, oublie-la ». Un 5xx dit
 *  « indisponible pour le moment, repasse ». Une panne d'API doit dire la
 *  seconde chose. C'est la différence entre perdre son référencement et
 *  attendre la fin d'un incident. */
async function getProduct(ean: string): Promise<Product | null> {
  let res: Response;
  try {
    res = await fetch(`${API}/api/catalog/product/${encodeURIComponent(ean)}`, {
      next: { revalidate: 1800 },
      signal: AbortSignal.timeout(8000),
    });
  } catch (e) {
    // Réseau coupé ou délai dépassé : on ne sait rien du produit.
    throw new CatalogueIndisponible(e instanceof Error ? e.name : "réseau");
  }
  // Seul un 404 franc prouve que le produit n'existe pas.
  if (res.status === 404) return null;
  if (!res.ok) throw new CatalogueIndisponible(`HTTP ${res.status}`);
  try {
    return (await res.json()) as Product;
  } catch {
    throw new CatalogueIndisponible("réponse illisible");
  }
}

function money(price: number | null, currency: string | null): string {
  if (price == null) return "—";
  const sym = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
}

export async function generateMetadata({ params }: { params: Promise<{ ean: string }> }): Promise<Metadata> {
  const { ean } = await params;
  const p = await getProduct(ean);
  if (!p) {
    return buildMetadata({ path: `/produits/${ean}`, title: "Produit", description: "Produit comparé par FILON." });
  }
  const label = [p.brand, p.name].filter(Boolean).join(" ");
  const from = p.price_min != null ? ` à partir de ${money(p.price_min, p.currency)}` : "";
  return buildMetadata({
    path: `/produits/${ean}`,
    title: `${label}${from}`,
    description: `${label} comparé chez ${p.merchants_count} marchand${p.merchants_count > 1 ? "s" : ""}${from}. Prix, disponibilité et meilleure offre réunis par FILON.`,
    image: p.image || undefined,
  });
}

export default async function ProduitGroupePage({ params }: { params: Promise<{ ean: string }> }) {
  const { ean } = await params;
  const p = await getProduct(ean);
  if (!p) notFound();

  const inStock = p.offers.filter((o) => o.in_stock !== false);
  const best = inStock[0] ?? p.offers[0];
  const saving =
    p.price_min != null && p.price_max != null && p.price_max > p.price_min
      ? p.price_max - p.price_min
      : null;

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "Product",
          name: p.name,
          brand: p.brand ? { "@type": "Brand", name: p.brand } : undefined,
          gtin13: p.ean,
          image: p.image || undefined,
          offers: {
            "@type": "AggregateOffer",
            priceCurrency: p.currency || "EUR",
            lowPrice: p.price_min ?? undefined,
            highPrice: p.price_max ?? undefined,
            offerCount: p.offers_count,
            url: `${site.url}/produits/${p.ean}`,
          },
        }}
      />

      <section className="ed-band" style={{ paddingTop: "clamp(90px, 12vw, 130px)" }}>
        <div className="ed-wrap">
          <p style={{ marginBottom: 20 }}>
            <a href="/catalogue" style={{ fontSize: 13.5, color: "var(--ink-3)" }}>← Retour au catalogue</a>
          </p>

          <div className="pg-grid">
            <div className="pg-media">
              {p.image ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={p.image} alt={p.name} />
              ) : <span aria-hidden="true">—</span>}
            </div>

            <ProductDetails p={p} best={best} saving={saving} />
          </div>
        </div>
      </section>
    </>
  );
}
