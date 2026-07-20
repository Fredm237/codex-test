import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/carrieres",
  title: "Carrières",
  description:
    "FILON construit le copilote d'achat IA de référence en francophonie. Nous cherchons des personnes exigeantes et curieuses pour bâtir le produit, la donnée et la marque. Candidatures spontanées bienvenues.",
});

export default function CarrieresPage() {
  return (
    <>
      <ContentHero
        eyebrow="Carrières"
        title={<>Construisez le <span className="it">réflexe</span> de millions d&apos;acheteurs.</>}
        intro="FILON en est à ses débuts, le meilleur moment pour rejoindre. Nous bâtissons un copilote d'achat qui fait gagner du temps et de l'argent à tout le monde, avec la transparence pour boussole."
        breadcrumb={[{ name: "Carrières", path: "/carrieres" }]}
      />

      <ProseBlock heading={<>Ce que nous <span className="it">construisons</span>.</>}>
        <p>
          Pas un énième comparateur, mais une <b>intelligence d&apos;achat</b> : une IA qui recommande la bonne décision,
          présente au bon moment. C&apos;est un projet technique et éditorial ambitieux, avec un impact concret sur le
          portefeuille des gens.
        </p>
        <p>
          Nous croyons à une petite équipe exigeante, à l&apos;autonomie et à un produit soigné jusqu&apos;au dernier détail.
          Tout l&apos;inverse du « vite fait, mal fait ».
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "22ch" }}>Les profils qui nous font vibrer.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Produit & IA", p: "Ingénierie, data et modèles : bâtir l'intelligence qui recommande le bon achat." },
              { n: "02", h: "Extension & front", p: "Une extension navigateur ultra-fluide, présente sans jamais gêner." },
              { n: "03", h: "Contenu & marque média", p: "Vidéo, newsletter « Le Filon », réseaux : faire de FILON une marque qu'on suit." },
              { n: "04", h: "Growth & partenariats", p: "Nouer les intégrations marchands et plateformes, faire grandir l'audience." },
              { n: "05", h: "Design", p: "Une exécution de niveau, du micro-détail à l'expérience globale." },
              { n: "06", h: "Ops & confiance", p: "Conformité RGPD, qualité de la donnée, relation utilisateur irréprochable." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Pas d&apos;offre qui vous <span className="it">correspond</span> ?</>}>
        <p>
          Nous n&apos;avons pas toujours de poste ouvert, mais nous lisons chaque candidature spontanée. Si le projet vous parle
          et que vous êtes excellent·e dans ce que vous faites, présentez-vous.
        </p>
        <p>
          Écrivez à <a href={`mailto:jobs@${site.domain}`}>jobs@{site.domain}</a> : dites-nous ce que vous voulez construire,
          montrez ce que vous avez déjà fait. Basé·e en Belgique ou en télétravail francophone.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Envie d&apos;en <span className="it">être</span> ?</>} sub="Écrivez-nous. Les meilleures histoires commencent tôt." />
    </>
  );
}
