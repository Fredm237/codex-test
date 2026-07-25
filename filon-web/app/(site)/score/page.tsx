import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { Reveal } from "@/components/editorial/Reveal";

export const metadata: Metadata = buildMetadata({
  path: "/score",
  title: "Le Score FILON",
  description:
    "Comment FILON calcule le Score : prix vs historique, fiabilité du marchand, avis vérifiés, livraison et cashback. Une note neutre, jamais achetée.",
});

const CRITERIA: Array<[string, string, string]> = [
  [
    "35 %",
    "Prix vs son propre historique",
    "On compare le prix du jour à sa moyenne récente. Un prix bas dans l'absolu, mais qui n'a jamais été aussi cher, perd des points.",
  ],
  [
    "25 %",
    "Fiabilité du marchand",
    "Réputation, service après-vente, délais tenus, politique de retour. Un prix bas chez un vendeur douteux n'est pas une bonne affaire.",
  ],
  [
    "20 %",
    "Avis produit vérifiés",
    "Volume et qualité des avis, pondérés pour écarter les faux. On regarde la satisfaction réelle, pas la note brute.",
  ],
  [
    "12 %",
    "Livraison et garantie",
    "Délai, frais de port réels et durée de garantie inclus dans le prix total, pas seulement l'étiquette affichée.",
  ],
  [
    "8 %",
    "Coupons et cashback cumulables",
    "Réductions et cashback réellement applicables à cet achat, une fois vérifiés au paiement.",
  ],
];

const NEVERS: Array<[string, string]> = [
  ["Vendre une place", "Aucune marque, aucun marchand ne peut acheter un meilleur score."],
  ["Gonfler une offre affiliée", "Un lien qui nous rémunère n'obtient pas un point de plus."],
  ["Cacher le raisonnement", "Chaque score se décompose, ligne par ligne, dans le détail de l'offre."],
];

export default function ScorePage() {
  return (
    <>
      <section className="ed-content-hero">
        <div className="ed-wrap">
          <span className="eyebrow" style={{ display: "block", marginBottom: 22 }}>
            Transparence
          </span>
          <h1>
            Comment se calcule le <span className="it">Score FILON</span>.
          </h1>
          <p className="intro">
            Une note sur 100, unique par offre. Elle répond à une seule question :{" "}
            <b>est-ce un bon achat, maintenant ?</b> Voici exactement ce qu'elle mesure,
            et ce qu'elle ne mesure pas.
          </p>
        </div>
      </section>

      <section className="ed-band">
        <div className="ed-wrap">
          <Reveal className="ed-lead">
            <span className="idx">5 critères</span>
            <h2>
              Le calcul, <span className="it">poids par poids</span>.
            </h2>
          </Reveal>
          <div className="ed-infogrid">
            {CRITERIA.map(([weight, title, desc]) => (
              <div className="ed-info" key={title}>
                <div className="n">{weight}</div>
                <h3>{title}</h3>
                <p>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="ed-band alt">
        <div className="ed-wrap ed-prose">
          <h2>
            Ce que le Score ne fait <span className="it">jamais</span>.
          </h2>
          {NEVERS.map(([head, body]) => (
            <p key={head}>
              <b>{head}.</b> {body}
            </p>
          ))}
          <p style={{ color: "var(--ink-3)", fontSize: 14 }}>
            Tant que nos partenariats marchands ne sont pas signés, certaines composantes
            (cashback, historique long) reposent sur des estimations, clairement signalées.
            Le Score deviendra pleinement chiffré à mesure que les données réelles arrivent.
          </p>
        </div>
      </section>
    </>
  );
}
