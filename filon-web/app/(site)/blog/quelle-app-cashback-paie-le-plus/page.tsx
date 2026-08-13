import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";
import { Localized } from "@/components/editorial/Localized";

const PATH = "/blog/quelle-app-cashback-paie-le-plus";
const TITLE = "Quelle app de cashback paie le plus ? (guide 2026)";
const DESC =
  "Les taux de cashback varient énormément d'une app à l'autre. Voici comment comparer, et comment prendre le meilleur à chaque achat.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

function ArticleFR() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Comparatif · 6 min · 2026</div>
          <h1>Quelle app de cashback paie le plus&nbsp;?</h1>
          <p className="lede">
            Spoiler : il n&apos;y a pas de « meilleure app » universelle. Le taux le plus élevé change selon le marchand,
            le jour et les promotions. Voici comment ne plus jamais laisser d&apos;argent sur la table.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-app-cashback.webp" alt="" />
        <p>
          Le cashback est devenu un réflexe pour des millions de consommateurs francophones. Le principe est simple : en
          passant par une plateforme partenaire avant de payer, vous récupérez un pourcentage de votre achat. Mais une
          erreur revient sans cesse : <b>s&apos;inscrire à une seule app et s&apos;y tenir</b>.
        </p>
        <p>
          Les taux, les plafonds, les exclusions et les délais peuvent varier selon le marchand, le pays et le moment.
          Consultez toujours les conditions affichées par la plateforme et l&apos;offre avant de passer commande.
        </p>

        <h2>Les principales apps de cashback francophones</h2>
        <p>Voici les acteurs que l&apos;on retrouve le plus souvent, et leur point fort :</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Plateforme</th>
                <th>Point fort</th>
                <th>À surveiller</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>iGraal</b></td><td>Couverture large, marchands nombreux</td><td>Taux variables selon promos</td></tr>
              <tr><td><b>Poulpeo</b></td><td>Taux souvent élevés, boosts fréquents</td><td>Seuils de retrait</td></tr>
              <tr><td><b>Widilo</b></td><td>Interface simple, bons taux mode/tech</td><td>Catalogue plus restreint</td></tr>
              <tr><td><b>Joko</b></td><td>Expérience mobile soignée, points</td><td>Logique de points à comprendre</td></tr>
              <tr><td><b>eBuyClub</b></td><td>Ancienneté, offres régulières</td><td>Ergonomie datée</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Aucune ne gagne sur tous les marchands. C&apos;est mathématique : la « meilleure » dépend de <b>où</b> et{" "}
          <b>quand</b> vous achetez.
        </p>

        <h2>La bonne méthode : comparer avant chaque achat</h2>
        <p>Concrètement, pour maximiser votre cashback, il faudrait à chaque fois :</p>
        <ul>
          <li>vérifier le taux du marchand sur <b>chaque</b> plateforme où vous avez un compte&nbsp;;</li>
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
          <li>Il n&apos;existe pas d&apos;app de cashback « meilleure » partout&nbsp;: le taux gagnant change selon le marchand.</li>
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
          <h1>Welke cashback-app betaalt het meest&nbsp;?</h1>
          <p className="lede">
            Spoiler : er is geen universele « beste app ». Het hoogste percentage verandert naargelang de winkel, de dag
            en de promoties. Hier lees je hoe je nooit meer geld op tafel laat liggen.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-app-cashback.webp" alt="" />
        <p>
          Cashback is een reflex geworden voor miljoenen consumenten. Het principe is simpel : door vóór je betaalt via
          een partnerplatform te passeren, krijg je een percentage van je aankoop terug. Maar één fout keert steeds
          terug : <b>je inschrijven bij één enkele app en daaraan vasthouden</b>.
        </p>
        <p>
          Percentages, plafonds, uitsluitingen en termijnen kunnen variëren per winkel, land en moment. Raadpleeg altijd
          de voorwaarden die het platform en aanbod tonen vóór je bestelt.
        </p>

        <h2>De voornaamste cashback-apps</h2>
        <p>Hier de spelers die je het vaakst terugvindt, en hun sterkte :</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Platform</th>
                <th>Sterkte</th>
                <th>Om in de gaten te houden</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>iGraal</b></td><td>Brede dekking, veel winkels</td><td>Variabele percentages naargelang promo's</td></tr>
              <tr><td><b>Poulpeo</b></td><td>Vaak hoge percentages, frequente boosts</td><td>Opname-drempels</td></tr>
              <tr><td><b>Widilo</b></td><td>Simpele interface, goede mode/tech-percentages</td><td>Beperkter aanbod</td></tr>
              <tr><td><b>Joko</b></td><td>Verzorgde mobiele ervaring, punten</td><td>Puntenlogica te begrijpen</td></tr>
              <tr><td><b>eBuyClub</b></td><td>Anciënniteit, regelmatige aanbiedingen</td><td>Gedateerde ergonomie</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Geen enkele wint bij alle winkels. Het is wiskundig : de « beste » hangt af van <b>waar</b> en{" "}
          <b>wanneer</b> je koopt.
        </p>

        <h2>De juiste methode : vergelijken vóór elke aankoop</h2>
        <p>Concreet zou je, om je cashback te maximaliseren, telkens moeten :</p>
        <ul>
          <li>het percentage van de winkel controleren op <b>elk</b> platform waar je een account hebt&nbsp;;</li>
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
          <li>Er bestaat geen cashback-app die overal « de beste » is&nbsp;: het winnende percentage verandert per winkel.</li>
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
          <h1>Which cashback app pays the most&nbsp;?</h1>
          <p className="lede">
            Spoiler: there&apos;s no universal « best app ». The highest rate changes by merchant, day and
            promotions. Here&apos;s how never to leave money on the table again.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-app-cashback.webp" alt="" />
        <p>
          Cashback has become a reflex for millions of consumers. The principle is simple: by going through a partner
          platform before you pay, you get back a percentage of your purchase. But one mistake keeps coming back:
          <b> signing up for a single app and sticking to it</b>.
        </p>
        <p>
          Rates, caps, exclusions and timing can vary by merchant, country and moment. Always consult the conditions
          displayed by the platform and offer before ordering.
        </p>

        <h2>The main cashback apps</h2>
        <p>Here are the players you find most often, and their strength:</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Platform</th>
                <th>Strength</th>
                <th>Watch out for</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>iGraal</b></td><td>Broad coverage, many merchants</td><td>Rates vary by promo</td></tr>
              <tr><td><b>Poulpeo</b></td><td>Often high rates, frequent boosts</td><td>Withdrawal thresholds</td></tr>
              <tr><td><b>Widilo</b></td><td>Simple interface, good fashion/tech rates</td><td>Smaller catalogue</td></tr>
              <tr><td><b>Joko</b></td><td>Polished mobile experience, points</td><td>Points logic to grasp</td></tr>
              <tr><td><b>eBuyClub</b></td><td>Longevity, regular offers</td><td>Dated ergonomics</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          None wins on every merchant. It&apos;s mathematical: the « best » depends on <b>where</b> and{" "}
          <b>when</b> you buy.
        </p>

        <h2>The right method: compare before every purchase</h2>
        <p>Concretely, to maximise your cashback, you&apos;d have to each time:</p>
        <ul>
          <li>check the merchant&apos;s rate on <b>each</b> platform where you have an account&nbsp;;</li>
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
          <li>No cashback app is « the best » everywhere&nbsp;: the winning rate changes by merchant.</li>
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
          { name: "Quelle app de cashback paie le plus ?", path: PATH },
        ])}
      />
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} en={<ArticleEN />} />
    </>
  );
}
