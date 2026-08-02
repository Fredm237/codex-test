"use client";

import { useLocale, type Locale } from "@/lib/i18n";
import { ProductCard, CARD_COPY } from "@/components/filon/ProductCard";

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

export function CatalogueRails({ sections }: { sections: RailSection[] }) {
  const { locale } = useLocale();
  const copy = SECTIONS[locale];
  const card = CARD_COPY[locale];

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
                <ProductCard key={`${s.key}-${o.id}`} offer={o} copy={card} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
