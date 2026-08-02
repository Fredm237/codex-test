"use client";

// Fil d'Ariane, titre et décompte du catalogue.
//
// Composants clients pour une seule raison : l'i18n de FILON vit dans un
// contexte React, qu'une page serveur ne peut pas lire. La grille produits,
// elle, reste rendue côté serveur — c'est elle qui porte le référencement.
// Le texte d'habillage se traduit au client ; les produits arrivent peuplés.

import { href, type CatalogueQuery } from "@/lib/catalogue";
import { useLocale } from "@/lib/i18n";

const TAG = { fr: "fr-BE", nl: "nl-BE", en: "en-GB" } as const;

type Named = { name: string; slug: string } | null;

export function CatalogueHeader({
  query,
  department,
  category,
  subcategory,
  total,
  unavailable,
}: {
  query: CatalogueQuery;
  department: Named;
  category: Named;
  subcategory: string | null;
  total: number;
  unavailable: boolean;
}) {
  const { t, locale } = useLocale();

  return (
    <>
      <nav className="fx-crumb" aria-label={t("cat.crumb")}>
        <a href="/catalogue/">{t("nav.catalogue")}</a>
        {department && (
          <>
            <span aria-hidden="true">/</span>
            <a href={href({}, { dept: department.slug })}>{department.name}</a>
          </>
        )}
        {category && (
          <>
            <span aria-hidden="true">/</span>
            <a href={href({}, { dept: department?.slug, cat: category.slug })}>{category.name}</a>
          </>
        )}
        {subcategory && (
          <>
            <span aria-hidden="true">/</span>
            <span aria-current="page">{subcategory}</span>
          </>
        )}
        {query.q && (
          <>
            <span aria-hidden="true">/</span>
            <span aria-current="page">« {query.q} »</span>
          </>
        )}
      </nav>

      <h1 className="fx-display fx-catalogue-title">
        {subcategory || category?.name || department?.name || (
          <>
            {t("cat.title1")}
            <br />
            <span className="it">{t("cat.title2")}</span>
          </>
        )}
      </h1>

      <p className="fx-lede fx-catalogue-lede">
        {unavailable
          ? t("cat.down")
          : `${total.toLocaleString(TAG[locale])} ${t("cat.count")}`}
      </p>
    </>
  );
}

export function CataloguePager({
  query,
  page,
  lastPage,
  pages,
}: {
  query: CatalogueQuery;
  page: number;
  lastPage: number;
  pages: Array<number | null>;
}) {
  const { t, locale } = useLocale();
  const status = t("cat.pageOf")
    .replace("{p}", page.toLocaleString(TAG[locale]))
    .replace("{n}", lastPage.toLocaleString(TAG[locale]));

  return (
    <>
      {lastPage > 1 && (
        <nav className="fx-pagination" aria-label={status}>
          <a
            className="fx-page-step"
            href={href(query, { page: String(Math.max(1, page - 1)) })}
            aria-disabled={page <= 1}
            tabIndex={page <= 1 ? -1 : undefined}
          >
            {t("cat.prev")}
          </a>
          <span className="fx-page-list">
            {pages.map((p, i) =>
              p === null ? (
                <span className="fx-page-gap" key={`gap-${i}`} aria-hidden="true">
                  …
                </span>
              ) : (
                <a
                  key={p}
                  className="fx-page"
                  aria-current={p === page ? "page" : undefined}
                  href={href(query, { page: String(p) })}
                >
                  {p}
                </a>
              )
            )}
          </span>
          <a
            className="fx-page-step"
            href={href(query, { page: String(Math.min(lastPage, page + 1)) })}
            aria-disabled={page >= lastPage}
            tabIndex={page >= lastPage ? -1 : undefined}
          >
            {t("cat.next")}
          </a>
        </nav>
      )}
      <p className="fx-fine fx-page-status">{status}</p>
    </>
  );
}

export function CatalogueEmpty() {
  const { t } = useLocale();
  return (
    <p className="fx-body fx-catalogue-empty">
      {t("cat.empty")} <a href="/catalogue/">{t("cat.reset")}</a>.
    </p>
  );
}

export function CatalogueNavToggle() {
  const { t } = useLocale();
  return (
    <summary className="fx-nav-toggle">
      <span>{t("cat.browse")}</span>
      <svg viewBox="0 0 16 16" aria-hidden="true" width="14" height="14">
        <path
          d="m4 6 4 4 4-4"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </summary>
  );
}
