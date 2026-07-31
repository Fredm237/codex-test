import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { OffersBrowser } from "@/components/editorial/OffersBrowser";
import { Localized } from "@/components/editorial/Localized";
import { CatalogueRails, type RailSection } from "@/components/editorial/CatalogueRails";
import { API } from "@/lib/api";

// Les rails sont rendus côté serveur (pas de spinner, et indexables), puis
// revalidés toutes les 5 min. Une fenêtre de 30 min rendait tout correctif
// invisible pendant une demi-heure, au point de faire douter du correctif
// lui-même ; le coût d'une régénération est négligeable à côté.
export const revalidate = 300;

export const metadata: Metadata = buildMetadata({
  path: "/catalogue",
  title: "Le catalogue",
  description:
    "Parcourez les produits que FILON compare pour vous : prix réel, cashback et codes promo réunis, chez nos marchands partenaires.",
});

async function getHighlights(): Promise<RailSection[]> {
  try {
    // Délai d'expiration explicite : cette page est prérendue au build. Sans
    // lui, un backend injoignable ne refuse pas la connexion, il la laisse
    // pendre — et c'est le déploiement entier qui échoue. Le site doit se
    // construire même quand l'API est à terre : les rails sont alors masqués.
    const res = await fetch(`${API}/api/catalog/highlights?limit=12`, {
      next: { revalidate: 300 },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) return [];
    const data = await res.json();
    return (data.sections || []) as RailSection[];
  } catch {
    return [];
  }
}

function Hero({ eyebrow, title, intro, crumb }: { eyebrow: string; title: React.ReactNode; intro: string; crumb: string }) {
  return <ContentHero eyebrow={eyebrow} title={title} intro={intro} breadcrumb={[{ name: crumb, path: "/catalogue" }]} />;
}

export default async function CataloguePage() {
  const sections = await getHighlights();

  return (
    <>
      <Localized
        fr={<Hero eyebrow="Catalogue" crumb="Catalogue" title={<>Parcourez, FILON <span className="it">compare</span>.</>} intro="Les produits de nos marchands partenaires. Cherchez, comparez, et laissez FILON trouver votre vrai prix." />}
        nl={<Hero eyebrow="Catalogus" crumb="Catalogus" title={<>Blader, FILON <span className="it">vergelijkt</span>.</>} intro="De producten van onze partnerwinkels. Zoek, vergelijk, en laat FILON je echte prijs vinden." />}
        en={<Hero eyebrow="Catalogue" crumb="Catalogue" title={<>Browse, FILON <span className="it">compares</span>.</>} intro="The products from our partner merchants. Search, compare, and let FILON find your real price." />}
      />

      {sections.length > 0 && (
        <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
          <div className="ed-wrap">
            <CatalogueRails sections={sections} />
          </div>
        </section>
      )}

      <section className="ed-band" style={{ paddingTop: sections.length ? undefined : 0, borderTop: sections.length ? undefined : 0 }}>
        <div className="ed-wrap">
          <h2 className="cat-rail-title" style={{ marginBottom: 6 }}>
            <Localized fr="Explorer tout le catalogue" nl="Verken de hele catalogus" en="Explore the whole catalogue" />
          </h2>
          <p className="cat-rail-sub" style={{ marginBottom: 22 }}>
            <Localized
              fr="Filtrez par catégorie, marque et budget."
              nl="Filter op categorie, merk en budget."
              en="Filter by category, brand and budget."
            />
          </p>
          <OffersBrowser />
        </div>
      </section>
    </>
  );
}
