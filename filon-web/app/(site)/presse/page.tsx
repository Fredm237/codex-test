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
          <b>FILON est un assistant de comparaison.</b> Vous décrivez un besoin ; il classe les offres indexées,
          expose les preuves disponibles et s&apos;abstient lorsque les données ne suffisent pas.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Les points clés.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◆", h: "Ce que c'est", p: "Un assistant qui compare le périmètre indexé et nomme les informations manquantes." },
              { n: "◆", h: "Pour qui", p: "Toute personne qui veut acheter mieux, sans y passer des heures." },
              { n: "◆", h: "Prix", p: "Accès public actuel à 0 €, sans carte bancaire ; la page Tarifs fait foi." },
              { n: "◆", h: "Marché", p: "Belgique francophone d'abord, puis France et francophonie européenne." },
              { n: "◆", h: "Basé à", p: `${site.city}.` },
              { n: "◆", h: "Statut", p: "Catalogue et assistant web accessibles ; extension Chrome en attente de publication." },
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
          <b>FILON is een vergelijkingsassistent.</b> Je beschrijft een behoefte; FILON rangschikt geïndexeerde
          aanbiedingen, toont beschikbaar bewijs en onthoudt zich bij onvoldoende gegevens.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>De kernpunten.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◆", h: "Wat het is", p: "Een assistent die het geïndexeerde bereik vergelijkt en ontbrekende informatie benoemt." },
              { n: "◆", h: "Voor wie", p: "Iedereen die beter wil kopen, zonder er uren aan te besteden." },
              { n: "◆", h: "Prijs", p: "Huidige publieke toegang voor 0 € zonder bankkaart; Tarieven is de referentie." },
              { n: "◆", h: "Markt", p: "Franstalig België eerst, daarna Frankrijk en de Europese francofonie." },
              { n: "◆", h: "Gevestigd te", p: `${site.city}.` },
              { n: "◆", h: "Status", p: "Webcatalogus en assistent toegankelijk; Chrome-extensie wacht op publicatie." },
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

function PresseEN() {
  return (
    <>
      <ContentHero
        eyebrow="Press"
        title={<>FILON, <span className="it">in the clear</span>.</>}
        intro="Everything you need to talk about FILON. Journalists, creators, podcasters, write to us, we reply fast."
        breadcrumb={[{ name: "Press", path: "/presse" }]}
      />

      <ProseBlock heading={<>In one <span className="it">sentence</span>.</>}>
        <p>
          <b>FILON is a comparison assistant.</b> You describe a need; it ranks indexed offers, exposes available
          evidence and abstains when the data is insufficient.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>The key points.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◆", h: "What it is", p: "An assistant that compares the indexed scope and names missing information." },
              { n: "◆", h: "For whom", p: "Anyone who wants to buy better, without spending hours on it." },
              { n: "◆", h: "Price", p: "Current public access at €0 with no payment card; Pricing is the reference." },
              { n: "◆", h: "Market", p: "French-speaking Belgium first, then France and the European francophonie." },
              { n: "◆", h: "Based in", p: `${site.city}.` },
              { n: "◆", h: "Status", p: "Web catalogue and assistant accessible; Chrome extension awaiting publication." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Media <span className="it">contact</span>.</>} alt>
        <p>
          For an interview or visuals, write to{" "}
          <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. We provide logo and assets on request.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Let&apos;s talk about what&apos;s <span className="it">changing</span>.</>} sub="An angle, an interview, a figure to check. Write to us, we reply fast." />
    </>
  );
}

export default function PressePage() {
  return <Localized fr={<PresseFR />} nl={<PresseNL />} en={<PresseEN />} />;
}
