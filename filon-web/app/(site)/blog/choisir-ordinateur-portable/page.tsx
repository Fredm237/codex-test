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
              <tr><td><b>Mémoire (RAM)</b></td><td>Vérifiez le besoin des logiciels utilisés ; 8 Go et 16 Go ne conviennent pas aux mêmes usages.</td></tr>
              <tr><td><b>Stockage</b></td><td>Un <b>SSD</b> améliore généralement la réactivité ; choisissez la capacité selon vos fichiers.</td></tr>
              <tr><td><b>Processeur</b></td><td>Comparez le processeur à la charge prévue et aux exigences de vos logiciels.</td></tr>
              <tr><td><b>Écran</b></td><td>Choisissez résolution, taille et luminosité selon l&apos;usage et votre environnement.</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          La marque, le design, la connectique et la réparabilité peuvent aussi compter selon votre usage.
        </p>

        <h2>3. Quel niveau de configuration, selon le besoin</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Usage</th>
                <th>Ce qu&apos;il faut privilégier</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Bureautique & études</b></td><td>Un SSD, une mémoire adaptée à vos logiciels et une bonne autonomie si vous vous déplacez.</td></tr>
              <tr><td><b>Polyvalent</b></td><td>Un équilibre entre processeur, mémoire, stockage, écran et connectique.</td></tr>
              <tr><td><b>Création ou jeu</b></td><td>Vérifiez les besoins précis des logiciels, la carte graphique, le refroidissement et l&apos;écran.</td></tr>
            </tbody>
          </table>
        </div>

        <h2>4. Les pièges classiques</h2>
        <ul>
          <li><b>Une RAM insuffisante</b>&nbsp;: vérifiez les besoins de vos applications et la possibilité d&apos;évoluer.</li>
          <li><b>Le type de stockage</b>&nbsp;: contrôlez si l&apos;offre mentionne SSD ou disque mécanique.</li>
          <li><b>L&apos;écran</b>&nbsp;: vérifiez taille, résolution, luminosité et connectique selon votre usage.</li>
          <li><b>La «&nbsp;promo&nbsp;» gonflée</b>&nbsp;: un prix barré n&apos;est pas une preuve de bonne affaire.</li>
        </ul>

        <h2>Neuf ou reconditionné ?</h2>
        <p>
          Une offre reconditionnée peut constituer une alternative, mais le prix, l&apos;état, la batterie, les accessoires,
          la garantie et le retour varient. Consultez notre guide{" "}
          <a href="/blog/neuf-vs-reconditionne-economie-reelle">Neuf vs reconditionné</a> pour les vérifier par offre.
        </p>

        <div className="callout">
          <b>Un point de départ :</b> décrivez simplement votre besoin («&nbsp;un portable pour la fac&nbsp;»). FILON
          peut rechercher des offres dans son catalogue et présenter les informations disponibles. Vérifiez le modèle,
          la configuration, le prix et les conditions avant de commander.
        </div>

        <h2>En résumé</h2>
        <ul>
          <li>Choisissez selon l&apos;<b>usage</b>, pas selon les plus gros chiffres.</li>
          <li>Vérifiez la <b>RAM</b>, le stockage, le processeur et l&apos;écran en fonction de vos logiciels.</li>
          <li>Comparez les <b>configurations</b> plutôt qu&apos;un budget présenté comme universel.</li>
          <li>Pour le reconditionné, vérifiez l&apos;état, la garantie et les conditions du vendeur.</li>
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
              <tr><td><b>Geheugen (RAM)</b></td><td>Controleer de vereisten van je software; 8 GB en 16 GB passen niet bij dezelfde gebruiken.</td></tr>
              <tr><td><b>Opslag</b></td><td>Een <b>SSD</b> verbetert doorgaans de reactiesnelheid; kies capaciteit volgens je bestanden.</td></tr>
              <tr><td><b>Processor</b></td><td>Vergelijk de processor met de geplande belasting en vereisten van je software.</td></tr>
              <tr><td><b>Scherm</b></td><td>Kies resolutie, formaat en helderheid volgens gebruik en omgeving.</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Merk, design, aansluitingen en repareerbaarheid kunnen ook tellen volgens je gebruik.
        </p>

        <h2>3. Welk configuratieniveau, volgens de behoefte</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Gebruik</th>
                <th>Wat je moet voorrang geven</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Kantoorwerk & studie</b></td><td>Een SSD, geheugen aangepast aan je software en goede autonomie als je veel onderweg bent.</td></tr>
              <tr><td><b>Veelzijdig</b></td><td>Een evenwicht tussen processor, geheugen, opslag, scherm en aansluitingen.</td></tr>
              <tr><td><b>Creatie of gaming</b></td><td>Controleer de precieze softwarevereisten, grafische kaart, koeling en scherm.</td></tr>
            </tbody>
          </table>
        </div>

        <h2>4. De klassieke valkuilen</h2>
        <ul>
          <li><b>Onvoldoende RAM</b>&nbsp;: controleer de behoeften van je toepassingen en eventuele uitbreidbaarheid.</li>
          <li><b>Het type opslag</b>&nbsp;: controleer of het aanbod SSD of een mechanische schijf vermeldt.</li>
          <li><b>Het scherm</b>&nbsp;: controleer formaat, resolutie, helderheid en aansluitingen volgens je gebruik.</li>
          <li><b>De opgeblazen «&nbsp;promo&nbsp;»</b>&nbsp;: een doorstreepte prijs bewijst geen koopje.</li>
        </ul>

        <h2>Nieuw of refurbished ?</h2>
        <p>
          Een refurbished aanbod kan een alternatief zijn, maar prijs, staat, batterij, accessoires, garantie en retour
          verschillen. Lees onze gids{" "}
          <a href="/blog/neuf-vs-reconditionne-economie-reelle">Nieuw vs refurbished</a> om die per aanbod te controleren.
        </p>

        <div className="callout">
          <b>Een vertrekpunt:</b> beschrijf eenvoudig je behoefte («&nbsp;een laptop voor de unief&nbsp;»). FILON kan
          aanbiedingen in zijn catalogus zoeken en de beschikbare informatie tonen. Controleer model, configuratie,
          prijs en voorwaarden vóór je bestelt.
        </div>

        <h2>Samengevat</h2>
        <ul>
          <li>Kies volgens het <b>gebruik</b>, niet volgens de grootste cijfers.</li>
          <li>Controleer <b>RAM</b>, opslag, processor en scherm volgens je software.</li>
          <li>Vergelijk <b>configuraties</b> in plaats van een budget als universeel voor te stellen.</li>
          <li>Controleer bij refurbished de staat, garantie en voorwaarden van de verkoper.</li>
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
              <tr><td><b>Memory (RAM)</b></td><td>Check the needs of your software; 8 GB and 16 GB do not suit the same uses.</td></tr>
              <tr><td><b>Storage</b></td><td>An <b>SSD</b> generally improves responsiveness; choose capacity for your files.</td></tr>
              <tr><td><b>Processor</b></td><td>Compare the processor with the workload and requirements of your software.</td></tr>
              <tr><td><b>Screen</b></td><td>Choose resolution, size and brightness for your use and environment.</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          Brand, design, ports and repairability can also matter depending on your use.
        </p>

        <h2>3. Which configuration level, by need</h2>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Use</th>
                <th>What to prioritise</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Office work & study</b></td><td>An SSD, memory suited to your software and good battery life if you travel.</td></tr>
              <tr><td><b>Versatile</b></td><td>A balance of processor, memory, storage, screen and ports.</td></tr>
              <tr><td><b>Creation or gaming</b></td><td>Check precise software requirements, graphics, cooling and screen.</td></tr>
            </tbody>
          </table>
        </div>

        <h2>4. The classic traps</h2>
        <ul>
          <li><b>Insufficient RAM</b>&nbsp;: check the needs of your applications and upgrade options.</li>
          <li><b>The storage type</b>&nbsp;: check whether the offer states an SSD or mechanical drive.</li>
          <li><b>The screen</b>&nbsp;: check size, resolution, brightness and ports for your use.</li>
          <li><b>The inflated «&nbsp;promo&nbsp;»</b>&nbsp;: a struck-through price is no proof of a bargain.</li>
        </ul>

        <h2>New or refurbished ?</h2>
        <p>
          A refurbished offer can be an alternative, but price, condition, battery, accessories, warranty and returns
          vary. Read our guide{" "}
          <a href="/blog/neuf-vs-reconditionne-economie-reelle">New vs refurbished</a> to check them offer by offer.
        </p>

        <div className="callout">
          <b>A starting point:</b> simply describe your need («&nbsp;a laptop for university&nbsp;»). FILON can search
          offers in its catalogue and present available information. Check the model, configuration, price and terms
          before ordering.
        </div>

        <h2>In short</h2>
        <ul>
          <li>Choose by <b>use</b>, not by the biggest numbers.</li>
          <li>Check <b>RAM</b>, storage, processor and screen against your software.</li>
          <li>Compare <b>configurations</b> rather than treat one budget as universal.</li>
          <li>For refurbished, check condition, warranty and the seller&apos;s terms.</li>
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
