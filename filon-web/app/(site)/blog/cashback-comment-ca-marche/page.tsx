import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";
import { Localized } from "@/components/editorial/Localized";

const PATH = "/blog/cashback-comment-ca-marche";
const TITLE = "Le cashback expliqué simplement : comment ça marche (et les pièges)";
const DESC =
  "Le cashback rembourse une partie de vos achats. Mais d'où vient l'argent, combien récupère-t-on vraiment, et quels pièges éviter ? Le guide clair, sans jargon.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

function ArticleFR() {
  return (
    <article>
      <div className="ed-article-hero">
        <div className="ed-article">
          <div className="ed-article-meta">Guide · 6 min · 2026</div>
          <h1>Le cashback, expliqué simplement</h1>
          <p className="lede">
            «&nbsp;Récupérez de l&apos;argent sur vos achats&nbsp;»&nbsp;: le cashback semble trop beau pour être
            vrai. Il ne l&apos;est pas, mais il faut comprendre d&apos;où vient l&apos;argent, et repérer les pièges.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-cashback-explique.webp" alt="" />
        <p>
          Le cashback, c&apos;est un remboursement d&apos;une partie de votre achat, versé après coup. Vous payez le
          prix normal chez le marchand, et quelques jours ou semaines plus tard, un pourcentage revient sur votre
          cagnotte. Rien de magique&nbsp;: juste un partage de commission bien organisé.
        </p>

        <h2>D&apos;où vient l&apos;argent, exactement</h2>
        <p>
          Quand un site de cashback vous envoie chez un marchand et que vous achetez, le marchand lui verse une{" "}
          <b>commission d&apos;affiliation</b>. Le site de cashback vous en <b>reverse une partie</b>, et garde le
          reste. C&apos;est tout le modèle&nbsp;: une commission partagée entre le site et vous.
        </p>
        <p>
          Conséquence importante&nbsp;: le cashback <b>ne change pas le prix</b> que vous payez au marchand. Vous
          payez pareil qu&apos;en direct&nbsp;; simplement, une partie vous revient ensuite.
        </p>

        <h2>Combien récupère-t-on vraiment ?</h2>
        <p>
          Les taux varient énormément selon la catégorie et la marque. Voici des ordres de grandeur courants&nbsp;:
        </p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Catégorie</th>
                <th>Cashback typique</th>
                <th>Bon à savoir</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>High-tech</b></td><td className="g">1 – 4 %</td><td>Marges faibles, donc taux modérés</td></tr>
              <tr><td><b>Mode & habillement</b></td><td className="g">5 – 12 %</td><td>Souvent les meilleurs taux</td></tr>
              <tr><td><b>Voyage & hôtels</b></td><td className="g">3 – 10 %</td><td>Le montant peut être élevé</td></tr>
              <tr><td><b>Beauté & maison</b></td><td className="g">4 – 8 %</td><td>Variable selon les marques</td></tr>
              <tr><td><b>Abonnements & télécom</b></td><td className="g">jusqu&apos;à 100 €</td><td>Souvent un montant fixe à la souscription</td></tr>
            </tbody>
          </table>
        </div>

        <h2>Les pièges à connaître</h2>
        <p>
          <b>Le taux «&nbsp;boosté&nbsp;» temporaire.</b> Un «&nbsp;jusqu&apos;à 16&nbsp;%&nbsp;» affiché un jour peut
          retomber à 4&nbsp;% le lendemain. Vérifiez le taux <b>au moment de l&apos;achat</b>, pas celui vu la veille.
        </p>
        <p>
          <b>Le délai de validation.</b> Le cashback n&apos;est pas immédiat&nbsp;: il est d&apos;abord «&nbsp;en
          attente&nbsp;» le temps que le marchand confirme (souvent 30 à 90 jours), puis retirable au-delà d&apos;un
          seuil minimum.
        </p>
        <p>
          <b>Les conditions qui l&apos;annulent.</b> Utiliser un code promo non autorisé, un bloqueur de pub, ou passer
          par une autre app juste avant, peut faire sauter le cashback. Terminez toujours l&apos;achat dans la foulée,
          depuis le lien du service.
        </p>

        <div className="callout">
          <b>Le vrai calcul&nbsp;:</b> une bonne affaire, ce n&apos;est pas le plus gros cashback, c&apos;est le
          <span className="g"> prix final le plus bas</span> une fois tout combiné&nbsp;: prix marchand, coupon et
          cashback réunis. C&apos;est exactement ce que FILON calcule pour vous.
        </div>

        <h2>En résumé</h2>
        <ul>
          <li>Le cashback = une part de la commission d&apos;affiliation, reversée à vous.</li>
          <li>Il <b>ne change pas</b> le prix payé au marchand.</li>
          <li>Les taux vont de <b>1&nbsp;%</b> (high-tech) à <b>12&nbsp;%+</b> (mode).</li>
          <li>Attention aux <b>taux temporaires</b>, aux <b>délais</b> et aux conditions qui l&apos;annulent.</li>
          <li>Jugez sur le <b>prix final</b>, pas sur le taux affiché.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Voir mon vrai prix, cashback inclus
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
          <h1>Cashback, simpel uitgelegd</h1>
          <p className="lede">
            «&nbsp;Krijg geld terug op je aankopen&nbsp;»&nbsp;: cashback lijkt te mooi om waar te zijn. Dat is het
            niet, maar je moet begrijpen waar het geld vandaan komt, en de valkuilen herkennen.
          </p>
        </div>
      </div>

      <div className="ed-article" style={{ paddingBottom: 60 }}>
        <img className="ed-article-cover" src="/img/blog-cashback-explique.webp" alt="" />
        <p>
          Cashback is een terugbetaling van een deel van je aankoop, achteraf uitgekeerd. Je betaalt de normale prijs
          bij de winkel, en enkele dagen of weken later komt een percentage terug op je spaarpot. Niets magisch&nbsp;:
          gewoon een goed georganiseerde commissiedeling.
        </p>

        <h2>Waar komt het geld precies vandaan</h2>
        <p>
          Wanneer een cashback-site je naar een winkel stuurt en je koopt, betaalt de winkel hem een{" "}
          <b>affiliatiecommissie</b>. De cashback-site <b>geeft je daar een deel van terug</b>, en houdt de rest.
          Dat is het hele model&nbsp;: een commissie gedeeld tussen de site en jou.
        </p>
        <p>
          Belangrijk gevolg&nbsp;: cashback <b>verandert de prijs niet</b> die je bij de winkel betaalt. Je betaalt
          hetzelfde als rechtstreeks&nbsp;; alleen komt een deel daarna terug.
        </p>

        <h2>Hoeveel krijg je echt terug ?</h2>
        <p>
          De percentages verschillen enorm naargelang de categorie en het merk. Hier enkele courante ordes van
          grootte&nbsp;:
        </p>
        <div className="ed-tablewrap">
          <table>
            <thead>
              <tr>
                <th>Categorie</th>
                <th>Typische cashback</th>
                <th>Goed om te weten</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><b>High-tech</b></td><td className="g">1 – 4 %</td><td>Lage marges, dus gematigde percentages</td></tr>
              <tr><td><b>Mode & kleding</b></td><td className="g">5 – 12 %</td><td>Vaak de beste percentages</td></tr>
              <tr><td><b>Reizen & hotels</b></td><td className="g">3 – 10 %</td><td>Het bedrag kan hoog oplopen</td></tr>
              <tr><td><b>Beauty & wonen</b></td><td className="g">4 – 8 %</td><td>Variabel naargelang de merken</td></tr>
              <tr><td><b>Abonnementen & telecom</b></td><td className="g">tot 100 €</td><td>Vaak een vast bedrag bij inschrijving</td></tr>
            </tbody>
          </table>
        </div>

        <h2>De valkuilen om te kennen</h2>
        <p>
          <b>Het tijdelijke «&nbsp;geboosterde&nbsp;» percentage.</b> Een «&nbsp;tot 16&nbsp;%&nbsp;» dat vandaag
          getoond wordt, kan morgen terugvallen op 4&nbsp;%. Controleer het percentage <b>op het moment van de
          aankoop</b>, niet dat van de dag ervoor.
        </p>
        <p>
          <b>De validatietermijn.</b> Cashback is niet onmiddellijk&nbsp;: hij staat eerst «&nbsp;in
          afwachting&nbsp;» tot de winkel bevestigt (vaak 30 tot 90 dagen), en is dan opneembaar boven een minimum
          drempel.
        </p>
        <p>
          <b>De voorwaarden die hem annuleren.</b> Een niet-toegestane promocode gebruiken, een adblocker, of vlak
          ervoor via een andere app passeren, kan de cashback doen wegvallen. Rond de aankoop altijd meteen af,
          vanaf de link van de dienst.
        </p>

        <div className="callout">
          <b>De echte berekening&nbsp;:</b> een koopje is niet de grootste cashback, het is de
          <span className="g"> laagste eindprijs</span> zodra alles gecombineerd is&nbsp;: winkelprijs, coupon en
          cashback samen. Dat is precies wat FILON voor je berekent.
        </div>

        <h2>Samengevat</h2>
        <ul>
          <li>Cashback = een deel van de affiliatiecommissie, aan jou teruggegeven.</li>
          <li>Het <b>verandert</b> de bij de winkel betaalde prijs <b>niet</b>.</li>
          <li>De percentages gaan van <b>1&nbsp;%</b> (high-tech) tot <b>12&nbsp;%+</b> (mode).</li>
          <li>Let op <b>tijdelijke percentages</b>, <b>termijnen</b> en de voorwaarden die hem annuleren.</li>
          <li>Beoordeel op de <b>eindprijs</b>, niet op het getoonde percentage.</li>
        </ul>

        <p style={{ marginTop: 30 }}>
          <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
            Bekijk mijn echte prijs, cashback inbegrepen
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
          { name: "Le cashback expliqué", path: PATH },
        ])}
      />
      <Localized fr={<ArticleFR />} nl={<ArticleNL />} />
    </>
  );
}
