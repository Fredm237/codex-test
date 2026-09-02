import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { buildMetadata } from "@/lib/seo";
import type { VerdictData } from "@/components/editorial/Verdict";
import type { DecisionData } from "@/components/filon/DecisionPanel";
import { OfferBackLink, OfferProductDetails } from "@/components/filon/OfferProductDetails";
import { isPurchasableOffer, money } from "@/components/filon/product-copy";
import { API } from "@/lib/api";

// Une offre à la frontière des 72 h ne doit jamais rester achetable dans un
// HTML ISR ancien. Le composant client garde ensuite cette frontière vivante.
export const dynamic = "force-dynamic";
export const revalidate = 0;
export const dynamicParams = true;

type Hist = { price: number | null; currency?: string | null; at: string | null; in_stock?: boolean | null };
type Offer = {
  id: number;
  name: string;
  brand: string | null;
  category: string | null;
  ean: string | null;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  observed_at: string | null;
  evidence_current: boolean | null;
  image: string | null;
  link: string | null;
  merchant: { name: string; slug: string; domain: string | null; region: string | null };
  history: Hist[];
  verdict: VerdictData | null;
  decision: DecisionData | null;
  product: {
    ean: string;
  } | null;
};

class CatalogueIndisponible extends Error {
  constructor(cause: string) {
    super(`Catalogue indisponible : ${cause}`);
    this.name = "CatalogueIndisponible";
  }
}

async function getOffer(id: string): Promise<Offer | null> {
  let res: Response;
  try {
    res = await fetch(`${API}/api/catalog/offer/${encodeURIComponent(id)}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });
  } catch (error) {
    throw new CatalogueIndisponible(error instanceof Error ? error.name : "réseau");
  }
  if (res.status === 404) return null;
  if (!res.ok) throw new CatalogueIndisponible(`HTTP ${res.status}`);
  try {
    return (await res.json()) as Offer;
  } catch {
    throw new CatalogueIndisponible("réponse illisible");
  }
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const o = await getOffer(id);
  if (!o) return buildMetadata({ path: `/produit/${encodeURIComponent(id)}`, title: "Fiche produit", description: "Produit comparé par FILON." });
  const parts = [o.brand, o.name].filter(Boolean).join(" ");
  const formattedPrice = isPurchasableOffer(o) ? money(o.price, o.currency) : "—";
  const price = formattedPrice !== "—" ? ` — ${formattedPrice}` : "";
  return buildMetadata({
    path: `/produit/${encodeURIComponent(id)}`,
    title: `${parts}${price}`,
    description: `${parts}${price} chez ${o.merchant.name}. Offre indexée, avec historique lorsqu'il est disponible.`,
    image: o.image || undefined,
  });
}

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const o = await getOffer(id);
  if (!o) notFound();

  return (
    <section className="ed-band p11-product-surface" style={{ paddingTop: "clamp(90px, 12vw, 130px)" }}>
      <div className="ed-wrap">
        <p style={{ marginBottom: 20 }}>
            <OfferBackLink />
        </p>
        <div style={{ display: "grid", gap: 32, gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.1fr)", alignItems: "start" }} className="pd-grid">
          <div style={{ aspectRatio: "1 / 1", background: "#fff", borderRadius: 20, border: "1px solid var(--line-2)", display: "grid", placeItems: "center", overflow: "hidden" }}>
            {o.image ? (
              <img src={o.image} alt={o.name} style={{ width: "100%", height: "100%", objectFit: "contain", padding: 22 }} />
            ) : <span aria-hidden="true">—</span>}
          </div>
          <OfferProductDetails offer={o} />
        </div>
      </div>
    </section>
  );
}
