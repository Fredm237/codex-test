import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/faq",
  title: "Questions fréquentes",
  description:
    "Ce qu'est FILON, pourquoi c'est gratuit, ce qu'il fait de vos données, le reconditionné, l'extension. Les réponses, sans jargon.",
});

const GENERAL_FR = [
  { q: "C'est quoi FILON, en une phrase ?", a: "Un assistant d'achat. Vous lui dites ce que vous cherchez, il vous dit quoi acheter, où, et si c'est le bon moment." },
  { q: "En quoi c'est différent d'une simple comparaison ?", a: "Une comparaison vous donne une liste et vous laisse trancher. FILON tranche pour vous : une réponse claire, « voici ce que vous devriez acheter »." },
  { q: "FILON est-il vraiment gratuit ?", a: "Oui, entièrement, pour tout le monde, sans abonnement ni carte bancaire. Il n'y a pas de version payante." },
];

const CONFIANCE_FR = [
  { q: "Puis-je faire confiance à la recommandation ?", a: "Elle est calculée sur votre seul intérêt. Aucune marque ne peut acheter sa place. FILON vous indique ce qui est vraiment le mieux pour vous." },
  { q: "Mes données de navigation sont-elles revendues ?", a: "Jamais. Pas de profil publicitaire, pas de revente à des tiers. FILON en garde le moins possible, conforme RGPD par défaut." },
  { q: "Le reconditionné proposé est-il fiable ?", a: "Uniquement du reconditionné vérifié, chez des vendeurs certifiés et sous garantie. Vous voyez la garantie et l'économie avant de décider." },
];

const PRODUIT_FR = [
  { q: "Le cashback, ça change quoi pour moi ?", a: "FILON trouve la meilleure offre du moment et vous y emmène. Vous n'avez rien à chercher, ni à comparer." },
  { q: "Quand l'extension et l'application arrivent-elles ?", a: "L'extension d'abord, puis l'application mobile et l'assistant. Ajoutez FILON pour être prévenu à chaque lancement." },
  { q: "FILON fonctionne-t-il en dehors de la Belgique ?", a: "Nous commençons par la Belgique francophone, puis la France et le reste de la francophonie européenne." },
];

const GENERAL_NL = [
  { q: "Wat is FILON, in één zin ?", a: "Een koopassistent. Je zegt hem wat je zoekt, hij zegt je wat te kopen, waar, en of het het juiste moment is." },
  { q: "Waarin verschilt het van een simpele vergelijking ?", a: "Een vergelijking geeft je een lijst en laat je zelf beslissen. FILON beslist voor jou : een duidelijk antwoord, « dit zou je moeten kopen »." },
  { q: "Is FILON echt gratis ?", a: "Ja, volledig, voor iedereen, zonder abonnement of bankkaart. Er is geen betalende versie." },
];

const CONFIANCE_NL = [
  { q: "Kan ik de aanbeveling vertrouwen ?", a: "Ze wordt berekend op jouw belang alleen. Geen enkel merk kan zijn plaats kopen. FILON toont je wat echt het beste voor je is." },
  { q: "Worden mijn surfgegevens doorverkocht ?", a: "Nooit. Geen advertentieprofiel, geen doorverkoop aan derden. FILON bewaart zo weinig mogelijk, GDPR-conform standaard." },
  { q: "Is de aangeboden refurbished betrouwbaar ?", a: "Alleen geverifieerde refurbished, bij gecertificeerde verkopers en onder garantie. Je ziet de garantie en de besparing vóór je beslist." },
];

const PRODUIT_NL = [
  { q: "Wat verandert de cashback voor mij ?", a: "FILON vindt het beste aanbod van het moment en brengt je erheen. Je hoeft niets te zoeken, noch te vergelijken." },
  { q: "Wanneer komen de extensie en de applicatie ?", a: "De extensie eerst, daarna de mobiele app en de assistent. Voeg FILON toe om bij elke lancering verwittigd te worden." },
  { q: "Werkt FILON buiten België ?", a: "We beginnen met Franstalig België, daarna Frankrijk en de rest van de Europese francofonie." },
];

function FaqFR() {
  return (
    <>
      <ContentHero
        eyebrow="FAQ"
        title={<>Vos questions, nos réponses <span className="it">claires</span>.</>}
        intro="Ce que fait FILON, pourquoi c'est gratuit, ce qu'on fait de vos données. Les vraies questions, et des réponses franches."
        breadcrumb={[{ name: "FAQ", path: "/faq" }]}
      />
      <FaqBlock items={GENERAL_FR} id="general" eyebrow="Général" title="L'essentiel." />
      <FaqBlock items={CONFIANCE_FR} id="confiance" eyebrow="Confiance & données" title="Confiance et vie privée." />
      <FaqBlock items={PRODUIT_FR} id="produit" eyebrow="Produit" title="Reconditionné, extension, disponibilité." />
      <ClosingCta title={<>Une autre <span className="it">question</span> ?</>} sub="Écrivez-nous. On répond vite, et par un humain." />
    </>
  );
}

function FaqNL() {
  return (
    <>
      <ContentHero
        eyebrow="FAQ"
        title={<>Je vragen, onze <span className="it">heldere</span> antwoorden.</>}
        intro="Wat FILON doet, waarom het gratis is, wat we met je gegevens doen. De echte vragen, en eerlijke antwoorden."
        breadcrumb={[{ name: "FAQ", path: "/faq" }]}
      />
      <FaqBlock items={GENERAL_NL} id="general" eyebrow="Algemeen" title="Het essentiële." />
      <FaqBlock items={CONFIANCE_NL} id="confiance" eyebrow="Vertrouwen & gegevens" title="Vertrouwen en privacy." />
      <FaqBlock items={PRODUIT_NL} id="produit" eyebrow="Product" title="Refurbished, extensie, beschikbaarheid." />
      <ClosingCta title={<>Nog een <span className="it">vraag</span> ?</>} sub="Schrijf ons. We antwoorden snel, en door een mens." />
    </>
  );
}

export default function FaqPage() {
  return <Localized fr={<FaqFR />} nl={<FaqNL />} />;
}
