import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Reveal } from "@/components/editorial/Reveal";
import { ChromeCta } from "@/components/editorial/ChromeCta";
import { CHROME_STORE_URL } from "@/lib/config";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/extension",
  title: "L'extension",
  description:
    "L’extension FILON est conçue pour accompagner les fiches produit des marchands pris en charge. Elle aide à comparer les offres, l’historique de prix et les alternatives disponibles sans quitter la page.",
});

const FAQ_FR = [
  { q: "Sur quels navigateurs l'extension fonctionne-t-elle ?", a: "Chrome est la première version en cours de publication. Edge, Firefox et Safari feront l’objet d’annonces distinctes après le lancement Chrome." },
  { q: "L'extension ralentit-elle ma navigation ?", a: "Elle est conçue pour ne se déclencher que sur les fiches produit des marchands pris en charge. Hors de ces pages, elle n’analyse pas votre navigation." },
  { q: "Quelles données l'extension lit-elle ?", a: "Uniquement ce qui est nécessaire à la comparaison : le produit et le marchand de la page consultée. Pas de profil publicitaire, pas de revente. Le détail figure dans notre politique de confidentialité." },
  { q: "Dois-je créer un compte ?", a: "Non pour l'essentiel. Un compte devient utile pour les alertes de baisse de prix, mais la comparaison et le verdict fonctionnent sans inscription, et c'est gratuit." },
];

const FAQ_NL = [
  { q: "Op welke browsers werkt de extensie ?", a: "Chrome is de eerste versie die wordt gepubliceerd. Edge, Firefox en Safari worden afzonderlijk aangekondigd na de Chrome-lancering." },
  { q: "Vertraagt de extensie mijn browsen ?", a: "De extensie is ontworpen om alleen te starten op productpagina’s van ondersteunde winkels. Buiten die pagina’s analyseert ze je browsegedrag niet." },
  { q: "Welke gegevens leest de extensie ?", a: "Alleen wat nodig is voor de vergelijking : het product en de winkel van de bekeken pagina. Geen advertentieprofiel, geen doorverkoop. De details staan in ons privacybeleid." },
  { q: "Moet ik een account aanmaken ?", a: "Voor het essentiële niet. Een account wordt nuttig voor prijsdalings-meldingen, maar de vergelijking en het oordeel werken zonder inschrijving, en het is gratis." },
];

const FAQ_EN = [
  { q: "Which browsers does the extension work on ?", a: "Chrome is the first version being published. Edge, Firefox and Safari will be announced separately after the Chrome launch." },
  { q: "Does the extension slow down my browsing ?", a: "It is designed to activate only on product pages from supported merchants. Away from those pages, it does not analyse your browsing." },
  { q: "What data does the extension read ?", a: "Only what's needed for the comparison : the product and the merchant of the page viewed. No advertising profile, no reselling. The details are in our privacy policy." },
  { q: "Do I need to create an account ?", a: "Not for the essentials. An account becomes useful for price-drop alerts, but the comparison and the verdict work without signing up, and it's free." },
];

function Browsers({ chromeLabel, storeNote, statusChrome, waitNote }: { chromeLabel: string; storeNote: string; statusChrome: string; waitNote: string }) {
  return (
    <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
      <div className="ed-wrap">
        <Reveal>
          {CHROME_STORE_URL ? (
            <>
              <ChromeCta variant="wave" label={chromeLabel} />
              <p style={{ color: "var(--ink-3)", fontSize: 13.5, marginTop: 14 }}>{storeNote}</p>
            </>
          ) : (
            <>
              <div className="ed-browsers">
                <span className="bw live"><span className="dot" /> {statusChrome}</span>
                <span className="bw"><span className="dot" /> Edge</span>
                <span className="bw"><span className="dot" /> Firefox</span>
                <span className="bw"><span className="dot" /> Safari</span>
              </div>
              <p style={{ color: "var(--ink-3)", fontSize: 13.5, marginTop: 4 }}>{waitNote}</p>
            </>
          )}
        </Reveal>
      </div>
    </section>
  );
}

function ExtensionFR() {
  return (
    <>
      <ContentHero
        eyebrow="Extension"
        title={<>Votre copilote d&apos;achat, sur les pages <span className="it">prises en charge</span>.</>}
        intro="L’extension FILON est conçue pour vous accompagner sur les fiches produit des marchands pris en charge. Lorsqu’elle reconnaît un produit, elle vous aide à vérifier les offres, l’historique de prix et les alternatives disponibles."
        breadcrumb={[{ name: "Extension", path: "/extension" }]}
        photo="/img/video-extension-poster.webp"
        video="/video/phone-scroll.mp4"
      />
      <Browsers
        chromeLabel="Ajouter à Chrome — gratuit"
        storeNote="Installation en un clic depuis le Chrome Web Store. Aussi sur Edge. Firefox et Safari à suivre."
        statusChrome="Chrome · en cours de publication"
        waitNote="L'extension est prête et en cours de validation sur le Chrome Web Store. Dès qu'elle est en ligne, le bouton « Ajouter à Chrome » l'installe en un clic. Laissez votre e-mail pour être prévenu·e."
      />
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Ce que l&apos;extension peut vous montrer.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Les offres comparables", p: "Les prix disponibles pour le même produit chez les marchands indexés." },
              { n: "%", h: "Le cashback documenté", p: "Les avantages affichés lorsqu’ils sont renseignés pour l’offre concernée." },
              { n: "↻", h: "L’alternative reconditionnée", p: "Une offre comparable lorsqu’elle est indexée ; état et garantie restent ceux du marchand." },
              { n: "↧", h: "L’historique de prix", p: "Un contexte de prix quand l’historique disponible est suffisant." },
              { n: "★", h: "La fiabilité du vendeur", p: "Réputation et garanties prises en compte lorsque les données sont disponibles." },
              { n: "✓", h: "La conclusion", p: "Acheter, attendre ou vérifier : FILON peut s'abstenir lorsque les preuves manquent." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_FR} eyebrow="Extension · FAQ" title="L'extension, sans zone d'ombre." />
      <ClosingCta title={<>Installez le <span className="it">réflexe</span>.</>} sub="Sur une page prise en charge, ouvrez l'analyse FILON puis confirmez les conditions chez le marchand." />
    </>
  );
}

function ExtensionNL() {
  return (
    <>
      <ContentHero
        eyebrow="Extensie"
        title={<>Je koopcopiloot, op <span className="it">ondersteunde pagina&apos;s</span>.</>}
        intro="De FILON-extensie is ontworpen voor productpagina’s van ondersteunde winkels. Wanneer hij een product herkent, helpt hij je beschikbare aanbiedingen, prijsgeschiedenis en alternatieven te controleren."
        breadcrumb={[{ name: "Extensie", path: "/extension" }]}
        photo="/img/video-extension-poster.webp"
        video="/video/phone-scroll.mp4"
      />
      <Browsers
        chromeLabel="Toevoegen aan Chrome — gratis"
        storeNote="Installatie in één klik via de Chrome Web Store. Ook op Edge. Firefox en Safari volgen."
        statusChrome="Chrome · wordt gepubliceerd"
        waitNote="De extensie is klaar en wordt gevalideerd op de Chrome Web Store. Zodra hij online is, installeert de knop « Toevoegen aan Chrome » hem in één klik. Laat je e-mail achter om verwittigd te worden."
      />
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Wat de extensie kan tonen.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Vergelijkbare aanbiedingen", p: "Beschikbare prijzen voor hetzelfde product bij geïndexeerde winkels." },
              { n: "%", h: "Gedocumenteerde cashback", p: "Voordelen die worden getoond wanneer ze voor het betrokken aanbod vermeld zijn." },
              { n: "↻", h: "Het refurbished alternatief", p: "Een vergelijkbare aanbieding wanneer ze geïndexeerd is; staat en garantie blijven die van de winkel." },
              { n: "↧", h: "De prijsgeschiedenis", p: "Prijscontext wanneer er voldoende geschiedenis beschikbaar is." },
              { n: "★", h: "Betrouwbaarheid van de verkoper", p: "Reputatie en garanties worden meegenomen wanneer de gegevens beschikbaar zijn." },
              { n: "✓", h: "De conclusie", p: "Kopen, wachten of controleren: FILON kan zich onthouden wanneer bewijs ontbreekt." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_NL} eyebrow="Extensie · FAQ" title="De extensie, zonder grijze zones." />
      <ClosingCta title={<>Installeer de <span className="it">reflex</span>.</>} sub="Open op een ondersteunde pagina de FILON-analyse en bevestig daarna de voorwaarden bij de winkel." />
    </>
  );
}

function ExtensionEN() {
  return (
    <>
      <ContentHero
        eyebrow="Extension"
        title={<>Your shopping copilot, on <span className="it">supported pages</span>.</>}
        intro="The FILON extension is designed for product pages from supported merchants. When it recognises a product, it helps you check available offers, price history and alternatives."
        breadcrumb={[{ name: "Extension", path: "/extension" }]}
        photo="/img/video-extension-poster.webp"
        video="/video/phone-scroll.mp4"
      />
      <Browsers
        chromeLabel="Add to Chrome — free"
        storeNote="One-click install from the Chrome Web Store. Also on Edge. Firefox and Safari to follow."
        statusChrome="Chrome · being published"
        waitNote="The extension is ready and under review on the Chrome Web Store. As soon as it's live, the « Add to Chrome » button installs it in one click. Leave your email to be notified."
      />
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>What the extension can show.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Comparable offers", p: "Available prices for the same product across indexed merchants." },
              { n: "%", h: "Documented cashback", p: "Benefits shown when they are listed for the offer concerned." },
              { n: "↻", h: "The refurbished alternative", p: "A comparable offer when indexed; condition and warranty remain the merchant's terms." },
              { n: "↧", h: "Price history", p: "Price context when sufficient history is available." },
              { n: "★", h: "Merchant reliability", p: "Reputation and warranties are considered when the data is available." },
              { n: "✓", h: "The conclusion", p: "Buy, wait or verify: FILON can abstain when evidence is missing." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_EN} eyebrow="Extension · FAQ" title="The extension, with no grey areas." />
      <ClosingCta title={<>Install the <span className="it">reflex</span>.</>} sub="On a supported page, open the FILON analysis, then confirm the terms with the merchant." />
    </>
  );
}

export default function ExtensionPage() {
  return <Localized fr={<ExtensionFR />} nl={<ExtensionNL />} en={<ExtensionEN />} />;
}
