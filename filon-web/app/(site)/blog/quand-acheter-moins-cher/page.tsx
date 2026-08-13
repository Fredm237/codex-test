import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";
import { Localized } from "@/components/editorial/Localized";

const PATH = "/blog/quand-acheter-moins-cher";
const TITLE = "Quand acheter pour payer moins cher : le calendrier des bons moments";
const DESC =
  "Le même produit ne coûte pas le même prix en janvier et en octobre. Soldes belges, Black Friday, rentrée, fin de cycle : voici quand les prix baissent vraiment.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

function ArticleFR() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Guide · 6 min · 2026</div>
          <h1>Quand acheter pour payer moins cher</h1>
          <p className="lede">
            Les prix d&apos;un même produit peuvent évoluer au fil de l&apos;année. Voici des repères pour comparer une offre et
            vérifier son contexte, sans présumer d&apos;une baisse garantie.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-quand-acheter.webp" alt="" />
        <p>
          Le moment d&apos;achat peut influencer le prix affiché, mais les évolutions dépendent du marchand, du modèle, du
          stock et de la zone de vente. Un calendrier sert de point de départ, pas de garantie de prix.
        </p>

        <h2>Les soldes, mais les vraies dates</h2>
        <p>
          En Belgique, les soldes sont encadrés par la loi. Deux grandes périodes&nbsp;: les <b>soldes d&apos;hiver</b>,
          à partir du 3 janvier, et les <b>soldes d&apos;été</b>, à partir du 1er juillet. Chacune dure environ un mois.
        </p>
        <p>
          Juste avant, il y a une <b>période d&apos;attente</b> (décembre et juin) pendant laquelle les vraies
          réductions sont limitées. Une «&nbsp;promo&nbsp;» affichée à ce moment mérite un œil méfiant.
        </p>

        <h2>Les périodes à surveiller</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Période</th>
                <th>À surveiller</th>
                <th>Bon réflexe</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Janvier</b> (soldes hiver)</td><td className="g">Les offres publiées</td><td>Comparez le produit et ses conditions</td></tr>
              <tr><td><b>Février-mars</b></td><td className="g">Les changements de gamme</td><td>Vérifiez le modèle exact et sa configuration</td></tr>
              <tr><td><b>Juillet</b> (soldes été)</td><td className="g">Les offres publiées</td><td>Ne déduisez pas une réduction du seul calendrier</td></tr>
              <tr><td><b>Fin août</b> (rentrée)</td><td className="g">Les offres adaptées aux études</td><td>Contrôlez les conditions de l&apos;offre</td></tr>
              <tr><td><b>Fin novembre</b> (Black Friday)</td><td className="g">Les promotions affichées</td><td>Utilisez l&apos;historique lorsqu&apos;il est disponible</td></tr>
              <tr><td><b>Décembre</b> (avant Noël)</td><td>Le stock et les délais de livraison</td><td>Vérifiez le prix et les conditions au moment d&apos;acheter</td></tr>
            </tbody>
          </table>
        </div>

        <h2>Le bon moment d&apos;un produit précis</h2>
        <p>
          Au-delà du calendrier, les prix d&apos;un modèle peuvent évoluer avec les stocks, les nouveautés et les décisions
          de chaque marchand. Une évolution passée ne permet pas de garantir le prix à venir.
        </p>
        <p>
          Un modèle précédent peut parfois être proposé à un prix différent, mais il faut comparer ses caractéristiques,
          sa disponibilité et ses conditions avec les autres offres accessibles au moment de votre recherche.
        </p>

        <h2>Le piège des fausses promos</h2>
        <p>
          Un prix barré n&apos;est pas une preuve de bonne affaire. Lorsqu&apos;un <b>historique</b> est disponible, il peut
          apporter du contexte, mais il ne remplace pas la vérification du modèle, des frais, du stock et des conditions.
        </p>

        <div className="callout">
          <b>Le bon réflexe :</b> avant d&apos;acheter, consultez les informations disponibles pour l&apos;offre. FILON peut
          afficher le prix, le score ou l&apos;historique lorsqu&apos;ils sont renseignés afin de vous aider à comparer ; la
          décision finale vous appartient.
        </div>

        <h2>En résumé</h2>
        <ul>
          <li>Les périodes de soldes peuvent être des moments utiles à surveiller en Belgique.</li>
          <li>Les promotions et leur niveau varient selon le marchand et l&apos;offre.</li>
          <li>Un changement de gamme ne garantit pas le prix d&apos;un modèle.</li>
          <li>Utilisez l&apos;<b>historique</b> lorsqu&apos;il est disponible, avec les autres informations de l&apos;offre.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Comparer les offres disponibles
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
          <h1>Wanneer kopen om minder te betalen</h1>
          <p className="lede">
            Hetzelfde product kost niet dezelfde prijs in januari en in oktober. De juiste timing kan tientallen euro's
            waard zijn. Hier lees je wanneer de prijzen echt dalen, en wanneer je je moet inhouden.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-quand-acheter.webp" alt="" />
        <p>
          Goed kopen is niet alleen het juiste product vinden. Het is het ook op het juiste moment kopen. Prijzen
          volgen vrij regelmatige cycli : ze kennen, is minder betalen zonder iets op te offeren.
        </p>

        <h2>De solden, maar de echte data</h2>
        <p>
          In België zijn de solden wettelijk omkaderd. Twee grote periodes&nbsp;: de <b>wintersolden</b>, vanaf 3
          januari, en de <b>zomersolden</b>, vanaf 1 juli. Elk duurt ongeveer een maand.
        </p>
        <p>
          Net ervoor is er een <b>sperperiode</b> (december en juni) waarin de echte kortingen beperkt zijn. Een
          «&nbsp;promo&nbsp;» die op dat moment getoond wordt, verdient een wantrouwig oog.
        </p>

        <h2>De kalender van de dalingen, periode per periode</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Periode</th>
                <th>Wat daalt</th>
                <th>Goed om te weten</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Januari</b> (wintersolden)</td><td className="g">Mode, elektro, high-tech</td><td>De beste kortingen van de winter</td></tr>
              <tr><td><b>Februari-maart</b></td><td className="g">Uitgaande high-tech</td><td>Vóór de komst van de lentenieuwigheden</td></tr>
              <tr><td><b>Juli</b> (zomersolden)</td><td className="g">Bijna alles</td><td>De grote afspraak van halfjaar</td></tr>
              <tr><td><b>Eind augustus</b> (terug naar school)</td><td className="g">Laptops, studentenaanbiedingen</td><td>Ideaal voor een studie-pc</td></tr>
              <tr><td><b>Eind november</b> (Black Friday)</td><td className="g">High-tech, groot elektro</td><td>De piek van het jaar op tech</td></tr>
              <tr><td><b>December</b> (vóór Kerst)</td><td>Weinig, zelfs stijgingen</td><td>Voorzichtig : sommige prijzen gaan omhoog</td></tr>
            </tbody>
          </table>
        </div>

        <h2>Het juiste moment van een specifiek product</h2>
        <p>
          Naast de kalender heeft elk product zijn eigen cyclus. De prijs is het <b>hoogst bij de lancering</b>, daalt
          dan geleidelijk, en raakt vaak zijn <b>bodem net vóór de komst van de volgende generatie</b>.
        </p>
        <p>
          Concreet&nbsp;: smartphones vernieuwen vooral in de herfst, de pc-reeksen in de lente. Het model van vorig
          jaar kopen, enkele weken vóór de nieuwigheid, is vaak de beste prijs-kwaliteitverhouding van het jaar.
        </p>

        <h2>De valkuil van de valse promo's</h2>
        <p>
          Een doorstreepte prijs bewijst geen koopje. Het echte ijkpunt is de <b>geschiedenis</b>&nbsp;: een
          «&nbsp;verlaagde&nbsp;» prijs die boven zijn gemiddelde van de laatste maanden blijft, is geen buitenkans.
          Vergelijk altijd met het gebruikelijke niveau, nooit met de doorstreepte prijs.
        </p>

        <div className="callout">
          <b>De goede reflex :</b> vóór je koopt, vraag je af of de prijs laag is <span className="g">binnen zijn
          cyclus</span>. FILON zegt je het in één oogopslag : nu kopen, of wachten.
        </div>

        <h2>Samengevat</h2>
        <ul>
          <li>Twee grote vensters in België&nbsp;: <b>januari</b> en <b>juli</b>.</li>
          <li>Voor tech blijft de piek de <b>Black Friday</b> eind november.</li>
          <li>De beste prijs van een product valt vaak <b>vóór zijn nieuwe generatie</b>.</li>
          <li>Beoordeel een promo op de <b>geschiedenis</b>, nooit op de doorstreepte prijs.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Weten of het het juiste moment is
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
          <h1>When to buy to pay less</h1>
          <p className="lede">
            The price of a product can move through the year. Here are reference points to compare an offer and check
            its context, without assuming a guaranteed price drop.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-quand-acheter.webp" alt="" />
        <p>
          Timing can influence a displayed price, but changes depend on the merchant, model, stock and selling area.
          A calendar is a starting point, not a price guarantee.
        </p>

        <h2>The sales, but the real dates</h2>
        <p>
          In Belgium, the sales are governed by law. Two main periods&nbsp;: the <b>winter sales</b>, from 3 January,
          and the <b>summer sales</b>, from 1 July. Each lasts about a month.
        </p>
        <p>
          Just before, there&apos;s a <b>blackout period</b> (December and June) during which real discounts are
          limited. A «&nbsp;promo&nbsp;» shown at that time deserves a wary eye.
        </p>

        <h2>Periods to watch</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Period</th>
                <th>What to watch</th>
                <th>Useful reflex</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>January</b> (winter sales)</td><td className="g">Published offers</td><td>Compare the product and its terms</td></tr>
              <tr><td><b>February-March</b></td><td className="g">Range changes</td><td>Check the exact model and configuration</td></tr>
              <tr><td><b>July</b> (summer sales)</td><td className="g">Published offers</td><td>Do not infer a discount from the calendar alone</td></tr>
              <tr><td><b>Late August</b> (back to school)</td><td className="g">Education-oriented offers</td><td>Check the offer terms</td></tr>
              <tr><td><b>Late November</b> (Black Friday)</td><td className="g">Displayed promotions</td><td>Use history when it is available</td></tr>
              <tr><td><b>December</b> (before Christmas)</td><td>Stock and delivery times</td><td>Check price and terms when buying</td></tr>
            </tbody>
          </table>
        </div>

        <h2>The right moment for a specific product</h2>
        <p>
          Beyond the calendar, a model&apos;s price can change with stock, new releases and each merchant&apos;s decisions.
          Past movement cannot guarantee a future price.
        </p>
        <p>
          A previous model can sometimes be offered at a different price, but compare its features, availability and
          terms with the other offers accessible at the time of your search.
        </p>

        <h2>The fake-promo trap</h2>
        <p>
          A struck-through price is no proof of a bargain. When <b>history</b> is available, it can add context, but it
          does not replace checking the model, fees, stock and terms.
        </p>

        <div className="callout">
          <b>The useful reflex:</b> before buying, consult the information available for the offer. FILON can display
          the price, score or history when listed to help you compare; the final decision remains yours.
        </div>

        <h2>In short</h2>
        <ul>
          <li>Sale periods can be useful moments to watch in Belgium.</li>
          <li>Promotions and their level vary by merchant and offer.</li>
          <li>A range change does not guarantee a model&apos;s price.</li>
          <li>Use <b>history</b> when it is available, with the other offer information.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Compare available offers
          </a>
        </p>
      </div>
    </article>
  );
}

export default function ArticlePage() {
  return (
    <>
      <JsonLd data={articleSchema({ title: TITLE, description: DESC, path: PATH, datePublished: "2026-06-18" })} />
      <JsonLd
        data={breadcrumbSchema([
          { name: "Accueil", path: "/" },
          { name: "Blog", path: "/blog" },
          { name: "Quand acheter moins cher", path: PATH },
        ])}
      />
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} en={<ArticleEN />} />
    </>
  );
}
