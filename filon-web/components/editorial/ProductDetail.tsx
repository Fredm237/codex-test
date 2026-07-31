"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useLocale, type Locale } from "@/lib/i18n";
import { API } from "@/lib/api";

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

const L: Record<Locale, {
  loading: string; error: string; back: string; see: string; from: string; inStock: string; outStock: string;
  history: string; noHistory: string; lowest: string; highest: string; current: string; disclaimer: string;
}> = {
  fr: {
    loading: "Chargement du produit…",
    error: "Produit introuvable.",
    back: "← Retour au catalogue",
    see: "Voir l'offre chez le marchand",
    from: "chez",
    inStock: "En stock",
    outStock: "Indisponible",
    history: "Historique de prix",
    noHistory: "L'historique se constitue jour après jour. Revenez bientôt.",
    lowest: "Plus bas",
    highest: "Plus haut",
    current: "Actuel",
    disclaimer: "Prix indicatif, susceptible d'évoluer chez le marchand. En achetant via ce lien, FILON peut percevoir une commission, sans surcoût pour vous.",
  },
  nl: {
    loading: "Product laden…",
    error: "Product niet gevonden.",
    back: "← Terug naar de catalogus",
    see: "Bekijk het aanbod bij de winkel",
    from: "bij",
    inStock: "Op voorraad",
    outStock: "Niet beschikbaar",
    history: "Prijsgeschiedenis",
    noHistory: "De geschiedenis bouwt zich dag na dag op. Kom binnenkort terug.",
    lowest: "Laagste",
    highest: "Hoogste",
    current: "Huidig",
    disclaimer: "Indicatieve prijs, kan wijzigen bij de winkel. Door via deze link te kopen kan FILON een commissie ontvangen, zonder meerkost voor jou.",
  },
  en: {
    loading: "Loading product…",
    error: "Product not found.",
    back: "← Back to the catalogue",
    see: "See the offer at the merchant",
    from: "at",
    inStock: "In stock",
    outStock: "Unavailable",
    history: "Price history",
    noHistory: "The history builds up day by day. Come back soon.",
    lowest: "Lowest",
    highest: "Highest",
    current: "Current",
    disclaimer: "Indicative price, may change at the merchant. Buying via this link may earn FILON a commission, at no extra cost to you.",
  },
};

function money(price: number | null, currency: string | null): string {
  if (price == null) return "—";
  const sym = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
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

function Detail({ id }: { id: string }) {
  const { locale } = useLocale();
  const t = L[locale];
  const [offer, setOffer] = useState<Offer | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch(`${API}/api/catalog/offer/${encodeURIComponent(id)}`);
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        if (alive) setOffer(data as Offer);
      } catch {
        if (alive) setError(true);
      }
    })();
    return () => { alive = false; };
  }, [id]);

  if (error) return <p style={{ color: "var(--ink-3)" }}>{t.error} <a href="/catalogue">{t.back}</a></p>;
  if (!offer) return <p style={{ color: "var(--ink-3)" }}>{t.loading}</p>;

  const hasHistory = offer.history.filter((h) => h.price != null).length >= 2;

  return (
    <div>
      <p style={{ marginBottom: 20 }}><a href="/catalogue" style={{ fontSize: 13.5, color: "var(--ink-3)" }}>{t.back}</a></p>
      <div style={{ display: "grid", gap: 32, gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.1fr)", alignItems: "start" }} className="pd-grid">
        <div style={{ aspectRatio: "1 / 1", background: "#fff", borderRadius: 20, border: "1px solid var(--line-2)", display: "grid", placeItems: "center", overflow: "hidden" }}>
          {offer.image ? (
            <img src={offer.image} alt={offer.name} style={{ width: "100%", height: "100%", objectFit: "contain", padding: 22 }} />
          ) : <span aria-hidden="true">—</span>}
        </div>
        <div>
          {offer.brand && <span style={{ fontSize: 12.5, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--ink-3)" }}>{offer.brand}</span>}
          <h1 style={{ fontFamily: "var(--serif)", fontSize: "clamp(24px, 4vw, 34px)", lineHeight: 1.15, margin: "6px 0 14px" }}>{offer.name}</h1>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            <b style={{ fontSize: 30, color: "var(--ink)" }}>{money(offer.price, offer.currency)}</b>
            <span style={{ fontSize: 13, fontWeight: 600, color: offer.in_stock === false ? "var(--ink-3)" : "var(--accent)" }}>
              {offer.in_stock === false ? t.outStock : t.inStock}
            </span>
          </div>
          <p style={{ fontSize: 14, color: "var(--ink-2)", marginTop: 6 }}>{t.from} <b>{offer.merchant.name}</b></p>
          {offer.link && (
            <a className="ed-btn wave" href={offer.link} target="_blank" rel="noopener noreferrer sponsored" style={{ marginTop: 18, textDecoration: "none" }}>
              {t.see}
            </a>
          )}

          <div style={{ marginTop: 30, background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: 16, padding: 18 }}>
            <span style={{ fontSize: 12.5, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--ink-3)" }}>{t.history}</span>
            {hasHistory ? (
              <>
                <div style={{ marginTop: 12 }}><Sparkline hist={offer.history} /></div>
                <div style={{ display: "flex", gap: 22, marginTop: 12, fontSize: 13 }}>
                  <span><span style={{ color: "var(--ink-3)" }}>{t.lowest} </span><b>{money(offer.price_min, offer.currency)}</b></span>
                  <span><span style={{ color: "var(--ink-3)" }}>{t.highest} </span><b>{money(offer.price_max, offer.currency)}</b></span>
                  <span><span style={{ color: "var(--ink-3)" }}>{t.current} </span><b>{money(offer.price, offer.currency)}</b></span>
                </div>
              </>
            ) : (
              <p style={{ fontSize: 13.5, color: "var(--ink-3)", marginTop: 10 }}>{t.noHistory}</p>
            )}
          </div>

          <p style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 16, lineHeight: 1.5 }}>{t.disclaimer}</p>
        </div>
      </div>
      <style>{`@media (max-width: 720px){ .pd-grid{ grid-template-columns: 1fr !important; } }`}</style>
    </div>
  );
}

export function ProductDetail() {
  const params = useSearchParams();
  const { locale } = useLocale();
  const id = params.get("id");
  if (!id) return <p style={{ color: "var(--ink-3)" }}><a href="/catalogue">{L[locale].back}</a></p>;
  return <Detail id={id} />;
}
