import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ProductCard } from "@/components/filon/ProductCard";
import { CARD_COPY } from "@/components/filon/product-copy";
import { CatalogueSearch, CatalogueControls } from "@/components/filon/CatalogueControls";
import { CatalogueNav } from "@/components/filon/CatalogueNav";
import {
  getDepartments,
  getOffers,
  resolve,
  href,
  pageNumber,
  pageSize,
  pageWindow,
  sortValue,
  type CatalogueQuery,
} from "@/lib/catalogue";

// Rendu serveur + ISR. La grille était chargée depuis le navigateur : elle
// dépendait du réseau du visiteur, n'était pas indexable, et tombait sur une
// phrase sans issue (« Impossible de charger le catalogue »). Ici la page
// arrive peuplée, ou le dit clairement avec un moyen de repartir.
export const revalidate = 300;

export async function generateMetadata({
  searchParams,
}: {
  searchParams: Promise<CatalogueQuery>;
}): Promise<Metadata> {
  const query = await searchParams;
  const departments = await getDepartments();
  const { category, subcategory } = resolve(departments, query);
  const title = subcategory
    ? `${subcategory} — ${category?.name}`
    : category
      ? category.name
      : "Le catalogue";
  return buildMetadata({
    path: "/catalogue",
    title,
    description:
      "Les produits de nos marchands partenaires, regroupés par code-barres et comparés. Prix relevés, historique conservé, meilleure offre en évidence.",
  });
}

function Breadcrumb({
  query,
  department,
  category,
  subcategory,
}: {
  query: CatalogueQuery;
  department: { name: string; slug: string } | null;
  category: { name: string; slug: string } | null;
  subcategory: string | null;
}) {
  return (
    <nav className="fx-crumb" aria-label="Fil d'Ariane">
      <a href="/catalogue/">Catalogue</a>
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
  );
}

export default async function CataloguePage({
  searchParams,
}: {
  searchParams: Promise<CatalogueQuery>;
}) {
  const query = await searchParams;
  const departments = await getDepartments();
  const resolved = resolve(departments, query);
  const { department, category, subcategory } = resolved;
  const result = await getOffers(query, resolved);

  const per = pageSize(query);
  const page = pageNumber(query);
  const total = result?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / per));

  return (
    <section className="fx-section page-top fx-catalogue">
      <div className="fx-container fx-catalogue-layout">
        {/* Colonne de navigation. En dessous de 900 px elle se replie dans un
            dépliant natif : l'arborescence complète mangerait l'écran avant
            le premier produit. */}
        {/* Pas d'attribut `open` : replié par défaut, donc les produits
            viennent en premier sur mobile. Au-dessus de 900 px, le CSS force
            l'arborescence visible — la colonne y est permanente. */}
        <details className="fx-nav-shell">
          <summary className="fx-nav-toggle">
            <span>Parcourir les rayons</span>
            <svg viewBox="0 0 16 16" aria-hidden="true" width="14" height="14">
              <path d="m4 6 4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.7"
                strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </summary>
          <CatalogueNav
            departments={departments}
            query={query}
            activeDepartment={department}
            activeCategory={category}
            activeSubcategory={subcategory}
          />
        </details>

        <div className="fx-catalogue-main">
          <Breadcrumb query={query} department={department} category={category} subcategory={subcategory} />

          <h1 className="fx-display fx-catalogue-title">
            {subcategory || category?.name || department?.name || (
              <>
                Le catalogue,
                <br />
                <span className="it">rayon par rayon.</span>
              </>
            )}
          </h1>

          <p className="fx-lede fx-catalogue-lede">
            {result === null
              ? "Le catalogue est momentanément indisponible. Réessayez dans un instant."
              : `${total.toLocaleString("fr-BE")} produits comparés chez nos marchands partenaires.`}
          </p>

          <CatalogueSearch query={query} />

          {result !== null && total > 0 && (
            <>
              <CatalogueControls query={query} sort={sortValue(query)} per={per} />

              <div className="fx-product-grid fx-catalogue-grid">
                {result.items.map((o) => (
                  <ProductCard key={o.id} offer={o} copy={CARD_COPY.fr} />
                ))}
              </div>

              {lastPage > 1 && (
                <nav className="fx-pagination" aria-label={`Page ${page} sur ${lastPage}`}>
                  <a
                    className="fx-page-step"
                    href={href(query, { page: String(Math.max(1, page - 1)) })}
                    aria-disabled={page <= 1}
                    tabIndex={page <= 1 ? -1 : undefined}
                  >
                    Précédent
                  </a>
                  <span className="fx-page-list">
                    {pageWindow(page, lastPage).map((p, i) =>
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
                    Suivant
                  </a>
                </nav>
              )}

              <p className="fx-fine fx-page-status">
                Page {page} sur {lastPage.toLocaleString("fr-BE")}
              </p>
            </>
          )}

          {result !== null && total === 0 && (
            <p className="fx-body fx-catalogue-empty">
              Aucun produit ne correspond à cette sélection.{" "}
              <a href="/catalogue/">Repartir de tout le catalogue</a>.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
