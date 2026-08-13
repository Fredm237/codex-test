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
  { q: "C'est quoi FILON, en une phrase ?", a: "Un copilote d'achat qui recherche des offres dans le catalogue FILON et les met en regard pour vous aider à choisir." },
  { q: "En quoi c'est différent d'une simple comparaison ?", a: "FILON réunit les informations disponibles sur une offre — prix affiché, cashback et codes promo lorsqu'ils sont renseignés — afin de rendre la comparaison plus lisible. Vous gardez toujours le dernier mot." },
  { q: "FILON est-il vraiment gratuit ?", a: "Oui. L'accès au catalogue et à l'assistant ne demande ni abonnement ni carte bancaire. Il n'existe actuellement pas de formule payante." },
];

const CONFIANCE_FR = [
  { q: "Puis-je faire confiance à la recommandation ?", a: "FILON s'appuie sur les informations présentes dans son catalogue et affiche ce qu'il sait d'une offre. Vérifiez toujours le prix, la disponibilité et les conditions du marchand avant de commander." },
  { q: "Mes données de navigation sont-elles revendues ?", a: "Non. FILON ne revend pas vos données de navigation. Les détails sur les données traitées et vos droits sont disponibles dans notre politique de confidentialité." },
  { q: "Le reconditionné proposé est-il fiable ?", a: "Une offre reconditionnée peut apparaître lorsqu'elle est référencée dans le catalogue. L'état, la garantie, le retour et le vendeur varient selon l'offre : vérifiez-les directement avant l'achat." },
];

const PRODUIT_FR = [
  { q: "Le cashback, ça change quoi pour moi ?", a: "Quand une offre indique du cashback, FILON l'affiche avec les autres informations disponibles. Son attribution et ses conditions dépendent du marchand et du lien utilisé." },
  { q: "Quand l'extension et l'application arrivent-elles ?", a: "Le catalogue et l'assistant sont déjà accessibles sur le site. L'extension Chrome attend sa publication ; toute nouvelle expérience mobile sera annoncée lorsqu'elle sera disponible." },
  { q: "FILON fonctionne-t-il en dehors de la Belgique ?", a: "Le catalogue rassemble des marchands partenaires actifs dans plusieurs pays. La disponibilité d'une offre dépend toutefois de la zone de livraison et des conditions du marchand." },
];

const GENERAL_NL = [
  { q: "Wat is FILON, in één zin ?", a: "Een koopcopiloot die aanbiedingen in de FILON-catalogus opzoekt en naast elkaar zet om je te helpen kiezen." },
  { q: "Waarin verschilt het van een simpele vergelijking ?", a: "FILON bundelt de beschikbare informatie over een aanbod — getoonde prijs, cashback en kortingscodes wanneer die vermeld zijn — zodat vergelijken duidelijker wordt. Jij houdt altijd het laatste woord." },
  { q: "Is FILON echt gratis ?", a: "Ja. Voor de catalogus en de assistent heb je geen abonnement of bankkaart nodig. Er is momenteel geen betalende formule." },
];

const CONFIANCE_NL = [
  { q: "Kan ik de aanbeveling vertrouwen ?", a: "FILON gebruikt de informatie die in zijn catalogus aanwezig is en toont wat het over een aanbod weet. Controleer vóór je bestelt altijd de prijs, beschikbaarheid en voorwaarden van de winkel." },
  { q: "Worden mijn surfgegevens doorverkocht ?", a: "Nee. FILON verkoopt je surfgegevens niet. Details over verwerkte gegevens en je rechten vind je in ons privacybeleid." },
  { q: "Is de aangeboden refurbished betrouwbaar ?", a: "Een refurbished aanbod kan verschijnen wanneer het in de catalogus is opgenomen. De staat, garantie, retour en verkoper verschillen per aanbod: controleer die rechtstreeks vóór je koopt." },
];

const PRODUIT_NL = [
  { q: "Wat verandert de cashback voor mij ?", a: "Wanneer een aanbod cashback vermeldt, toont FILON die naast de andere beschikbare informatie. Toekenning en voorwaarden hangen af van de winkel en de gebruikte link." },
  { q: "Wanneer komen de extensie en de applicatie ?", a: "De catalogus en de assistent zijn al beschikbaar op de website. De Chrome-extensie wacht op publicatie; een nieuwe mobiele ervaring wordt aangekondigd zodra die beschikbaar is." },
  { q: "Werkt FILON buiten België ?", a: "De catalogus verzamelt partnerwinkels die actief zijn in verschillende landen. De beschikbaarheid van een aanbod hangt echter af van de leveringszone en voorwaarden van de winkel." },
];

const GENERAL_EN = [
  { q: "What is FILON, in one sentence ?", a: "A shopping copilot that searches offers in the FILON catalogue and puts them side by side to help you choose." },
  { q: "How is it different from a simple comparison ?", a: "FILON brings together the information available for an offer — displayed price, cashback and promo codes when listed — to make comparison clearer. You always keep the final say." },
  { q: "Is FILON really free ?", a: "Yes. Access to the catalogue and assistant requires no subscription or card. There is currently no paid plan." },
];

const CONFIANCE_EN = [
  { q: "Can I trust the recommendation ?", a: "FILON relies on the information available in its catalogue and shows what it knows about an offer. Always check a merchant's price, availability and terms before ordering." },
  { q: "Is my browsing data resold ?", a: "No. FILON does not resell your browsing data. Our privacy policy explains the data processed and your rights." },
  { q: "Is the refurbished offered reliable ?", a: "A refurbished offer may appear when it is listed in the catalogue. Its condition, warranty, returns and seller vary by offer, so check them directly before buying." },
];

const PRODUIT_EN = [
  { q: "What does cashback change for me ?", a: "When an offer lists cashback, FILON displays it alongside the other available information. Its attribution and conditions depend on the merchant and the link used." },
  { q: "When do the extension and the app arrive ?", a: "The catalogue and assistant are already available on the website. The Chrome extension is awaiting publication; a new mobile experience will be announced when it is available." },
  { q: "Does FILON work outside Belgium ?", a: "The catalogue includes partner merchants active in several countries. An offer's availability still depends on the merchant's delivery area and terms." },
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

function FaqEN() {
  return (
    <>
      <ContentHero
        eyebrow="FAQ"
        title={<>Your questions, our <span className="it">clear</span> answers.</>}
        intro="What FILON does, why it's free, what we do with your data. The real questions, and honest answers."
        breadcrumb={[{ name: "FAQ", path: "/faq" }]}
      />
      <FaqBlock items={GENERAL_EN} id="general" eyebrow="General" title="The essentials." />
      <FaqBlock items={CONFIANCE_EN} id="confiance" eyebrow="Trust & data" title="Trust and privacy." />
      <FaqBlock items={PRODUIT_EN} id="produit" eyebrow="Product" title="Refurbished, extension, availability." />
      <ClosingCta title={<>Another <span className="it">question</span> ?</>} sub="Write to us. We reply fast, and by a human." />
    </>
  );
}

export default function FaqPage() {
  return <Localized fr={<FaqFR />} nl={<FaqNL />} en={<FaqEN />} />;
}
