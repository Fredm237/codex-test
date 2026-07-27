"use client";

import { faqSchema, JsonLd } from "@/lib/seo";
import { Reveal } from "./Reveal";
import { useLocale } from "@/lib/i18n";

export type QA = { q: string; a: string };

export const HOME_FAQ: QA[] = [
  {
    q: "FILON est-il vraiment gratuit ?",
    a: "Oui, entièrement. Aucune carte, aucun abonnement, aucune option payante. Et vos données ne sont jamais revendues.",
  },
  {
    q: "Puis-je faire confiance à sa recommandation ?",
    a: "Elle sert votre intérêt, jamais le nôtre. Aucune marque ne peut acheter sa place. FILON vous indique ce qui est vraiment le mieux pour vous.",
  },
  {
    q: "Le reconditionné proposé est-il fiable ?",
    a: "Uniquement du reconditionné vérifié, chez des vendeurs certifiés, sous garantie. Vous voyez la garantie et l'économie avant de décider.",
  },
  {
    q: "Mes données sont-elles revendues ?",
    a: "Jamais. Pas de profil publicitaire, pas de revente. FILON en garde le moins possible, et rien d'autre.",
  },
  {
    q: "Quand arrivent l'extension et l'application ?",
    a: "L'extension d'abord, puis l'application mobile et l'assistant. Ajoutez FILON pour être prévenu.",
  },
];

const HOME_FAQ_NL: QA[] = [
  { q: "Is FILON echt gratis?", a: "Ja, volledig. Geen kaart, geen abonnement, geen betaalde opties. En je gegevens worden nooit doorverkocht." },
  { q: "Kan ik zijn aanbeveling vertrouwen?", a: "Ze dient jouw belang, nooit het onze. Geen enkel merk kan zijn plaats kopen. FILON toont je wat echt het beste is voor jou." },
  { q: "Is het aangeboden refurbished betrouwbaar?", a: "Alleen geverifieerd refurbished, bij gecertificeerde verkopers, met garantie. Je ziet de garantie en de besparing voordat je beslist." },
  { q: "Worden mijn gegevens doorverkocht?", a: "Nooit. Geen advertentieprofiel, geen doorverkoop. FILON bewaart zo weinig mogelijk, en niets anders." },
  { q: "Wanneer komen de extensie en de app?", a: "Eerst de extensie, daarna de mobiele app en de assistent. Voeg FILON toe om verwittigd te worden." },
];

const HOME_FAQ_EN: QA[] = [
  { q: "Is FILON really free?", a: "Yes, entirely. No card, no subscription, no paid options. And your data is never resold." },
  { q: "Can I trust its recommendation?", a: "It serves your interest, never ours. No brand can buy its place. FILON shows you what's genuinely best for you." },
  { q: "Is the refurbished offered reliable?", a: "Only verified refurbished, from certified sellers, under warranty. You see the warranty and the saving before you decide." },
  { q: "Is my data resold?", a: "Never. No advertising profile, no reselling. FILON keeps as little as possible, and nothing else." },
  { q: "When do the extension and the app arrive?", a: "The extension first, then the mobile app and the assistant. Add FILON to be notified." },
];

export function FaqBlock({
  items,
  id = "faq",
  eyebrow = "FAQ",
  title = "Les questions que vous vous posez.",
}: {
  items: QA[];
  id?: string;
  eyebrow?: string;
  title?: string;
}) {
  return (
    <section className="ed-band" id={id}>
      <JsonLd data={faqSchema(items)} />
      <div className="ed-wrap">
        <Reveal>
          <div className="ed-lead">
            <span className="idx">{eyebrow}</span>
            <h2>{title}</h2>
          </div>
        </Reveal>
        <div className="ed-faq">
          {items.map((it) => (
            <details className="ed-qa" key={it.q}>
              <summary>
                {it.q}
                <span className="pl" aria-hidden="true" />
              </summary>
              <div className="a">{it.a}</div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Faq() {
  const { locale } = useLocale();
  const items = locale === "nl" ? HOME_FAQ_NL : locale === "en" ? HOME_FAQ_EN : HOME_FAQ;
  const title =
    locale === "nl" ? "De vragen die je je stelt." : locale === "en" ? "The questions you're asking." : "Les questions que vous vous posez.";
  return <FaqBlock items={items} title={title} />;
}
