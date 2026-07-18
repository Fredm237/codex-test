import { faqSchema, JsonLd } from "@/lib/seo";
import { Reveal } from "./Reveal";

export const FAQ_ITEMS = [
  {
    q: "FILON est-il vraiment gratuit ?",
    a: "Oui, totalement et pour toujours. FILON se rémunère via une part de la commission d'apport versée par les plateformes partenaires quand vous activez une offre — jamais en vous facturant, ni en revendant vos données.",
  },
  {
    q: "Comment FILON choisit-il l'offre à recommander ?",
    a: "Il calcule le coût réel total (prix, cashback, code promo, livraison, garantie) et le croise avec la fiabilité du vendeur. La recommandation est celle qui vous fait économiser le plus, indépendamment de ce que FILON gagne.",
  },
  {
    q: "Le reconditionné proposé est-il fiable ?",
    a: "FILON ne propose que du reconditionné de grade vérifié, issu de vendeurs certifiés et garanti 12 à 24 mois. Vous voyez le grade, la garantie et l'économie avant de décider.",
  },
  {
    q: "Mes données de navigation sont-elles revendues ?",
    a: "Jamais. Pas de profil publicitaire, pas de revente à des tiers. FILON n'analyse que ce qui est nécessaire à la comparaison, conforme RGPD par défaut.",
  },
  {
    q: "Quand l'extension et l'application arrivent-elles ?",
    a: "L'extension Chrome d'abord, puis Edge, Firefox, Safari, l'application mobile et l'assistant conversationnel. Ajoutez FILON pour être prévenu·e du lancement.",
  },
];

export function Faq() {
  return (
    <section className="ed-band" id="faq">
      <JsonLd data={faqSchema(FAQ_ITEMS.map((i) => ({ q: i.q, a: i.a })))} />
      <div className="ed-wrap">
        <Reveal>
          <div className="ed-lead">
            <span className="idx">FAQ</span>
            <h2>Les questions que vous vous posez.</h2>
          </div>
        </Reveal>
        <div className="ed-faq">
          {FAQ_ITEMS.map((it) => (
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
