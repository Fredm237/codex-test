"use client";

import { Verdict, type VerdictData } from "@/components/editorial/Verdict";
import { useLocale } from "@/lib/i18n";

type Hist = { price: number | null; at: string | null };
type Offer = {
  id: number;
  name: string;
  brand: string | null;
  ean: string | null;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  link: string | null;
  merchant: { name: string; slug: string; domain: string | null; region: string | null };
  history: Hist[];
  price_min: number | null;
  price_max: number | null;
  verdict: VerdictData | null;
  product: { ean: string; merchants_count: number; price_min: number | null; currency: string | null } | null;
};

const COPY = {
  fr: {
    back: "← Retour au catalogue", stock: "En stock", unavailable: "Indisponible", at: "chez",
    offer: "Voir l’offre chez le marchand", available: "Aussi disponible chez", merchants: "marchands",
    from: "dès", compare: "Comparer toutes les offres de ce produit →", history: "Historique de prix",
    low: "Plus bas", high: "Plus haut", current: "Actuel", accumulating: "L’historique se constitue jour après jour. Revenez bientôt.",
    note: "Prix indicatif, susceptible d’évoluer chez le marchand. En achetant via ce lien, FILON peut percevoir une commission, sans surcoût pour vous.",
  },
  nl: {
    back: "← Terug naar de catalogus", stock: "Op voorraad", unavailable: "Niet beschikbaar", at: "bij",
    offer: "Bekijk de aanbieding bij de winkel", available: "Ook beschikbaar bij", merchants: "winkels",
    from: "vanaf", compare: "Vergelijk alle aanbiedingen voor dit product →", history: "Prijsgeschiedenis",
    low: "Laagste", high: "Hoogste", current: "Huidig", accumulating: "De prijsgeschiedenis groeit dag na dag. Kom binnenkort terug.",
    note: "Prijs is indicatief en kan wijzigen bij de winkel. Via deze link kan FILON een commissie ontvangen, zonder extra kost voor jou.",
  },
  en: {
    back: "← Back to catalogue", stock: "In stock", unavailable: "Unavailable", at: "at",
    offer: "See offer at merchant", available: "Also available at", merchants: "merchants",
    from: "from", compare: "Compare all offers for this product →", history: "Price history",
    low: "Lowest", high: "Highest", current: "Current", accumulating: "Price history is building day by day. Check back soon.",
    note: "Price is indicative and may change at the merchant. FILON may earn a commission through this link, at no additional cost to you.",
  },
} as const;

const TAG = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

function money(price: number | null, currency: string | null, locale: keyof typeof COPY) {
  if (price == null) return "—";
  const sym = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString(TAG[locale], { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
}

function Sparkline({ hist }: { hist: Hist[] }) {
  const values = hist.map((entry) => entry.price).filter((price): price is number => price != null);
  if (values.length < 2) return null;
  const width = 600; const height = 120; const padding = 8;
  const min = Math.min(...values); const max = Math.max(...values); const span = max - min || 1;
  const step = (width - padding * 2) / (values.length - 1);
  const path = values.map((price, index) => `${index === 0 ? "M" : "L"} ${padding + index * step} ${height - padding - ((price - min) / span) * (height - padding * 2)}`).join(" ");
  return <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="120" preserveAspectRatio="none" aria-hidden="true" style={{ display: "block" }}><path d={path} fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" /></svg>;
}

export function OfferBackLink() {
  const { locale } = useLocale();
  return <a href="/catalogue" style={{ fontSize: 13.5, color: "var(--ink-3)" }}>{COPY[locale].back}</a>;
}

export function OfferProductDetails({ offer }: { offer: Offer }) {
  const { locale } = useLocale();
  const C = COPY[locale];
  const hasHistory = offer.history.filter((entry) => entry.price != null).length >= 2;

  return (
    <div>
      {offer.brand && <span style={{ fontSize: 12.5, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--ink-3)" }}>{offer.brand}</span>}
      <h1 style={{ fontFamily: "var(--serif)", fontSize: "clamp(24px, 4vw, 34px)", lineHeight: 1.15, margin: "6px 0 14px" }}>{offer.name}</h1>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        <b style={{ fontSize: 30, color: "var(--ink)" }}>{money(offer.price, offer.currency, locale)}</b>
        <span style={{ fontSize: 13, fontWeight: 600, color: offer.in_stock === false ? "var(--ink-3)" : "var(--accent)" }}>{offer.in_stock === false ? C.unavailable : C.stock}</span>
      </div>
      <p style={{ fontSize: 14, color: "var(--ink-2)", marginTop: 6 }}>{C.at} <b>{offer.merchant.name}</b></p>
      {offer.link && <a className="ed-btn wave" href={offer.link} target="_blank" rel="noopener noreferrer sponsored" style={{ marginTop: 18, textDecoration: "none" }}>{C.offer}</a>}
      {offer.verdict && <Verdict v={offer.verdict} />}
      {offer.product && <a className="pd-compare" href={`/produits/${offer.product.ean}/`}><b>{C.available} {offer.product.merchants_count} {C.merchants}{offer.product.price_min != null && offer.price != null && offer.product.price_min < offer.price ? ` — ${C.from} ${money(offer.product.price_min, offer.product.currency ?? offer.currency, locale)}` : ""}</b><span>{C.compare}</span></a>}
      <div style={{ marginTop: 30, background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: 16, padding: 18 }}>
        <span style={{ fontSize: 12.5, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--ink-3)" }}>{C.history}</span>
        {hasHistory ? <><div style={{ marginTop: 12 }}><Sparkline hist={offer.history} /></div><div style={{ display: "flex", gap: 22, marginTop: 12, fontSize: 13 }}><span><span style={{ color: "var(--ink-3)" }}>{C.low} </span><b>{money(offer.price_min, offer.currency, locale)}</b></span><span><span style={{ color: "var(--ink-3)" }}>{C.high} </span><b>{money(offer.price_max, offer.currency, locale)}</b></span><span><span style={{ color: "var(--ink-3)" }}>{C.current} </span><b>{money(offer.price, offer.currency, locale)}</b></span></div></> : <p style={{ fontSize: 13.5, color: "var(--ink-3)", marginTop: 10 }}>{C.accumulating}</p>}
      </div>
      <p style={{ fontSize: 12, color: "var(--ink-3)", marginTop: 16, lineHeight: 1.5 }}>{C.note}</p>
    </div>
  );
}
