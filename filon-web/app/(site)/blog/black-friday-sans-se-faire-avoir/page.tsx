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
            C&apos;est le pic de l&apos;année sur la tech. Il y a de vraies affaires — et énormément de fausses.
            Voici comment distinguer les deux, et repartir avec un vrai bon prix.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-black-friday.webp" alt="" />
        <p>
          Fin novembre, tout devient «&nbsp;-50&nbsp;%&nbsp;». Le problème, c&apos;est qu&apos;un prix barré ne prouve
          rien&nbsp;: certains marchands montent le prix quelques semaines avant pour mieux le «&nbsp;baisser&nbsp;» le
          jour J. La bonne nouvelle&nbsp;: quelques réflexes suffisent pour ne pas tomber dans le panneau.
        </p>

        <h2>La règle d&apos;or : juger sur l&apos;historique</h2>
        <p>
          Une réduction ne vaut que par rapport au <b>prix habituel des derniers mois</b>, pas au prix barré affiché.
          Un produit «&nbsp;-40&nbsp;%&nbsp;» dont le prix «&nbsp;promo&nbsp;» reste au-dessus de sa moyenne des 90
          derniers jours n&apos;est pas une affaire. Le seul repère fiable, c&apos;est la <b>courbe de prix</b>.
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
          Le Black Friday reste le <b>meilleur moment de l&apos;année pour la tech</b>&nbsp;: TV, ordinateurs
          portables, casques audio, gros électroménager, consoles. Les générations sortantes profitent des plus
          fortes baisses, juste avant les nouveautés. À l&apos;inverse, les nouveautés récentes bougent peu.
        </p>

        <h2>La méthode en 4 réflexes</h2>
        <ul>
          <li><b>Repérez avant.</b> Notez le prix habituel des produits visés une à deux semaines avant.</li>
          <li><b>Comparez à l&apos;historique</b>, jamais au prix barré.</li>
          <li><b>Vérifiez le vrai prix final</b>&nbsp;: prix marchand + coupon + cashback, chez tous les vendeurs.</li>
          <li><b>Ne cédez pas au chrono.</b> Une vraie bonne affaire tient rarement à trois minutes près.</li>
        </ul>

        <div className="callout">
          <b>Le raccourci&nbsp;:</b> plutôt que de tout surveiller à la main, demandez à FILON. Il compare le prix
          à son <span className="g">historique</span>, tous marchands confondus, et vous dit d&apos;un coup d&apos;œil
          si c&apos;est une vraie affaire — ou du décor.
        </div>

        <h2>En résumé</h2>
        <ul>
          <li>Le prix barré ne prouve rien&nbsp;: jugez sur l&apos;<b>historique</b>.</li>
          <li>Méfiez-vous des <b>hausses avant l&apos;offre</b> et de la pression au chrono.</li>
          <li>La tech sortante offre les <b>vraies baisses</b>.</li>
          <li>Ce qui compte, c&apos;est le <b>prix final réel</b>, pas le pourcentage affiché.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Vraie affaire ou pas ? Demander à FILON
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
            Het is de piek van het jaar op tech. Er zijn echte koopjes — en heel veel valse. Hier lees je hoe je de
            twee onderscheidt, en met een echt goede prijs vertrekt.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-black-friday.webp" alt="" />
        <p>
          Eind november wordt alles «&nbsp;-50&nbsp;%&nbsp;». Het probleem is dat een doorstreepte prijs niets
          bewijst&nbsp;: sommige winkels verhogen de prijs enkele weken vooraf om hem op de dag zelf beter te kunnen
          «&nbsp;verlagen&nbsp;». Het goede nieuws&nbsp;: enkele reflexen volstaan om er niet in te trappen.
        </p>

        <h2>De gouden regel : oordeel op de geschiedenis</h2>
        <p>
          Een korting is alleen iets waard ten opzichte van de <b>gebruikelijke prijs van de laatste maanden</b>,
          niet van de getoonde doorstreepte prijs. Een product «&nbsp;-40&nbsp;%&nbsp;» waarvan de
          «&nbsp;promo&nbsp;»-prijs boven zijn gemiddelde van de laatste 90 dagen blijft, is geen koopje. Het enige
          betrouwbare ijkpunt is de <b>prijscurve</b>.
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
          Black Friday blijft het <b>beste moment van het jaar voor tech</b>&nbsp;: tv's, laptops, hoofdtelefoons,
          groot huishoudtoestellen, consoles. De uitgaande generaties profiteren van de grootste dalingen, net vóór
          de nieuwigheden. Omgekeerd bewegen recente nieuwigheden weinig.
        </p>

        <h2>De methode in 4 reflexen</h2>
        <ul>
          <li><b>Spot het vooraf.</b> Noteer de gebruikelijke prijs van de gemikte producten één tot twee weken vooraf.</li>
          <li><b>Vergelijk met de geschiedenis</b>, nooit met de doorstreepte prijs.</li>
          <li><b>Controleer de echte eindprijs</b>&nbsp;: winkelprijs + coupon + cashback, bij alle verkopers.</li>
          <li><b>Geef niet toe aan de klok.</b> Een echt koopje hangt zelden af van drie minuten.</li>
        </ul>

        <div className="callout">
          <b>De shortcut&nbsp;:</b> in plaats van alles met de hand te bewaken, vraag het aan FILON. Hij vergelijkt de
          prijs met zijn <span className="g">geschiedenis</span>, over alle winkels heen, en zegt je in één oogopslag
          of het een echt koopje is — of louter decor.
        </div>

        <h2>Samengevat</h2>
        <ul>
          <li>De doorstreepte prijs bewijst niets&nbsp;: oordeel op de <b>geschiedenis</b>.</li>
          <li>Wees op je hoede voor <b>stijgingen vóór het aanbod</b> en voor de druk van de klok.</li>
          <li>De uitgaande tech biedt de <b>echte dalingen</b>.</li>
          <li>Wat telt, is de <b>echte eindprijs</b>, niet het getoonde percentage.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Echt koopje of niet ? Vraag het aan FILON
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
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} />
    </>
  );
}
