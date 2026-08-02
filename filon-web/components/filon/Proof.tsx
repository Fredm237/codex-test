"use client";

// Bande de preuves, refonte 2026.
//
// Tout ce qui est chiffré vient du catalogue réel, lu au rendu de la page
// (lib/proof.ts). L'ancienne version annonçait « 5+ marchands » et « chiffres
// réels à venir » sous les logos d'enseignes qui ne sont pas nos partenaires :
// elle sous-vendait un catalogue de 795 000 offres tout en promettant ce que
// nous ne distribuons pas.
//
// La vidéo d'unboxing décorative est retirée. Elle pesait 500 Ko, n'apportait
// aucune information, et occupait à elle seule une part notable des 1 973 px
// que cette section faisait sur mobile. « Trust & Authority » se démontre par
// des faits vérifiables, pas par une image d'ambiance.
//
// Sans catalogue joignable, `live` vaut null : la section se réduit aux faits
// de transparence, qui restent vrais. Jamais de zéro affiché.

import { useLocale } from "@/lib/i18n";
import type { Proof } from "@/lib/proof";

const COPY = {
  fr: {
    eyebrow: "Ce que contient le catalogue",
    title: "Des chiffres qu'on peut",
    titleIt: "aller vérifier.",
    note: "Marchands partenaires actifs, relus à chaque synchronisation du catalogue.",
    labels: {
      merchants: "marchands partenaires",
      offers: "offres suivies",
      multi: "produits vendus par plusieurs marchands",
      snapshots: "relevés de prix conservés",
    },
    spreadEyebrow: "Un écart réel",
    spreadTitle: "Le même article,",
    spreadTitleIt: "deux prix.",
    spreadBody:
      "Ce produit est vendu par plusieurs de nos marchands. Voici ce que nous avons relevé, sans arrondi et sans exemple inventé.",
    merchants: "marchands le vendent",
    highest: "Le plus cher constaté",
    lowest: "Le moins cher constaté",
    gap: "Écart",
    see: "Voir le dossier",
    trust: [
      ["Aucune place ne s'achète", "Aucune marque ni marchand ne peut payer pour un meilleur classement ou un meilleur Verdict. Jamais."],
      ["Gratuit, et de votre côté", "Notre rémunération vient de l'affiliation, sans jamais augmenter votre prix ni fausser un conseil."],
      ["Vos données restent à vous", "Analytics sans cookies, aucune revente. Ce que vous cherchez ne quitte jamais FILON."],
    ] as Array<[string, string]>,
  },
  nl: {
    eyebrow: "Wat de catalogus bevat",
    title: "Cijfers die je",
    titleIt: "kunt nagaan.",
    note: "Actieve partnerwinkels, herlezen bij elke synchronisatie van de catalogus.",
    labels: {
      merchants: "partnerwinkels",
      offers: "gevolgde aanbiedingen",
      multi: "producten bij meerdere winkels",
      snapshots: "bewaarde prijsmetingen",
    },
    spreadEyebrow: "Een echt verschil",
    spreadTitle: "Hetzelfde artikel,",
    spreadTitleIt: "twee prijzen.",
    spreadBody:
      "Dit product wordt door meerdere van onze winkels verkocht. Dit is wat we hebben gemeten, zonder afronding en zonder verzonnen voorbeeld.",
    merchants: "winkels verkopen het",
    highest: "Duurst vastgesteld",
    lowest: "Goedkoopst vastgesteld",
    gap: "Verschil",
    see: "Bekijk de fiche",
    trust: [
      ["Geen plaats te koop", "Geen enkel merk of winkel kan betalen voor een betere rangschikking of een beter Verdict. Nooit."],
      ["Gratis, en aan jouw kant", "Onze vergoeding komt uit affiliatie, zonder ooit je prijs te verhogen of een advies te vervalsen."],
      ["Je gegevens blijven van jou", "Analytics zonder cookies, geen doorverkoop. Wat je zoekt verlaat FILON nooit."],
    ] as Array<[string, string]>,
  },
  en: {
    eyebrow: "What the catalogue holds",
    title: "Figures you can",
    titleIt: "go and check.",
    note: "Active partner merchants, re-read on every catalogue synchronisation.",
    labels: {
      merchants: "partner merchants",
      offers: "offers tracked",
      multi: "products sold by several merchants",
      snapshots: "price readings kept",
    },
    spreadEyebrow: "A real spread",
    spreadTitle: "The same item,",
    spreadTitleIt: "two prices.",
    spreadBody:
      "This product is sold by several of our merchants. Here is what we recorded — no rounding, no invented example.",
    merchants: "merchants sell it",
    highest: "Highest observed",
    lowest: "Lowest observed",
    gap: "Spread",
    see: "See the product",
    trust: [
      ["No place is for sale", "No brand or merchant can pay for a better ranking or a better Verdict. Ever."],
      ["Free, and on your side", "Our income comes from affiliation, without ever raising your price or skewing a recommendation."],
      ["Your data stays yours", "Cookie-free analytics, no reselling. What you search for never leaves FILON."],
    ] as Array<[string, string]>,
  },
};

const TAG = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

function money(value: number, currency: string, tag: string): string {
  const symbol = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${value.toLocaleString(tag, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${symbol}`;
}

export function Proof({ live }: { live: Proof | null }) {
  const { locale } = useLocale();
  const x = COPY[locale];
  const tag = TAG[locale];
  const n = (v: number) => v.toLocaleString(tag);
  const product = live?.product ?? null;

  return (
    <section className="fx-section sunken" id="preuves">
      <div className="fx-container">
        {live && (
          <>
            <span className="fx-eyebrow brand">{x.eyebrow}</span>
            <h2 className="fx-h2 fx-section-title">
              {x.title}
              <br />
              <span className="it">{x.titleIt}</span>
            </h2>

            <div className="fx-grid cols-4 fx-proof-stats">
              {(
                [
                  [n(live.stats.merchants), x.labels.merchants],
                  [n(live.stats.offers), x.labels.offers],
                  [n(live.stats.multiMerchant), x.labels.multi],
                  [n(live.stats.snapshots), x.labels.snapshots],
                ] as Array<[string, string]>
              ).map(([value, label]) => (
                <div className="fx-card padded" key={label}>
                  <div className="fx-stat-value">{value}</div>
                  <div className="fx-stat-label">{label}</div>
                </div>
              ))}
            </div>

            {live.merchants.length > 0 && (
              <>
                <ul className="fx-proof-merchants">
                  {live.merchants.map((name) => (
                    <li key={name}>{name}</li>
                  ))}
                </ul>
                <p className="fx-fine fx-proof-note">{x.note}</p>
              </>
            )}
          </>
        )}

        {product && (
          <div className="fx-proof-spread">
            <div>
              <span className="fx-eyebrow brand">{x.spreadEyebrow}</span>
              <h3 className="fx-h2 fx-section-title">
                {x.spreadTitle}
                <br />
                <span className="it">{x.spreadTitleIt}</span>
              </h3>
              <p className="fx-body fx-proof-spread-body">{x.spreadBody}</p>
            </div>

            <article className="fx-card fx-verdict-card">
              <header className="fx-verdict-head">
                <span className="fx-badge brand">{product.brand || "Catalogue"}</span>
                <span className="fx-fine">
                  {product.merchants} {x.merchants}
                </span>
              </header>

              <div className="fx-verdict-product">
                {product.image && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={product.image} alt="" loading="lazy" width={72} height={72} />
                )}
                <div>
                  <a className="fx-verdict-name" href={`/produits/${product.ean}/`}>
                    {product.name}
                  </a>
                </div>
              </div>

              <dl className="fx-verdict-rows">
                <div>
                  <dt>{x.highest}</dt>
                  <dd className="strike">{money(product.priceMax, product.currency, tag)}</dd>
                </div>
                <div>
                  <dt>{x.lowest}</dt>
                  <dd className="lead">{money(product.priceMin, product.currency, tag)}</dd>
                </div>
              </dl>

              <footer className="fx-verdict-foot">
                <span className="fx-badge gain">
                  {x.gap} −{money(product.priceMax - product.priceMin, product.currency, tag)}
                </span>
                <a className="fx-verdict-link" href={`/produits/${product.ean}/`}>
                  {x.see}
                  <svg viewBox="0 0 16 16" aria-hidden="true" width="14" height="14">
                    <path d="M3 8h9M8.5 4.5 12 8l-3.5 3.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </a>
              </footer>
            </article>
          </div>
        )}

        <div className="fx-grid cols-3 fx-proof-trust">
          {x.trust.map(([title, body]) => (
            <div className="fx-card padded" key={title}>
              <h3 className="fx-h3">{title}</h3>
              <p className="fx-body fx-proof-trust-body">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
