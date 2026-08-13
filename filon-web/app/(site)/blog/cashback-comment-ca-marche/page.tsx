import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";
import { Localized } from "@/components/editorial/Localized";

const PATH = "/blog/cashback-comment-ca-marche";
const TITLE = "Le cashback expliqué simplement : comment ça marche (et les pièges)";
const DESC =
  "Le cashback rembourse une partie de vos achats. Mais d'où vient l'argent, combien récupère-t-on vraiment, et quels pièges éviter ? Le guide clair, sans jargon.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

function ArticleFR() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Guide · 6 min · 2026</div>
          <h1>Le cashback, expliqué simplement</h1>
          <p className="lede">
            «&nbsp;Récupérez de l&apos;argent sur vos achats&nbsp;»&nbsp;: le cashback semble trop beau pour être
            vrai. Il ne l&apos;est pas, mais il faut comprendre d&apos;où vient l&apos;argent, et repérer les pièges.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-cashback-explique.webp" alt="" />
        <p>
          Le cashback est un avantage qui peut être attribué après un achat éligible. Son montant, son délai et ses
          conditions varient selon le marchand et l&apos;offre. Il ne s&apos;agit généralement pas d&apos;une réduction appliquée
          directement au paiement&nbsp;: le suivi doit d&apos;abord être validé.
        </p>

        <h2>D&apos;où vient l&apos;argent, exactement</h2>
        <p>
          Quand un site de cashback vous envoie chez un marchand et que vous achetez, le marchand lui verse une{" "}
          <b>commission d&apos;affiliation</b>. Le site de cashback vous en <b>reverse une partie</b>, et garde le
          reste. C&apos;est tout le modèle&nbsp;: une commission partagée entre le site et vous.
        </p>
        <p>
          Conséquence importante&nbsp;: regardez séparément le <b>prix affiché au paiement</b> et le cashback éventuel.
          Ce dernier dépend d&apos;une validation ultérieure par le marchand ou le programme partenaire.
        </p>

        <h2>Combien récupère-t-on vraiment ?</h2>
        <p>
          Les taux, les plafonds et les exclusions changent selon la catégorie, le marchand, le pays et parfois le
          statut du client. Vérifiez toujours les conditions affichées pour l&apos;offre précise que vous consultez&nbsp;:
        </p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Élément à vérifier</th>
                <th>Pourquoi</th>
                <th>Réflexe utile</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Taux affiché</b></td><td className="g">Il peut évoluer</td><td>Regardez-le juste avant l&apos;achat</td></tr>
              <tr><td><b>Produits éligibles</b></td><td className="g">Ils peuvent être exclus</td><td>Lisez les conditions de l&apos;offre</td></tr>
              <tr><td><b>Code promo</b></td><td className="g">Il peut modifier l&apos;éligibilité</td><td>Vérifiez s&apos;il est compatible</td></tr>
              <tr><td><b>Validation</b></td><td className="g">Elle n&apos;est pas immédiate</td><td>Conservez votre confirmation de commande</td></tr>
              <tr><td><b>Versement</b></td><td className="g">Les règles diffèrent</td><td>Consultez le seuil et le calendrier du programme</td></tr>
            </tbody>
          </table>
        </div>

        <h2>Les pièges à connaître</h2>
        <p>
          <b>Le taux temporaire.</b> Un taux affiché peut être modifié ou soumis à des conditions. Vérifiez-le
          <b>au moment de l&apos;achat</b>, avec les exclusions applicables.
        </p>
        <p>
          <b>Le délai de validation.</b> Le cashback peut apparaître comme «&nbsp;en attente&nbsp;» tant que le
          marchand ou le programme ne l&apos;a pas validé. Le délai et un éventuel seuil de versement dépendent de
          chaque programme.
        </p>
        <p>
          <b>Les conditions de suivi.</b> Un code promo non éligible, un bloqueur de contenu, des paramètres de
          confidentialité ou une autre source de trafic peuvent empêcher le suivi. Suivez les consignes du programme
          avant de valider votre commande.
        </p>

        <div className="callout">
          <b>Le bon réflexe&nbsp;:</b> ne regardez pas uniquement le taux de cashback. Comparez le
          <span className="g"> prix affiché, les conditions et le cashback éventuel</span>. FILON présente ces
          informations lorsqu&apos;elles sont renseignées dans les données de l&apos;offre.
        </div>

        <h2>En résumé</h2>
        <ul>
          <li>Le cashback est généralement lié à une commission d&apos;affiliation après une vente éligible.</li>
          <li>Il est distinct du <b>prix affiché</b> lors du paiement.</li>
          <li>Le <b>taux</b>, les exclusions et le plafond dépendent de l&apos;offre.</li>
          <li>Attention aux <b>conditions de suivi</b> et au délai de validation.</li>
          <li>Comparez le <b>prix affiché</b>, les conditions et le cashback éventuel.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Voir les offres disponibles
          </a>
        </p>
      </div>
    </article>
  );
}

function ArticleNL() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Gids · 6 min · 2026</div>
          <h1>Cashback, simpel uitgelegd</h1>
          <p className="lede">
            «&nbsp;Krijg geld terug op je aankopen&nbsp;»&nbsp;: cashback lijkt te mooi om waar te zijn. Dat is het
            niet, maar je moet begrijpen waar het geld vandaan komt, en de valkuilen herkennen.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-cashback-explique.webp" alt="" />
        <p>
          Cashback is een voordeel dat na een in aanmerking komende aankoop kan worden toegekend. Het bedrag, de termijn
          en de voorwaarden verschillen per winkel en aanbod. Het is doorgaans geen korting die rechtstreeks bij betaling
          wordt toegepast: de tracking moet eerst worden gevalideerd.
        </p>

        <h2>Waar komt het geld precies vandaan</h2>
        <p>
          Wanneer een cashback-site je naar een winkel stuurt en je koopt, betaalt de winkel hem een{" "}
          <b>affiliatiecommissie</b>. De cashback-site <b>geeft je daar een deel van terug</b>, en houdt de rest.
          Dat is het hele model&nbsp;: een commissie gedeeld tussen de site en jou.
        </p>
        <p>
          Belangrijk gevolg&nbsp;: bekijk de <b>getoonde prijs bij betaling</b> en eventuele cashback afzonderlijk.
          Die laatste hangt af van een latere validatie door de winkel of het partnerprogramma.
        </p>

        <h2>Hoeveel krijg je echt terug ?</h2>
        <p>
          Percentages, plafonds en uitsluitingen veranderen per categorie, winkel, land en soms klantstatus. Controleer
          altijd de voorwaarden die bij het specifieke aanbod staan:
        </p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Te controleren</th>
                <th>Waarom</th>
                <th>Nuttige reflex</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Getoond percentage</b></td><td className="g">Het kan veranderen</td><td>Controleer vlak vóór je koopt</td></tr>
              <tr><td><b>In aanmerking komende producten</b></td><td className="g">Sommige kunnen uitgesloten zijn</td><td>Lees de aanbodvoorwaarden</td></tr>
              <tr><td><b>Promocode</b></td><td className="g">Die kan de geldigheid beïnvloeden</td><td>Controleer of die compatibel is</td></tr>
              <tr><td><b>Validatie</b></td><td className="g">Die is niet onmiddellijk</td><td>Bewaar je bestelbevestiging</td></tr>
              <tr><td><b>Uitbetaling</b></td><td className="g">De regels verschillen</td><td>Controleer drempel en kalender van het programma</td></tr>
            </tbody>
          </table>
        </div>

        <h2>De valkuilen om te kennen</h2>
        <p>
          <b>Het tijdelijke percentage.</b> Een getoond percentage kan worden gewijzigd of aan voorwaarden gebonden zijn.
          Controleer het <b>op het moment van de aankoop</b>, samen met de toepasselijke uitsluitingen.
        </p>
        <p>
          <b>De validatietermijn.</b> Cashback kan «&nbsp;in afwachting&nbsp;» staan zolang de winkel of het programma
          die niet heeft gevalideerd. De termijn en eventuele uitbetalingsdrempel hangen af van elk programma.
        </p>
        <p>
          <b>De trackingvoorwaarden.</b> Een niet-geschikte promocode, contentblocker, privacy-instelling of andere
          verkeersbron kan tracking verhinderen. Volg de instructies van het programma vóór je je bestelling bevestigt.
        </p>

        <div className="callout">
          <b>De nuttige reflex&nbsp;:</b> kijk niet alleen naar het cashbackpercentage. Vergelijk de
          <span className="g"> getoonde prijs, voorwaarden en eventuele cashback</span>. FILON toont die gegevens
          wanneer ze in de aanbodgegevens vermeld zijn.
        </div>

        <h2>Samengevat</h2>
        <ul>
          <li>Cashback is doorgaans gekoppeld aan een affiliatiecommissie na een geldige verkoop.</li>
          <li>Het staat los van de <b>getoonde prijs</b> bij betaling.</li>
          <li>Het <b>percentage</b>, uitsluitingen en plafond hangen af van het aanbod.</li>
          <li>Let op de <b>trackingvoorwaarden</b> en de validatietermijn.</li>
          <li>Vergelijk de <b>getoonde prijs</b>, voorwaarden en eventuele cashback.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Bekijk beschikbare aanbiedingen
          </a>
        </p>
      </div>
    </article>
  );
}

function ArticleEN() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Guide · 6 min · 2026</div>
          <h1>Cashback, simply explained</h1>
          <p className="lede">
            «&nbsp;Get money back on your purchases&nbsp;»&nbsp;: cashback sounds too good to be true. It isn&apos;t,
            but you need to understand where the money comes from, and spot the traps.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-cashback-explique.webp" alt="" />
        <p>
          Cashback is a benefit that may be granted after an eligible purchase. Its amount, timing and conditions vary
          by merchant and offer. It is generally not a discount applied directly at checkout: the tracking must first
          be validated.
        </p>

        <h2>Where the money comes from, exactly</h2>
        <p>
          When a cashback site sends you to a merchant and you buy, the merchant pays it an{" "}
          <b>affiliation commission</b>. The cashback site <b>gives you back a part of it</b>, and keeps the rest.
          That&apos;s the whole model&nbsp;: a commission shared between the site and you.
        </p>
        <p>
          Important consequence&nbsp;: look separately at the <b>price displayed at checkout</b> and any cashback.
          The latter depends on a subsequent validation by the merchant or partner programme.
        </p>

        <h2>How much do you really get back ?</h2>
        <p>
          Rates, caps and exclusions change by category, merchant, country and sometimes customer status. Always
          check the terms displayed for the exact offer you are considering:
        </p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>What to check</th>
                <th>Why</th>
                <th>Useful reflex</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Displayed rate</b></td><td className="g">It can change</td><td>Check it just before purchase</td></tr>
              <tr><td><b>Eligible products</b></td><td className="g">Some can be excluded</td><td>Read the offer terms</td></tr>
              <tr><td><b>Promo code</b></td><td className="g">It can affect eligibility</td><td>Check that it is compatible</td></tr>
              <tr><td><b>Validation</b></td><td className="g">It is not immediate</td><td>Keep your order confirmation</td></tr>
              <tr><td><b>Payout</b></td><td className="g">Rules differ</td><td>Check the programme threshold and schedule</td></tr>
            </tbody>
          </table>
        </div>

        <h2>The traps to know</h2>
        <p>
          <b>The temporary rate.</b> A displayed rate can change or be subject to conditions. Check it <b>at the
          moment of purchase</b>, along with any exclusions.
        </p>
        <p>
          <b>The validation delay.</b> Cashback can remain «&nbsp;pending&nbsp;» until the merchant or programme
          validates it. The timing and any payout threshold depend on each programme.
        </p>
        <p>
          <b>The tracking conditions.</b> An ineligible promo code, content blocker, privacy setting or another traffic
          source can prevent tracking. Follow the programme instructions before confirming your order.
        </p>

        <div className="callout">
          <b>The useful reflex&nbsp;:</b> do not look at the cashback rate alone. Compare the
          <span className="g"> displayed price, conditions and any cashback</span>. FILON presents these details
          when they are listed in the offer data.
        </div>

        <h2>In short</h2>
        <ul>
          <li>Cashback is generally linked to an affiliate commission after an eligible sale.</li>
          <li>It is separate from the <b>price displayed</b> at checkout.</li>
          <li>The <b>rate</b>, exclusions and cap depend on the offer.</li>
          <li>Watch the <b>tracking conditions</b> and validation timing.</li>
          <li>Compare the <b>displayed price</b>, terms and any cashback.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            See available offers
          </a>
        </p>
      </div>
    </article>
  );
}

export default function ArticlePage() {
  return (
    <>
      <JsonLd data={articleSchema({ title: TITLE, description: DESC, path: PATH, datePublished: "2026-07-25" })} />
      <JsonLd
        data={breadcrumbSchema([
          { name: "Accueil", path: "/" },
          { name: "Blog", path: "/blog" },
          { name: "Le cashback expliqué", path: PATH },
        ])}
      />
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} en={<ArticleEN />} />
    </>
  );
}
