import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/a-propos",
  title: "À propos",
  description:
    "FILON veut devenir le premier réflexe avant chaque achat, en commençant par la Belgique. Notre vision, notre mission.",
});

const VALUES = [
  { n: "01", h: "De votre côté", p: "Pas de publicité, pas d'intérêt caché. Ce qu'on vous montre sert votre intérêt." },
  { n: "02", h: "Intelligence", p: "La bonne information, au bon moment, sans effort pour vous." },
  { n: "03", h: "Simplicité", p: "Une seule expérience à la place de dix onglets." },
  { n: "04", h: "Exigence", p: "Un produit soigné, jusqu'au dernier détail." },
  { n: "05", h: "Confiance", p: "Vos données restent les vôtres. Sans exception." },
];

export default function AProposPage() {
  return (
    <>
      <ContentHero
        eyebrow="À propos"
        title={<>Ne jamais payer le <span className="it">prix fort</span>.</>}
        intro="FILON réunit en une expérience simple ce qui prenait dix onglets. Notre ambition : devenir le premier réflexe avant chaque achat, en commençant par la Belgique."
        breadcrumb={[{ name: "À propos", path: "/a-propos" }]}
      />

      <ProseBlock heading={<>Le problème que nous <span className="it">réglons</span>.</>}>
        <p>
          Bien acheter prend du temps : vérifier, comparer, douter, recommencer. La plupart des gens abandonnent et
          paient plein tarif.
        </p>
        <p>
          FILON fait ce travail à votre place. En une seconde, il vous donne une réponse claire et votre vrai prix. Vous
          ne changez rien à vos habitudes, vous payez simplement moins.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Nos cinq valeurs.</h2>
          </div>
          <div className="ed-infogrid" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            {VALUES.map((v) => (
              <div className="ed-info" key={v.h}>
                <div className="n mono">{v.n}</div>
                <h3>{v.h}</h3>
                <p>{v.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <ProseBlock heading={<>Le <span className="it">fondateur</span>.</>}>
        <p>
          FILON est porté par <b>{site.founder}</b>, à {site.city}. Entrepreneur, à la croisée du produit, de la
          technologie et de la marque.
        </p>
      </ProseBlock>

      <ProseBlock heading={<>Pourquoi la <span className="it">Belgique</span> d&apos;abord.</>} alt>
        <p>
          Nous commençons par la Belgique francophone. Un marché que l&apos;on connaît, où l&apos;on peut faire les choses
          bien avant de grandir.
        </p>
        <p>
          La confiance se construit près de chez soi. Ensuite viendront la France et le reste de la francophonie.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Rejoignez le <span className="it">réflexe</span> malin.</>} sub="Ajoutez FILON et ne payez plus jamais le prix fort." />
    </>
  );
}
