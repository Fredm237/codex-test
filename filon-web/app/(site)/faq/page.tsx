import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";

export const metadata: Metadata = buildMetadata({
  path: "/faq",
  title: "Questions fréquentes",
  description:
    "Ce qu'est FILON, pourquoi c'est gratuit, ce qu'il fait de vos données, le reconditionné, l'extension. Les réponses, sans jargon.",
});

const GENERAL = [
  { q: "C'est quoi FILON, en une phrase ?", a: "Un assistant d'achat. Vous lui dites ce que vous cherchez, il vous dit quoi acheter, où, et si c'est le bon moment." },
  { q: "En quoi c'est différent d'une simple comparaison ?", a: "Une comparaison vous donne une liste et vous laisse trancher. FILON tranche pour vous : une réponse claire, « voici ce que vous devriez acheter »." },
  { q: "FILON est-il vraiment gratuit ?", a: "Oui, entièrement, pour tout le monde, sans abonnement ni carte bancaire. Il n'y a pas de version payante." },
];

const CONFIANCE = [
  { q: "Puis-je faire confiance à la recommandation ?", a: "Elle est calculée sur votre seul intérêt. Aucune marque ne peut acheter sa place. FILON vous indique ce qui est vraiment le mieux pour vous." },
  { q: "Mes données de navigation sont-elles revendues ?", a: "Jamais. Pas de profil publicitaire, pas de revente à des tiers. FILON en garde le moins possible, conforme RGPD par défaut." },
  { q: "Le reconditionné proposé est-il fiable ?", a: "Uniquement du reconditionné vérifié, chez des vendeurs certifiés et sous garantie. Vous voyez la garantie et l'économie avant de décider." },
];

const PRODUIT = [
  { q: "Le cashback, ça change quoi pour moi ?", a: "FILON trouve la meilleure offre du moment et vous y emmène. Vous n'avez rien à chercher, ni à comparer." },
  { q: "Quand l'extension et l'application arrivent-elles ?", a: "L'extension d'abord, puis l'application mobile et l'assistant. Ajoutez FILON pour être prévenu à chaque lancement." },
  { q: "FILON fonctionne-t-il en dehors de la Belgique ?", a: "Nous commençons par la Belgique francophone, puis la France et le reste de la francophonie européenne." },
];

export default function FaqPage() {
  return (
    <>
      <ContentHero
        eyebrow="FAQ"
        title={<>Vos questions, nos réponses <span className="it">claires</span>.</>}
        intro="Ce que fait FILON, pourquoi c'est gratuit, ce qu'on fait de vos données. Les vraies questions, et des réponses franches."
        breadcrumb={[{ name: "FAQ", path: "/faq" }]}
      />
      <FaqBlock items={GENERAL} id="general" eyebrow="Général" title="L'essentiel." />
      <FaqBlock items={CONFIANCE} id="confiance" eyebrow="Confiance & données" title="Confiance et vie privée." />
      <FaqBlock items={PRODUIT} id="produit" eyebrow="Produit" title="Reconditionné, extension, disponibilité." />
      <ClosingCta title={<>Une autre <span className="it">question</span> ?</>} sub="Écrivez-nous. On répond vite, et par un humain." />
    </>
  );
}
