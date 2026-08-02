"use client";

// Hero de la refonte 2026.
//
// Deux partis pris, tous deux issus des motifs de refus reçus d'Awin.
//
// 1. Le mot « cashback » n'y figure pas. Les refus « l'annonceur ne travaille
//    pas avec ce type d'éditeurs » et « pas en affinité avec la marque »
//    visent une catégorie d'éditeur — celle des sites de bons de réduction.
//    FILON se présente donc par ce qu'il fait réellement : réunir les offres,
//    conserver l'historique, et trancher.
// 2. Le visuel n'est pas une abstraction mais une fiche du catalogue, avec un
//    produit réel et son écart de prix constaté. Montrer le produit convainc
//    un partenaire ; une animation ne le convainc pas.
//
// Sans catalogue joignable, la colonne de droite disparaît et la mise en page
// se recentre : jamais de carte vide, jamais de chiffre inventé.

import type { Proof } from "@/lib/proof";
import { useLocale } from "@/lib/i18n";
import { HeroSearch } from "./HeroSearch";

function money(value: number, currency: string): string {
  const symbol = currency === "GBP" ? "£" : currency === "USD" ? "$" : "€";
  return `${value.toLocaleString("fr-BE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ${symbol}`;
}

export function Hero({ proof }: { proof: Proof | null }) {
  const { t, locale } = useLocale();
  const tag = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  const product = proof?.product ?? null;
  const stats = proof?.stats ?? null;

  return (
    <section className={`fx-hero${product ? "" : " solo"}`}>
      <div className="fx-container fx-hero-grid">
        <div className="fx-hero-copy">
          <span className="fx-eyebrow brand">{t("hero.eyebrowNew")}</span>

          <h1 className="fx-display xl fx-hero-title">
            {t("hero.l1")}
            <br />
            {t("hero.l2")}
            <br />
            <span className="it">{t("hero.l3")}</span>
          </h1>

          <p className="fx-lede fx-hero-lede">
            {t("hero.ledeA")} {stats ? stats.merchants.toLocaleString(tag) : t("hero.ledeOur")}{" "}
            {t("hero.ledeB")}
          </p>

          <HeroSearch />

          {/* Lien et non bouton : à côté des suggestions, un second bouton
              plein se lisait comme une puce de plus. */}
          <p className="fx-hero-actions">
            <a className="fx-hero-secondary" href="/catalogue/">
              {t("hero.explore")}
              <svg viewBox="0 0 16 16" aria-hidden="true" width="14" height="14">
                <path
                  d="M3 8h9M8.5 4.5 12 8l-3.5 3.5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </a>
          </p>

          {stats && (
            <p className="fx-hero-facts">
              <span>{stats.offers.toLocaleString(tag)} {t("hero.offersTracked")}</span>
              <span aria-hidden="true">·</span>
              <span>{stats.multiMerchant.toLocaleString(tag)} {t("hero.multiMerchant")}</span>
              <span aria-hidden="true">·</span>
              <span>{stats.snapshots.toLocaleString(tag)} {t("hero.snapshots")}</span>
            </p>
          )}
        </div>

        {product && (
          <aside className="fx-hero-panel" aria-label="Exemple de produit suivi">
            <article className="fx-card fx-verdict-card">
              <header className="fx-verdict-head">
                <span className="fx-badge brand">{t("hero.tracked")}</span>
                <span className="fx-fine">{product.merchants} {t("hero.sellIt")}</span>
              </header>

              <div className="fx-verdict-product">
                {product.image && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={product.image} alt="" loading="lazy" width={72} height={72} />
                )}
                <div>
                  {product.brand && <span className="fx-eyebrow">{product.brand}</span>}
                  <a className="fx-verdict-name" href={`/produits/${product.ean}/`}>
                    {product.name}
                  </a>
                </div>
              </div>

              <dl className="fx-verdict-rows">
                <div>
                  <dt>{t("hero.highest")}</dt>
                  <dd className="strike">{money(product.priceMax, product.currency)}</dd>
                </div>
                <div>
                  <dt>{t("hero.lowest")}</dt>
                  <dd className="lead">{money(product.priceMin, product.currency)}</dd>
                </div>
              </dl>

              <footer className="fx-verdict-foot">
                <span className="fx-badge gain">
                  −{money(product.priceMax - product.priceMin, product.currency)} {t("hero.gap")}
                </span>
                <a className="fx-verdict-link" href={`/produits/${product.ean}/`}>
                  {t("hero.dossier")}
                  <svg viewBox="0 0 16 16" aria-hidden="true" width="14" height="14">
                    <path
                      d="M3 8h9M8.5 4.5 12 8l-3.5 3.5"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </a>
              </footer>
            </article>

            <p className="fx-hero-panel-note">
              {t("hero.realData")}
            </p>
          </aside>
        )}
      </div>
    </section>
  );
}
