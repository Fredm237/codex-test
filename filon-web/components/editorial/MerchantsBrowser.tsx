"use client";

import { useEffect, useMemo, useState } from "react";
import { useLocale, type Locale } from "@/lib/i18n";
import { API } from "@/lib/api";

export type Merchant = {
  mid: number;
  name: string;
  slug: string;
  domain: string | null;
  region: string | null;
  sector: string | null;
  logo: string | null;
};

const L: Record<Locale, {
  search: string; all: string; loading: string; error: string; empty: string;
  count: (n: number) => string; sectors: string;
}> = {
  fr: {
    search: "Rechercher un marchand…",
    all: "Tous",
    loading: "Chargement des marchands…",
    error: "Impossible de charger les marchands pour le moment. Réessayez plus tard.",
    empty: "Aucun marchand pour cette recherche.",
    count: (n) => `${n} marchand${n > 1 ? "s" : ""} partenaire${n > 1 ? "s" : ""}`,
    sectors: "Tous les secteurs",
  },
  nl: {
    search: "Zoek een winkel…",
    all: "Alle",
    loading: "Winkels laden…",
    error: "Kan de winkels momenteel niet laden. Probeer later opnieuw.",
    empty: "Geen winkel voor deze zoekopdracht.",
    count: (n) => `${n} partnerwinkel${n > 1 ? "s" : ""}`,
    sectors: "Alle sectoren",
  },
  en: {
    search: "Search a merchant…",
    all: "All",
    loading: "Loading merchants…",
    error: "Couldn't load the merchants right now. Please try again later.",
    empty: "No merchant for this search.",
    count: (n) => `${n} partner merchant${n > 1 ? "s" : ""}`,
    sectors: "All sectors",
  },
};

const REGION_LABEL: Record<string, string> = {
  BE: "Belgique", FR: "France", NL: "Nederland", LU: "Luxembourg", CH: "Suisse",
};

function Monogram({ name }: { name: string }) {
  const letter = (name.trim()[0] || "?").toUpperCase();
  return (
    <span
      aria-hidden="true"
      style={{
        display: "grid", placeItems: "center", width: 44, height: 44, flex: "0 0 auto",
        borderRadius: 12, background: "var(--paper)", border: "1px solid var(--line-2)",
        fontFamily: "var(--serif)", fontSize: 20, color: "var(--ink-2)",
      }}
    >
      {letter}
    </span>
  );
}

function Card({ m }: { m: Merchant }) {
  const [imgOk, setImgOk] = useState(true);
  return (
    <div
      style={{
        display: "flex", alignItems: "center", gap: 14, padding: 16,
        background: "var(--card)", border: "1px solid var(--line-2)", borderRadius: 16,
      }}
    >
      {m.logo && imgOk ? (
        <img
          src={m.logo} alt="" loading="lazy" onError={() => setImgOk(false)}
          style={{ width: 44, height: 44, objectFit: "contain", borderRadius: 12, flex: "0 0 auto", background: "#fff" }}
        />
      ) : (
        <Monogram name={m.name} />
      )}
      <span style={{ minWidth: 0 }}>
        <b style={{ display: "block", fontSize: 15, color: "var(--ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {m.name}
        </b>
        <span style={{ fontSize: 12.5, color: "var(--ink-3)" }}>
          {[m.sector, m.region ? REGION_LABEL[m.region] || m.region : null].filter(Boolean).join(" · ") || m.domain}
        </span>
      </span>
    </div>
  );
}

export function MerchantsBrowser({ initialItems = null }: { initialItems?: Merchant[] | null }) {
  const { locale } = useLocale();
  const t = L[locale];
  const [items, setItems] = useState<Merchant[] | null>(initialItems);
  const [error, setError] = useState(false);
  const [q, setQ] = useState("");
  const [region, setRegion] = useState<string>("");

  useEffect(() => {
    // Les données SSR sont déjà disponibles lors des navigations normales.
    // Le client ne contacte Railway qu’en repli si ce préchargement a échoué.
    if (initialItems !== null) return;

    let alive = true;
    (async () => {
      try {
        const res = await fetch(`${API}/api/catalog/merchants?limit=500`);
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        if (alive) setItems((data.items || []) as Merchant[]);
      } catch {
        if (alive) setError(true);
      }
    })();
    return () => { alive = false; };
  }, [initialItems]);

  const regions = useMemo(() => {
    const set = new Set<string>();
    (items || []).forEach((m) => m.region && set.add(m.region));
    return Array.from(set).sort();
  }, [items]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (items || []).filter(
      (m) =>
        (!region || m.region === region) &&
        (!needle || m.name.toLowerCase().includes(needle) || (m.sector || "").toLowerCase().includes(needle))
    );
  }, [items, q, region]);

  if (error) {
    return <p style={{ color: "var(--ink-3)", fontSize: 14.5 }}>{t.error}</p>;
  }
  if (items === null) {
    return (
      <div className="merchant-skeleton" role="status" aria-live="polite">
        <span className="merchant-skeleton__sr">{t.loading}</span>
        <div className="merchant-skeleton__toolbar"><i /><i /></div>
        <div className="merchant-skeleton__filters"><i /><i /><i /><i /></div>
        <div className="merchant-skeleton__grid" aria-hidden="true">
          {Array.from({ length: 8 }, (_, index) => <i key={index} />)}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center", marginBottom: 22 }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t.search}
          aria-label={t.search}
          style={{
            flex: "1 1 240px", minWidth: 0, background: "var(--card)", border: "1px solid var(--line-2)",
            borderRadius: "var(--r-full)", padding: "11px 18px", color: "var(--ink)",
            fontFamily: "var(--sans)", fontSize: 14.5, outline: "none",
          }}
        />
        <span style={{ fontSize: 13, color: "var(--ink-3)", fontVariantNumeric: "tabular-nums" }}>
          {t.count(filtered.length)}
        </span>
      </div>

      {regions.length > 1 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 24 }}>
          {["", ...regions].map((r) => (
            <button
              key={r || "all"}
              className="fx-region-chip"
              type="button"
              onClick={() => setRegion(r)}
              aria-pressed={region === r}
              style={{
                cursor: "pointer", padding: "7px 14px", borderRadius: "var(--fx-radius-caption)", fontSize: 13, fontWeight: 600,
                border: "1px solid " + (region === r ? "var(--accent)" : "var(--line-2)"),
                background: region === r ? "var(--accent)" : "transparent",
                // Sur l'ambre, le texte est sombre : du blanc n'y tient pas le
                // contraste. C'est la règle du système, pas une préférence.
                color: region === r ? "var(--fx-ink-1000)" : "var(--ink-2)",
              }}
            >
              {r ? REGION_LABEL[r] || r : t.all}
            </button>
          ))}
        </div>
      )}

      {filtered.length === 0 ? (
        <p style={{ color: "var(--ink-3)", fontSize: 14.5 }}>{t.empty}</p>
      ) : (
        <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
          {filtered.map((m) => (
            <Card key={m.mid} m={m} />
          ))}
        </div>
      )}
    </div>
  );
}
