import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";
import { Localized } from "@/components/editorial/Localized";

const PATH = "/blog/quelle-app-cashback-paie-le-plus";
const TITLE = "Comment comparer les conditions des apps de cashback ?";
const DESC =
  "Taux annoncé, plafond, exclusions, validation et retrait : les champs à comparer pour une offre de cashback donnée.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

function ArticleFR() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Comparatif · 6 min · 2026</div>
          <h1>Comment comparer les conditions des apps de cashback&nbsp;?</h1>
          <p className="lede">
            Il n&apos;est pas prudent de supposer une « meilleure app » universelle. Les taux peuvent varier selon le marchand,
            le jour et les promotions. Il faut donc comparer les conditions de l&apos;offre précise au moment de choisir.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-app-cashback.webp" alt="" />
        <p>
          Une plateforme de cashback peut annoncer un avantage conditionnel après un achat éligible. Le taux affiché ne
          suffit pas : plafond, exclusions, validation et retrait font partie de la comparaison.
        </p>
        <p>
          Les taux, les plafonds, les exclusions et les délais peuvent varier selon le marchand, le pays et le moment.
          Consultez toujours les conditions affichées par la plateforme et l&apos;offre avant de passer commande.
        </p>

        <h2>Les champs à relever pour chaque offre</h2>
        <p>Une comparaison reproductible s&apos;appuie sur les conditions publiées, pas sur une réputation générale :</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Champ</th>
                <th>Ce qu&apos;il documente</th>
                <th>À confirmer</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Taux annoncé</b></td><td>Avantage avant plafond</td><td>Catégorie, produit et date</td></tr>
              <tr><td><b>Plafond</b></td><td>Montant maximal éligible</td><td>Période et compte</td></tr>
              <tr><td><b>Exclusions</b></td><td>Achats non admissibles</td><td>Codes, cartes-cadeaux et pays</td></tr>
              <tr><td><b>Validation</b></td><td>Délai et conditions d&apos;acceptation</td><td>Annulation, retour et suivi</td></tr>
              <tr><td><b>Retrait</b></td><td>Seuil et moyen de versement</td><td>Identité et frais éventuels</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Aucun programme ne doit être supposé gagnant partout : la « meilleure » option dépend de <b>où</b> et{" "}
          <b>quand</b> vous achetez.
        </p>

        <h2>Une méthode bornée : comparer l&apos;offre concernée</h2>
        <p>Avant de compter un cashback dans un total, vérifiez :</p>
        <ul>
          <li>le taux annoncé sur les plateformes que vous utilisez&nbsp;;</li>
          <li>repérer les <b>offres boostées</b> temporaires&nbsp;;</li>
          <li>vérifier les conditions (durée de validité, seuil de retrait, délai de validation)&nbsp;;</li>
          <li>et seulement ensuite, cliquer et payer.</li>
        </ul>
        <p>
          Fait à la main, ce contrôle peut être fastidieux. FILON recherche des offres dans son propre catalogue et
          présente les informations disponibles pour vous aider à les comparer.
        </p>

        <div className="callout">
          <b>Un point de départ :</b> demandez à FILON de rechercher une offre dans son catalogue. Prix affiché,
          cashback, code promo et score peuvent être montrés lorsqu&apos;ils sont renseignés ; vérifiez les conditions du
          marchand avant de commander.
        </div>

        <h2>Ne comparez plus le cashback seul</h2>
        <p>
          Il est utile de ne pas raisonner uniquement en cashback. Comparez le <b>prix affiché</b>, les frais, les
          conditions, et les éventuels avantages indiqués pour l&apos;offre. Un produit reconditionné ou un code promo ne se
          compare qu&apos;après avoir vérifié son état, son éligibilité et ses propres conditions.
        </p>
        <p>
          FILON organise les informations disponibles dans son catalogue pour vous aider à comparer. Il ne remplace pas
          votre vérification du prix, de la disponibilité et des conditions du marchand.
        </p>

        <h2>En résumé</h2>
        <ul>
          <li>Ne supposez pas qu&apos;une app est « meilleure » partout&nbsp;: comparez le taux et les conditions pour le marchand concerné.</li>
          <li>Comparer les conditions peut prendre du temps et les résultats varient selon l&apos;offre.</li>
          <li>Comparez <b>prix affiché</b>, frais, conditions et avantages éventuels, pas le cashback seul.</li>
          <li>FILON présente les informations disponibles de son catalogue pour aider votre comparaison.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Essayer l&apos;assistant FILON
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
          <div className="ed-article-meta">Vergelijking · 6 min · 2026</div>
          <h1>Hoe vergelijk je de voorwaarden van cashback-apps&nbsp;?</h1>
          <p className="lede">
            Ga niet uit van een universele « beste app ». Tarieven kunnen verschillen per winkel, dag
            en promoties. Vergelijk daarom de voorwaarden van de concrete aanbieding wanneer je kiest.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-app-cashback.webp" alt="" />
        <p>
          Een cashbackplatform kan na een geschikte aankoop een voorwaardelijk voordeel aankondigen. Het getoonde
          percentage volstaat niet: plafond, uitsluitingen, validatie en opname horen bij de vergelijking.
        </p>
        <p>
          Percentages, plafonds, uitsluitingen en termijnen kunnen variëren per winkel, land en moment. Raadpleeg altijd
          de voorwaarden die het platform en aanbod tonen vóór je bestelt.
        </p>

        <h2>Velden die je per aanbieding controleert</h2>
        <p>Een reproduceerbare vergelijking steunt op gepubliceerde voorwaarden, niet op algemene reputatie :</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Veld</th>
                <th>Wat het documenteert</th>
                <th>Te bevestigen</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Vermeld tarief</b></td><td>Voordeel vóór plafond</td><td>Categorie, product en datum</td></tr>
              <tr><td><b>Plafond</b></td><td>Maximaal geschikt bedrag</td><td>Periode en account</td></tr>
              <tr><td><b>Uitsluitingen</b></td><td>Niet-geschikte aankopen</td><td>Codes, cadeaubonnen en land</td></tr>
              <tr><td><b>Validatie</b></td><td>Termijn en acceptatievoorwaarden</td><td>Annulering, retour en tracking</td></tr>
              <tr><td><b>Opname</b></td><td>Drempel en betaalwijze</td><td>Identiteit en eventuele kosten</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Ga er niet van uit dat één programma overal wint: de « beste » optie hangt af van <b>waar</b> en{" "}
          <b>wanneer</b> je koopt.
        </p>

        <h2>Een afgebakende methode : vergelijk de betrokken aanbieding</h2>
        <p>Controleer voordat je cashback in een totaal meetelt :</p>
        <ul>
          <li>het vermelde tarief op de platforms die je gebruikt&nbsp;;</li>
          <li>de tijdelijke <b>geboosterde aanbiedingen</b> spotten&nbsp;;</li>
          <li>de voorwaarden controleren (geldigheidsduur, opname-drempel, validatietermijn)&nbsp;;</li>
          <li>en pas daarna klikken en betalen.</li>
        </ul>
        <p>
          Handmatig kan die controle omslachtig zijn. FILON zoekt aanbiedingen in zijn eigen catalogus en toont de
          beschikbare informatie om je te helpen vergelijken.
        </p>

        <div className="callout">
          <b>Een vertrekpunt:</b> vraag FILON om een aanbod in zijn catalogus te zoeken. Getoonde prijs, cashback,
          promocode en score kunnen verschijnen wanneer ze vermeld zijn; controleer de winkelvoorwaarden vóór je bestelt.
        </div>

        <h2>Vergelijk niet langer cashback alleen</h2>
        <p>
          Het is nuttig om niet alleen in cashback te redeneren. Vergelijk de <b>getoonde prijs</b>, kosten,
          voorwaarden en eventuele voordelen voor het aanbod. Een refurbished product of promocode vergelijk je pas na
          controle van staat, geldigheid en eigen voorwaarden.
        </p>
        <p>
          FILON ordent de beschikbare informatie in zijn catalogus om je te helpen vergelijken. Het vervangt niet je
          eigen controle van prijs, beschikbaarheid en winkelvoorwaarden.
        </p>

        <h2>Samengevat</h2>
        <ul>
          <li>Ga er niet van uit dat een cashback-app overal « de beste » is&nbsp;: vergelijk percentage en voorwaarden per winkel.</li>
          <li>Voorwaarden vergelijken kan tijd kosten en de uitkomst varieert per aanbod.</li>
          <li>Vergelijk <b>getoonde prijs</b>, kosten, voorwaarden en eventuele voordelen, niet alleen cashback.</li>
          <li>FILON toont beschikbare catalogusinformatie om je vergelijking te helpen.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            De FILON-assistent proberen
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
          <div className="ed-article-meta">Comparison · 6 min · 2026</div>
          <h1>How should cashback-app terms be compared&nbsp;?</h1>
          <p className="lede">
            Do not assume a universal « best app ». Rates may vary by merchant, day and
            promotions. Compare the specific offer terms at the time you choose.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-app-cashback.webp" alt="" />
        <p>
          A cashback platform may advertise a conditional benefit after an eligible purchase. The displayed rate is
          not enough: caps, exclusions, validation and withdrawal belong in the comparison.
        </p>
        <p>
          Rates, caps, exclusions and timing can vary by merchant, country and moment. Always consult the conditions
          displayed by the platform and offer before ordering.
        </p>

        <h2>Fields to record for each offer</h2>
        <p>A reproducible comparison relies on published terms, not general reputation:</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Field</th>
                <th>What it documents</th>
                <th>To confirm</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Advertised rate</b></td><td>Benefit before caps</td><td>Category, product and date</td></tr>
              <tr><td><b>Cap</b></td><td>Maximum eligible amount</td><td>Period and account</td></tr>
              <tr><td><b>Exclusions</b></td><td>Ineligible purchases</td><td>Codes, gift cards and country</td></tr>
              <tr><td><b>Validation</b></td><td>Timing and acceptance terms</td><td>Cancellation, return and tracking</td></tr>
              <tr><td><b>Withdrawal</b></td><td>Threshold and payment method</td><td>Identity and possible fees</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          No programme should be assumed to win everywhere: the « best » option depends on <b>where</b> and{" "}
          <b>when</b> you buy.
        </p>

        <h2>A bounded method: compare the offer concerned</h2>
        <p>Before counting cashback in a total, check:</p>
        <ul>
          <li>the advertised rate on platforms you use&nbsp;;</li>
          <li>spot the temporary <b>boosted offers</b>&nbsp;;</li>
          <li>check the conditions (validity, withdrawal threshold, validation delay)&nbsp;;</li>
          <li>and only then, click and pay.</li>
        </ul>
        <p>
          Checked manually, this can be time-consuming. FILON searches offers in its own catalogue and presents the
          available information to help you compare.
        </p>

        <div className="callout">
          <b>A starting point:</b> ask FILON to search an offer in its catalogue. Displayed price, cashback, promo code
          and score may be shown when listed; check the merchant&apos;s terms before ordering.
        </div>

        <h2>Stop comparing cashback alone</h2>
        <p>
          It is useful not to reason in cashback alone. Compare the <b>displayed price</b>, fees, terms and any
          benefits listed for the offer. Only compare a refurbished product or promo code after checking its condition,
          eligibility and own terms.
        </p>
        <p>
          FILON organises the available information in its catalogue to help you compare. It does not replace your own
          verification of the price, availability and merchant terms.
        </p>

        <h2>In short</h2>
        <ul>
          <li>Do not assume a cashback app is « the best » everywhere&nbsp;: compare the rate and terms for the merchant concerned.</li>
          <li>Comparing terms can take time and results vary by offer.</li>
          <li>Compare <b>displayed price</b>, fees, terms and any benefits, not cashback alone.</li>
          <li>FILON presents available catalogue information to help your comparison.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Try the FILON assistant
          </a>
        </p>
      </div>
    </article>
  );
}

export default function ArticlePage() {
  return (
    <>
      <JsonLd data={articleSchema({ title: TITLE, description: DESC, path: PATH, datePublished: "2026-01-15" })} />
      <JsonLd
        data={breadcrumbSchema([
          { name: "Accueil", path: "/" },
          { name: "Blog", path: "/blog" },
          { name: "Comment comparer les conditions des apps de cashback ?", path: PATH },
        ])}
      />
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} en={<ArticleEN />} />
    </>
  );
}
