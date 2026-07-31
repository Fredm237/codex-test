import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { MerchantsBrowser } from "@/components/editorial/MerchantsBrowser";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/marchands",
  title: "Les marchands partenaires",
  description:
    "Les marchands que FILON compare pour vous. Prix, cashback et codes promo réunis sur chaque fiche produit, en toute transparence.",
});

function Hero({ eyebrow, title, intro, crumb }: { eyebrow: string; title: React.ReactNode; intro: string; crumb: string }) {
  return (
    <ContentHero eyebrow={eyebrow} title={title} intro={intro} breadcrumb={[{ name: crumb, path: "/marchands" }]} />
  );
}

export default function MarchandsPage() {
  return (
    <>
      <Localized
        fr={<Hero eyebrow="Partenaires" crumb="Marchands" title={<>Les marchands que FILON <span className="it">compare</span>.</>} intro="Les enseignes que nous comparons pour vous. Sur chaque produit, FILON réunit le prix, le cashback et les codes promo — et vous montre votre vrai prix." />}
        nl={<Hero eyebrow="Partners" crumb="Winkels" title={<>De winkels die FILON <span className="it">vergelijkt</span>.</>} intro="De winkels die we voor je vergelijken. Bij elk product brengt FILON de prijs, de cashback en de kortingscodes samen — en toont je je echte prijs." />}
        en={<Hero eyebrow="Partners" crumb="Merchants" title={<>The merchants FILON <span className="it">compares</span>.</>} intro="The stores we compare for you. On every product, FILON brings together the price, the cashback and the promo codes — and shows you your real price." />}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <MerchantsBrowser />
        </div>
      </section>
    </>
  );
}
