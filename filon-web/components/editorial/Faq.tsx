import { faqSchema, JsonLd } from "@/lib/seo";
import { Reveal } from "./Reveal";

export type QA = { q: string; a: string };

export const HOME_FAQ: QA[] = [
  {
    q: "FILON est-il vraiment gratuit ?",
    a: "Oui, et pour de bon. Nous touchons une part de la commission que la plateforme partenaire verse quand vous activez une offre. Vous ne payez rien, et nous ne revendons pas vos données.",
  },
  {
    q: "Comment FILON choisit-il l'offre à recommander ?",
    a: "Il additionne tout ce que vous payez vraiment, prix, cashback, code promo, livraison et garantie, puis regarde la fiabilité du vendeur. Il recommande ce qui vous coûte le moins, pas ce qui lui rapporte le plus.",
  },
  {
    q: "Le reconditionné proposé est-il fiable ?",
    a: "Nous ne montrons que du reconditionné vérifié, chez des vendeurs certifiés, garanti 12 à 24 mois. Vous voyez le grade, la garantie et l'économie avant de décider.",
  },
  {
    q: "Mes données de navigation sont-elles revendues ?",
    a: "Jamais. Pas de profil publicitaire, pas de revente. FILON ne lit que ce qu'il faut pour comparer, et rien d'autre.",
  },
  {
    q: "Quand l'extension et l'application arrivent-elles ?",
    a: "L'extension Chrome en premier, puis Edge, Firefox et Safari. L'application mobile et l'assistant suivront. Ajoutez FILON pour savoir quand.",
  },
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
  return <FaqBlock items={HOME_FAQ} />;
}
