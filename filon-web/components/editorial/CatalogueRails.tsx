"use client";

import { useLocale, type Locale } from "@/lib/i18n";

export type RailOffer = {
  id: number;
  name: string;
  brand: string | null;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  image: string | null;
  link: string | null;
  merchant: { name: string; slug: string };
  drop_pct?: number;
  price_high?: number | null;
  price_low?: number | null;
  is_lowest?: boolean;
};

export type RailSection = { key: string; items: RailOffer[] };

type Copy = {
  title: string;
  sub: string;
};

const SECTIONS: Record<Locale, Record<string, Copy>> = {
  fr: {
    drops: { title: "Les plus grosses baisses", sub: "Le prix a reculé depuis notre dernier relevé." },
    lowest: { title: "Au plus bas jamais vu", sub: "Jamais relevé moins cher depuis que FILON les suit." },
    budget: { title: "Moins de 100 €", sub: "De quoi se faire plaisir sans y penser." },
    fresh: { title: "Nouveaux au catalogue", sub: "Les derniers produits entrés chez nos marchands." },
  },
  nl: {
    drops: { title: "De grootste dalingen", sub: "De prijs is gezakt sinds onze laatste meting." },
    lowest: { title: "Laagste ooit", sub: "Nooit goedkoper gemeten sinds FILON ze volgt." },
    budget: { title: "Minder dan 100 €", sub: "Iets leuks zonder erover na te denken." },
    fresh: { title: "Nieuw in de catalogus", sub: "De laatste producten bij onze winkels." },
  },
  en: {
    drops: { title: "Biggest price drops", sub: "The price fell since our last reading." },
    lowest: { title: "Lowest ever seen", sub: "Never recorded cheaper since FILON started tracking." },
    budget: { title: "Under €100", sub: "Something nice without thinking twice." },
    fresh: { title: "New in the catalogue", sub: "The latest products from our merchants." },
  },
};

const UI: Record<Locale, {
  see: string; at: string; lowest: string; was: string; all: string; sinceNote: string;
}> = {
  fr: { see: "Voir l'offre", at: "chez", lowest: "Prix le plus bas", was: "avant", all: "Tout voir", sinceNote: "Relevés par FILON, jour après jour." },
  nl: { see: "Bekijk aanbod", at: "bij", lowest: "Laagste prijs", was: "eerder", all: "Alles zien", sinceNote: "Dag na dag gemeten door FILON." },
  en: { see: "See offer", at: "at", lowest: "Lowest price", was: "was", all: "See all", sinceNote: "Recorded by FILON, day after day." },
};

function money(price: number | null | undefined, currency: string | null): string {
  if (price == null) return "—";
  const sym = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
}

function Card({ o, t }: { o: RailOffer; t: (typeof UI)[Locale] }) {
  const drop = o.drop_pct && o.drop_pct >= 1 ? Math.round(o.drop_pct) : null;
  return (
    <article className="cat-card">
      <a className="cat-card-media" href={`/produit/${o.id}/`} aria-label={o.name}>
        {o.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={o.image} alt="" loading="lazy" />
        ) : (
          <span aria-hidden="true">—</span>
        )}
        <span className="cat-badges">
          {drop && <span className="cat-badge drop">−{drop}&nbsp;%</span>}
          {o.is_lowest && <span className="cat-badge low">{t.lowest}</span>}
        </span>
      </a>
      <div className="cat-card-body">
        {o.brand && <span className="cat-card-brand">{o.brand}</span>}
        <a className="cat-card-title" href={`/produit/${o.id}/`}>{o.name}</a>
        <span className="cat-card-merchant">{t.at} {o.merchant.name}</span>
        <div className="cat-card-foot">
          <span className="cat-card-prices">
            <b>{money(o.price, o.currency)}</b>
            {drop && o.price_high != null && (
              <s>{money(o.price_high, o.currency)}</s>
            )}
          </span>
          {o.link && (
            <a
              className="cat-card-cta"
              href={o.link}
              target="_blank"
              rel="noopener noreferrer sponsored"
            >
              {t.see}
            </a>
          )}
        </div>
      </div>
    </article>
  );
}

export function CatalogueRails({ sections }: { sections: RailSection[] }) {
  const { locale } = useLocale();
  const copy = SECTIONS[locale];
  const t = UI[locale];

  if (!sections.length) return null;

  return (
    <div className="cat-rails">
      {sections.map((s) => {
        const c = copy[s.key];
        if (!c) return null;
        return (
          <section className="cat-rail" key={s.key}>
            <header className="cat-rail-head">
              <div>
                <h2 className="cat-rail-title">{c.title}</h2>
                <p className="cat-rail-sub">{c.sub}</p>
              </div>
            </header>
            <div className="cat-rail-scroll">
              {s.items.map((o) => (
                <Card key={`${s.key}-${o.id}`} o={o} t={t} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
