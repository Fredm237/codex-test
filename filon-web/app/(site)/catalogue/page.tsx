import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ProductCard } from "@/components/filon/ProductCard";
import { CatalogueSearch, CatalogueControls } from "@/components/filon/CatalogueControls";
import { CatalogueNav } from "@/components/filon/CatalogueNav";
import {
  CatalogueHeader, CataloguePager, CatalogueEmpty, CatalogueNavToggle,
} from "@/components/filon/CatalogueHeader";
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
        {/* Pas d'attribut `open` : replié par défaut, donc les produits
            viennent en premier sur mobile. Au-dessus de 900 px, le CSS force
            l'arborescence visible — la colonne y est permanente. */}
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
          <CatalogueHeader
            query={query}
            department={department}
            category={category}
            subcategory={subcategory}
            total={total}
            unavailable={result === null}
          />

          <CatalogueSearch query={query} />

          {result !== null && total > 0 && (
            <>
              <CatalogueControls query={query} sort={sortValue(query)} per={per} />

              {/* La grille reste rendue côté serveur : c'est elle que Google
                  lit, et elle arrive peuplée quel que soit le réseau. */}
              <div className="fx-product-grid fx-catalogue-grid">
                {result.items.map((o) => (
                  <ProductCard key={o.id} offer={o} />
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
        </div>
      </div>
    </section>
  );
}
