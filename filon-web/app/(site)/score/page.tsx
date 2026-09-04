import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { Reveal } from "@/components/editorial/Reveal";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/score",
  title: "Le Score FILON",
  description:
    "Comment le score actuel structure cinq signaux observés : comparaison de prix, historique, stock, fraîcheur et largeur du périmètre.",
});

const CRITERIA_FR: Array<[string, string, string]> = [
  ["35 pts", "Comparaison de prix", "Le prix obtient ces points seulement s'il est le plus bas parmi au moins deux marchands comparables observés."],
  ["25 pts", "Moment dans l'historique", "Le signal n'est actif qu'avec au moins cinq relevés couvrant sept jours. Sinon l'historique reste insuffisant."],
  ["15 pts", "Disponibilité", "Le stock apporte des points uniquement quand le dernier flux indique explicitement que l'offre est disponible."],
  ["15 pts", "Fraîcheur", "Un relevé de moins de 72 heures renforce la décision. Une date absente reste inconnue."],
  ["10 pts", "Largeur de comparaison", "Le nombre de marchands observés documente le périmètre ; il ne constitue pas une note de qualité marchand."],
];

const CRITERIA_NL: Array<[string, string, string]> = [
  ["35 pt", "Prijsvergelijking", "De prijs krijgt deze punten alleen wanneer hij de laagste is bij minstens twee vergelijkbare bekeken winkels."],
  ["25 pt", "Moment in de historiek", "Dit signaal wordt pas actief met minstens vijf metingen over zeven dagen. Anders blijft de historiek onvoldoende."],
  ["15 pt", "Beschikbaarheid", "Voorraad telt alleen mee wanneer de laatste feed uitdrukkelijk aangeeft dat de aanbieding beschikbaar is."],
  ["15 pt", "Actualiteit", "Een meting jonger dan 72 uur versterkt de beslissing. Een ontbrekende datum blijft onbekend."],
  ["10 pt", "Vergelijkingsbereik", "Het aantal bekeken winkels beschrijft het bereik; het is geen kwaliteitsscore voor winkels."],
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
  ["35 pts", "Price comparison", "The price earns these points only when it is the lowest among at least two observed comparable merchants."],
  ["25 pts", "Position in price history", "This signal activates only with at least five readings over seven days. Otherwise history remains insufficient."],
  ["15 pts", "Availability", "Stock contributes only when the latest feed explicitly says that the offer is available."],
  ["15 pts", "Freshness", "A reading under 72 hours old strengthens the decision. A missing date remains unknown."],
  ["10 pts", "Comparison breadth", "The number of observed merchants documents scope; it is not a merchant-quality rating."],
];

const NEVERS_EN: Array<[string, string]> = [
  ["Sell a place", "No brand, no merchant can buy a better score."],
  ["Inflate an affiliate offer", "A link that pays us doesn't get one extra point."],
  ["Hide the reasoning", "Every score breaks down, line by line, in the offer's details."],
];

function ScoreBody({ t }: { t: {
  eye: string; h1a: string; h1b: string; h1c: string; introA: string; introB: string; introC: string;
  total: string; idx: string; h2a: string; h2b: string; criteria: Array<[string, string, string]>;
  neverA: string; neverB: string; nevers: Array<[string, string]>; note: string;
} }) {
  return (
    <div className="p19-decision-surface p19-score-surface" data-decision-plan="score">
      <section className="p19-decision-hero">
        <div className="ed-wrap p19-decision-hero-grid">
          <div className="p19-decision-copy">
            <span className="eyebrow">{t.eye}</span>
            <h1>{t.h1a} <span className="it">{t.h1b}</span>{t.h1c}</h1>
            <p className="intro">{t.introA} <b>{t.introB}</b> {t.introC}</p>
          </div>
          <div className="p19-score-instrument" aria-hidden="true">
            <span className="p19-score-total">{t.total}</span>
            {t.criteria.map(([weight]) => (
              <i key={weight}>{weight}</i>
            ))}
          </div>
        </div>
      </section>
      <section className="p19-decision-ledger">
        <div className="ed-wrap">
          <Reveal className="ed-lead">
            <span className="idx">{t.idx}</span>
            <h2>{t.h2a} <span className="it">{t.h2b}</span>.</h2>
          </Reveal>
          <ol className="p19-signal-ledger">
            {t.criteria.map(([weight, title, desc], index) => (
              <li key={title}>
                <span className="p19-signal-index">0{index + 1}</span>
                <strong>{weight}</strong>
                <div>
                  <h3>{title}</h3>
                  <p>{desc}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>
      <section className="p19-decision-guardrails">
        <div className="ed-wrap p19-guardrail-grid">
          <h2>{t.neverA} <span className="it">{t.neverB}</span>.</h2>
          <div>
            {t.nevers.map(([head, body]) => (
              <p key={head}><b>{head}.</b> {body}</p>
            ))}
            <p className="p19-decision-note">{t.note}</p>
          </div>
        </div>
      </section>
    </div>
  );
}

const FR = {
  total: "100 points mesurables",
  eye: "Transparence", h1a: "Comment se calcule le", h1b: "Score FILON", h1c: ".",
  introA: "Un rapport entre les points observés et les points mesurables pour l'offre. Il aide à répondre à une question bornée :",
  introB: "que peut-on conclure avec les données disponibles maintenant ?",
  introC: "Ce n'est ni une note universelle du produit ni une garantie d'achat.",
  idx: "5 signaux observables", h2a: "Le calcul actuel,", h2b: "preuve par preuve", criteria: CRITERIA_FR,
  neverA: "Ce que le Score ne fait", neverB: "jamais", nevers: NEVERS_FR,
  note: "Toutes les offres n’ont pas le même historique. Lorsqu’une donnée est trop récente ou indisponible, FILON l’indique plutôt que de la présenter comme certaine.",
};

const NL = {
  total: "100 meetbare punten",
  eye: "Transparantie", h1a: "Hoe de", h1b: "FILON-Score", h1c: " wordt berekend.",
  introA: "Een verhouding tussen bekeken punten en meetbare punten voor de aanbieding. Ze helpt een afgebakende vraag te beantwoorden:",
  introB: "wat kunnen de beschikbare gegevens nu ondersteunen?",
  introC: "Dit is geen universele productscore en geen aankoopgarantie.",
  idx: "5 waarneembare signalen", h2a: "De huidige berekening,", h2b: "bewijs per bewijs", criteria: CRITERIA_NL,
  neverA: "Wat de Score", neverB: "nooit", nevers: NEVERS_NL,
  note: "Niet elke aanbieding heeft dezelfde prijsgeschiedenis. Wanneer een gegeven te recent of niet beschikbaar is, vermeldt FILON dat in plaats van het als zekerheid te presenteren.",
};

const EN = {
  total: "100 measurable points",
  eye: "Transparency", h1a: "How the", h1b: "FILON Score", h1c: " is calculated.",
  introA: "A ratio between observed points and measurable points for the offer. It helps answer one bounded question:",
  introB: "what can the available data support now?",
  introC: "It is neither a universal product rating nor a purchase guarantee.",
  idx: "5 observable signals", h2a: "The current calculation,", h2b: "evidence by evidence", criteria: CRITERIA_EN,
  neverA: "What the Score", neverB: "never", nevers: NEVERS_EN,
  note: "Not every offer has the same price history. When a data point is too recent or unavailable, FILON says so rather than presenting it as certain.",
};

export default function ScorePage() {
  return <Localized fr={<ScoreBody t={FR} />} nl={<ScoreBody t={NL} />} en={<ScoreBody t={EN} />} />;
}
