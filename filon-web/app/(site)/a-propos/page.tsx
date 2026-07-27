import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/a-propos",
  title: "À propos",
  description:
    "FILON veut devenir le premier réflexe avant chaque achat, en commençant par la Belgique. Notre vision, notre mission.",
});

const VALUES_FR = [
  { n: "01", h: "De votre côté", p: "Pas de publicité, pas d'intérêt caché. Ce qu'on vous montre sert votre intérêt." },
  { n: "02", h: "Intelligence", p: "La bonne information, au bon moment, sans effort pour vous." },
  { n: "03", h: "Simplicité", p: "Une seule expérience à la place de dix onglets." },
  { n: "04", h: "Exigence", p: "Un produit soigné, jusqu'au dernier détail." },
  { n: "05", h: "Confiance", p: "Vos données restent les vôtres. Sans exception." },
];

const VALUES_NL = [
  { n: "01", h: "Aan jouw kant", p: "Geen reclame, geen verborgen belang. Wat we je tonen dient jouw belang." },
  { n: "02", h: "Intelligentie", p: "De juiste informatie, op het juiste moment, moeiteloos voor jou." },
  { n: "03", h: "Eenvoud", p: "Eén enkele ervaring in plaats van tien tabbladen." },
  { n: "04", h: "Veeleisendheid", p: "Een verzorgd product, tot in het laatste detail." },
  { n: "05", h: "Vertrouwen", p: "Je gegevens blijven van jou. Zonder uitzondering." },
];

function Values({ heading, items }: { heading: string; items: typeof VALUES_FR }) {
  return (
    <section className="ed-band alt">
      <div className="ed-wrap">
        <div className="ed-prose" style={{ marginBottom: 28 }}>
          <h2 style={{ maxWidth: "18ch" }}>{heading}</h2>
        </div>
        <div className="ed-infogrid" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
          {items.map((v) => (
            <div className="ed-info" key={v.h}>
              <div className="n mono">{v.n}</div>
              <h3>{v.h}</h3>
              <p>{v.p}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function AProposFR() {
  return (
    <>
      <ContentHero
        eyebrow="À propos"
        title={<>Ne jamais payer le <span className="it">prix fort</span>.</>}
        intro="FILON réunit en une expérience simple ce qui prenait dix onglets. Notre ambition : devenir le premier réflexe avant chaque achat, en commençant par la Belgique."
        breadcrumb={[{ name: "À propos", path: "/a-propos" }]}
        photo="/img/page-apropos.webp"
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
      <Values heading="Nos cinq valeurs." items={VALUES_FR} />
      <ProseBlock heading={<>Le <span className="it">fondateur</span>.</>}>
        <p>
          FILON est porté par <b>{site.founder}</b>, entrepreneur bruxellois à la croisée du produit, de la technologie
          et de la marque. Il conçoit des produits de bout en bout : l&apos;ingénierie, l&apos;expérience, le récit.
        </p>
        <p>
          Avant FILON, il a fondé et développé <b>SmartWave FX</b>, une plateforme SaaS qu&apos;il a menée de
          l&apos;infrastructure technique jusqu&apos;à la marque et la communauté. Bilingue français-néerlandais, il
          transforme une idée en produit vivant, et une intuition en exécution soignée.
        </p>
        <p>
          Avec FILON, il applique cette exigence à un problème que tout le monde connaît : payer trop cher, faute de
          temps. Sa conviction tient en une phrase. Bien acheter ne devrait demander ni effort, ni compromis.
        </p>
      </ProseBlock>
      <ProseBlock heading={<>Pourquoi la <span className="it">Belgique</span> d&apos;abord.</>} alt>
        <p>
          Nous commençons par la Belgique. Un marché que l&apos;on connaît, où l&apos;on peut faire les choses bien avant
          de grandir, en français comme en néerlandais.
        </p>
        <p>
          La confiance se construit près de chez soi. Ensuite viendront la France, les Pays-Bas et le reste.
        </p>
      </ProseBlock>
      <ClosingCta title={<>Rejoignez le <span className="it">réflexe</span> malin.</>} sub="Ajoutez FILON et ne payez plus jamais le prix fort." />
    </>
  );
}

function AProposNL() {
  return (
    <>
      <ContentHero
        eyebrow="Over ons"
        title={<>Nooit de <span className="it">hoofdprijs</span> betalen.</>}
        intro="FILON brengt in één eenvoudige ervaring samen wat vroeger tien tabbladen kostte. Onze ambitie : de eerste reflex worden vóór elke aankoop, te beginnen met België."
        breadcrumb={[{ name: "Over ons", path: "/a-propos" }]}
        photo="/img/page-apropos.webp"
      />
      <ProseBlock heading={<>Het probleem dat we <span className="it">oplossen</span>.</>}>
        <p>
          Goed kopen kost tijd : checken, vergelijken, twijfelen, opnieuw beginnen. De meeste mensen geven op en betalen
          de volle prijs.
        </p>
        <p>
          FILON doet dat werk in jouw plaats. In één seconde geeft het je een duidelijk antwoord en je echte prijs. Je
          verandert niets aan je gewoontes, je betaalt gewoon minder.
        </p>
      </ProseBlock>
      <Values heading="Onze vijf waarden." items={VALUES_NL} />
      <ProseBlock heading={<>De <span className="it">oprichter</span>.</>}>
        <p>
          FILON wordt gedragen door <b>{site.founder}</b>, een Brusselse ondernemer op het kruispunt van product,
          technologie en merk. Hij ontwerpt producten van begin tot eind : de engineering, de ervaring, het verhaal.
        </p>
        <p>
          Vóór FILON richtte en ontwikkelde hij <b>SmartWave FX</b> op, een SaaS-platform dat hij van de technische
          infrastructuur tot het merk en de community bracht. Tweetalig Frans-Nederlands, verandert hij een idee in een
          levend product, en een intuïtie in een verzorgde uitvoering.
        </p>
        <p>
          Met FILON past hij die veeleisendheid toe op een probleem dat iedereen kent : te veel betalen, bij gebrek aan
          tijd. Zijn overtuiging in één zin. Goed kopen zou noch moeite, noch compromis mogen vragen.
        </p>
      </ProseBlock>
      <ProseBlock heading={<>Waarom eerst <span className="it">België</span>.</>} alt>
        <p>
          We beginnen in België. Een markt die we kennen, waar we het goed kunnen doen voordat we groeien, in het Frans
          én in het Nederlands.
        </p>
        <p>
          Vertrouwen bouw je dicht bij huis op. Daarna volgen Frankrijk, Nederland en de rest.
        </p>
      </ProseBlock>
      <ClosingCta title={<>Sluit je aan bij de slimme <span className="it">reflex</span>.</>} sub="Voeg FILON toe en betaal nooit meer de hoofdprijs." />
    </>
  );
}

export default function AProposPage() {
  return <Localized fr={<AProposFR />} nl={<AProposNL />} />;
}
