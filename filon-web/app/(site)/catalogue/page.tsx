import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { OffersBrowser } from "@/components/editorial/OffersBrowser";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/catalogue",
  title: "Le catalogue",
  description:
    "Parcourez les produits que FILON compare pour vous : prix réel, cashback et codes promo réunis, chez nos marchands partenaires.",
});

function Hero({ eyebrow, title, intro, crumb }: { eyebrow: string; title: React.ReactNode; intro: string; crumb: string }) {
  return <ContentHero eyebrow={eyebrow} title={title} intro={intro} breadcrumb={[{ name: crumb, path: "/catalogue" }]} />;
}

export default function CataloguePage() {
  return (
    <>
      <Localized
        fr={<Hero eyebrow="Catalogue" crumb="Catalogue" title={<>Parcourez, FILON <span className="it">compare</span>.</>} intro="Les produits de nos marchands partenaires. Cherchez, comparez, et laissez FILON trouver votre vrai prix." />}
        nl={<Hero eyebrow="Catalogus" crumb="Catalogus" title={<>Blader, FILON <span className="it">vergelijkt</span>.</>} intro="De producten van onze partnerwinkels. Zoek, vergelijk, en laat FILON je echte prijs vinden." />}
        en={<Hero eyebrow="Catalogue" crumb="Catalogue" title={<>Browse, FILON <span className="it">compares</span>.</>} intro="The products from our partner merchants. Search, compare, and let FILON find your real price." />}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <OffersBrowser />
        </div>
      </section>
    </>
  );
}
