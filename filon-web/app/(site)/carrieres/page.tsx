import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/carrieres",
  title: "Carrières",
  description:
    "FILON construit le copilote d'achat IA de référence en francophonie. Nous cherchons des personnes exigeantes et curieuses pour bâtir le produit, la donnée et la marque. Candidatures spontanées bienvenues.",
});

function CarrieresFR() {
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
          Écrivez à <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a> : dites-nous ce que vous voulez construire,
          montrez ce que vous avez déjà fait. Basé·e en Belgique ou en télétravail francophone.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Envie d&apos;en <span className="it">être</span> ?</>} sub="Écrivez-nous. Les meilleures histoires commencent tôt." />
    </>
  );
}

function CarrieresNL() {
  return (
    <>
      <ContentHero
        eyebrow="Vacatures"
        title={<>Bouw de <span className="it">reflex</span> van miljoenen kopers.</>}
        intro="FILON staat aan het begin, het beste moment om aan te sluiten. We bouwen een koopcopiloot die iedereen tijd en geld doet besparen, met transparantie als kompas."
        breadcrumb={[{ name: "Vacatures", path: "/carrieres" }]}
      />

      <ProseBlock heading={<>Wat we <span className="it">bouwen</span>.</>}>
        <p>
          Niet de zoveelste vergelijker, maar een <b>koopintelligentie</b> : een AI die de juiste beslissing aanbeveelt,
          aanwezig op het juiste moment. Het is een ambitieus technisch en redactioneel project, met een concrete impact
          op de portemonnee van mensen.
        </p>
        <p>
          We geloven in een klein en veeleisend team, in autonomie en in een product verzorgd tot in het laatste detail.
          Het tegenovergestelde van « snel gedaan, slecht gedaan ».
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "22ch" }}>De profielen die ons doen trillen.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Product & AI", p: "Engineering, data en modellen : de intelligentie bouwen die de juiste aankoop aanbeveelt." },
              { n: "02", h: "Extensie & front", p: "Een ultravloeiende browserextensie, aanwezig zonder ooit te storen." },
              { n: "03", h: "Content & mediamerk", p: "Video, nieuwsbrief « Le Filon », sociale media : van FILON een merk maken dat men volgt." },
              { n: "04", h: "Growth & partnerschappen", p: "De integraties met winkels en platforms smeden, het publiek doen groeien." },
              { n: "05", h: "Design", p: "Een uitvoering van niveau, van het microdetail tot de globale ervaring." },
              { n: "06", h: "Ops & vertrouwen", p: "GDPR-conformiteit, datakwaliteit, onberispelijke gebruikersrelatie." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Geen vacature die bij je <span className="it">past</span> ?</>}>
        <p>
          We hebben niet altijd een openstaande functie, maar we lezen elke spontane sollicitatie. Als het project je
          aanspreekt en je uitstekend bent in wat je doet, stel je voor.
        </p>
        <p>
          Schrijf naar <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a> : zeg ons wat je wil bouwen,
          toon wat je al hebt gedaan. Gevestigd in België of in Franstalig telewerk.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Zin om erbij te <span className="it">zijn</span> ?</>} sub="Schrijf ons. De beste verhalen beginnen vroeg." />
    </>
  );
}

function CarrieresEN() {
  return (
    <>
      <ContentHero
        eyebrow="Careers"
        title={<>Build the <span className="it">reflex</span> of millions of shoppers.</>}
        intro="FILON is at its beginnings, the best moment to join. We're building a shopping copilot that saves everyone time and money, with transparency as our compass."
        breadcrumb={[{ name: "Careers", path: "/carrieres" }]}
      />

      <ProseBlock heading={<>What we&apos;re <span className="it">building</span>.</>}>
        <p>
          Not yet another comparison site, but a <b>shopping intelligence</b>: an AI that recommends the right
          decision, present at the right moment. It&apos;s an ambitious technical and editorial project, with a
          concrete impact on people&apos;s wallets.
        </p>
        <p>
          We believe in a small, exacting team, in autonomy and in a product polished down to the last detail. The
          exact opposite of « quick and sloppy ».
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "22ch" }}>The profiles that make us tick.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Product & AI", p: "Engineering, data and models: building the intelligence that recommends the right purchase." },
              { n: "02", h: "Extension & front", p: "An ultra-smooth browser extension, present without ever getting in the way." },
              { n: "03", h: "Content & media brand", p: "Video, the « Le Filon » newsletter, social: making FILON a brand people follow." },
              { n: "04", h: "Growth & partnerships", p: "Forging merchant and platform integrations, growing the audience." },
              { n: "05", h: "Design", p: "Top-tier execution, from the micro-detail to the overall experience." },
              { n: "06", h: "Ops & trust", p: "GDPR compliance, data quality, an impeccable user relationship." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>No opening that <span className="it">fits</span> you ?</>}>
        <p>
          We don&apos;t always have an open role, but we read every spontaneous application. If the project speaks
          to you and you&apos;re excellent at what you do, introduce yourself.
        </p>
        <p>
          Write to <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>: tell us what you want to
          build, show what you&apos;ve already done. Based in Belgium or French-speaking remote.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Want to be <span className="it">part of it</span> ?</>} sub="Write to us. The best stories start early." />
    </>
  );
}

export default function CarrieresPage() {
  return <Localized fr={<CarrieresFR />} nl={<CarrieresNL />} en={<CarrieresEN />} />;
}
