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
    "L'extension FILON travaille partout où vous achetez. Sur chaque fiche produit, elle affiche le meilleur prix ailleurs, le cashback disponible, l'alternative reconditionnée et l'historique de prix, sans quitter la page.",
});

const FAQ_FR = [
  { q: "Sur quels navigateurs l'extension fonctionne-t-elle ?", a: "Chrome en premier, puis Edge, Firefox et Safari. L'application mobile et l'assistant conversationnel suivront. Rejoignez la liste pour être prévenu·e du lancement de chaque version." },
  { q: "L'extension ralentit-elle ma navigation ?", a: "Non. Elle ne s'active que sur les pages produit des marchands reconnus, reste invisible le reste du temps, et n'exécute aucune analyse tant que vous ne consultez pas un article." },
  { q: "Quelles données l'extension lit-elle ?", a: "Uniquement ce qui est nécessaire à la comparaison : le produit et le marchand de la page consultée. Pas de profil publicitaire, pas de revente. Le détail figure dans notre politique de confidentialité." },
  { q: "Dois-je créer un compte ?", a: "Non pour l'essentiel. Un compte devient utile pour les alertes de baisse de prix, mais la comparaison et le verdict fonctionnent sans inscription, et c'est gratuit." },
];

const FAQ_NL = [
  { q: "Op welke browsers werkt de extensie ?", a: "Chrome eerst, daarna Edge, Firefox en Safari. De mobiele app en de conversationele assistent volgen. Schrijf je in om verwittigd te worden bij elke versie." },
  { q: "Vertraagt de extensie mijn browsen ?", a: "Nee. Ze activeert alleen op de productpagina's van herkende winkels, blijft de rest van de tijd onzichtbaar, en voert geen analyse uit zolang je geen artikel bekijkt." },
  { q: "Welke gegevens leest de extensie ?", a: "Alleen wat nodig is voor de vergelijking : het product en de winkel van de bekeken pagina. Geen advertentieprofiel, geen doorverkoop. De details staan in ons privacybeleid." },
  { q: "Moet ik een account aanmaken ?", a: "Voor het essentiële niet. Een account wordt nuttig voor prijsdalings-meldingen, maar de vergelijking en het oordeel werken zonder inschrijving, en het is gratis." },
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
        title={<>Votre copilote d&apos;achat, <span className="it">partout</span>.</>}
        intro="L'extension FILON est présente sur chaque site marchand. Au moment où vous regardez un produit, elle vous dit s'il est moins cher ailleurs, quel cashback l'accompagne, s'il existe une alternative reconditionnée, et si c'est le bon moment pour acheter."
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
            <h2 style={{ maxWidth: "20ch" }}>Ce qui s&apos;affiche pendant que vous regardez un produit.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Le prix ailleurs", p: "« Vous regardez ce produit à 899€, il est à 799€ chez un autre marchand. »" },
              { n: "%", h: "Le cashback disponible", p: "Le taux le plus élevé du moment, activable en un geste avant de payer." },
              { n: "↻", h: "L'alternative reconditionnée", p: "L'équivalent garanti, souvent 20 à 45 % moins cher, quand il existe." },
              { n: "↧", h: "L'historique de prix", p: "Prix élevé, normal ou au plancher, pour savoir s'il faut acheter ou attendre." },
              { n: "★", h: "La fiabilité du vendeur", p: "Réputation et garanties, pour éviter la fausse bonne affaire." },
              { n: "✓", h: "Le verdict", p: "Un seul message clair : « acheter maintenant » ou « mieux vaut attendre »." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_FR} eyebrow="Extension · FAQ" title="L'extension, sans zone d'ombre." />
      <ClosingCta title={<>Installez le <span className="it">réflexe</span>.</>} sub="Ajoutez FILON à votre navigateur et laissez-le veiller avant chaque achat." />
    </>
  );
}

function ExtensionNL() {
  return (
    <>
      <ContentHero
        eyebrow="Extensie"
        title={<>Je koopcopiloot, <span className="it">overal</span>.</>}
        intro="De FILON-extensie is aanwezig op elke webshop. Op het moment dat je een product bekijkt, zegt hij of het elders goedkoper is, welke cashback erbij hoort, of er een refurbished alternatief bestaat, en of het het juiste moment is om te kopen."
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
            <h2 style={{ maxWidth: "20ch" }}>Wat verschijnt terwijl je een product bekijkt.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "De prijs elders", p: "« Je bekijkt dit product aan 899€, het is 799€ bij een andere winkel. »" },
              { n: "%", h: "De beschikbare cashback", p: "Het hoogste percentage van het moment, met één handeling te activeren vóór je betaalt." },
              { n: "↻", h: "Het refurbished alternatief", p: "Het gelijkwaardige met garantie, vaak 20 tot 45 % goedkoper, wanneer het bestaat." },
              { n: "↧", h: "De prijsgeschiedenis", p: "Hoge, normale of bodemprijs, om te weten of je moet kopen of wachten." },
              { n: "★", h: "De betrouwbaarheid van de verkoper", p: "Reputatie en garanties, om de valse koopjes te vermijden." },
              { n: "✓", h: "Het oordeel", p: "Eén duidelijke boodschap : « nu kopen » of « beter wachten »." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_NL} eyebrow="Extensie · FAQ" title="De extensie, zonder grijze zones." />
      <ClosingCta title={<>Installeer de <span className="it">reflex</span>.</>} sub="Voeg FILON toe aan je browser en laat het waken vóór elke aankoop." />
    </>
  );
}

export default function ExtensionPage() {
  return <Localized fr={<ExtensionFR />} nl={<ExtensionNL />} />;
}
