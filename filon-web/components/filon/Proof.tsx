"use client";

// Bande de preuves, refonte 2026.
//
// Tout ce qui est chiffré vient du catalogue réel, lu au rendu de la page
// (lib/proof.ts). L'ancienne version annonçait « 5+ marchands » et « chiffres
// réels à venir » sous des logos qui ne prouvaient ni la source ni le
// périmètre. La version actuelle n'affiche que les agrégats renvoyés par le
// catalogue au moment du rendu.
//
// La vidéo d'unboxing décorative est retirée. Elle pesait 500 Ko, n'apportait
// aucune information, et occupait à elle seule une part notable des 1 973 px
// que cette section faisait sur mobile. « Trust & Authority » se démontre par
// des faits vérifiables, pas par une image d'ambiance.
//
// Sans catalogue joignable, `live` vaut null : la section se réduit aux faits
// de transparence, qui restent vrais. Jamais de zéro affiché.

import { motion } from "framer-motion";
import { useLocale } from "@/lib/i18n";
import type { Proof } from "@/lib/proof";
import { money } from "./product-copy";

const COPY = {
  fr: {
    eyebrow: "Ce que contient le catalogue",
    title: "Des chiffres qu'on peut",
    titleIt: "aller vérifier.",
    note: "Sources marchandes indexées dans l'état courant du catalogue.",
    labels: {
      merchants: "sources marchandes indexées",
      offers: "offres indexées",
      multi: "produits vendus par plusieurs marchands",
      snapshots: "relevés de prix conservés",
    },
    spreadEyebrow: "Un écart réel",
    spreadTitle: "Le même article,",
    spreadTitleIt: "deux prix.",
    spreadBody:
      "Ces offres partagent l'identifiant produit affiché. Voici les valeurs renvoyées par le catalogue, sans exemple inventé.",
    merchants: "marchands le vendent",
    highest: "Le plus cher constaté",
    lowest: "Le moins cher constaté",
    gap: "Écart",
    see: "Voir le dossier",
    trust: [
      ["Commission hors score actuel", "Le taux de commission n'est pas un champ du calcul de score actuellement déployé."],
      ["Affiliation signalée", "Certains liens peuvent générer une commission ; confirmez le total chez le marchand."],
      ["Confidentialité documentée", "La politique de confidentialité décrit les données traitées et vos droits."],
    ] as Array<[string, string]>,
  },
  nl: {
    eyebrow: "Wat de catalogus bevat",
    title: "Cijfers die je",
    titleIt: "kunt nagaan.",
    note: "Winkelbronnen die in de huidige catalogus zijn geïndexeerd.",
    labels: {
      merchants: "geïndexeerde winkelbronnen",
      offers: "geïndexeerde aanbiedingen",
      multi: "producten bij meerdere winkels",
      snapshots: "bewaarde prijsmetingen",
    },
    spreadEyebrow: "Een echt verschil",
    spreadTitle: "Hetzelfde artikel,",
    spreadTitleIt: "twee prijzen.",
    spreadBody:
      "Deze aanbiedingen delen de getoonde productidentificatie. Dit zijn de cataloguswaarden, zonder verzonnen voorbeeld.",
    merchants: "winkels verkopen het",
    highest: "Duurst vastgesteld",
    lowest: "Goedkoopst vastgesteld",
    gap: "Verschil",
    see: "Bekijk de fiche",
    trust: [
      ["Commissie buiten huidige score", "Het commissietarief is geen invoerveld van de momenteel geïmplementeerde score."],
      ["Affiliatie vermeld", "Sommige links kunnen een commissie opleveren; bevestig het totaal bij de winkel."],
      ["Privacy gedocumenteerd", "Het privacybeleid beschrijft verwerkte gegevens en je rechten."],
    ] as Array<[string, string]>,
  },
  en: {
    eyebrow: "What the catalogue holds",
    title: "Figures you can",
    titleIt: "go and check.",
    note: "Merchant sources indexed in the current catalogue state.",
    labels: {
      merchants: "indexed merchant sources",
      offers: "indexed offers",
      multi: "products sold by several merchants",
      snapshots: "price readings kept",
    },
    spreadEyebrow: "A real spread",
    spreadTitle: "The same item,",
    spreadTitleIt: "two prices.",
    spreadBody:
      "These offers share the displayed product identifier. These are catalogue values, with no invented example.",
    merchants: "merchants sell it",
    highest: "Highest observed",
    lowest: "Lowest observed",
    gap: "Spread",
    see: "See the product",
    trust: [
      ["Commission outside current score", "The commission rate is not an input field in the currently implemented score."],
      ["Affiliation disclosed", "Some links may generate a commission; confirm the total with the merchant."],
      ["Privacy documented", "The privacy policy describes processed data and your rights."],
    ] as Array<[string, string]>,
  },
};

const TAG = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

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

            <motion.div 
              className="fx-grid cols-4 fx-proof-stats"
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-100px" }}
              variants={{
                hidden: { opacity: 0 },
                show: {
                  opacity: 1,
                  transition: { staggerChildren: 0.1 }
                }
              }}
            >
              {(
                [
                  [n(live.stats.merchants), x.labels.merchants],
                  [n(live.stats.offers), x.labels.offers],
                  [n(live.stats.multiMerchant), x.labels.multi],
                  [n(live.stats.snapshots), x.labels.snapshots],
                ] as Array<[string, string]>
              ).map(([value, label]) => (
                <motion.div 
                  className="fx-card padded" 
                  key={label}
                  variants={{
                    hidden: { opacity: 0, y: 20 },
                    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 260, damping: 20 } }
                  }}
                >
                  <div className="fx-stat-value">{value}</div>
                  <div className="fx-stat-label">{label}</div>
                </motion.div>
              ))}
            </motion.div>

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
                  <dd className="strike">{money(product.priceMax, product.currency, locale)}</dd>
                </div>
                <div>
                  <dt>{x.lowest}</dt>
                  <dd className="lead">{money(product.priceMin, product.currency, locale)}</dd>
                </div>
              </dl>

              <footer className="fx-verdict-foot">
                <span className="fx-badge gain">
                  {x.gap} −{money(product.priceMax - product.priceMin, product.currency, locale)}
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

        <motion.div 
          className="fx-grid cols-3 fx-proof-trust"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
          variants={{
            hidden: { opacity: 0 },
            show: {
              opacity: 1,
              transition: { staggerChildren: 0.15 }
            }
          }}
        >
          {x.trust.map(([title, body]) => (
            <motion.div 
              className="fx-card padded" 
              key={title}
              variants={{
                hidden: { opacity: 0, y: 20 },
                show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 260, damping: 20 } }
              }}
            >
              <h3 className="fx-h3">{title}</h3>
              <p className="fx-body fx-proof-trust-body">{body}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
