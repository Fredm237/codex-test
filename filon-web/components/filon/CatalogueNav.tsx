"use client";

// Navigation du catalogue : l'arborescence complète, dépliable.
//
// Elle remplace un mur de puces. Vingt-six rayons et cent sous-rayons étalés
// à plat ne se parcourent pas — il faut pouvoir ouvrir un département, voir
// ses rayons, ouvrir un rayon, voir ses sous-rayons, sans quitter la page ni
// perdre le contexte.
//
// Bâtie sur <details>/<summary> : le dépliement est natif, donc il fonctionne
// sans JavaScript, il est accessible au clavier et annoncé par les lecteurs
// d'écran sans un seul attribut ARIA à maintenir. La branche courante est
// ouverte au rendu serveur, ce qu'aucun état React ne permettrait sans un
// aller-retour.

import { href, type CatalogueQuery, type Department } from "@/lib/catalogue";
import { useLocale } from "@/lib/i18n";
import { catalogueLabel } from "@/lib/catalogue-labels";

const TAG = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

export function CatalogueNav({
  departments,
  query,
  activeDepartment,
  activeCategory,
  activeSubcategory,
}: {
  departments: Department[];
  query: CatalogueQuery;
  activeDepartment: Department | null;
  activeCategory: { slug: string } | null;
  activeSubcategory: string | null;
}) {
  const { t, locale } = useLocale();
  const count = (n: number) => n.toLocaleString(TAG[locale]);
  return (
    <nav className="fx-nav-tree" aria-label={t("cat.aisles")}>
      <p className="fx-nav-tree-title">{t("cat.aisles")}</p>

      <a
        className="fx-nav-all"
        href="/catalogue/"
        aria-current={!activeDepartment ? "true" : undefined}
      >
        {t("cat.all")}
      </a>

      {departments.map((d) => {
        const openDepartment = activeDepartment?.slug === d.slug;
        return (
          <details className="fx-nav-dept" key={d.slug} open={openDepartment}>
            <summary>
              <span className="fx-nav-label">{catalogueLabel(d.name, locale)}</span>
              <span className="fx-nav-count">{count(d.count)}</span>
              <svg className="fx-nav-caret" viewBox="0 0 16 16" aria-hidden="true" width="14" height="14">
                <path
                  d="m6 4 4 4-4 4"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.7"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </summary>

            <ul className="fx-nav-cats">
              <li>
                <a
                  className="fx-nav-link"
                  aria-current={openDepartment && !activeCategory ? "true" : undefined}
                  href={href({}, { dept: d.slug })}
                >
                  {t("cat.allOf")} {catalogueLabel(d.name, locale)}
                </a>
              </li>

              {d.categories.map((c) => {
                const openCategory = openDepartment && activeCategory?.slug === c.slug;
                const subs = c.subcategories || [];
                if (subs.length === 0) {
                  return (
                    <li key={c.slug}>
                      <a
                        className="fx-nav-link"
                        aria-current={openCategory ? "true" : undefined}
                        href={href({}, { dept: d.slug, cat: c.slug })}
                      >
                        <span>{catalogueLabel(c.name, locale)}</span>
                        <span className="fx-nav-count">{count(c.count)}</span>
                      </a>
                    </li>
                  );
                }
                return (
                  <li key={c.slug}>
                    <details className="fx-nav-cat" open={openCategory}>
                      <summary>
                        <span className="fx-nav-label">{catalogueLabel(c.name, locale)}</span>
                        <span className="fx-nav-count">{count(c.count)}</span>
                        <svg className="fx-nav-caret" viewBox="0 0 16 16" aria-hidden="true" width="12" height="12">
                          <path
                            d="m6 4 4 4-4 4"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.7"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </summary>
                      <ul className="fx-nav-subs">
                        <li>
                          <a
                            className="fx-nav-link"
                            aria-current={openCategory && !activeSubcategory ? "true" : undefined}
                            href={href({}, { dept: d.slug, cat: c.slug })}
                          >
                            {t("cat.allOf")} {catalogueLabel(c.name, locale)}
                          </a>
                        </li>
                        {subs.map((s) => (
                          <li key={s.name}>
                            <a
                              className="fx-nav-link"
                              aria-current={
                                openCategory && activeSubcategory === s.name ? "true" : undefined
                              }
                              href={href({}, { dept: d.slug, cat: c.slug, sub: s.name })}
                            >
                              <span>{s.name}</span>
                              <span className="fx-nav-count">{count(s.count)}</span>
                            </a>
                          </li>
                        ))}
                      </ul>
                    </details>
                  </li>
                );
              })}
            </ul>
          </details>
        );
      })}

      {/* Les filtres en cours restent visibles dans la colonne : sur mobile
          l'arbre se referme, et il fallait pouvoir les retirer sans le rouvrir. */}
      {(query.q || query.brand || query.min || query.max) && (
        <a className="fx-nav-reset" href={href({}, { dept: query.dept, cat: query.cat, sub: query.sub })}>
          {t("cat.clear")}
        </a>
      )}
    </nav>
  );
}
