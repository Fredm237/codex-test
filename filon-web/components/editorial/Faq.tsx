import { faqSchema, JsonLd } from "@/lib/seo";
import { Reveal } from "./Reveal";

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
