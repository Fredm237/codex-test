import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";
import { Localized } from "@/components/editorial/Localized";

const PATH = "/blog/neuf-vs-reconditionne-economie-reelle";
const TITLE = "Neuf vs reconditionné : l'économie réelle, produit par produit";
const DESC =
  "Combien économise-t-on vraiment en choisissant le reconditionné ? Écarts de prix, grades, garanties, et le cumul avec le cashback, le guide clair pour décider.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

function ArticleFR() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Guide · 5 min · 2026</div>
          <h1>Neuf vs reconditionné&nbsp;: l&apos;économie réelle</h1>
          <p className="lede">
            « Reconditionné » rime souvent avec « moins cher », mais l&apos;écart et les conditions varient. Voici les
            points à vérifier pour décider avec plus de contexte.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-neuf-vs-reconditionne.webp" alt="" />
        <p>
          Une offre reconditionnée concerne généralement un appareil déjà utilisé et remis en vente après un processus
          défini par le vendeur. Les contrôles, accessoires, garanties et conditions de retour varient selon l&apos;offre.
          Comparez le <b>type de produit</b>, l&apos;état annoncé et les <b>conditions du marchand</b>.
        </p>

        <h2>Ce qu&apos;il faut comparer, catégorie par catégorie</h2>
        <p>Il n&apos;existe pas d&apos;écart universel avec le neuf. Comparez les éléments affichés pour chaque offre :</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Catégorie</th>
                <th>À vérifier</th>
                <th>Bon réflexe</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Smartphones</b></td><td className="g">État, batterie, stockage</td><td>Comparez le modèle exact et la capacité</td></tr>
              <tr><td><b>Ordinateurs portables</b></td><td className="g">Batterie, écran, clavier</td><td>Contrôlez la configuration annoncée</td></tr>
              <tr><td><b>Consoles & tablettes</b></td><td className="g">Accessoires et connectique</td><td>Vérifiez ce qui est inclus</td></tr>
              <tr><td><b>Audio</b></td><td className="g">Hygiène et accessoires</td><td>Lisez les conditions du vendeur</td></tr>
              <tr><td><b>Électroménager</b></td><td className="g">Installation et garantie</td><td>Vérifiez retour, livraison et prise en charge</td></tr>
            </tbody>
          </table>
        </div>

        <h2>Comprendre les grades</h2>
        <ul>
          <li><b>Grade A+ / « comme neuf »</b>, aucune ou quasi aucune trace d&apos;usage. Le meilleur compromis prix/état.</li>
          <li><b>Grade A / « très bon état »</b>, micro-rayures invisibles à distance d&apos;usage.</li>
          <li><b>Grade B / « bon état »</b>, marques visibles mais sans impact sur le fonctionnement. Le plus économique.</li>
        </ul>
        <p>
          Les appellations de grade ne sont pas standardisées. Elles décrivent souvent l&apos;aspect extérieur, mais il faut
          vérifier chez le vendeur ce qu&apos;elles couvrent, ainsi que les tests réalisés, l&apos;état de la batterie et les
          accessoires inclus.
        </p>

        <h2>La garantie, le vrai filet de sécurité</h2>
        <p>
          La durée et l&apos;étendue de la garantie diffèrent selon le vendeur, le pays et le produit. Avant d&apos;acheter,
          vérifiez la <b>garantie proposée</b>, la procédure de retour, les exclusions et l&apos;identité du vendeur. Une
          garantie ne supprime pas tous les risques, mais elle précise le recours disponible.
        </p>

        <div className="callout">
          <b>Le bon calcul :</b> comparez le <span className="g">prix affiché, l&apos;état, la garantie, le retour et les
          avantages éventuels</span>. Le cashback et les codes promo ne doivent être pris en compte que lorsqu&apos;ils sont
          indiqués pour l&apos;offre ; FILON les présente alors avec les autres informations disponibles.
        </div>

        <h2>Et l&apos;écologie ?</h2>
        <p>
          Réutiliser un appareil peut prolonger sa durée d&apos;usage et éviter un remplacement immédiat. Son impact dépend
          toutefois de son état, de la remise en état, de la durée d&apos;utilisation et du transport. Ne déduisez pas une
          performance environnementale identique pour chaque offre.
        </p>

        <h2>En résumé</h2>
        <ul>
          <li>Le prix et l&apos;écart avec le neuf dépendent de l&apos;offre précise.</li>
          <li>Les <b>grades</b> n&apos;ont pas une définition universelle.</li>
          <li>Vérifiez toujours la <b>garantie</b>, le retour et les exclusions du vendeur.</li>
          <li>Ajoutez cashback ou code promo uniquement lorsqu&apos;ils sont confirmés pour l&apos;offre.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Comparer neuf et reconditionné avec FILON
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
          <div className="ed-article-meta">Gids · 5 min · 2026</div>
          <h1>Nieuw vs refurbished&nbsp;: de echte besparing</h1>
          <p className="lede">
            « Refurbished » rijmt vaak met « goedkoper », maar het verschil en de voorwaarden variëren. Dit zijn de
            punten die je moet controleren om met meer context te beslissen.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-neuf-vs-reconditionne.webp" alt="" />
        <p>
          Een refurbished aanbod betreft doorgaans een eerder gebruikt toestel dat na een door de verkoper bepaald
          proces opnieuw wordt verkocht. Controles, accessoires, garantie en retourvoorwaarden verschillen per aanbod.
          Vergelijk het <b>type product</b>, de aangegeven staat en de <b>voorwaarden van de winkel</b>.
        </p>

        <h2>Wat je vergelijkt, categorie per categorie</h2>
        <p>Er bestaat geen universeel verschil met nieuw. Vergelijk de elementen die bij elk aanbod worden getoond:</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Categorie</th>
                <th>Te controleren</th>
                <th>Nuttige reflex</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Smartphones</b></td><td className="g">Staat, batterij, opslag</td><td>Vergelijk exact model en capaciteit</td></tr>
              <tr><td><b>Laptops</b></td><td className="g">Batterij, scherm, toetsenbord</td><td>Controleer de aangegeven configuratie</td></tr>
              <tr><td><b>Consoles & tablets</b></td><td className="g">Accessoires en aansluitingen</td><td>Controleer wat inbegrepen is</td></tr>
              <tr><td><b>Audio</b></td><td className="g">Hygiëne en accessoires</td><td>Lees de verkopersvoorwaarden</td></tr>
              <tr><td><b>Huishoudtoestellen</b></td><td className="g">Installatie en garantie</td><td>Controleer retour, levering en ondersteuning</td></tr>
            </tbody>
          </table>
        </div>

        <h2>De grades begrijpen</h2>
        <ul>
          <li><b>Grade A+ / « als nieuw »</b>, geen of nauwelijks gebruikssporen. Het beste compromis prijs/toestand.</li>
          <li><b>Grade A / « zeer goede staat »</b>, microkrasjes onzichtbaar op gebruiksafstand.</li>
          <li><b>Grade B / « goede staat »</b>, zichtbare sporen maar zonder impact op de werking. Het goedkoopst.</li>
        </ul>
        <p>
          Gradebenamingen zijn niet gestandaardiseerd. Ze beschrijven vaak het uiterlijk, maar controleer bij de
          verkoper wat ze dekken, samen met uitgevoerde tests, batterijtoestand en inbegrepen accessoires.
        </p>

        <h2>De garantie, het echte vangnet</h2>
        <p>
          De duur en reikwijdte van de garantie verschillen per verkoper, land en product. Controleer vóór je koopt de
          <b>geboden garantie</b>, retourprocedure, uitsluitingen en identiteit van de verkoper. Een garantie neemt niet
          elk risico weg, maar verduidelijkt wel het mogelijke verhaal.
        </p>

        <div className="callout">
          <b>De juiste berekening:</b> vergelijk de <span className="g">getoonde prijs, staat, garantie, retour en
          eventuele voordelen</span>. Cashback en promotiecodes tel je alleen mee wanneer ze voor het aanbod vermeld zijn;
          FILON toont ze dan met de andere beschikbare gegevens.
        </div>

        <h2>En de ecologie ?</h2>
        <p>
          Een toestel opnieuw gebruiken kan de gebruiksduur verlengen en een onmiddellijke vervanging vermijden. De
          impact hangt echter af van de staat, opknapbeurt, gebruiksduur en het transport. Leid geen gelijke
          milieuprestatie af voor elk aanbod.
        </p>

        <h2>Samengevat</h2>
        <ul>
          <li>Prijs en verschil met nieuw hangen af van het concrete aanbod.</li>
          <li><b>Grades</b> hebben geen universele definitie.</li>
          <li>Controleer altijd <b>garantie</b>, retour en uitsluitingen van de verkoper.</li>
          <li>Voeg cashback of promocode alleen toe wanneer die voor het aanbod bevestigd zijn.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Nieuw en refurbished vergelijken met FILON
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
          <div className="ed-article-meta">Guide · 5 min · 2026</div>
          <h1>New vs refurbished&nbsp;: the real saving</h1>
          <p className="lede">
            « Refurbished » often rhymes with « cheaper », but the difference and conditions vary. Here are the points
            to check so you can decide with more context.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-neuf-vs-reconditionne.webp" alt="" />
        <p>
          A refurbished offer generally concerns a previously used device resold after a process defined by the seller.
          Checks, accessories, warranty and return terms vary by offer. Compare the <b>type of product</b>, stated
          condition and the <b>merchant&apos;s terms</b>.
        </p>

        <h2>What to compare, category by category</h2>
        <p>There is no universal gap with new. Compare the elements shown for each offer:</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>What to check</th>
                <th>Useful reflex</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Smartphones</b></td><td className="g">Condition, battery, storage</td><td>Compare the exact model and capacity</td></tr>
              <tr><td><b>Laptops</b></td><td className="g">Battery, screen, keyboard</td><td>Check the stated configuration</td></tr>
              <tr><td><b>Consoles & tablets</b></td><td className="g">Accessories and ports</td><td>Check what is included</td></tr>
              <tr><td><b>Audio</b></td><td className="g">Hygiene and accessories</td><td>Read the seller&apos;s terms</td></tr>
              <tr><td><b>Home appliances</b></td><td className="g">Installation and warranty</td><td>Check returns, delivery and support</td></tr>
            </tbody>
          </table>
        </div>

        <h2>Understanding the grades</h2>
        <ul>
          <li><b>Grade A+ / « like new »</b>, no or almost no signs of use. The best price/condition compromise.</li>
          <li><b>Grade A / « very good condition »</b>, micro-scratches invisible at use distance.</li>
          <li><b>Grade B / « good condition »</b>, visible marks but no impact on functioning. The most economical.</li>
        </ul>
        <p>
          Grade labels are not standardised. They often describe appearance, but check with the seller what they cover,
          along with tests performed, battery condition and included accessories.
        </p>

        <h2>The warranty, the real safety net</h2>
        <p>
          Warranty length and scope differ by seller, country and product. Before buying, check the <b>warranty offered</b>,
          return process, exclusions and seller identity. A warranty does not remove every risk, but clarifies the
          recourse available.
        </p>

        <div className="callout">
          <b>The useful calculation:</b> compare the <span className="g">displayed price, condition, warranty, returns
          and any benefits</span>. Only include cashback and promo codes when they are listed for the offer; FILON then
          presents them with the other available details.
        </div>

        <h2>And the ecology ?</h2>
        <p>
          Reusing a device can extend its period of use and avoid an immediate replacement. Its impact nevertheless
          depends on condition, refurbishment, length of use and transport. Do not infer an identical environmental
          performance for every offer.
        </p>

        <h2>In short</h2>
        <ul>
          <li>The price and gap with new depend on the exact offer.</li>
          <li><b>Grades</b> do not have a universal definition.</li>
          <li>Always check the seller&apos;s <b>warranty</b>, returns and exclusions.</li>
          <li>Only add cashback or promo codes when they are confirmed for the offer.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Compare new and refurbished with FILON
          </a>
        </p>
      </div>
    </article>
  );
}

export default function ArticlePage() {
  return (
    <>
      <JsonLd data={articleSchema({ title: TITLE, description: DESC, path: PATH, datePublished: "2026-01-22" })} />
      <JsonLd
        data={breadcrumbSchema([
          { name: "Accueil", path: "/" },
          { name: "Blog", path: "/blog" },
          { name: "Neuf vs reconditionné", path: PATH },
        ])}
      />
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} en={<ArticleEN />} />
    </>
  );
}
