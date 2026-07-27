import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/presse",
  title: "Presse",
  description:
    "L'essentiel sur FILON pour la presse : ce que fait le produit, pour qui, et le contact média.",
});

function PresseFR() {
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

function PresseNL() {
  return (
    <>
      <ContentHero
        eyebrow="Pers"
        title={<>FILON, <span className="it">helder</span> uitgelegd.</>}
        intro="Alles wat nodig is om over FILON te praten. Journalisten, creators, podcasters, schrijf ons, we antwoorden snel."
        breadcrumb={[{ name: "Pers", path: "/presse" }]}
      />

      <ProseBlock heading={<>In één <span className="it">zin</span>.</>}>
        <p>
          <b>FILON is een koopassistent.</b> Je zegt hem wat je zoekt, hij zegt je wat te kopen, waar, en of het het
          juiste moment is. Vóór elke aankoop, in enkele seconden.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>De kernpunten.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◆", h: "Wat het is", p: "Een koopassistent die de beste beslissing aanbeveelt, geen simpele prijslijst." },
              { n: "◆", h: "Voor wie", p: "Iedereen die beter wil kopen, zonder er uren aan te besteden." },
              { n: "◆", h: "Prijs", p: "100 % gratis. Zonder abonnement, zonder bankkaart." },
              { n: "◆", h: "Markt", p: "Franstalig België eerst, daarna Frankrijk en de Europese francofonie." },
              { n: "◆", h: "Gevestigd te", p: `${site.city}.` },
              { n: "◆", h: "Status", p: "In lanceringsfase, extensie daarna applicatie en assistent." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Contact <span className="it">media</span>.</>} alt>
        <p>
          Voor een interview of visuals, schrijf naar{" "}
          <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. We bezorgen logo en materiaal op aanvraag.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Laten we praten over wat <span className="it">verandert</span>.</>} sub="Een invalshoek, een interview, een cijfer om te checken. Schrijf ons, we antwoorden snel." />
    </>
  );
}

export default function PressePage() {
  return <Localized fr={<PresseFR />} nl={<PresseNL />} />;
}
