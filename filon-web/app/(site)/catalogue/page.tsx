import type { Metadata } from "next";
import { Suspense } from "react";
import { buildMetadata } from "@/lib/seo";
import { ProductCard } from "@/components/filon/ProductCard";
import { CatalogueSearch, CatalogueControls } from "@/components/filon/CatalogueControls";
import { CatalogueNav } from "@/components/filon/CatalogueNav";
import { Pulse } from "@/components/filon/Pulse";
import { Rails } from "@/components/filon/Rails";
import {
  CatalogueHeader, CataloguePager, CatalogueEmpty, CatalogueNavToggle,
} from "@/components/filon/CatalogueHeader";
import {
  getDepartments,
  getOffers,
  getPulse,
  getRails,
  resolve,
  href,
  pageNumber,
  pageSize,
  pageWindow,
  sortValue,
  type CatalogueQuery,
} from "@/lib/catalogue";

// La grille et les filtres doivent être disponibles dès que les données
// essentielles arrivent. Le pouls et les rangées sont utiles, mais jamais au
// prix d'un clic qui semble inerte : ils sont diffusés après le HTML principal.
export const revalidate = 300;

async function CataloguePulse() {
  const pulse = await getPulse();
  return <Pulse data={pulse} />;
}

async function CatalogueRails() {
  const rails = await getRails();
  return rails.length > 0 ? <Rails sections={rails} /> : null;
}

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

export default async function CataloguePage({
  searchParams,
}: {
  searchParams: Promise<CatalogueQuery>;
}) {
  const query = await searchParams;
  const departments = await getDepartments();
  const resolved = resolve(departments, query);
  const { department, category, subcategory } = resolved;
  const browsing = !department && !category && !query.q;

  // Chemin critique : uniquement les offres affichées et la taxonomie déjà
  // requise par la navigation. Le reste est diffusé ensuite sous Suspense.
  const result = await getOffers(query, resolved);
  const per = pageSize(query);
  const page = pageNumber(query);
  const total = result?.total ?? 0;
  const lastPage = Math.max(1, Math.ceil(total / per));

  return (
    <section className="fx-section page-top fx-catalogue">
      <div className="fx-container fx-catalogue-layout">
        <details className="fx-nav-shell">
          <CatalogueNavToggle />
          <CatalogueNav
            departments={departments}
            query={query}
            activeDepartment={department}
            activeCategory={category}
            activeSubcategory={subcategory}
          />
        </details>

        <div className="fx-catalogue-main">
          <div className="fx-catalogue-intro">
            <div className="fx-catalogue-intro-copy">
              <CatalogueHeader
                query={query}
                department={department}
                category={category}
                subcategory={subcategory}
                total={total}
                unavailable={result === null}
              />

              <Suspense fallback={null}>
                <CataloguePulse />
              </Suspense>
            </div>
            <CatalogueSearch query={query} />
          </div>

          {result !== null && total > 0 && (
            <>
              <CatalogueControls query={query} sort={sortValue(query)} per={per} />
              <div className="fx-product-grid fx-catalogue-grid">
                {result.items.map((o) => (
                  <ProductCard key={o.id} offer={o} showEvidence />
                ))}
              </div>
              <CataloguePager
                query={query}
                page={page}
                lastPage={lastPage}
                pages={pageWindow(page, lastPage)}
              />
            </>
          )}

          {result !== null && total === 0 && <CatalogueEmpty />}

          {/* Les rangées éditoriales viennent après la grille : leur lenteur ne
              bloque ni la navigation, ni le premier produit consultable. */}
          {browsing && (
            <Suspense fallback={null}>
              <CatalogueRails />
            </Suspense>
          )}
        </div>
      </div>
    </section>
  );
}
