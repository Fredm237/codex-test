"use client";

// Sections de la home, refonte 2026.
//
// Elles remplacent les scènes WebGL défilantes de l'ancienne home. Mesure à
// l'appui : celle-ci faisait 11 202 px de haut sur un écran de 390 px, dont
// plusieurs milliers de pixels de dégradés sombres sans contenu. Un visiteur
// mobile devait traverser ça pour atteindre la moindre information — et un
// partenaire n'allait jamais jusqu'au bout.
//
// Rien ici n'affirme de chiffre : les preuves chiffrées vivent dans
// Proof, qui les lit dans le catalogue.

import type { Proof } from "@/lib/proof";
import { useLocale } from "@/lib/i18n";

// Les trois temps, désignés par leurs clés : le texte vit au dictionnaire.
const STEP_KEYS = ["1", "2", "3"];

export function Method() {
  const { t } = useLocale();
  return (
    <section className="fx-section" id="methode">
      <div className="fx-container">
        <span className="fx-eyebrow brand">{t("method.eyebrow")}</span>
        <h2 className="fx-h2 fx-section-title">
          {t("method.t1")}
          <br />
          <span className="it">{t("method.t2")}</span>
        </h2>

        <ol className="fx-steps">
          {STEP_KEYS.map((n) => (
            <li className="fx-card padded fx-step" key={n}>
              <span className="fx-step-n">0{n}</span>
              <h3 className="fx-h3">{t(`method.s${n}t`)}</h3>
              <p className="fx-body">{t(`method.s${n}b`)}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function Closing({ proof }: { proof: Proof | null }) {
  const { t, locale } = useLocale();
  const tag = locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-BE";
  const stats = proof?.stats ?? null;
  return (
    <section className="fx-section ink fx-closing">
      <div className="fx-container narrow">
        <span className="fx-eyebrow">{t("closing.eyebrow")}</span>
        <h2 className="fx-h2 fx-closing-title">
          {t("closing.t1")}
          <br />
          <span className="it">{t("closing.t2")}</span>
        </h2>
        <p className="fx-lede fx-closing-lede">
          {stats
            ? `${stats.offers.toLocaleString(tag)} ${t("closing.factsA")} ${stats.merchants.toLocaleString(tag)} ${t("closing.factsB")}`
            : t("closing.fallback")}
        </p>
        <p className="fx-closing-actions">
          <a className="fx-btn on-ink" href="/recherche/">
            {t("cta.try")}
          </a>
          <a className="fx-btn secondary fx-btn-on-ink-ghost" href="/catalogue/">
            {t("hero.explore")}
          </a>
        </p>
      </div>
    </section>
  );
}
