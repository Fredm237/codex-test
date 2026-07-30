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
          Or les taux varient énormément. Pour un même marchand, un même jour, vous pouvez trouver 3 % ici, 6 % là, et une
          offre boostée à 8 % ailleurs. Choisir la mauvaise app, c&apos;est souvent diviser votre cashback par deux.
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
          Fait à la main, c&apos;est fastidieux, et la plupart des gens abandonnent. C&apos;est exactement le travail que{" "}
          <b>FILON automatise</b>.
        </p>

        <div className="callout">
          <b>Le raccourci :</b> au lieu de comparer les apps une par une, laissez FILON le faire. Il trouve la{" "}
          <span className="g">meilleure offre du moment</span> et vous y emmène. Vous n&apos;avez rien à chercher.
        </div>

        <h2>Ne comparez plus le cashback seul</h2>
        <p>
          L&apos;erreur suivante est de raisonner « cashback » alors que la vraie question est <b>le prix réel final</b>. Un
          cashback de 6 % sur un produit neuf peut être battu par un <b>reconditionné équivalent</b> 30 % moins cher, ou par
          un <b>code promo</b> cumulable. Le bon réflexe, c&apos;est de comparer le <b>coût total</b>, pas une seule ligne.
        </p>
        <p>
          C&apos;est la philosophie de FILON : vous donner un seul chiffre, votre vrai prix, et vous dire s&apos;il faut
          acheter ou attendre.
        </p>

        <h2>En résumé</h2>
        <ul>
          <li>Il n&apos;existe pas d&apos;app de cashback « meilleure » partout&nbsp;: le taux gagnant change selon le marchand.</li>
          <li>Comparer avant chaque achat peut doubler votre cashback, mais c&apos;est chronophage à la main.</li>
          <li>Raisonnez <b>prix réel final</b> (cashback + reconditionné + code promo), pas cashback seul.</li>
          <li>FILON fait cette comparaison pour vous, gratuitement, à chaque achat.</li>
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
          Nu variëren de percentages enorm. Voor eenzelfde winkel, op eenzelfde dag, kun je hier 3 % vinden, daar 6 %, en
          elders een geboosterd aanbod aan 8 %. De verkeerde app kiezen, is vaak je cashback halveren.
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
          Met de hand gedaan is dat omslachtig, en de meeste mensen geven op. Dat is precies het werk dat{" "}
          <b>FILON automatiseert</b>.
        </p>

        <div className="callout">
          <b>De shortcut :</b> in plaats van de apps één voor één te vergelijken, laat FILON het doen. Hij vindt het{" "}
          <span className="g">beste aanbod van het moment</span> en brengt je erheen. Je hoeft niets te zoeken.
        </div>

        <h2>Vergelijk niet langer cashback alleen</h2>
        <p>
          De volgende fout is redeneren in « cashback » terwijl de echte vraag <b>de echte eindprijs</b> is. Een cashback
          van 6 % op een nieuw product kan verslagen worden door een <b>gelijkwaardig refurbished</b> 30 % goedkoper, of
          door een cumuleerbare <b>promocode</b>. De goede reflex is de <b>totale kost</b> vergelijken, niet één enkele
          lijn.
        </p>
        <p>
          Dat is de filosofie van FILON : je één enkel cijfer geven, je echte prijs, en je zeggen of je moet kopen of
          wachten.
        </p>

        <h2>Samengevat</h2>
        <ul>
          <li>Er bestaat geen cashback-app die overal « de beste » is&nbsp;: het winnende percentage verandert per winkel.</li>
          <li>Vergelijken vóór elke aankoop kan je cashback verdubbelen, maar het is tijdrovend met de hand.</li>
          <li>Redeneer in <b>echte eindprijs</b> (cashback + refurbished + promocode), niet cashback alleen.</li>
          <li>FILON maakt die vergelijking voor je, gratis, bij elke aankoop.</li>
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
          Yet rates vary hugely. For the same merchant, on the same day, you can find 3% here, 6% there, and a
          boosted offer at 8% elsewhere. Choosing the wrong app often halves your cashback.
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
          Done by hand, it&apos;s tedious, and most people give up. That&apos;s exactly the work that{" "}
          <b>FILON automates</b>.
        </p>

        <div className="callout">
          <b>The shortcut:</b> instead of comparing the apps one by one, let FILON do it. It finds the{" "}
          <span className="g">best offer of the moment</span> and takes you there. You have nothing to search for.
        </div>

        <h2>Stop comparing cashback alone</h2>
        <p>
          The next mistake is reasoning in « cashback » when the real question is <b>the real final price</b>. A 6%
          cashback on a new product can be beaten by an <b>equivalent refurbished</b> 30% cheaper, or by a stackable{" "}
          <b>promo code</b>. The right reflex is to compare the <b>total cost</b>, not one single line.
        </p>
        <p>
          That&apos;s FILON&apos;s philosophy: giving you one single number, your real price, and telling you whether
          to buy or wait.
        </p>

        <h2>In short</h2>
        <ul>
          <li>No cashback app is « the best » everywhere&nbsp;: the winning rate changes by merchant.</li>
          <li>Comparing before every purchase can double your cashback, but it&apos;s time-consuming by hand.</li>
          <li>Reason in <b>real final price</b> (cashback + refurbished + promo code), not cashback alone.</li>
          <li>FILON makes that comparison for you, free, on every purchase.</li>
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
