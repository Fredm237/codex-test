import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { buildMetadata } from "@/lib/seo";
import type { VerdictData } from "@/components/editorial/Verdict";
import type { DecisionData } from "@/components/filon/DecisionPanel";
import { OfferBackLink, OfferProductDetails } from "@/components/filon/OfferProductDetails";
import { API } from "@/lib/api";

// Rendu serveur + ISR : la page est mise en cache et revalidée toutes les heures.
// Chaque produit devient une URL propre, indexable par Google.
export const revalidate = 3600;
export const dynamicParams = true;

type Hist = { price: number | null; at: string | null };
type Offer = {
  id: number;
  name: string;
  brand: string | null;
  category: string | null;
  ean: string | null;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  image: string | null;
  link: string | null;
  merchant: { name: string; slug: string; domain: string | null; region: string | null };
  history: Hist[];
  price_min: number | null;
  price_max: number | null;
  verdict: VerdictData | null;
  decision: DecisionData | null;
  product: {
    ean: string;
    merchants_count: number;
    price_min: number | null;
    currency: string | null;
  } | null;
};

async function getOffer(id: string): Promise<Offer | null> {
  try {
    const res = await fetch(`${API}/api/catalog/offer/${encodeURIComponent(id)}`, {
      next: { revalidate: 3600 },
      // Un backend qui ne répond pas doit donner un 404 franc, pas une page
      // qui pend jusqu'au timeout de la plateforme.
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) return null;
    return (await res.json()) as Offer;
  } catch {
    return null;
  }
}

function money(price: number | null, currency: string | null): string {
  if (price == null) return "—";
  const sym = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const o = await getOffer(id);
  if (!o) return buildMetadata({ path: `/produit/${id}`, title: "Fiche produit", description: "Produit comparé par FILON." });
  const parts = [o.brand, o.name].filter(Boolean).join(" ");
  const price = o.price != null ? ` — ${money(o.price, o.currency)}` : "";
  return buildMetadata({
    path: `/produit/${id}`,
    title: `${parts}${price}`,
    description: `${parts}${price} chez ${o.merchant.name}. Prix, historique et meilleure offre, comparés par FILON.`,
    image: o.image || undefined,
  });
}

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const o = await getOffer(id);
  if (!o) notFound();

  return (
    <section className="ed-band" style={{ paddingTop: "clamp(90px, 12vw, 130px)" }}>
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
