import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";

export const metadata: Metadata = buildMetadata({
  path: "/faq",
  title: "FAQ — toutes vos questions sur FILON",
  description:
    "Comment fonctionne le copilote d'achat FILON, comment il gagne de l'argent (sans vous facturer), ce qu'il fait de vos données, le cashback, le reconditionné et l'extension. Toutes les réponses, sans jargon.",
});

const GENERAL = [
  { q: "C'est quoi FILON, en une phrase ?", a: "Un copilote d'achat : vous lui dites ce que vous cherchez, il analyse le marché (prix, cashback, reconditionné, codes promo, fiabilité, historique) et vous dit quoi acheter, où, et si c'est le bon moment." },
  { q: "En quoi c'est différent d'un comparateur ?", a: "Un comparateur affiche une liste de prix et vous laisse trancher. FILON va plus loin : il calcule le coût réel total, croise les sources d'économie et vous donne une recommandation claire — « voici ce que vous devriez acheter », pas seulement « voici les prix »." },
  { q: "FILON est-il vraiment gratuit ?", a: "Oui, totalement — pour tout le monde, pour toujours, sans abonnement ni carte bancaire. Il n'y a pas de version payante. FILON se rémunère uniquement via une part de la commission d'apport des plateformes partenaires quand vous activez une offre, jamais en vous facturant." },
  { q: "Comment FILON gagne-t-il de l'argent, alors ?", a: "Via une part de la commission d'apport que les plateformes partenaires nous reversent quand vous activez une offre. Cela n'augmente jamais votre prix. Et la recommandation reste celle qui vous fait économiser le plus, pas celle qui nous rapporte le plus." },
];

const CONFIANCE = [
  { q: "La recommandation est-elle influencée par ce que FILON gagne ?", a: "Non. Le verdict est calculé sur votre intérêt : coût réel le plus bas et fiabilité du vendeur. Notre rémunération est signalée en toute transparence — c'est notre modèle, pas un argument marketing." },
  { q: "Mes données de navigation sont-elles revendues ?", a: "Jamais. Pas de profil publicitaire, pas de revente à des tiers. FILON n'analyse que ce qui est nécessaire à la comparaison, conforme RGPD par défaut. Détails dans notre politique de confidentialité." },
  { q: "Le reconditionné proposé est-il fiable ?", a: "FILON ne propose que du reconditionné de grade vérifié, issu de vendeurs certifiés et garanti 12 à 24 mois. Vous voyez le grade, la garantie et l'économie avant de décider." },
];

const PRODUIT = [
  { q: "Comment fonctionne le cashback ?", a: "FILON compare les taux d'iGraal, Poulpeo, Widilo, Joko, eBuyClub et d'autres pour votre marchand, puis vous oriente vers le plus rémunérateur. Il teste aussi le cumul avec un code promo quand c'est possible." },
  { q: "Quand l'extension et l'application arrivent-elles ?", a: "L'extension Chrome d'abord, puis Edge, Firefox, Safari, l'application mobile et l'assistant conversationnel. Ajoutez FILON pour être prévenu·e à chaque lancement." },
  { q: "FILON fonctionne-t-il en dehors de la Belgique ?", a: "Nous commençons par la Belgique francophone, puis la France et le reste de la francophonie européenne. Les marchands et plateformes couverts s'étendent au fil des versions." },
];

export default function FaqPage() {
  return (
    <>
      <ContentHero
        eyebrow="FAQ"
        title={<>Vos questions, nos réponses <span className="it">claires</span>.</>}
        intro="Le fonctionnement du copilote, notre modèle économique, vos données, le cashback, le reconditionné et l'extension — tout ce qu'il faut savoir avant de faire de FILON votre réflexe d'achat."
        breadcrumb={[{ name: "FAQ", path: "/faq" }]}
      />
      <FaqBlock items={GENERAL} id="general" eyebrow="Général" title="L'essentiel." />
      <FaqBlock items={CONFIANCE} id="confiance" eyebrow="Confiance & données" title="Transparence et vie privée." />
      <FaqBlock items={PRODUIT} id="produit" eyebrow="Produit" title="Cashback, reconditionné, extension." />
      <ClosingCta title={<>Une autre <span className="it">question</span> ?</>} sub="Écrivez-nous, on répond vite — et humainement." />
    </>
  );
}
