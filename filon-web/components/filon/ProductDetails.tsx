"use client";

import { Verdict, type VerdictData } from "@/components/editorial/Verdict";
import { useLocale } from "@/lib/i18n";

type Offer = {
  id: number;
  price: number | null;
  currency: string | null;
  in_stock: boolean | null;
  link: string | null;
  merchant: { name: string; slug: string; region: string | null };
};

type Product = {
  ean: string;
  name: string;
  brand: string | null;
  price_min: number | null;
  price_max: number | null;
  currency: string | null;
  offers_count: number;
  merchants_count: number;
  offers: Offer[];
  verdict: VerdictData | null;
};

const COPY = {
  fr: {
    from: "à partir de", at: "chez", merchant: "marchand", merchants: "marchands",
    save: "Vous économisez", saveTail: "en choisissant le moins cher plutôt que le plus cher.",
    best: "Voir la meilleure offre chez", all: "Toutes les offres", bestPrice: "Meilleur prix",
    stock: "En stock", unavailable: "Indisponible", see: "Voir", note: "Prix indicatifs, susceptibles d’évoluer chez les marchands. Les offres sont regroupées par code-barres", commission: "En achetant via ces liens, FILON peut percevoir une commission, sans surcoût pour vous.",
  },
  nl: {
    from: "vanaf", at: "bij", merchant: "winkel", merchants: "winkels",
    save: "Je bespaart", saveTail: "door de goedkoopste in plaats van de duurste te kiezen.",
    best: "Bekijk de beste aanbieding bij", all: "Alle aanbiedingen", bestPrice: "Beste prijs",
    stock: "Op voorraad", unavailable: "Niet beschikbaar", see: "Bekijk", note: "Prijzen zijn indicatief en kunnen veranderen bij de winkels. Aanbiedingen zijn gegroepeerd per barcode", commission: "Via deze links kan FILON een commissie ontvangen, zonder extra kost voor jou.",
  },
  en: {
    from: "from", at: "at", merchant: "merchant", merchants: "merchants",
    save: "You save", saveTail: "by choosing the lowest-priced offer over the highest.",
    best: "See the best offer at", all: "All offers", bestPrice: "Best price",
    stock: "In stock", unavailable: "Unavailable", see: "View", note: "Prices are indicative and may change at merchants. Offers are grouped by barcode", commission: "FILON may earn a commission through these links, at no additional cost to you.",
  },
} as const;

const LOCALE_TAG = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

function money(price: number | null, currency: string | null, locale: keyof typeof COPY) {
  if (price == null) return "—";
  const sym = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${price.toLocaleString(LOCALE_TAG[locale], { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${sym}`;
}

export function ProductDetails({ p, best, saving }: { p: Product; best: Offer | undefined; saving: number | null }) {
  const { locale } = useLocale();
  const C = COPY[locale];
  const merchantLabel = p.merchants_count === 1 ? C.merchant : C.merchants;

  return (
    <div>
      {p.brand && <span className="pg-brand">{p.brand}</span>}
      <h1 className="pg-title">{p.name}</h1>

      <div className="pg-headline">
        <span>
          <span className="pg-from">{C.from}</span>
          <b className="pg-price">{money(p.price_min, p.currency, locale)}</b>
        </span>
        <span className="pg-count">{C.at} {p.merchants_count} {merchantLabel}</span>
      </div>

      {p.verdict && <Verdict v={p.verdict} />}

      {saving != null && (
        <p className="pg-saving">{C.save} <b>{money(saving, p.currency, locale)}</b> {C.saveTail}</p>
      )}

      {best?.link && (
        <a className="fx-btn primary" href={best.link} target="_blank" rel="noopener noreferrer sponsored" style={{ marginTop: 18 }}>
          {C.best} {best.merchant.name}
        </a>
      )}

      <h2 className="pg-sub">{C.all}</h2>
      <ul className="pg-offers">
        {p.offers.map((offer, index) => (
          <li key={offer.id} className={`pg-offer${index === 0 ? " best" : ""}`}>
            <span className="pg-offer-merchant">
              {offer.merchant.name}
              {offer.merchant.region && <span className="pg-region">{offer.merchant.region}</span>}
              {index === 0 && <span className="pg-badge">{C.bestPrice}</span>}
            </span>
            <span className="pg-offer-right">
              <b>{money(offer.price, offer.currency, locale)}</b>
              <span className="pg-stock">{offer.in_stock === false ? C.unavailable : C.stock}</span>
              {offer.link && <a className="pg-go" href={offer.link} target="_blank" rel="noopener noreferrer sponsored">{C.see}</a>}
            </span>
          </li>
        ))}
      </ul>

      <p className="pg-note">{C.note} (EAN&nbsp;{p.ean}). {C.commission}</p>
    </div>
  );
}
