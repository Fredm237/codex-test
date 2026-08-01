"use client";

import { useEffect, useMemo, useRef, useState } from "react";
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

type Facet = { value: string; count: number };

const L: Record<Locale, {
  search: string; loading: string; error: string; empty: string; see: string; from: string; results: (n: number) => string;
  category: string; brand: string; allCat: string; allBrand: string; priceMin: string; priceMax: string; sort: string;
  sortRelevance: string; sortPriceAsc: string; sortPriceDesc: string; sortName: string; reset: string;
  prev: string; next: string; page: string; of: string; perPage: string;
  range: (a: number, b: number, n: number) => string;
}> = {
  fr: {
    search: "Rechercher un produit…", loading: "Chargement…", error: "Impossible de charger le catalogue pour le moment.",
    empty: "Aucun produit pour cette recherche.", see: "Voir l'offre", from: "chez",
    results: (n) => `${n.toLocaleString("fr-FR")} produit${n > 1 ? "s" : ""}`,
    category: "Catégorie", brand: "Marque", allCat: "Toutes catégories", allBrand: "Toutes marques",
    priceMin: "Prix min", priceMax: "Prix max", sort: "Trier",
    sortRelevance: "Pertinence", sortPriceAsc: "Prix croissant", sortPriceDesc: "Prix décroissant", sortName: "Nom (A-Z)", reset: "Réinitialiser",
    prev: "Précédent", next: "Suivant", page: "Page", of: "sur", perPage: "par page",
    range: (a, b, n) => `${a.toLocaleString("fr-FR")}–${b.toLocaleString("fr-FR")} sur ${n.toLocaleString("fr-FR")} produits`,
  },
  nl: {
    search: "Zoek een product…", loading: "Laden…", error: "Kan de catalogus momenteel niet laden.",
    empty: "Geen product voor deze zoekopdracht.", see: "Bekijk het aanbod", from: "bij",
    results: (n) => `${n.toLocaleString("nl-BE")} product${n > 1 ? "en" : ""}`,
    category: "Categorie", brand: "Merk", allCat: "Alle categorieën", allBrand: "Alle merken",
    priceMin: "Min. prijs", priceMax: "Max. prijs", sort: "Sorteren",
    sortRelevance: "Relevantie", sortPriceAsc: "Prijs oplopend", sortPriceDesc: "Prijs aflopend", sortName: "Naam (A-Z)", reset: "Resetten",
    prev: "Vorige", next: "Volgende", page: "Pagina", of: "van", perPage: "per pagina",
    range: (a, b, n) => `${a.toLocaleString("nl-BE")}–${b.toLocaleString("nl-BE")} van ${n.toLocaleString("nl-BE")} producten`,
  },
  en: {
    search: "Search a product…", loading: "Loading…", error: "Couldn't load the catalogue right now.",
    empty: "No product for this search.", see: "See the offer", from: "at",
    results: (n) => `${n.toLocaleString("en-GB")} product${n > 1 ? "s" : ""}`,
    category: "Category", brand: "Brand", allCat: "All categories", allBrand: "All brands",
    priceMin: "Min price", priceMax: "Max price", sort: "Sort",
    sortRelevance: "Relevance", sortPriceAsc: "Price low to high", sortPriceDesc: "Price high to low", sortName: "Name (A-Z)", reset: "Reset",
    prev: "Previous", next: "Next", page: "Page", of: "of", perPage: "per page",
    range: (a, b, n) => `${a.toLocaleString("en-GB")}–${b.toLocaleString("en-GB")} of ${n.toLocaleString("en-GB")} products`,
  },
};

function money(price: number | null, currency: string | null): string {
  if (price == null) return "—";
  const sym = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
}

const selectStyle: React.CSSProperties = {
  background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: "var(--r-full)",
  padding: "9px 14px", color: "var(--ink)", fontFamily: "var(--sans)", fontSize: 13.5, outline: "none", cursor: "pointer",
};
const inputStyle: React.CSSProperties = {
  background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: "var(--r-full)",
  padding: "9px 14px", color: "var(--ink)", fontFamily: "var(--sans)", fontSize: 13.5, outline: "none", width: 100,
};

function OfferCard({ o, see, from }: { o: Offer; see: string; from: string }) {
  const [imgOk, setImgOk] = useState(true);
  return (
    <div style={{ display: "flex", flexDirection: "column", background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: 16, overflow: "hidden" }}>
      <a href={`/produit/${o.id}/`} style={{ aspectRatio: "4 / 3", background: "#fff", display: "grid", placeItems: "center", overflow: "hidden" }}>
        {o.image && imgOk ? (
          <img src={o.image} alt="" loading="lazy" onError={() => setImgOk(false)} style={{ width: "100%", height: "100%", objectFit: "contain", padding: 12 }} />
        ) : (
          <span aria-hidden="true" style={{ color: "var(--ink-4, var(--ink-3))", fontSize: 12 }}>—</span>
        )}
      </a>
      <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 6, flex: 1 }}>
        {o.brand && <span style={{ fontSize: 11.5, letterSpacing: "0.04em", textTransform: "uppercase", color: "var(--ink-3)" }}>{o.brand}</span>}
        <a href={`/produit/${o.id}/`} style={{ textDecoration: "none" }}>
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

/** Suite de pages à afficher, avec ellipses : 1 … 4 5 [6] 7 8 … 250. */
function pageWindow(current: number, last: number): (number | "…")[] {
  if (last <= 7) return Array.from({ length: last }, (_, i) => i + 1);
  const out: (number | "…")[] = [1];
  const from = Math.max(2, current - 2);
  const to = Math.min(last - 1, current + 2);
  if (from > 2) out.push("…");
  for (let p = from; p <= to; p++) out.push(p);
  if (to < last - 1) out.push("…");
  out.push(last);
  return out;
}

function Pagination({
  page, lastPage, onGo, t,
}: {
  page: number; lastPage: number; onGo: (p: number) => void;
  t: (typeof L)[Locale];
}) {
  if (lastPage <= 1) return null;
  return (
    <nav className="pgn" aria-label={`${t.page} ${page} ${t.of} ${lastPage}`}>
      <button type="button" className="pgn-step" onClick={() => onGo(page - 1)} disabled={page <= 1}>
        ‹ {t.prev}
      </button>
      <span className="pgn-pages">
        {pageWindow(page, lastPage).map((p, i) =>
          p === "…" ? (
            <span key={`gap-${i}`} className="pgn-gap" aria-hidden="true">…</span>
          ) : (
            <button
              key={p}
              type="button"
              className={`pgn-page${p === page ? " current" : ""}`}
              aria-current={p === page ? "page" : undefined}
              onClick={() => onGo(p)}
            >
              {p}
            </button>
          )
        )}
      </span>
      <button type="button" className="pgn-step" onClick={() => onGo(page + 1)} disabled={page >= lastPage}>
        {t.next} ›
      </button>
    </nav>
  );
}

export function OffersBrowser() {
  const { locale } = useLocale();
  const t = L[locale];
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [brand, setBrand] = useState("");
  const [priceMin, setPriceMin] = useState("");
  const [priceMax, setPriceMax] = useState("");
  const [sort, setSort] = useState("relevance");
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(48);
  const [facets, setFacets] = useState<{ categories: Facet[]; brands: Facet[] }>({ categories: [], brands: [] });
  const [items, setItems] = useState<Offer[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState(false);
  const reqId = useRef(0);
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/api/catalog/facets`);
        if (res.ok) setFacets(await res.json());
      } catch { /* facets are optional */ }
    })();
  }, []);

  useEffect(() => {
    const id = ++reqId.current;
    setError(false);
    const handle = setTimeout(async () => {
      try {
        const p = new URLSearchParams({
          limit: String(perPage),
          offset: String((page - 1) * perPage),
          sort,
        });
        if (q.trim()) p.set("q", q.trim());
        if (category) p.set("category", category);
        if (brand) p.set("brand", brand);
        if (priceMin) p.set("price_min", priceMin);
        if (priceMax) p.set("price_max", priceMax);
        const res = await fetch(`${API}/api/catalog/offers?${p.toString()}`);
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        if (reqId.current === id) { setItems((data.items || []) as Offer[]); setTotal(data.total || 0); }
      } catch {
        if (reqId.current === id) setError(true);
      }
    }, 300);
    return () => clearTimeout(handle);
  }, [q, category, brand, priceMin, priceMax, sort, page, perPage]);

  // Changer un filtre doit ramener à la première page : rester en page 37 d'un
  // résultat qui n'en compte plus que 2 afficherait une grille vide.
  useEffect(() => {
    setPage(1);
  }, [q, category, brand, priceMin, priceMax, sort, perPage]);

  const lastPage = Math.max(1, Math.ceil(total / perPage));
  const firstShown = total === 0 ? 0 : (page - 1) * perPage + 1;
  const lastShown = Math.min(page * perPage, total);

  const goToPage = (p: number) => {
    const next = Math.min(Math.max(1, p), lastPage);
    if (next === page) return;
    setPage(next);
    gridRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const hasFilter = useMemo(() => !!(q || category || brand || priceMin || priceMax || sort !== "relevance"), [q, category, brand, priceMin, priceMax, sort]);

  const reset = () => { setQ(""); setCategory(""); setBrand(""); setPriceMin(""); setPriceMax(""); setSort("relevance"); setPage(1); };

  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center", marginBottom: 16 }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t.search} aria-label={t.search}
          style={{ flex: "1 1 220px", minWidth: 0, background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: "var(--r-full)", padding: "11px 18px", color: "var(--ink)", fontFamily: "var(--sans)", fontSize: 14.5, outline: "none" }} />
        {items !== null && !error && total > 0 && (
          <span style={{ fontSize: 13, color: "var(--ink-3)", fontVariantNumeric: "tabular-nums" }}>
            {t.range(firstShown, lastShown, total)}
          </span>
        )}
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center", marginBottom: 26 }}>
        <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label={t.category} style={selectStyle}>
          <option value="">{t.allCat}</option>
          {facets.categories.map((c) => <option key={c.value} value={c.value}>{c.value} ({c.count})</option>)}
        </select>
        <select value={brand} onChange={(e) => setBrand(e.target.value)} aria-label={t.brand} style={selectStyle}>
          <option value="">{t.allBrand}</option>
          {facets.brands.map((b) => <option key={b.value} value={b.value}>{b.value} ({b.count})</option>)}
        </select>
        <input type="number" inputMode="numeric" min={0} value={priceMin} onChange={(e) => setPriceMin(e.target.value)} placeholder={t.priceMin} aria-label={t.priceMin} style={inputStyle} />
        <input type="number" inputMode="numeric" min={0} value={priceMax} onChange={(e) => setPriceMax(e.target.value)} placeholder={t.priceMax} aria-label={t.priceMax} style={inputStyle} />
        <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label={t.sort} style={selectStyle}>
          <option value="relevance">{t.sortRelevance}</option>
          <option value="price_asc">{t.sortPriceAsc}</option>
          <option value="price_desc">{t.sortPriceDesc}</option>
          <option value="name">{t.sortName}</option>
        </select>
        <select value={perPage} onChange={(e) => setPerPage(Number(e.target.value))} aria-label={t.perPage} style={selectStyle}>
          {[24, 48, 96].map((n) => <option key={n} value={n}>{n} {t.perPage}</option>)}
        </select>
        {hasFilter && (
          <button type="button" onClick={reset} style={{ ...selectStyle, background: "transparent", color: "var(--ink-3)" }}>{t.reset}</button>
        )}
      </div>

      {error ? (
        <p style={{ color: "var(--ink-3)", fontSize: 14.5 }}>{t.error}</p>
      ) : items === null ? (
        <p style={{ color: "var(--ink-3)", fontSize: 14.5 }}>{t.loading}</p>
      ) : items.length === 0 ? (
        <p style={{ color: "var(--ink-3)", fontSize: 14.5 }}>{t.empty}</p>
      ) : (
        <div ref={gridRef}>
          <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
            {items.map((o, i) => (
              <OfferCard key={`${o.merchant.slug}-${i}-${o.id}`} o={o} see={t.see} from={t.from} />
            ))}
          </div>
          <Pagination page={page} lastPage={lastPage} onGo={goToPage} t={t} />
          <p className="pgn-status">{t.page} {page} {t.of} {lastPage.toLocaleString("fr-FR")}</p>
        </div>
      )}
    </div>
  );
}
