import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/presse",
  title: "Presse",
  description:
    "L'essentiel sur FILON pour la presse : ce que fait le produit, pour qui, et le contact média.",
});

export default function PressePage() {
  return (
    <>
      <ContentHero
        eyebrow="Presse"
        title={<>FILON, en <span className="it">clair</span>.</>}
        intro="Tout ce qu'il faut pour parler de FILON. Journalistes, créateurs, podcasteurs, écrivez-nous, on répond vite."
        breadcrumb={[{ name: "Presse", path: "/presse" }]}
      />

      <ProseBlock heading={<>En une <span className="it">phrase</span>.</>}>
        <p>
          <b>FILON est un assistant d&apos;achat.</b> Vous lui dites ce que vous cherchez, il vous dit quoi acheter, où,
          et si c&apos;est le bon moment. Avant chaque achat, en quelques secondes.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Les points clés.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◆", h: "Ce que c'est", p: "Un assistant d'achat qui recommande la meilleure décision, pas une simple liste de prix." },
              { n: "◆", h: "Pour qui", p: "Toute personne qui veut acheter mieux, sans y passer des heures." },
              { n: "◆", h: "Prix", p: "100 % gratuit. Sans abonnement, sans carte bancaire." },
              { n: "◆", h: "Marché", p: "Belgique francophone d'abord, puis France et francophonie européenne." },
              { n: "◆", h: "Basé à", p: `${site.city}.` },
              { n: "◆", h: "Statut", p: "En phase de lancement, extension puis application et assistant." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Contact <span className="it">média</span>.</>} alt>
        <p>
          Pour une interview ou des visuels, écrivez à{" "}
          <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. Nous fournissons logo et éléments sur demande.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Parlons de ce qui <span className="it">change</span>.</>} sub="Un angle, une interview, un chiffre à vérifier. Écrivez-nous, on répond vite." />
    </>
  );
}
