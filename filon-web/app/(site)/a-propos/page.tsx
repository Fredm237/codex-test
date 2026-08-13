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
  { n: "01", h: "De votre côté", p: "Nous expliquons notre modèle d'affiliation et signalons les liens concernés." },
  { n: "02", h: "Intelligence", p: "Les informations disponibles, réunies pour vous aider à comparer." },
  { n: "03", h: "Simplicité", p: "Une même expérience pour rechercher, comprendre et décider." },
  { n: "04", h: "Exigence", p: "Un produit soigné, jusque dans ses détails." },
  { n: "05", h: "Confiance", p: "Vos données de navigation ne sont pas revendues. Notre politique précise vos droits." },
];

const VALUES_NL = [
  { n: "01", h: "Aan jouw kant", p: "We leggen ons affiliatiemodel uit en duiden de betrokken links aan." },
  { n: "02", h: "Intelligentie", p: "De beschikbare informatie, samengebracht om je te helpen vergelijken." },
  { n: "03", h: "Eenvoud", p: "Eén ervaring om te zoeken, te begrijpen en te beslissen." },
  { n: "04", h: "Veeleisendheid", p: "Een verzorgd product, ook in de details." },
  { n: "05", h: "Vertrouwen", p: "Je surfgegevens worden niet doorverkocht. Ons privacybeleid legt je rechten uit." },
];

const VALUES_EN = [
  { n: "01", h: "On your side", p: "We explain our affiliate model and identify the links concerned." },
  { n: "02", h: "Intelligence", p: "The information available, brought together to help you compare." },
  { n: "03", h: "Simplicity", p: "One experience to search, understand and decide." },
  { n: "04", h: "Exactingness", p: "A polished product, including the details." },
  { n: "05", h: "Trust", p: "Your browsing data is not resold. Our privacy policy explains your rights." },
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
        title={<>Mieux choisir, avant d&apos;<span className="it">acheter</span>.</>}
        intro="FILON réunit dans une expérience claire les informations utiles avant un achat. Notre ambition : devenir un réflexe de comparaison, en commençant par la Belgique."
        breadcrumb={[{ name: "À propos", path: "/a-propos" }]}
        photo="/img/page-apropos.webp"
      />
      <ProseBlock heading={<>Le problème que nous <span className="it">réglons</span>.</>}>
        <p>
          Bien acheter prend du temps : vérifier, comparer, douter, recommencer. Il est facile de se perdre entre les
          informations, les prix et les conditions.
        </p>
        <p>
          FILON rassemble les données disponibles dans une même vue et les organise pour rendre la comparaison plus
          claire. Prix affiché, cashback et codes promo sont montrés lorsqu'ils sont renseignés ; vous décidez ensuite.
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
      <ClosingCta title={<>Adoptez le <span className="it">bon réflexe</span>.</>} sub="Consultez FILON avant de décider de votre prochain achat." />
    </>
  );
}

function AProposNL() {
  return (
    <>
      <ContentHero
        eyebrow="Over ons"
        title={<>Beter kiezen, vóór je <span className="it">koopt</span>.</>}
        intro="FILON brengt nuttige informatie vóór een aankoop samen in één heldere ervaring. Onze ambitie: een reflex voor vergelijking worden, te beginnen met België."
        breadcrumb={[{ name: "Over ons", path: "/a-propos" }]}
        photo="/img/page-apropos.webp"
      />
      <ProseBlock heading={<>Het probleem dat we <span className="it">oplossen</span>.</>}>
        <p>
          Goed kopen kost tijd: checken, vergelijken, twijfelen, opnieuw beginnen. Het is makkelijk om te verdwalen in
          informatie, prijzen en voorwaarden.
        </p>
        <p>
          FILON brengt beschikbare gegevens samen in één overzicht en ordent ze om vergelijken duidelijker te maken.
          Getoonde prijs, cashback en kortingscodes verschijnen wanneer ze vermeld zijn; daarna beslis jij.
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
      <ClosingCta title={<>Kies de juiste <span className="it">reflex</span>.</>} sub="Bekijk FILON vóór je over je volgende aankoop beslist." />
    </>
  );
}

function AProposEN() {
  return (
    <>
      <ContentHero
        eyebrow="About"
        title={<>Choose better, before you <span className="it">buy</span>.</>}
        intro="FILON brings useful information together in one clear experience before a purchase. Our ambition is to become a comparison reflex, starting with Belgium."
        breadcrumb={[{ name: "About", path: "/a-propos" }]}
        photo="/img/page-apropos.webp"
      />
      <ProseBlock heading={<>The problem we <span className="it">solve</span>.</>}>
        <p>
          Buying well takes time: checking, comparing, doubting, starting over. It is easy to get lost between
          information, prices and terms.
        </p>
        <p>
          FILON brings the available data into one view and organises it to make comparison clearer. Displayed price,
          cashback and promo codes appear when they are listed; you decide what to do next.
        </p>
      </ProseBlock>
      <Values heading="Our five values." items={VALUES_EN} />
      <ProseBlock heading={<>The <span className="it">founder</span>.</>}>
        <p>
          FILON is driven by <b>{site.founder}</b>, a Brussels entrepreneur at the crossroads of product, technology
          and brand. He designs products end to end: the engineering, the experience, the story.
        </p>
        <p>
          Before FILON, he founded and grew <b>SmartWave FX</b>, a SaaS platform he led from the technical
          infrastructure all the way to the brand and community. Bilingual French-Dutch, he turns an idea into a
          living product, and an intuition into polished execution.
        </p>
        <p>
          With FILON, he applies that exactingness to a problem everyone knows: paying too much, for lack of time.
          His conviction fits in one sentence. Buying well should require neither effort nor compromise.
        </p>
      </ProseBlock>
      <ProseBlock heading={<>Why <span className="it">Belgium</span> first.</>} alt>
        <p>
          We&apos;re starting with Belgium. A market we know, where we can do things well before growing, in French
          as in Dutch.
        </p>
        <p>Trust is built close to home. Then come France, the Netherlands and the rest.</p>
      </ProseBlock>
      <ClosingCta title={<>Make it a better <span className="it">reflex</span>.</>} sub="Check FILON before deciding on your next purchase." />
    </>
  );
}

export default function AProposPage() {
  return <Localized fr={<AProposFR />} nl={<AProposNL />} en={<AProposEN />} />;
}
