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
            Le même produit ne coûte pas le même prix en janvier et en octobre. Le bon timing peut valoir des dizaines
            d&apos;euros. Voici quand les prix baissent vraiment, et quand se retenir.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-quand-acheter.webp" alt="" />
        <p>
          Bien acheter, ce n&apos;est pas seulement trouver le bon produit. C&apos;est aussi l&apos;acheter au bon
          moment. Les prix suivent des cycles assez réguliers : les connaître, c&apos;est payer moins sans rien
          sacrifier.
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

        <h2>Le calendrier des baisses, période par période</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Période</th>
                <th>Ce qui baisse</th>
                <th>Bon à savoir</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Janvier</b> (soldes hiver)</td><td className="g">Mode, électro, high-tech</td><td>Les meilleurs rabais de l&apos;hiver</td></tr>
              <tr><td><b>Février-mars</b></td><td className="g">High-tech sortant</td><td>Avant l&apos;arrivée des nouveautés du printemps</td></tr>
              <tr><td><b>Juillet</b> (soldes été)</td><td className="g">Presque tout</td><td>Le grand rendez-vous de mi-année</td></tr>
              <tr><td><b>Fin août</b> (rentrée)</td><td className="g">Portables, offres étudiantes</td><td>Idéal pour un PC d&apos;études</td></tr>
              <tr><td><b>Fin novembre</b> (Black Friday)</td><td className="g">High-tech, gros électro</td><td>Le pic de l&apos;année sur la tech</td></tr>
              <tr><td><b>Décembre</b> (avant Noël)</td><td>Peu, voire hausses</td><td>Prudence : certains prix remontent</td></tr>
            </tbody>
          </table>
        </div>

        <h2>Le bon moment d&apos;un produit précis</h2>
        <p>
          Au-delà du calendrier, chaque produit a son propre cycle. Le prix est le plus <b>haut au lancement</b>, puis
          il baisse progressivement, et touche souvent son <b>plancher juste avant l&apos;arrivée de la génération
          suivante</b>.
        </p>
        <p>
          Concrètement&nbsp;: les smartphones se renouvellent surtout à l&apos;automne, les gammes de PC au printemps.
          Acheter le modèle de l&apos;an dernier, quelques semaines avant la nouveauté, c&apos;est souvent le meilleur
          rapport qualité-prix de l&apos;année.
        </p>

        <h2>Le piège des fausses promos</h2>
        <p>
          Un prix barré n&apos;est pas une preuve de bonne affaire. Le vrai repère, c&apos;est l&apos;<b>historique</b>
          &nbsp;: un prix «&nbsp;réduit&nbsp;» qui reste au-dessus de sa moyenne des derniers mois n&apos;a rien
          d&apos;une aubaine. Comparez toujours au niveau habituel, pas au prix barré.
        </p>

        <div className="callout">
          <b>Le bon réflexe :</b> avant d&apos;acheter, demandez-vous si le prix est bas <span className="g">dans son
          cycle</span>. FILON vous le dit d&apos;un coup d&apos;œil : acheter maintenant, ou attendre.
        </div>

        <h2>En résumé</h2>
        <ul>
          <li>Deux grandes fenêtres en Belgique&nbsp;: <b>janvier</b> et <b>juillet</b>.</li>
          <li>Pour la tech, le pic reste le <b>Black Friday</b> fin novembre.</li>
          <li>Le meilleur prix d&apos;un produit tombe souvent <b>avant sa nouvelle génération</b>.</li>
          <li>Jugez une promo sur l&apos;<b>historique</b>, jamais sur le prix barré.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Savoir si c&apos;est le bon moment
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
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} />
    </>
  );
}
