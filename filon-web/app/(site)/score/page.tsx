import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { Reveal } from "@/components/editorial/Reveal";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/score",
  title: "Le Score FILON",
  description:
    "Comment FILON calcule le Score : prix vs historique, fiabilité du marchand, avis vérifiés, livraison et cashback. Une note neutre, jamais achetée.",
});

const CRITERIA_FR: Array<[string, string, string]> = [
  ["35 %", "Prix vs son propre historique", "On compare le prix du jour à sa moyenne récente. Un prix bas dans l'absolu, mais qui n'a jamais été aussi cher, perd des points."],
  ["25 %", "Fiabilité du marchand", "Réputation, service après-vente, délais tenus, politique de retour. Un prix bas chez un vendeur douteux n'est pas une bonne affaire."],
  ["20 %", "Avis produit vérifiés", "Volume et qualité des avis, pondérés pour écarter les faux. On regarde la satisfaction réelle, pas la note brute."],
  ["12 %", "Livraison et garantie", "Délai, frais de port réels et durée de garantie inclus dans le prix total, pas seulement l'étiquette affichée."],
  ["8 %", "Coupons et cashback cumulables", "Réductions et cashback réellement applicables à cet achat, une fois vérifiés au paiement."],
];

const CRITERIA_NL: Array<[string, string, string]> = [
  ["35 %", "Prijs t.o.v. eigen geschiedenis", "We vergelijken de prijs van vandaag met zijn recente gemiddelde. Een op zich lage prijs die nog nooit zo hoog stond, verliest punten."],
  ["25 %", "Betrouwbaarheid van de winkel", "Reputatie, klantendienst, nagekomen termijnen, retourbeleid. Een lage prijs bij een dubieuze verkoper is geen goede zaak."],
  ["20 %", "Geverifieerde productreviews", "Volume en kwaliteit van de reviews, gewogen om valse te weren. We kijken naar echte tevredenheid, niet de ruwe score."],
  ["12 %", "Levering en garantie", "Termijn, echte verzendkosten en garantieduur inbegrepen in de totaalprijs, niet alleen het getoonde prijskaartje."],
  ["8 %", "Combineerbare codes en cashback", "Kortingen en cashback die echt toepasbaar zijn op deze aankoop, eenmaal geverifieerd bij het betalen."],
];

const NEVERS_FR: Array<[string, string]> = [
  ["Vendre une place", "Aucune marque, aucun marchand ne peut acheter un meilleur score."],
  ["Gonfler une offre affiliée", "Un lien qui nous rémunère n'obtient pas un point de plus."],
  ["Cacher le raisonnement", "Chaque score se décompose, ligne par ligne, dans le détail de l'offre."],
];

const NEVERS_NL: Array<[string, string]> = [
  ["Een plaats verkopen", "Geen enkel merk, geen enkele winkel kan een betere score kopen."],
  ["Een affiliatieaanbieding opblazen", "Een link die ons vergoedt krijgt geen punt extra."],
  ["De redenering verbergen", "Elke score wordt ontleed, regel per regel, in de details van de aanbieding."],
];

const CRITERIA_EN: Array<[string, string, string]> = [
  ["35%", "Price vs its own history", "We compare today's price to its recent average. A price that's low in absolute terms, but has never been this expensive, loses points."],
  ["25%", "Merchant reliability", "Reputation, after-sales service, deadlines met, returns policy. A low price at a dubious seller isn't a good deal."],
  ["20%", "Verified product reviews", "Volume and quality of reviews, weighted to filter out fakes. We look at real satisfaction, not the raw rating."],
  ["12%", "Delivery and warranty", "Delivery time, real shipping costs and warranty length included in the total price, not just the displayed tag."],
  ["8%", "Combinable coupons and cashback", "Discounts and cashback genuinely applicable to this purchase, once verified at checkout."],
];

const NEVERS_EN: Array<[string, string]> = [
  ["Sell a place", "No brand, no merchant can buy a better score."],
  ["Inflate an affiliate offer", "A link that pays us doesn't get one extra point."],
  ["Hide the reasoning", "Every score breaks down, line by line, in the offer's details."],
];

function ScoreBody({ t }: { t: {
  eye: string; h1a: string; h1b: string; h1c: string; introA: string; introB: string; introC: string;
  idx: string; h2a: string; h2b: string; criteria: Array<[string, string, string]>;
  neverA: string; neverB: string; nevers: Array<[string, string]>; note: string;
} }) {
  return (
    <>
      <section className="ed-content-hero">
        <div className="ed-wrap">
          <span className="eyebrow" style={{ display: "block", marginBottom: 22 }}>{t.eye}</span>
          <h1>{t.h1a} <span className="it">{t.h1b}</span>{t.h1c}</h1>
          <p className="intro">{t.introA} <b>{t.introB}</b> {t.introC}</p>
        </div>
      </section>
      <section className="ed-band">
        <div className="ed-wrap">
          <Reveal className="ed-lead">
            <span className="idx">{t.idx}</span>
            <h2>{t.h2a} <span className="it">{t.h2b}</span>.</h2>
          </Reveal>
          <div className="ed-infogrid">
            {t.criteria.map(([weight, title, desc]) => (
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
          <h2>{t.neverA} <span className="it">{t.neverB}</span>.</h2>
          {t.nevers.map(([head, body]) => (
            <p key={head}><b>{head}.</b> {body}</p>
          ))}
          <p style={{ color: "var(--ink-3)", fontSize: 14 }}>{t.note}</p>
        </div>
      </section>
    </>
  );
}

const FR = {
  eye: "Transparence", h1a: "Comment se calcule le", h1b: "Score FILON", h1c: ".",
  introA: "Une note sur 100, unique par offre. Elle répond à une seule question :",
  introB: "est-ce un bon achat, maintenant ?",
  introC: "Voici exactement ce qu'elle mesure, et ce qu'elle ne mesure pas.",
  idx: "5 critères", h2a: "Le calcul,", h2b: "poids par poids", criteria: CRITERIA_FR,
  neverA: "Ce que le Score ne fait", neverB: "jamais", nevers: NEVERS_FR,
  note: "Toutes les offres n’ont pas le même historique. Lorsqu’une donnée est trop récente ou indisponible, FILON l’indique plutôt que de la présenter comme certaine.",
};

const NL = {
  eye: "Transparantie", h1a: "Hoe de", h1b: "FILON-Score", h1c: " wordt berekend.",
  introA: "Een score op 100, uniek per aanbieding. Ze beantwoordt één vraag :",
  introB: "is dit een goede aankoop, nu ?",
  introC: "Dit is precies wat ze meet, en wat niet.",
  idx: "5 criteria", h2a: "De berekening,", h2b: "gewicht per gewicht", criteria: CRITERIA_NL,
  neverA: "Wat de Score", neverB: "nooit", nevers: NEVERS_NL,
  note: "Niet elke aanbieding heeft dezelfde prijsgeschiedenis. Wanneer een gegeven te recent of niet beschikbaar is, vermeldt FILON dat in plaats van het als zekerheid te presenteren.",
};

const EN = {
  eye: "Transparency", h1a: "How the", h1b: "FILON Score", h1c: " is calculated.",
  introA: "A score out of 100, unique per offer. It answers one question :",
  introB: "is this a good buy, now ?",
  introC: "Here's exactly what it measures, and what it doesn't.",
  idx: "5 criteria", h2a: "The calculation,", h2b: "weight by weight", criteria: CRITERIA_EN,
  neverA: "What the Score", neverB: "never", nevers: NEVERS_EN,
  note: "Not every offer has the same price history. When a data point is too recent or unavailable, FILON says so rather than presenting it as certain.",
};

export default function ScorePage() {
  return <Localized fr={<ScoreBody t={FR} />} nl={<ScoreBody t={NL} />} en={<ScoreBody t={EN} />} />;
}
