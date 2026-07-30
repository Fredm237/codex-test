import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";
import { Localized } from "@/components/editorial/Localized";

const PATH = "/blog/choisir-ordinateur-portable";
const TITLE = "Bien choisir son ordinateur portable : le guide simple";
const DESC =
  "Quelle RAM, quel stockage, quel processeur ? Le guide clair pour choisir un ordinateur portable selon votre usage et votre budget, sans jargon et sans se faire avoir.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

function ArticleFR() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Guide · 7 min · 2026</div>
          <h1>Bien choisir son ordinateur portable</h1>
          <p className="lede">
            Les fiches techniques sont conçues pour vous perdre. Voici l&apos;essentiel, expliqué simplement, pour
            choisir la bonne machine selon votre usage et votre budget.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-choisir-portable.webp" alt="" />
        <p>
          Un bon ordinateur portable n&apos;est pas le plus cher, ni celui avec les plus gros chiffres. C&apos;est celui
          qui correspond à ce que vous en ferez. Commencez toujours par là.
        </p>

        <h2>1. Partez de l&apos;usage, pas de la fiche technique</h2>
        <ul>
          <li><b>Bureautique et études</b>&nbsp;: navigation, traitement de texte, visios. Pas besoin d&apos;une bête de course.</li>
          <li><b>Création</b> (photo, vidéo, design)&nbsp;: là, le processeur, la mémoire et l&apos;écran comptent vraiment.</li>
          <li><b>Jeu</b>&nbsp;: une carte graphique dédiée devient indispensable.</li>
          <li><b>Mobilité</b>&nbsp;: si vous vous déplacez beaucoup, le poids et l&apos;autonomie priment sur la puissance.</li>
        </ul>

        <h2>2. Les quatre choses qui comptent vraiment</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Élément</th>
                <th>Le repère simple</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Mémoire (RAM)</b></td><td><b>16 Go</b> pour durer. 8 Go suffisent pour un usage léger, mais vieillissent vite.</td></tr>
              <tr><td><b>Stockage</b></td><td>Un <b>SSD</b>, jamais un disque mécanique. 512 Go est le bon confort.</td></tr>
              <tr><td><b>Processeur</b></td><td>Gamme intermédiaire (type Core i5 / Ryzen 5) pour l&apos;équilibre prix-performance.</td></tr>
              <tr><td><b>Écran</b></td><td>Résolution <b>Full HD</b> minimum, et une bonne luminosité si vous travaillez près d&apos;une fenêtre.</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Le reste (marque, design, détails) vient après. Ces quatre points décident 90&nbsp;% de la satisfaction.
        </p>

        <h2>3. Combien mettre, selon le besoin</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Budget</th>
                <th>Ce que vous avez</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>400 à 600 €</b></td><td>Bureautique et études, sans fioritures. Visez 16 Go et un SSD.</td></tr>
              <tr><td><b>700 à 900 €</b></td><td>Le vrai point d&apos;équilibre&nbsp;: polyvalent, rapide, durable.</td></tr>
              <tr><td><b>1000 € et plus</b></td><td>Création ou jeu&nbsp;: écran soigné, carte graphique, autonomie.</td></tr>
            </tbody>
          </table>
        </div>

        <h2>4. Les pièges classiques</h2>
        <ul>
          <li><b>Trop peu de RAM</b>&nbsp;: 8 Go aujourd&apos;hui, c&apos;est déjà juste pour les années à venir.</li>
          <li><b>Un disque mécanique</b> caché derrière un gros chiffre de stockage&nbsp;: fuyez, c&apos;est lent.</li>
          <li><b>Un écran terne</b>&nbsp;: on l&apos;oublie en magasin, on le regrette tous les jours.</li>
          <li><b>La «&nbsp;promo&nbsp;» gonflée</b>&nbsp;: un prix barré n&apos;est pas une preuve de bonne affaire.</li>
        </ul>

        <h2>Neuf ou reconditionné ?</h2>
        <p>
          Sur un portable, le reconditionné garanti fait souvent baisser la facture de 25 à 40&nbsp;% pour une machine
          identique. On détaille tout dans notre guide{" "}
          <a href="/blog/neuf-vs-reconditionne-economie-reelle">Neuf vs reconditionné</a>.
        </p>

        <div className="callout">
          <b>Le raccourci :</b> décrivez simplement votre besoin («&nbsp;un portable pour la fac à 800&nbsp;€&nbsp;»)
          et FILON vous propose les meilleurs choix, avec votre <span className="g">vrai prix</span> et le bon moment
          pour acheter.
        </div>

        <h2>En résumé</h2>
        <ul>
          <li>Choisissez selon l&apos;<b>usage</b>, pas selon les plus gros chiffres.</li>
          <li>Visez <b>16 Go de RAM</b> et un <b>SSD</b> pour durer.</li>
          <li>Le meilleur équilibre se situe autour de <b>700 à 900 €</b>.</li>
          <li>Pensez au <b>reconditionné garanti</b> pour la même machine, moins chère.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Trouver mon portable avec FILON
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
          <h1>Je laptop goed kiezen</h1>
          <p className="lede">
            Technische fiches zijn gemaakt om je te doen verdwalen. Hier lees je het essentiële, simpel uitgelegd, om
            de juiste machine te kiezen volgens je gebruik en je budget.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-choisir-portable.webp" alt="" />
        <p>
          Een goede laptop is niet de duurste, noch die met de grootste cijfers. Het is die welke past bij wat je
          ermee gaat doen. Begin daar altijd mee.
        </p>

        <h2>1. Vertrek van het gebruik, niet van de technische fiche</h2>
        <ul>
          <li><b>Kantoorwerk en studie</b>&nbsp;: surfen, tekstverwerking, videogesprekken. Geen krachtpatser nodig.</li>
          <li><b>Creatie</b> (foto, video, design)&nbsp;: daar tellen de processor, het geheugen en het scherm echt.</li>
          <li><b>Gaming</b>&nbsp;: een aparte grafische kaart wordt onmisbaar.</li>
          <li><b>Mobiliteit</b>&nbsp;: als je veel onderweg bent, primeren gewicht en autonomie op kracht.</li>
        </ul>

        <h2>2. De vier dingen die echt tellen</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Element</th>
                <th>Het simpele ijkpunt</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Geheugen (RAM)</b></td><td><b>16 GB</b> om lang mee te gaan. 8 GB volstaat voor licht gebruik, maar veroudert snel.</td></tr>
              <tr><td><b>Opslag</b></td><td>Een <b>SSD</b>, nooit een mechanische schijf. 512 GB is het goede comfort.</td></tr>
              <tr><td><b>Processor</b></td><td>Middenklasse (type Core i5 / Ryzen 5) voor de balans prijs-prestatie.</td></tr>
              <tr><td><b>Scherm</b></td><td><b>Full HD</b>-resolutie minimum, en een goede helderheid als je naast een raam werkt.</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          De rest (merk, design, details) komt daarna. Deze vier punten bepalen 90&nbsp;% van de tevredenheid.
        </p>

        <h2>3. Hoeveel uitgeven, volgens de behoefte</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Budget</th>
                <th>Wat je krijgt</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>400 tot 600 €</b></td><td>Kantoorwerk en studie, zonder franjes. Mik op 16 GB en een SSD.</td></tr>
              <tr><td><b>700 tot 900 €</b></td><td>Het echte evenwichtspunt&nbsp;: veelzijdig, snel, duurzaam.</td></tr>
              <tr><td><b>1000 € en meer</b></td><td>Creatie of gaming&nbsp;: verzorgd scherm, grafische kaart, autonomie.</td></tr>
            </tbody>
          </table>
        </div>

        <h2>4. De klassieke valkuilen</h2>
        <ul>
          <li><b>Te weinig RAM</b>&nbsp;: 8 GB vandaag is al krap voor de komende jaren.</li>
          <li><b>Een mechanische schijf</b> verborgen achter een groot opslagcijfer&nbsp;: vlucht ervoor, het is traag.</li>
          <li><b>Een fletse scherm</b>&nbsp;: je vergeet het in de winkel, je betreurt het elke dag.</li>
          <li><b>De opgeblazen «&nbsp;promo&nbsp;»</b>&nbsp;: een doorstreepte prijs bewijst geen koopje.</li>
        </ul>

        <h2>Nieuw of refurbished ?</h2>
        <p>
          Op een laptop doet gegarandeerd refurbished de factuur vaak met 25 tot 40&nbsp;% dalen voor een identieke
          machine. We leggen alles uit in onze gids{" "}
          <a href="/blog/neuf-vs-reconditionne-economie-reelle">Nieuw vs refurbished</a>.
        </p>

        <div className="callout">
          <b>De shortcut :</b> beschrijf gewoon je behoefte («&nbsp;een laptop voor de unief aan 800&nbsp;€&nbsp;»)
          en FILON stelt je de beste keuzes voor, met je <span className="g">echte prijs</span> en het juiste moment
          om te kopen.
        </div>

        <h2>Samengevat</h2>
        <ul>
          <li>Kies volgens het <b>gebruik</b>, niet volgens de grootste cijfers.</li>
          <li>Mik op <b>16 GB RAM</b> en een <b>SSD</b> om lang mee te gaan.</li>
          <li>De beste balans ligt rond <b>700 tot 900 €</b>.</li>
          <li>Denk aan <b>gegarandeerd refurbished</b> voor dezelfde machine, goedkoper.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Mijn laptop vinden met FILON
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
          <h1>Choosing your laptop well</h1>
          <p className="lede">
            Spec sheets are designed to lose you. Here are the essentials, explained simply, to choose the right
            machine by your use and your budget.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-choisir-portable.webp" alt="" />
        <p>
          A good laptop isn&apos;t the most expensive, nor the one with the biggest numbers. It&apos;s the one that
          matches what you&apos;ll do with it. Always start there.
        </p>

        <h2>1. Start from the use, not the spec sheet</h2>
        <ul>
          <li><b>Office work and study</b>&nbsp;: browsing, word processing, video calls. No need for a powerhouse.</li>
          <li><b>Creation</b> (photo, video, design)&nbsp;: there, the processor, memory and screen really count.</li>
          <li><b>Gaming</b>&nbsp;: a dedicated graphics card becomes essential.</li>
          <li><b>Mobility</b>&nbsp;: if you move around a lot, weight and battery life beat raw power.</li>
        </ul>

        <h2>2. The four things that really count</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Element</th>
                <th>The simple benchmark</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Memory (RAM)</b></td><td><b>16 GB</b> to last. 8 GB is enough for light use, but ages fast.</td></tr>
              <tr><td><b>Storage</b></td><td>An <b>SSD</b>, never a mechanical drive. 512 GB is the sweet spot.</td></tr>
              <tr><td><b>Processor</b></td><td>Mid-range (like Core i5 / Ryzen 5) for the price-performance balance.</td></tr>
              <tr><td><b>Screen</b></td><td><b>Full HD</b> resolution minimum, and good brightness if you work near a window.</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          The rest (brand, design, details) comes after. These four points decide 90&nbsp;% of satisfaction.
        </p>

        <h2>3. How much to spend, by need</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Budget</th>
                <th>What you get</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>€400 to €600</b></td><td>Office work and study, no frills. Aim for 16 GB and an SSD.</td></tr>
              <tr><td><b>€700 to €900</b></td><td>The real balance point&nbsp;: versatile, fast, durable.</td></tr>
              <tr><td><b>€1000 and up</b></td><td>Creation or gaming&nbsp;: polished screen, graphics card, battery life.</td></tr>
            </tbody>
          </table>
        </div>

        <h2>4. The classic traps</h2>
        <ul>
          <li><b>Too little RAM</b>&nbsp;: 8 GB today is already tight for the years ahead.</li>
          <li><b>A mechanical drive</b> hidden behind a big storage number&nbsp;: run away, it&apos;s slow.</li>
          <li><b>A dull screen</b>&nbsp;: you forget it in the shop, you regret it every day.</li>
          <li><b>The inflated «&nbsp;promo&nbsp;»</b>&nbsp;: a struck-through price is no proof of a bargain.</li>
        </ul>

        <h2>New or refurbished ?</h2>
        <p>
          On a laptop, guaranteed refurbished often cuts the bill by 25 to 40&nbsp;% for an identical machine. We
          detail everything in our guide{" "}
          <a href="/blog/neuf-vs-reconditionne-economie-reelle">New vs refurbished</a>.
        </p>

        <div className="callout">
          <b>The shortcut :</b> simply describe your need («&nbsp;a laptop for uni at €800&nbsp;») and FILON suggests
          the best choices, with your <span className="g">real price</span> and the right moment to buy.
        </div>

        <h2>In short</h2>
        <ul>
          <li>Choose by <b>use</b>, not by the biggest numbers.</li>
          <li>Aim for <b>16 GB of RAM</b> and an <b>SSD</b> to last.</li>
          <li>The best balance sits around <b>€700 to €900</b>.</li>
          <li>Think <b>guaranteed refurbished</b> for the same machine, cheaper.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Find my laptop with FILON
          </a>
        </p>
      </div>
    </article>
  );
}

export default function ArticlePage() {
  return (
    <>
      <JsonLd data={articleSchema({ title: TITLE, description: DESC, path: PATH, datePublished: "2026-07-09" })} />
      <JsonLd
        data={breadcrumbSchema([
          { name: "Accueil", path: "/" },
          { name: "Blog", path: "/blog" },
          { name: "Choisir son ordinateur portable", path: PATH },
        ])}
      />
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} en={<ArticleEN />} />
    </>
  );
}
