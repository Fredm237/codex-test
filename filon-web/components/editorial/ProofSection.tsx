"use client";

// Bande de preuves (home).
//
// Tout ce qui est chiffré vient du catalogue réel, lu au rendu de la page
// (voir lib/proof.ts). La version précédente annonçait « 5+ marchands » et
// « chiffres réels à venir » en affichant les logos d'enseignes qui ne sont pas
// nos partenaires : elle sous-vendait un catalogue de 795 000 offres tout en
// promettant ce que nous ne distribuons pas. On ne montre plus que des
// partenaires réellement inscrits, nommés, et un écart de prix constaté.
//
// Sans catalogue joignable, `live` vaut null : on retombe sur une rédaction
// générique et un exemple explicitement marqué comme tel, jamais sur un zéro.

import { useEffect, useRef, useState } from "react";
import { Reveal } from "./Reveal";
import { useLocale } from "@/lib/i18n";
import type { Proof } from "@/lib/proof";

const TRUST: Array<[string, string]> = [
  ["Aucune place ne s'achète", "Aucune marque ni marchand ne peut payer pour un meilleur classement ou un meilleur Verdict. Jamais."],
  ["Gratuit, et de votre côté", "Notre rémunération vient de l'affiliation, sans jamais augmenter votre prix, ni fausser un conseil."],
  ["Vos données restent à vous", "Analytics sans cookies, aucune revente. Ce que vous cherchez ne quitte jamais FILON."],
];

const PL = {
  fr: {
    eye: "FILON compare, en temps réel",
    note: "Marchands partenaires actifs, mis à jour à chaque synchronisation du catalogue.",
    labels: {
      merchants: "marchands partenaires",
      offers: "offres comparées",
      products: "produits distincts",
      multi: "vendus par plusieurs marchands",
      snapshots: "relevés de prix enregistrés",
    },
    updated: "Chiffres relevés dans notre catalogue, pas des estimations.",
    priceEye: "Le vrai prix, décomposé",
    priceH1: "L'étiquette n'est jamais ", priceH2: "le prix réel.",
    priceP: "Le même produit ne coûte pas le même prix partout. FILON regroupe les offres, garde l'historique et vous dit lequel prendre — et si c'est le moment.",
    at: "marchands le vendent",
    highest: "Le plus cher constaté",
    lowest: "Le moins cher constaté",
    gap: "Écart réel sur ce produit",
    see: "Voir la fiche",
    ex: "Exemple illustratif · Lenovo IdeaPad Slim 5",
    exRows: [
      ["Prix affiché sur cette page", "799 €", false],
      ["Meilleur marchand trouvé", "−60 €", true],
      ["Coupon vérifié au paiement", "−15 €", true],
      ["Cashback reversé", "−25 €", true],
    ] as Array<[string, string, boolean]>,
    total: "Vrai prix FILON",
    trust: TRUST,
  },
  nl: {
    eye: "FILON vergelijkt, in realtime",
    note: "Actieve partnerwinkels, bijgewerkt bij elke synchronisatie van de catalogus.",
    labels: {
      merchants: "partnerwinkels",
      offers: "vergeleken aanbiedingen",
      products: "verschillende producten",
      multi: "door meerdere winkels verkocht",
      snapshots: "geregistreerde prijsmetingen",
    },
    updated: "Cijfers uit onze eigen catalogus, geen schattingen.",
    priceEye: "De echte prijs, ontleed",
    priceH1: "Het prijskaartje is nooit ", priceH2: "de echte prijs.",
    priceP: "Hetzelfde product kost niet overal evenveel. FILON bundelt de aanbiedingen, bewaart de geschiedenis en zegt welke je moet nemen — en of het het juiste moment is.",
    at: "winkels verkopen het",
    highest: "Duurst vastgesteld",
    lowest: "Goedkoopst vastgesteld",
    gap: "Werkelijk verschil op dit product",
    see: "Bekijk de fiche",
    ex: "Illustratief voorbeeld · Lenovo IdeaPad Slim 5",
    exRows: [
      ["Getoonde prijs op deze pagina", "799 €", false],
      ["Beste winkel gevonden", "−60 €", true],
      ["Geverifieerde code bij betaling", "−15 €", true],
      ["Uitgekeerde cashback", "−25 €", true],
    ] as Array<[string, string, boolean]>,
    total: "Echte FILON-prijs",
    trust: [
      ["Geen plaats te koop", "Geen enkel merk of winkel kan betalen voor een betere rangschikking of een beter Verdict. Nooit."],
      ["Gratis, en aan jouw kant", "Onze vergoeding komt uit affiliatie, zonder ooit je prijs te verhogen of een advies te vervalsen."],
      ["Je gegevens blijven van jou", "Analytics zonder cookies, geen doorverkoop. Wat je zoekt verlaat FILON nooit."],
    ] as Array<[string, string]>,
  },
  en: {
    eye: "FILON compares, in real time",
    note: "Active partner merchants, refreshed on every catalogue synchronisation.",
    labels: {
      merchants: "partner merchants",
      offers: "offers compared",
      products: "distinct products",
      multi: "sold by several merchants",
      snapshots: "price readings recorded",
    },
    updated: "Figures read from our own catalogue, not estimates.",
    priceEye: "The real price, broken down",
    priceH1: "The tag is never ", priceH2: "the real price.",
    priceP: "The same product does not cost the same everywhere. FILON groups the offers, keeps the history and tells you which one to take — and whether now is the moment.",
    at: "merchants sell it",
    highest: "Highest observed",
    lowest: "Lowest observed",
    gap: "Real spread on this product",
    see: "See the product",
    ex: "Illustrative example · Lenovo IdeaPad Slim 5",
    exRows: [
      ["Price shown on this page", "€799", false],
      ["Best merchant found", "−€60", true],
      ["Coupon verified at checkout", "−€15", true],
      ["Cashback returned", "−€25", true],
    ] as Array<[string, string, boolean]>,
    total: "FILON real price",
    trust: [
      ["No place is for sale", "No brand or merchant can pay for a better ranking or a better Verdict. Ever."],
      ["Free, and on your side", "Our income comes from affiliation, without ever raising your price or skewing a recommendation."],
      ["Your data stays yours", "Cookie-free analytics, no reselling. What you search for never leaves FILON."],
    ] as Array<[string, string]>,
  },
};

const LOCALE_TAG = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

function symbolOf(currency: string): string {
  return currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
}

function money(value: number, currency: string, tag: string): string {
  return `${value.toLocaleString(tag, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${symbolOf(currency)}`;
}

/** Compte à rebours du prix haut vers le prix bas, déclenché à l'entrée dans
 *  le champ de vision. Respecte prefers-reduced-motion : la valeur finale est
 *  alors posée directement, sans animation. */
function PriceCountUp({
  from,
  to,
  currency,
  tag,
}: {
  from: number;
  to: number;
  currency: string;
  tag: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const [value, setValue] = useState(from);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setValue(to);
      return;
    }
    let done = false;
    const run = () => {
      if (done) return;
      done = true;
      const dur = 900;
      const t0 = performance.now();
      const step = (t: number) => {
        const p = Math.min(1, (t - t0) / dur);
        setValue(from + (to - from) * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && (run(), io.disconnect())),
      { threshold: 0.4 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [from, to]);

  return (
    <span ref={ref} className="ed-proof-total-val">
      {money(value, currency, tag)}
    </span>
  );
}

/** Bannière vivante : vidéo d'unboxing en boucle, poster + repli sans animation. */
function LifeBanner() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);
  return (
    <Reveal className="ed-proof-life">
      {reduced ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src="/img/proof-unboxing.webp" alt="" loading="lazy" />
      ) : (
        <video autoPlay muted loop playsInline poster="/img/proof-unboxing.webp" aria-hidden="true">
          <source src="/video/unboxing.mp4" type="video/mp4" />
        </video>
      )}
    </Reveal>
  );
}

export function ProofSection({ live }: { live?: Proof | null }) {
  const { locale } = useLocale();
  const x = PL[locale];
  const tag = LOCALE_TAG[locale];
  const n = (v: number) => v.toLocaleString(tag);

  // Quatre chiffres, tous vérifiables dans le catalogue. Les produits vendus
  // par plusieurs marchands sont mis en avant : c'est la part sur laquelle une
  // comparaison a réellement un sens.
  const stats: Array<[string, string]> = live
    ? [
        [n(live.stats.merchants), x.labels.merchants],
        [n(live.stats.offers), x.labels.offers],
        [n(live.stats.multiMerchant || live.stats.products), live.stats.multiMerchant ? x.labels.multi : x.labels.products],
        [n(live.stats.snapshots), x.labels.snapshots],
      ]
    : [];

  const product = live?.product ?? null;

  return (
    <section className="ed-band ed-proof" id="preuves">
      <div className="ed-wrap">
        <Reveal>
          <span className="eyebrow" style={{ display: "block", textAlign: "center" }}>
            {x.eye}
          </span>
        </Reveal>

        {live && live.merchants.length > 0 && (
          <>
            <Reveal className="ed-proof-marquee">
              <div className="track">
                {[...live.merchants, ...live.merchants].map((name, i) => (
                  <div className="ed-proof-logo is-word" key={`${name}-${i}`}>
                    <span>{name}</span>
                  </div>
                ))}
              </div>
            </Reveal>
            <Reveal>
              <p className="ed-proof-note">{x.note}</p>
            </Reveal>
          </>
        )}

        {live && (
          <>
            <Reveal className="ed-proof-stats">
              {stats.map(([value, label]) => (
                <div key={label}>
                  <div className="ed-proof-stat-v">{value}</div>
                  <div className="ed-proof-stat-l">{label}</div>
                </div>
              ))}
            </Reveal>
            <Reveal>
              <p className="ed-proof-legend">{x.updated}</p>
            </Reveal>
          </>
        )}

        <LifeBanner />

        <div className="ed-proof-price">
          <Reveal className="ed-proof-price-copy">
            <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>
              {x.priceEye}
            </span>
            <h2>
              {x.priceH1}
              <span className="it">{x.priceH2}</span>
            </h2>
            <p>{x.priceP}</p>
          </Reveal>

          {product ? (
            <Reveal className="ed-proof-card">
              <div className="ex">
                {product.brand ? `${product.brand} · ` : ""}
                {product.merchants} {x.at}
              </div>
              <div className="ed-proof-product">
                {product.image && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={product.image} alt="" loading="lazy" />
                )}
                <a className="ed-proof-product-name" href={`/produits/${product.ean}/`}>
                  {product.name}
                </a>
              </div>
              <div className="row">
                <span>{x.highest}</span>
                <span className="v">{money(product.priceMax, product.currency, tag)}</span>
              </div>
              <div className="row">
                <span>{x.gap}</span>
                <span className="v good">
                  −{money(product.priceMax - product.priceMin, product.currency, tag)}
                </span>
              </div>
              <div className="total">
                <span>{x.lowest}</span>
                <PriceCountUp
                  from={product.priceMax}
                  to={product.priceMin}
                  currency={product.currency}
                  tag={tag}
                />
              </div>
              <a className="ed-proof-card-cta" href={`/produits/${product.ean}/`}>
                {x.see}
              </a>
            </Reveal>
          ) : (
            <Reveal className="ed-proof-card">
              <div className="ex">{x.ex}</div>
              {x.exRows.map(([label, value, good]) => (
                <div className="row" key={label}>
                  <span>{label}</span>
                  <span className={good ? "v good" : "v"}>{value}</span>
                </div>
              ))}
              <div className="total">
                <span>{x.total}</span>
                <span className="ed-proof-total-val">699 €</span>
              </div>
            </Reveal>
          )}
        </div>

        <div className="ed-proof-trust">
          {x.trust.map(([title, body]) => (
            <Reveal className="ed-proof-tcard" key={title}>
              <h3>{title}</h3>
              <p>{body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
