import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { buildMetadata, JsonLd, siteUrl } from "@/lib/seo";
import { API } from "@/lib/api";
import type { VerdictData } from "@/components/editorial/Verdict";
import type { DecisionData } from "@/components/filon/DecisionPanel";
import { ProductDetails } from "@/components/filon/ProductDetails";
import { deriveProductComparison, money } from "@/components/filon/product-copy";

// Fiche d'un produit regroupé par EAN. Comparaison et JSON-LD expirent avec les
// observations : aucun cache ISR ne prolonge un prix au-delà de sa preuve.
export const dynamic = "force-dynamic";
export const revalidate = 0;
export const dynamicParams = true;

type ProductOffer = {
  id: number;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  observed_at: string | null;
  evidence_current: boolean | null;
  link: string | null;
  merchant: { name: string; slug: string; region: string | null };
};

type Product = {
  ean: string;
  name: string;
  brand: string | null;
  category: string | null;
  image: string | null;
  offers: ProductOffer[];
  verdict: VerdictData | null;
  decision: DecisionData | null;
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
      cache: "no-store",
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

function gtinSchema(ean: string): Record<string, string> {
  const normalized = ean.trim();
  if (!/^\d+$/.test(normalized)) return {};
  if (normalized.length === 8) return { gtin8: normalized };
  if (normalized.length === 13) return { gtin13: normalized };
  if (normalized.length === 14) return { gtin14: normalized };
  return {};
}

export async function generateMetadata({ params }: { params: Promise<{ ean: string }> }): Promise<Metadata> {
  const { ean } = await params;
  const p = await getProduct(ean);
  if (!p) {
    return buildMetadata({ path: `/produits/${encodeURIComponent(ean)}`, title: "Produit", description: "Produit comparé par FILON." });
  }
  const label = [p.brand, p.name].filter(Boolean).join(" ");
  const comparison = deriveProductComparison(p.offers);
  const merchantsCount = comparison
    ? new Set(comparison.offers.map((offer) => offer.merchant.slug || offer.merchant.name)).size
    : 0;
  const from = comparison ? ` à partir de ${money(comparison.priceMin, comparison.currency)}` : "";
  const scope = comparison
    ? ` observé chez ${merchantsCount} marchand${merchantsCount > 1 ? "s" : ""}`
    : " à comparer chez les marchands indexés";
  return buildMetadata({
    path: `/produits/${encodeURIComponent(ean)}`,
    title: `${label}${from}`,
    description: `${label}${scope}${from}. Prix et disponibilité déclarée des offres indexées réunis par FILON.`,
    image: p.image || undefined,
  });
}

export default async function ProduitGroupePage({ params }: { params: Promise<{ ean: string }> }) {
  const { ean } = await params;
  const p = await getProduct(ean);
  if (!p) notFound();

  const comparison = deriveProductComparison(p.offers);

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "Product",
          name: p.name,
          brand: p.brand ? { "@type": "Brand", name: p.brand } : undefined,
          ...gtinSchema(p.ean),
          image: p.image || undefined,
          offers: comparison ? {
            "@type": "AggregateOffer",
            priceCurrency: comparison.currency,
            lowPrice: comparison.priceMin,
            highPrice: comparison.priceMax,
            offerCount: comparison.offers.length,
            url: siteUrl(`/produits/${encodeURIComponent(p.ean)}`),
          } : undefined,
        }}
      />

      <section className="ed-band p11-product-surface p19-product-surface" data-product-evidence="exact">
        <div className="ed-wrap p19-product-wrap">
          <p className="p19-product-back">
            <a href="/catalogue">← Retour au catalogue</a>
          </p>

          <div className="pg-grid">
            <div className="pg-media">
              {p.image ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={p.image} alt={p.name} />
              ) : <span aria-hidden="true">—</span>}
              <span className="p19-product-ean">EAN&nbsp;{p.ean}</span>
              <span className="p19-product-axis" aria-hidden="true" />
            </div>

            <ProductDetails p={p} />
          </div>
        </div>
      </section>
    </>
  );
}
