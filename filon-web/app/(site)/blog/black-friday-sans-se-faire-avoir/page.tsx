import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";
import { Localized } from "@/components/editorial/Localized";

const PATH = "/blog/black-friday-sans-se-faire-avoir";
const TITLE = "Black Friday : le guide pour ne pas se faire avoir";
const DESC =
  "Le Black Friday, ce sont de vraies affaires… et beaucoup de fausses promos. Comment repérer les vrais rabais, éviter les prix gonflés, et acheter au bon moment.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

function ArticleFR() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Guide · 7 min · 2026</div>
          <h1>Black Friday : ne pas se faire avoir</h1>
          <p className="lede">
            Cette période concentre de nombreuses promotions, notamment sur la tech. Voici des repères pour analyser
            une offre sans vous fier au seul pourcentage affiché.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-black-friday.webp" alt="" />
        <p>
          Fin novembre, les pourcentages affichés se multiplient. Un prix barré ne suffit pas à évaluer une offre :
          comparez le produit exact, les conditions, les frais éventuels et, lorsqu&apos;elle est disponible, son évolution
          de prix. Quelques réflexes aident à prendre une décision plus posée.
        </p>

        <h2>La règle d&apos;or : juger sur l&apos;historique</h2>
        <p>
          Lorsqu&apos;un historique est disponible, il peut donner un contexte utile au prix affiché. Il ne remplace pas la
          vérification du modèle, de la disponibilité, des frais et des conditions de retour. Une <b>courbe de prix</b>
          est un indice parmi d&apos;autres, pas une garantie universelle.
        </p>

        <h2>Les fausses promos les plus courantes</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Ce que vous voyez</th>
                <th>Ce que ça cache souvent</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Prix barré très élevé</b></td><td>Un prix «&nbsp;conseillé&nbsp;» que personne ne payait</td></tr>
              <tr><td><b>Hausse juste avant l&apos;offre</b></td><td>Prix monté en octobre pour «&nbsp;baisser&nbsp;» en novembre</td></tr>
              <tr><td><b>«&nbsp;Stock limité&nbsp;», compte à rebours</b></td><td>Pression artificielle pour acheter vite</td></tr>
              <tr><td><b>Modèle «&nbsp;spécial Black Friday&nbsp;»</b></td><td>Version allégée, moins bien équipée</td></tr>
              <tr><td><b>-70&nbsp;% sur une marque inconnue</b></td><td>Produit dont le vrai prix est déjà bas ailleurs</td></tr>
            </tbody>
          </table>
        </div>

        <h2>Ce qui baisse vraiment fin novembre</h2>
        <p>
          Le Black Friday peut proposer des promotions sur la tech, l&apos;électroménager ou le jeu vidéo, mais leur niveau
          dépend du marchand, du modèle et du stock. Les générations précédentes peuvent parfois être concernées :
          comparez toujours l&apos;offre exacte plutôt que de supposer une baisse.
        </p>

        <h2>La méthode en 4 réflexes</h2>
        <ul>
          <li><b>Repérez avant.</b> Notez le prix affiché et les caractéristiques du produit qui vous intéresse.</li>
          <li><b>Utilisez l&apos;historique</b> lorsqu&apos;il est disponible, sans le confondre avec une garantie.</li>
          <li><b>Vérifiez le total applicable</b>&nbsp;: prix, frais, conditions, et coupon ou cashback seulement s&apos;ils sont indiqués.</li>
          <li><b>Prenez le temps.</b> Vérifiez l&apos;offre et les conditions avant de commander.</li>
        </ul>

        <div className="callout">
          <b>Un point de départ&nbsp;:</b> vous pouvez demander à FILON de rechercher des offres dans son catalogue.
          Lorsqu&apos;un prix, un historique, un score, un cashback ou un code est renseigné, il les présente pour vous
          aider à comparer. Vérifiez toujours les conditions du marchand avant de commander.
        </div>

        <h2>En résumé</h2>
        <ul>
          <li>Un prix barré ne suffit pas : utilisez l&apos;<b>historique</b> lorsqu&apos;il est disponible.</li>
          <li>Vérifiez le modèle, le vendeur, le stock et les conditions, sans céder à la pression du chrono.</li>
          <li>Les promotions varient selon les catégories, les marchands et les offres.</li>
          <li>Comparez le <b>prix affiché</b>, les frais et les avantages éventuels.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Analyser une offre avec FILON
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
          <div className="ed-article-meta">Gids · 7 min · 2026</div>
          <h1>Black Friday : je niet laten beetnemen</h1>
          <p className="lede">
            Deze periode bundelt veel promoties, vooral op tech. Dit zijn houvasten om een aanbod te analyseren zonder
            alleen op het getoonde percentage te vertrouwen.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-black-friday.webp" alt="" />
        <p>
          Eind november nemen de getoonde percentages toe. Een doorstreepte prijs volstaat niet om een aanbod te
          beoordelen: vergelijk het exacte product, de voorwaarden, eventuele kosten en, wanneer beschikbaar, de
          prijsontwikkeling. Enkele reflexen helpen om rustiger te beslissen.
        </p>

        <h2>De gouden regel : oordeel op de geschiedenis</h2>
        <p>
          Wanneer een historiek beschikbaar is, kan die nuttige context geven bij de getoonde prijs. Die vervangt niet
          de controle van model, beschikbaarheid, kosten en retourvoorwaarden. Een <b>prijscurve</b> is één aanwijzing,
          geen universele garantie.
        </p>

        <h2>De meest voorkomende valse promo's</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Wat je ziet</th>
                <th>Wat het vaak verbergt</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Erg hoge doorstreepte prijs</b></td><td>Een «&nbsp;adviesprijs&nbsp;» die niemand betaalde</td></tr>
              <tr><td><b>Stijging net vóór het aanbod</b></td><td>Prijs verhoogd in oktober om te «&nbsp;verlagen&nbsp;» in november</td></tr>
              <tr><td><b>«&nbsp;Beperkte voorraad&nbsp;», aftelklok</b></td><td>Kunstmatige druk om snel te kopen</td></tr>
              <tr><td><b>Model «&nbsp;speciaal Black Friday&nbsp;»</b></td><td>Uitgeklede versie, minder goed uitgerust</td></tr>
              <tr><td><b>-70&nbsp;% op een onbekend merk</b></td><td>Product waarvan de echte prijs elders al laag is</td></tr>
            </tbody>
          </table>
        </div>

        <h2>Wat echt daalt eind november</h2>
        <p>
          Black Friday kan promoties bieden op tech, huishoudtoestellen of gaming, maar hun niveau hangt af van de
          winkel, het model en de voorraad. Oudere generaties kunnen soms betrokken zijn: vergelijk altijd het exacte
          aanbod in plaats van een daling te veronderstellen.
        </p>

        <h2>De methode in 4 reflexen</h2>
        <ul>
          <li><b>Spot het vooraf.</b> Noteer de getoonde prijs en kenmerken van het product dat je wilt.</li>
          <li><b>Gebruik de historiek</b> wanneer die beschikbaar is, zonder die met een garantie te verwarren.</li>
          <li><b>Controleer het toepasselijke totaal</b>&nbsp;: prijs, kosten, voorwaarden en coupon of cashback alleen als die vermeld zijn.</li>
          <li><b>Neem de tijd.</b> Controleer het aanbod en de voorwaarden vóór je bestelt.</li>
        </ul>

        <div className="callout">
          <b>Een vertrekpunt:</b> je kunt FILON vragen om aanbiedingen in zijn catalogus te zoeken. Wanneer prijs,
          historiek, score, cashback of code vermeld zijn, toont het die om je te helpen vergelijken. Controleer altijd
          de voorwaarden van de winkel vóór je bestelt.
        </div>

        <h2>Samengevat</h2>
        <ul>
          <li>Een doorstreepte prijs volstaat niet: gebruik de <b>historiek</b> wanneer die beschikbaar is.</li>
          <li>Controleer model, winkel, voorraad en voorwaarden zonder toe te geven aan tijdsdruk.</li>
          <li>Promoties verschillen per categorie, winkel en aanbod.</li>
          <li>Vergelijk de <b>getoonde prijs</b>, kosten en eventuele voordelen.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Analyseer een aanbod met FILON
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
          <div className="ed-article-meta">Guide · 7 min · 2026</div>
          <h1>Black Friday : don&apos;t get fooled</h1>
          <p className="lede">
            This period brings together many promotions, especially in tech. Here are reference points to analyse an
            offer without relying on the percentage displayed alone.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-black-friday.webp" alt="" />
        <p>
          At the end of November, displayed percentages multiply. A struck-through price is not enough to assess an
          offer: compare the exact product, terms, possible fees and, when available, its price movement. A few
          reflexes help you make a more considered decision.
        </p>

        <h2>The golden rule: judge on the history</h2>
        <p>
          When a history is available, it can provide useful context for the displayed price. It does not replace
          checking the model, availability, fees and return terms. A <b>price curve</b> is one indicator among others,
          not a universal guarantee.
        </p>

        <h2>The most common fake promos</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>What you see</th>
                <th>What it often hides</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Very high struck-through price</b></td><td>A «&nbsp;recommended&nbsp;» price no one was paying</td></tr>
              <tr><td><b>Rise just before the offer</b></td><td>Price raised in October to «&nbsp;drop&nbsp;» in November</td></tr>
              <tr><td><b>«&nbsp;Limited stock&nbsp;», countdown</b></td><td>Artificial pressure to buy fast</td></tr>
              <tr><td><b>«&nbsp;Special Black Friday&nbsp;» model</b></td><td>Stripped-down version, less well equipped</td></tr>
              <tr><td><b>-70&nbsp;% on an unknown brand</b></td><td>Product whose real price is already low elsewhere</td></tr>
            </tbody>
          </table>
        </div>

        <h2>What really drops at the end of November</h2>
        <p>
          Black Friday can offer promotions on tech, appliances or gaming, but their level depends on the merchant,
          model and stock. Previous generations can sometimes be included: compare the exact offer rather than assume
          a price drop.
        </p>

        <h2>The method in 4 reflexes</h2>
        <ul>
          <li><b>Spot it beforehand.</b> Note the displayed price and features of the product you want.</li>
          <li><b>Use history</b> when it is available, without mistaking it for a guarantee.</li>
          <li><b>Check the applicable total</b>&nbsp;: price, fees, terms, and coupon or cashback only when listed.</li>
          <li><b>Take your time.</b> Check the offer and terms before ordering.</li>
        </ul>

        <div className="callout">
          <b>A starting point:</b> you can ask FILON to search offers in its catalogue. When a price, history, score,
          cashback or code is listed, it presents them to help you compare. Always check the merchant&apos;s terms before
          ordering.
        </div>

        <h2>In short</h2>
        <ul>
          <li>A struck-through price is not enough: use <b>history</b> when it is available.</li>
          <li>Check the model, merchant, stock and terms without giving in to time pressure.</li>
          <li>Promotions vary by category, merchant and offer.</li>
          <li>Compare the <b>displayed price</b>, fees and any benefits.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Analyse an offer with FILON
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
          { name: "Black Friday sans se faire avoir", path: PATH },
        ])}
      />
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} en={<ArticleEN />} />
    </>
  );
}
