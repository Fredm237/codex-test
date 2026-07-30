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
            « Reconditionné » rime souvent avec « moins cher », mais de combien exactement ? Et à quel compromis ? Voici les
            chiffres, sans langue de bois, pour décider en connaissance de cause.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-neuf-vs-reconditionne.webp" alt="" />
        <p>
          Un produit reconditionné est un appareil d&apos;occasion testé, remis en état et garanti par un professionnel. Sur
          le papier, l&apos;économie est évidente. Dans la réalité, elle dépend de trois choses : le <b>type de produit</b>,
          le <b>grade</b>, et ce que vous <b>cumulez</b> par-dessus.
        </p>

        <h2>Combien on économise, catégorie par catégorie</h2>
        <p>Ordres de grandeur observés sur le marché (écart moyen vs neuf) :</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Catégorie</th>
                <th>Économie typique</th>
                <th>Bon à savoir</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>Smartphones haut de gamme</b></td><td className="g">−30 à −45 %</td><td>Le segment roi du reconditionné</td></tr>
              <tr><td><b>Ordinateurs portables</b></td><td className="g">−25 à −40 %</td><td>Vérifier batterie et état écran</td></tr>
              <tr><td><b>Consoles & tablettes</b></td><td className="g">−20 à −35 %</td><td>Souvent quasi neuf en grade A+</td></tr>
              <tr><td><b>Audio (casques, écouteurs)</b></td><td className="g">−15 à −30 %</td><td>Attention aux accessoires inclus</td></tr>
              <tr><td><b>Électroménager</b></td><td className="g">−20 à −40 %</td><td>Garantie clé sur ces produits</td></tr>
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
          Le grade ne change rien au fonctionnement ni à la garantie, seulement l&apos;esthétique. Si l&apos;apparence
          n&apos;est pas votre priorité, un grade B maximise l&apos;économie.
        </p>

        <h2>La garantie, le vrai filet de sécurité</h2>
        <p>
          Un reconditionné sérieux est <b>garanti 12 à 24 mois</b>. C&apos;est ce qui distingue le reconditionné pro de la
          simple occasion entre particuliers. Ne renoncez jamais à la garantie pour quelques euros : c&apos;est elle qui
          rend l&apos;achat sans risque.
        </p>

        <div className="callout">
          <b>Le vrai calcul :</b> l&apos;économie ne s&apos;arrête pas au prix reconditionné. En ajoutant un{" "}
          <span className="g">cashback</span> (3 à 8 %) et parfois un code promo, l&apos;économie totale vs neuf atteint
          souvent <span className="g">45 à 50 %</span>. C&apos;est exactement ce que FILON calcule pour vous.
        </div>

        <h2>Et l&apos;écologie ?</h2>
        <p>
          Prolonger la vie d&apos;un appareil évite la fabrication d&apos;un neuf, l&apos;étape de loin la plus polluante du
          cycle de vie d&apos;un produit électronique. Choisir le reconditionné, c&apos;est donc l&apos;un des gestes les plus
          efficaces pour réduire l&apos;empreinte de vos achats, sans sacrifier la qualité.
        </p>

        <h2>En résumé</h2>
        <ul>
          <li>L&apos;économie va de <b>−15 %</b> (audio) à <b>−45 %</b> (smartphones premium) selon la catégorie.</li>
          <li>Le <b>grade</b> ne concerne que l&apos;esthétique ; un grade B maximise l&apos;économie.</li>
          <li>Exigez toujours une <b>garantie de 12 à 24 mois</b>.</li>
          <li>Avec le cashback, l&apos;économie totale grimpe souvent à <b>45–50 %</b>.</li>
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
            « Refurbished » rijmt vaak met « goedkoper », maar met hoeveel precies ? En met welk compromis ? Hier lees je
            de cijfers, zonder omwegen, om met kennis van zaken te beslissen.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-neuf-vs-reconditionne.webp" alt="" />
        <p>
          Een refurbished product is een tweedehands toestel dat getest, hersteld en gegarandeerd is door een
          professional. Op papier is de besparing evident. In werkelijkheid hangt ze af van drie dingen : het{" "}
          <b>type product</b>, de <b>grade</b>, en wat je er <b>bovenop cumuleert</b>.
        </p>

        <h2>Hoeveel je bespaart, categorie per categorie</h2>
        <p>Ordes van grootte waargenomen op de markt (gemiddeld verschil vs nieuw) :</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Categorie</th>
                <th>Typische besparing</th>
                <th>Goed om te weten</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>High-end smartphones</b></td><td className="g">−30 tot −45 %</td><td>Het koningssegment van refurbished</td></tr>
              <tr><td><b>Laptops</b></td><td className="g">−25 tot −40 %</td><td>Batterij en schermtoestand controleren</td></tr>
              <tr><td><b>Consoles & tablets</b></td><td className="g">−20 tot −35 %</td><td>Vaak zo goed als nieuw in grade A+</td></tr>
              <tr><td><b>Audio (hoofdtelefoons, oortjes)</b></td><td className="g">−15 tot −30 %</td><td>Let op de inbegrepen accessoires</td></tr>
              <tr><td><b>Huishoudtoestellen</b></td><td className="g">−20 tot −40 %</td><td>Garantie is sleutel op deze producten</td></tr>
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
          De grade verandert niets aan de werking noch aan de garantie, enkel het uiterlijk. Als het voorkomen niet je
          prioriteit is, maximaliseert een grade B de besparing.
        </p>

        <h2>De garantie, het echte vangnet</h2>
        <p>
          Een serieus refurbished product is <b>gegarandeerd 12 tot 24 maanden</b>. Dat is wat de professionele
          refurbished onderscheidt van de gewone tweedehands tussen particulieren. Zie nooit af van de garantie voor
          enkele euro's : zij maakt de aankoop risicoloos.
        </p>

        <div className="callout">
          <b>De echte berekening :</b> de besparing stopt niet bij de refurbished-prijs. Door een{" "}
          <span className="g">cashback</span> (3 tot 8 %) en soms een promocode toe te voegen, bereikt de totale
          besparing vs nieuw vaak <span className="g">45 tot 50 %</span>. Dat is precies wat FILON voor je berekent.
        </div>

        <h2>En de ecologie ?</h2>
        <p>
          Het leven van een toestel verlengen vermijdt de fabricage van een nieuw exemplaar, veruit de meest
          vervuilende stap in de levenscyclus van een elektronisch product. Refurbished kiezen is dus een van de meest
          doeltreffende gebaren om de voetafdruk van je aankopen te verkleinen, zonder kwaliteit op te offeren.
        </p>

        <h2>Samengevat</h2>
        <ul>
          <li>De besparing gaat van <b>−15 %</b> (audio) tot <b>−45 %</b> (premium smartphones) naargelang de categorie.</li>
          <li>De <b>grade</b> betreft enkel het uiterlijk ; een grade B maximaliseert de besparing.</li>
          <li>Eis altijd een <b>garantie van 12 tot 24 maanden</b>.</li>
          <li>Met de cashback klimt de totale besparing vaak tot <b>45–50 %</b>.</li>
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
            « Refurbished » often rhymes with « cheaper », but by how much exactly ? And at what compromise ? Here are
            the figures, no spin, to decide with full knowledge.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-neuf-vs-reconditionne.webp" alt="" />
        <p>
          A refurbished product is a second-hand device tested, restored and guaranteed by a professional. On paper,
          the saving is obvious. In reality, it depends on three things: the <b>type of product</b>, the
          <b> grade</b>, and what you <b>stack</b> on top.
        </p>

        <h2>How much you save, category by category</h2>
        <p>Orders of magnitude observed on the market (average gap vs new):</p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Typical saving</th>
                <th>Good to know</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>High-end smartphones</b></td><td className="g">−30 to −45 %</td><td>The flagship segment of refurbished</td></tr>
              <tr><td><b>Laptops</b></td><td className="g">−25 to −40 %</td><td>Check battery and screen condition</td></tr>
              <tr><td><b>Consoles & tablets</b></td><td className="g">−20 to −35 %</td><td>Often near-new in grade A+</td></tr>
              <tr><td><b>Audio (headphones, earbuds)</b></td><td className="g">−15 to −30 %</td><td>Watch the included accessories</td></tr>
              <tr><td><b>Home appliances</b></td><td className="g">−20 to −40 %</td><td>Warranty is key on these products</td></tr>
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
          The grade changes nothing about functioning or warranty, only the looks. If appearance isn&apos;t your
          priority, a grade B maximises the saving.
        </p>

        <h2>The warranty, the real safety net</h2>
        <p>
          A serious refurbished product is <b>guaranteed 12 to 24 months</b>. That&apos;s what distinguishes
          professional refurbished from plain second-hand between private individuals. Never give up the warranty for
          a few euros: it&apos;s what makes the purchase risk-free.
        </p>

        <div className="callout">
          <b>The real calculation:</b> the saving doesn&apos;t stop at the refurbished price. Adding a{" "}
          <span className="g">cashback</span> (3 to 8%) and sometimes a promo code, the total saving vs new often
          reaches <span className="g">45 to 50%</span>. That&apos;s exactly what FILON calculates for you.
        </div>

        <h2>And the ecology ?</h2>
        <p>
          Extending a device&apos;s life avoids manufacturing a new one, by far the most polluting step in an
          electronic product&apos;s life cycle. Choosing refurbished is therefore one of the most effective moves to
          reduce your purchases&apos; footprint, without sacrificing quality.
        </p>

        <h2>In short</h2>
        <ul>
          <li>The saving runs from <b>−15%</b> (audio) to <b>−45%</b> (premium smartphones) by category.</li>
          <li>The <b>grade</b> concerns only looks; a grade B maximises the saving.</li>
          <li>Always demand a <b>12 to 24-month warranty</b>.</li>
          <li>With cashback, the total saving often climbs to <b>45–50%</b>.</li>
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
