import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Reveal } from "@/components/editorial/Reveal";
import { ChromeCta } from "@/components/editorial/ChromeCta";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/tarifs",
  title: "Tarifs",
  description:
    "FILON est gratuit, pour tout le monde, pour toujours. Sans abonnement, sans carte bancaire, sans revente de vos données.",
});

const INCLUS_FR = [
  "Le meilleur prix réel, trouvé pour vous",
  "Un verdict clair : acheter maintenant, ou attendre",
  "Le bon moment pour passer commande",
  "Des alternatives fiables, quand elles existent",
  "L'extension, présente au bon moment",
  "Des alertes quand le prix baisse",
  "Vos données restent chez vous · RGPD",
];

const INCLUS_NL = [
  "De beste echte prijs, voor jou gevonden",
  "Een duidelijk oordeel : nu kopen, of wachten",
  "Het juiste moment om te bestellen",
  "Betrouwbare alternatieven, wanneer die bestaan",
  "De extensie, aanwezig op het juiste moment",
  "Meldingen wanneer de prijs daalt",
  "Je gegevens blijven van jou · AVG",
];

const INCLUS_EN = [
  "The best real price, found for you",
  "A clear verdict: buy now, or wait",
  "The right moment to place your order",
  "Reliable alternatives, when they exist",
  "The extension, present at the right moment",
  "Alerts when the price drops",
  "Your data stays yours · GDPR",
];

const FAQ_FR = [
  { q: "FILON est-il vraiment 100 % gratuit ?", a: "Oui. Tout est gratuit, pour tout le monde, sans abonnement ni carte bancaire. Il n'y a pas de version payante." },
  { q: "La recommandation est-elle neutre ?", a: "Oui. Elle est calculée sur votre seul intérêt. Aucune marque ne peut acheter sa place dans un conseil FILON." },
  { q: "Vais-je devoir payer un jour ?", a: "Non. FILON est gratuit, et le restera." },
  { q: "Mes données sont-elles revendues ?", a: "Jamais. Pas de profil publicitaire, pas de revente à des tiers. Conforme RGPD par défaut." },
];

const FAQ_NL = [
  { q: "Is FILON echt 100 % gratis ?", a: "Ja. Alles is gratis, voor iedereen, zonder abonnement of bankkaart. Er is geen betaalversie." },
  { q: "Is de aanbeveling neutraal ?", a: "Ja. Ze wordt berekend op jouw belang alleen. Geen enkel merk kan zijn plaats kopen in een FILON-advies." },
  { q: "Zal ik ooit moeten betalen ?", a: "Nee. FILON is gratis, en blijft dat." },
  { q: "Worden mijn gegevens doorverkocht ?", a: "Nooit. Geen advertentieprofiel, geen doorverkoop aan derden. AVG-conform standaard." },
];

const FAQ_EN = [
  { q: "Is FILON really 100% free ?", a: "Yes. Everything is free, for everyone, with no subscription or credit card. There is no paid version." },
  { q: "Is the recommendation neutral ?", a: "Yes. It's calculated on your interest alone. No brand can buy its place in a FILON recommendation." },
  { q: "Will I have to pay one day ?", a: "No. FILON is free, and will stay that way." },
  { q: "Is my data resold ?", a: "Never. No advertising profile, no reselling to third parties. GDPR-compliant by default." },
];

function Plan({ tag, price, lede, items, chromeLabel }: { tag: string; price: React.ReactNode; lede: string; items: string[]; chromeLabel: string }) {
  return (
    <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
      <div className="ed-wrap">
        <Reveal>
          <div className="ed-plan featured" style={{ maxWidth: 620, margin: "0 auto" }}>
            <span className="tag">{tag}</span>
            <div className="name">Filon</div>
            <div className="price">{price}</div>
            <p className="lede">{lede}</p>
            <ul>
              {items.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            <div className="cta-wrap">
              <ChromeCta variant="wave" label={chromeLabel} style={{ textDecoration: "none" }} />
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

function TarifsFR() {
  return (
    <>
      <ContentHero
        eyebrow="Tarifs"
        title={<>Gratuit. Pour tout le monde. <span className="it">Pour toujours.</span></>}
        intro="Pas d'abonnement, pas de version premium, pas de carte bancaire. FILON est entièrement gratuit, et le restera."
        breadcrumb={[{ name: "Tarifs", path: "/tarifs" }]}
      />
      <Plan
        tag="Le seul plan qui existe"
        price={<>0€ <small>/ pour toujours · sans carte bancaire</small></>}
        lede="Tout FILON. Décrivez un besoin, obtenez le meilleur prix réel et le verdict « acheter ou attendre », à chaque achat."
        items={INCLUS_FR}
        chromeLabel="Ajouter à Chrome"
      />
      <p style={{ textAlign: "center", color: "var(--ink-3)", fontSize: 13.5, marginTop: -20 }}>
        Le prix chez le marchand est le même avec ou sans FILON. Vous ne payez jamais.
      </p>
      <ProseBlock heading={<>Gratuit, sans <span className="it">arrière-pensée</span>.</>} alt>
        <p>
          Gratuit ne veut pas dire au rabais. FILON est complet, sans version payante cachée, sans publicité. Vous ne
          payez jamais.
        </p>
        <p>
          Et vos données ne sont pas à vendre. Le conseil que vous recevez ne sert qu&apos;une chose : votre intérêt.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_FR} eyebrow="Tarifs · FAQ" title="Ce que « gratuit » veut vraiment dire." />
      <ClosingCta title={<>Commencez, c&apos;est <span className="it">gratuit</span>.</>} sub="Sans abonnement ni carte bancaire. Vraiment." />
    </>
  );
}

function TarifsNL() {
  return (
    <>
      <ContentHero
        eyebrow="Tarieven"
        title={<>Gratis. Voor iedereen. <span className="it">Voor altijd.</span></>}
        intro="Geen abonnement, geen premiumversie, geen bankkaart. FILON is volledig gratis, en blijft dat."
        breadcrumb={[{ name: "Tarieven", path: "/tarifs" }]}
      />
      <Plan
        tag="Het enige plan dat bestaat"
        price={<>0€ <small>/ voor altijd · zonder bankkaart</small></>}
        lede="Heel FILON. Beschrijf een behoefte, krijg de beste echte prijs en het oordeel « kopen of wachten », bij elke aankoop."
        items={INCLUS_NL}
        chromeLabel="Toevoegen aan Chrome"
      />
      <p style={{ textAlign: "center", color: "var(--ink-3)", fontSize: 13.5, marginTop: -20 }}>
        De prijs bij de winkel is dezelfde met of zonder FILON. Je betaalt nooit.
      </p>
      <ProseBlock heading={<>Gratis, zonder <span className="it">bijbedoeling</span>.</>} alt>
        <p>
          Gratis betekent niet minderwaardig. FILON is volledig, zonder verborgen betaalversie, zonder reclame. Je
          betaalt nooit.
        </p>
        <p>
          En je gegevens staan niet te koop. Het advies dat je krijgt dient maar één ding : jouw belang.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_NL} eyebrow="Tarieven · FAQ" title="Wat « gratis » echt betekent." />
      <ClosingCta title={<>Begin, het is <span className="it">gratis</span>.</>} sub="Zonder abonnement of bankkaart. Echt." />
    </>
  );
}

function TarifsEN() {
  return (
    <>
      <ContentHero
        eyebrow="Pricing"
        title={<>Free. For everyone. <span className="it">Forever.</span></>}
        intro="No subscription, no premium version, no credit card. FILON is entirely free, and will stay that way."
        breadcrumb={[{ name: "Pricing", path: "/tarifs" }]}
      />
      <Plan
        tag="The only plan there is"
        price={<>€0 <small>/ forever · no credit card</small></>}
        lede="All of FILON. Describe a need, get the best real price and the « buy or wait » verdict, on every purchase."
        items={INCLUS_EN}
        chromeLabel="Add to Chrome"
      />
      <p style={{ textAlign: "center", color: "var(--ink-3)", fontSize: 13.5, marginTop: -20 }}>
        The price at the merchant is the same with or without FILON. You never pay.
      </p>
      <ProseBlock heading={<>Free, with no <span className="it">ulterior motive</span>.</>} alt>
        <p>
          Free doesn&apos;t mean second-rate. FILON is complete, with no hidden paid version, no advertising. You
          never pay.
        </p>
        <p>
          And your data isn&apos;t for sale. The advice you receive serves one thing only: your interest.
        </p>
      </ProseBlock>
      <FaqBlock items={FAQ_EN} eyebrow="Pricing · FAQ" title="What « free » really means." />
      <ClosingCta title={<>Get started, it&apos;s <span className="it">free</span>.</>} sub="No subscription or credit card. Really." />
    </>
  );
}

export default function TarifsPage() {
  return <Localized fr={<TarifsFR />} nl={<TarifsNL />} en={<TarifsEN />} />;
}
