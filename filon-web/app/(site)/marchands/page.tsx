import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { MerchantsBrowser, type Merchant } from "@/components/editorial/MerchantsBrowser";
import { Localized } from "@/components/editorial/Localized";
import { API } from "@/lib/api";

// Les logos et le portefeuille indexé évoluent, mais ne justifient pas
// un appel bloquant au backend à chaque visite.
export const revalidate = 3600;

export const metadata: Metadata = buildMetadata({
  path: "/marchands",
  title: "Les marchands indexés",
  description:
    "Les marchands dont FILON indexe des offres. Les prix observés et, lorsqu'ils existent, les avantages documentés restent identifiés par source.",
});

function Hero({ eyebrow, title, intro, crumb }: { eyebrow: string; title: React.ReactNode; intro: string; crumb: string }) {
  return (
    <ContentHero eyebrow={eyebrow} title={title} intro={intro} breadcrumb={[{ name: crumb, path: "/marchands" }]} />
  );
}

async function getMerchants(): Promise<Merchant[] | null> {
  try {
    const response = await fetch(`${API}/api/catalog/merchants?limit=500`, {
      next: { revalidate },
    });
    if (!response.ok) return null;
    const data = await response.json();
    return Array.isArray(data.items) ? data.items as Merchant[] : null;
  } catch {
    // Le composant client effectue une seconde tentative sans faire échouer la page.
    return null;
  }
}

export default async function MarchandsPage() {
  const initialItems = await getMerchants();

  return (
    <main className="p19-market-merchants" data-market-plan="merchants">
      <Localized
        fr={<Hero eyebrow="Catalogue" crumb="Marchands" title={<>Les marchands que FILON <span className="it">indexe</span>.</>} intro="FILON présente les prix observés chez les enseignes indexées. Un cashback ou un code promo n'apparaît que lorsqu'il est documenté ; ses conditions restent à confirmer chez le marchand." />}
        nl={<Hero eyebrow="Catalogus" crumb="Winkels" title={<>De winkels die FILON <span className="it">indexeert</span>.</>} intro="FILON toont waargenomen prijzen bij geïndexeerde winkels. Cashback of een kortingscode verschijnt alleen wanneer die is gedocumenteerd; controleer de voorwaarden bij de winkel." />}
        en={<Hero eyebrow="Catalogue" crumb="Merchants" title={<>The merchants FILON <span className="it">indexes</span>.</>} intro="FILON shows observed prices from indexed merchants. Cashback or a promo code appears only when documented; verify its terms with the merchant." />}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <MerchantsBrowser initialItems={initialItems} />
        </div>
      </section>
    </main>
  );
}
