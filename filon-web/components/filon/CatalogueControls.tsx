"use client";

// Recherche et réglages du catalogue.
//
// Tout passe par l'URL, pas par un état React : une sélection se partage, se
// met en favori, et le bouton Précédent revient au résultat attendu. Les
// formulaires fonctionnent d'ailleurs sans JavaScript — ce sont de vrais
// formulaires GET, et les champs cachés reconduisent les filtres en cours.

import { href, SORTS, PER_PAGE, type CatalogueQuery } from "@/lib/catalogue";
import { useLocale } from "@/lib/i18n";

/** Reconduit les filtres non modifiés par ce formulaire. */
function Hidden({ query, except }: { query: CatalogueQuery; except: string[] }) {
  return (
    <>
      {Object.entries(query)
        .filter(([k, v]) => v && !except.includes(k) && (k !== "sort" || SORTS.some((sort) => sort.value === v)))
        .map(([k, v]) => (
          <input type="hidden" name={k} value={String(v)} key={k} />
        ))}
    </>
  );
}

export function CatalogueSearch({ query }: { query: CatalogueQuery }) {
  const { t } = useLocale();
  return (
    <form className="fx-catalogue-search" action="/catalogue/" method="get" role="search">
      {/* La page repart à 1 : rester en page 7 après une nouvelle recherche
          affichait une page vide. */}
      <Hidden query={query} except={["q", "page", "min", "max"]} />
      <div className="fx-field">
        <svg viewBox="0 0 24 24" aria-hidden="true" width="19" height="19" className="fx-field-icon">
          <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="1.8" />
          <path d="m21 21-4.2-4.2" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        <input
          type="search"
          name="q"
          defaultValue={query.q || ""}
          placeholder={t("cat.search")}
          aria-label={t("cat.search")}
          autoComplete="off"
        />
        <button className="fx-btn primary" type="submit">
          {t("cat.searchBtn")}
        </button>
      </div>
    </form>
  );
}

export function CatalogueControls({
  query,
  sort,
  per,
}: {
  query: CatalogueQuery;
  sort: string;
  per: number;
}) {
  const { t } = useLocale();
  const active: Array<[string, string, string]> = [];
  if (query.q) active.push(["q", `« ${query.q} »`, href(query, { q: undefined })]);
  if (query.brand) active.push(["brand", query.brand, href(query, { brand: undefined })]);

  return (
    <div className="fx-catalogue-controls">
      {active.length > 0 && (
        <div className="fx-active-filters">
          {active.map(([key, label, to]) => (
            <a className="fx-filter-pill" key={key} href={to}>
              {label}
              <span aria-hidden="true">×</span>
              <span className="fx-sr">{t("cat.remove")}</span>
            </a>
          ))}
        </div>
      )}

      {/* Repliés sur mobile : déployés, prix, tri et pagination repoussaient
          le premier produit à 807 px du haut — soit un écran entier de
          réglages avant le moindre article. Sur bureau le CSS les rouvre. */}
      <details className="fx-controls-shell">
        <summary className="fx-controls-toggle">
          <span>{t("cat.filters")}</span>
          <svg viewBox="0 0 16 16" aria-hidden="true" width="14" height="14">
            <path d="m4 6 4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.7"
              strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </summary>
        <form className="fx-catalogue-form" action="/catalogue/" method="get">
        <Hidden query={query} except={["min", "max", "sort", "per", "page"]} />
        <label className="fx-inline-field">
          <span>{t("cat.sort")}</span>
          <select name="sort" defaultValue={sort}>
            {SORTS.map((s) => (
              <option value={s.value} key={s.value}>
                {t(s.labelKey)}
              </option>
            ))}
          </select>
        </label>
        <label className="fx-inline-field">
          <span>{t("cat.per")}</span>
          <select name="per" defaultValue={String(per)}>
            {PER_PAGE.map((n) => (
              <option value={n} key={n}>
                {n}
              </option>
            ))}
          </select>
        </label>

          <button className="fx-btn secondary" type="submit">
            {t("cat.apply")}
          </button>
        </form>
      </details>
    </div>
  );
}
