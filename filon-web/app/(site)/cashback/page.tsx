import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";

export const metadata: Metadata = buildMetadata({
  path: "/cashback",
  title: "Cashback : de l'argent qui revient",
  description:
    "Avec FILON, récupérez le maximum sur vos achats, automatiquement. Sans chercher, sans comparer.",
});

const FAQ = [
  { q: "Le cashback, c'est quoi au juste ?", a: "Une partie de votre achat qui vous revient après coup. Avec FILON, vous obtenez le maximum, sans rien faire." },
  { q: "Dois-je comparer moi-même ?", a: "Non. FILON trouve la meilleure offre du moment à votre place, et vous y emmène." },
  { q: "C'est cumulable avec une promo ?", a: "Souvent oui. FILON vous indique simplement le meilleur prix final." },
  { q: "Quand est-ce que je le reçois ?", a: "Selon la boutique, de quelques jours à quelques semaines. FILON vous indique les conditions avant que vous ne décidiez." },
];

export default function CashbackPage() {
  return (
    <>
      <ContentHero
        eyebrow="Cashback"
        title={<>De l&apos;argent qui revient. À chaque <span className="it">achat</span>.</>}
        intro="Sur beaucoup d'achats, une partie de la somme peut vous revenir. FILON récupère le maximum pour vous, automatiquement. Vous n'avez rien à chercher."
        breadcrumb={[{ name: "Cashback", path: "/cashback" }]}
      />

      <ProseBlock heading={<>L&apos;argent que vous oubliez de <span className="it">récupérer</span>.</>}>
        <p>
          Beaucoup de gens laissent cet argent sur la table, simplement par manque de temps. C&apos;est dommage, et
          c&apos;est évitable.
        </p>
        <p>
          FILON s&apos;en occupe. Au bon moment, il vous obtient la meilleure offre et vous encaissez plus. Vous gardez
          vos habitudes, vous payez moins.
        </p>
      </ProseBlock>

      <FaqBlock items={FAQ} eyebrow="Cashback · FAQ" title="Le cashback, sans zone d'ombre." />
      <ClosingCta title={<>Ne cliquez plus jamais « payer » <span className="it">sans</span> FILON.</>} sub="Il s'en occupe pour vous, gratuitement, à chaque achat." />
    </>
  );
}
