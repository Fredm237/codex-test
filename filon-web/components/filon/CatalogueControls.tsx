"use client";

// Recherche et réglages du catalogue.
//
// Tout passe par l'URL, pas par un état React : une sélection se partage, se
// met en favori, et le bouton Précédent revient au résultat attendu. Les
// formulaires fonctionnent d'ailleurs sans JavaScript — ce sont de vrais
// formulaires GET, et les champs cachés reconduisent les filtres en cours.

import { href, SORTS, PER_PAGE, type CatalogueQuery } from "@/lib/catalogue";

/** Reconduit les filtres non modifiés par ce formulaire. */
function Hidden({ query, except }: { query: CatalogueQuery; except: string[] }) {
  return (
    <>
      {Object.entries(query)
        .filter(([k, v]) => v && !except.includes(k))
        .map(([k, v]) => (
          <input type="hidden" name={k} value={String(v)} key={k} />
        ))}
    </>
  );
}

export function CatalogueSearch({ query }: { query: CatalogueQuery }) {
  return (
    <form className="fx-catalogue-search" action="/catalogue/" method="get" role="search">
      {/* La page repart à 1 : rester en page 7 après une nouvelle recherche
          affichait une page vide. */}
      <Hidden query={query} except={["q", "page"]} />
      <div className="fx-field">
        <svg viewBox="0 0 24 24" aria-hidden="true" width="19" height="19" className="fx-field-icon">
          <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="1.8" />
          <path d="m21 21-4.2-4.2" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        <input
          type="search"
          name="q"
          defaultValue={query.q || ""}
          placeholder="Rechercher dans le catalogue"
          aria-label="Rechercher dans le catalogue"
          autoComplete="off"
        />
        <button className="fx-btn primary" type="submit">
          Chercher
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
  const active: Array<[string, string, string]> = [];
  if (query.q) active.push(["q", `« ${query.q} »`, href(query, { q: undefined })]);
  if (query.brand) active.push(["brand", query.brand, href(query, { brand: undefined })]);
  if (query.min) active.push(["min", `à partir de ${query.min} €`, href(query, { min: undefined })]);
  if (query.max) active.push(["max", `jusqu'à ${query.max} €`, href(query, { max: undefined })]);

  return (
    <div className="fx-catalogue-controls">
      {active.length > 0 && (
        <div className="fx-active-filters">
          {active.map(([key, label, to]) => (
            <a className="fx-filter-pill" key={key} href={to}>
              {label}
              <span aria-hidden="true">×</span>
              <span className="fx-sr">Retirer ce filtre</span>
            </a>
          ))}
        </div>
      )}

      <form className="fx-catalogue-form" action="/catalogue/" method="get">
        <Hidden query={query} except={["min", "max", "sort", "per", "page"]} />

        <label className="fx-inline-field">
          <span>Prix min</span>
          <input type="number" name="min" min="0" step="1" defaultValue={query.min || ""} inputMode="numeric" />
        </label>
        <label className="fx-inline-field">
          <span>Prix max</span>
          <input type="number" name="max" min="0" step="1" defaultValue={query.max || ""} inputMode="numeric" />
        </label>
        <label className="fx-inline-field">
          <span>Trier par</span>
          <select name="sort" defaultValue={sort}>
            {SORTS.map((s) => (
              <option value={s.value} key={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <label className="fx-inline-field">
          <span>Par page</span>
          <select name="per" defaultValue={String(per)}>
            {PER_PAGE.map((n) => (
              <option value={n} key={n}>
                {n}
              </option>
            ))}
          </select>
        </label>

        <button className="fx-btn secondary" type="submit">
          Appliquer
        </button>
      </form>
    </div>
  );
}
