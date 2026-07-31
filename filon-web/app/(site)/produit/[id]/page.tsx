import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { buildMetadata } from "@/lib/seo";
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
};

async function getOffer(id: string): Promise<Offer | null> {
  try {
    const res = await fetch(`${API}/api/catalog/offer/${encodeURIComponent(id)}`, {
      next: { revalidate: 3600 },
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

function Sparkline({ hist }: { hist: Hist[] }) {
  const pts = hist.map((h) => h.price).filter((p): p is number => p != null);
  if (pts.length < 2) return null;
  const w = 600, h = 120, pad = 8;
  const min = Math.min(...pts), max = Math.max(...pts);
  const span = max - min || 1;
  const step = (w - pad * 2) / (pts.length - 1);
  const d = pts
    .map((p, i) => `${i === 0 ? "M" : "L"} ${pad + i * step} ${h - pad - ((p - min) / span) * (h - pad * 2)}`)
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" height="120" preserveAspectRatio="none" aria-hidden="true" style={{ display: "block" }}>
      <path d={d} fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

export default async function ProduitPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const o = await getOffer(id);
  if (!o) notFound();

  const hasHistory = o.history.filter((h) => h.price != null).length >= 2;

  return (
    <section className="ed-band" style={{ paddingTop: "clamp(90px, 12vw, 130px)" }}>
      <div className="ed-wrap">
        <p style={{ marginBottom: 20 }}>
          <a href="/catalogue" style={{ fontSize: 13.5, color: "var(--ink-3)" }}>← Retour au catalogue</a>
        </p>
        <div style={{ display: "grid", gap: 32, gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.1fr)", alignItems: "start" }} className="pd-grid">
          <div style={{ aspectRatio: "1 / 1", background: "#fff", borderRadius: 20, border: "1px solid var(--line-2)", display: "grid", placeItems: "center", overflow: "hidden" }}>
            {o.image ? (
              <img src={o.image} alt={o.name} style={{ width: "100%", height: "100%", objectFit: "contain", padding: 22 }} />
            ) : <span aria-hidden="true">—</span>}
          </div>
          <div>
            {o.brand && <span style={{ fontSize: 12.5, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--ink-3)" }}>{o.brand}</span>}
            <h1 style={{ fontFamily: "var(--serif)", fontSize: "clamp(24px, 4vw, 34px)", lineHeight: 1.15, margin: "6px 0 14px" }}>{o.name}</h1>
            <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
              <b style={{ fontSize: 30, color: "var(--ink)" }}>{money(o.price, o.currency)}</b>
              <span style={{ fontSize: 13, fontWeight: 600, color: o.in_stock === false ? "var(--ink-3)" : "var(--accent)" }}>
                {o.in_stock === false ? "Indisponible" : "En stock"}
              </span>
            </div>
            <p style={{ fontSize: 14, color: "var(--ink-2)", marginTop: 6 }}>chez <b>{o.merchant.name}</b></p>
            {o.link && (
              <a className="ed-btn wave" href={o.link} target="_blank" rel="noopener noreferrer sponsored" style={{ marginTop: 18, textDecoration: "none" }}>
                Voir l&apos;offre chez le marchand
              </a>
            )}

            <div style={{ marginTop: 30, background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: 16, padding: 18 }}>
              <span style={{ fontSize: 12.5, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--ink-3)" }}>Historique de prix</span>
              {hasHistory ? (
                <>
                  <div style={{ marginTop: 12 }}><Sparkline hist={o.history} /></div>
                  <div style={{ display: "flex", gap: 22, marginTop: 12, fontSize: 13 }}>
                    <span><span style={{ color: "var(--ink-3)" }}>Plus bas </span><b>{money(o.price_min, o.currency)}</b></span>
                    <span><span style={{ color: "var(--ink-3)" }}>Plus haut </span><b>{money(o.price_max, o.currency)}</b></span>
                    <span><span style={{ color: "var(--ink-3)" }}>Actuel </span><b>{money(o.price, o.currency)}</b></span>
                  </div>
                </>
              ) : (
                <p style={{ fontSize: 13.5, color: "var(--ink-3)", marginTop: 10 }}>L&apos;historique se constitue jour après jour. Revenez bientôt.</p>
              )}
            </div>

            <p style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 16, lineHeight: 1.5 }}>
              Prix indicatif, susceptible d&apos;évoluer chez le marchand. En achetant via ce lien, FILON peut percevoir une commission, sans surcoût pour vous.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
