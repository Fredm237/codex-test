"use client";

import { useEffect, useRef, useState } from "react";
import { useLocale, type Locale } from "@/lib/i18n";
import { API } from "@/lib/api";

type Offer = {
  id: number;
  name: string;
  brand: string | null;
  category: string | null;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  image: string | null;
  link: string | null;
  merchant: { name: string; slug: string };
};

const L: Record<Locale, {
  search: string; loading: string; error: string; empty: string; see: string; from: string; results: (n: number) => string;
}> = {
  fr: {
    search: "Rechercher un produit…",
    loading: "Chargement…",
    error: "Impossible de charger le catalogue pour le moment.",
    empty: "Aucun produit pour cette recherche.",
    see: "Voir l'offre",
    from: "chez",
    results: (n) => `${n} produit${n > 1 ? "s" : ""}`,
  },
  nl: {
    search: "Zoek een product…",
    loading: "Laden…",
    error: "Kan de catalogus momenteel niet laden.",
    empty: "Geen product voor deze zoekopdracht.",
    see: "Bekijk het aanbod",
    from: "bij",
    results: (n) => `${n} product${n > 1 ? "en" : ""}`,
  },
  en: {
    search: "Search a product…",
    loading: "Loading…",
    error: "Couldn't load the catalogue right now.",
    empty: "No product for this search.",
    see: "See the offer",
    from: "at",
    results: (n) => `${n} product${n > 1 ? "s" : ""}`,
  },
};

function money(price: number | null, currency: string | null): string {
  if (price == null) return "—";
  const sym = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
}

function OfferCard({ o, see, from }: { o: Offer; see: string; from: string }) {
  const [imgOk, setImgOk] = useState(true);
  return (
    <div style={{ display: "flex", flexDirection: "column", background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: 16, overflow: "hidden" }}>
      <a href={`/produit/?id=${o.id}`} style={{ aspectRatio: "4 / 3", background: "#fff", display: "grid", placeItems: "center", overflow: "hidden" }}>
        {o.image && imgOk ? (
          <img src={o.image} alt="" loading="lazy" onError={() => setImgOk(false)} style={{ width: "100%", height: "100%", objectFit: "contain", padding: 12 }} />
        ) : (
          <span aria-hidden="true" style={{ color: "var(--ink-4, var(--ink-3))", fontSize: 12 }}>—</span>
        )}
      </a>
      <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
        {o.brand && <span style={{ fontSize: 11.5, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--ink-3)" }}>{o.brand}</span>}
        <a href={`/produit/?id=${o.id}`} style={{ textDecoration: "none" }}>
          <b style={{ fontSize: 14, color: "var(--ink)", lineHeight: 1.3, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{o.name}</b>
        </a>
        <span style={{ fontSize: 12.5, color: "var(--ink-3)" }}>{from} {o.merchant.name}</span>
        <div style={{ marginTop: "auto", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, paddingTop: 8 }}>
          <b style={{ fontSize: 16, color: "var(--ink)" }}>{money(o.price, o.currency)}</b>
          {o.link && (
            <a className="ed-btn wave" href={o.link} target="_blank" rel="noopener noreferrer sponsored" style={{ fontSize: 12.5, padding: "8px 14px", textDecoration: "none" }}>
              {see}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

export function OffersBrowser() {
  const { locale } = useLocale();
  const t = L[locale];
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Offer[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState(false);
  const reqId = useRef(0);

  useEffect(() => {
    const id = ++reqId.current;
    setError(false);
    const handle = setTimeout(async () => {
      try {
        const url = `${API}/api/catalog/offers?limit=48${q.trim() ? `&q=${encodeURIComponent(q.trim())}` : ""}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        if (reqId.current === id) {
          setItems((data.items || []) as Offer[]);
          setTotal(data.total || 0);
        }
      } catch {
        if (reqId.current === id) setError(true);
      }
    }, q ? 300 : 0);
    return () => clearTimeout(handle);
  }, [q]);

  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center", marginBottom: 24 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t.search}
          aria-label={t.search}
          style={{ flex: "1 1 240px", minWidth: 0, background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: "var(--r-full)", padding: "11px 18px", color: "var(--ink)", fontFamily: "var(--sans)", fontSize: 14.5, outline: "none" }}
        />
        {items !== null && !error && (
          <span style={{ fontSize: 13, color: "var(--ink-3)", fontVariantNumeric: "tabular-nums" }}>{t.results(total)}</span>
        )}
      </div>

      {error ? (
        <p style={{ color: "var(--ink-3)", fontSize: 14.5 }}>{t.error}</p>
      ) : items === null ? (
        <p style={{ color: "var(--ink-3)", fontSize: 14.5 }}>{t.loading}</p>
      ) : items.length === 0 ? (
        <p style={{ color: "var(--ink-3)", fontSize: 14.5 }}>{t.empty}</p>
      ) : (
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
          {items.map((o, i) => (
            <OfferCard key={`${o.merchant.slug}-${i}-${o.name}`} o={o} see={t.see} from={t.from} />
          ))}
        </div>
      )}
    </div>
  );
}
