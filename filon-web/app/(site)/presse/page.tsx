import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/presse",
  title: "Presse & médias",
  description:
    "L'essentiel sur FILON pour la presse : notre mission, les chiffres clés du marché, notre positionnement de copilote d'achat IA transparent, et le contact média.",
});

export default function PressePage() {
  return (
    <>
      <ContentHero
        eyebrow="Presse"
        title={<>FILON, en <span className="it">clair</span>.</>}
        intro="Tout ce qu'il faut pour parler de FILON : notre mission, notre positionnement et un contact média direct. Journalistes, créateurs, podcasteurs — écrivez-nous, on répond vite."
        breadcrumb={[{ name: "Presse", path: "/presse" }]}
      />

      <ProseBlock heading={<>En une <span className="it">phrase</span>.</>}>
        <p>
          <b>FILON est un copilote d&apos;achat propulsé par l&apos;IA</b> : il analyse le marché, compare les options
          (prix, cashback, reconditionné, codes promo, fiabilité, historique de prix) et recommande la meilleure décision
          avant chaque achat — pas seulement le meilleur prix, mais le bon choix, au bon moment.
        </p>
        <p>
          Basé à {site.city}, FILON vise à devenir la référence francophone de l&apos;optimisation d&apos;achat, avec la{" "}
          <b>transparence</b> comme différence de fond, à l&apos;heure où les dérives d&apos;attribution (affaires Honey, Phia)
          ont ébranlé la confiance dans le secteur.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Les points clés.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◆", h: "Catégorie", p: "AdTech / IA d'aide à la décision d'achat — un copilote, pas un comparateur." },
              { n: "◆", h: "Différence", p: "Transparence totale : la rémunération est affichée, l'attribution est honnête." },
              { n: "◆", h: "Marché", p: "Belgique francophone d'abord, puis France et francophonie européenne." },
              { n: "◆", h: "Modèle", p: "100 % gratuit pour l'utilisateur ; rémunéré par la commission d'apport des partenaires." },
              { n: "◆", h: "Fondateur", p: `${site.founder}, ${site.city} — également fondateur de SmartWave FX.` },
              { n: "◆", h: "Statut", p: "En phase de lancement — extension navigateur puis application et assistant." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Ce qui rend le sujet <span className="it">intéressant</span>.</>}>
        <p>
          La bascule d&apos;un modèle de <b>comparateur</b> (« voici les prix ») vers un modèle de <b>copilote d&apos;achat</b>
          (« voici ce que vous devriez acheter ») — porté par l&apos;IA et une base produit propriétaire.
        </p>
        <p>
          La <b>transparence comme réponse</b> à la crise de confiance de l&apos;affiliation, et un pari d&apos;ancrage
          européen depuis la Belgique plutôt que la course frontale au marché français.
        </p>
      </ProseBlock>

      <ProseBlock heading={<>Contact <span className="it">média</span>.</>} alt>
        <p>
          Pour une interview, des éléments visuels ou des précisions, écrivez à{" "}
          <a href={`mailto:presse@${site.domain}`}>presse@{site.domain}</a>. Nous fournissons logo, visuels et éléments de
          langage sur demande.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Parlons de ce qui <span className="it">change</span>.</>} sub="Une question, un angle, une interview — le contact presse répond vite." />
    </>
  );
}
