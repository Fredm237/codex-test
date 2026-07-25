import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";

const PATH = "/blog/cashback-comment-ca-marche";
const TITLE = "Le cashback expliqué simplement : comment ça marche (et les pièges)";
const DESC =
  "Le cashback rembourse une partie de vos achats. Mais d'où vient l'argent, combien récupère-t-on vraiment, et quels pièges éviter ? Le guide clair, sans jargon.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

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
            💡 <b>Le vrai calcul&nbsp;:</b> une bonne affaire, ce n&apos;est pas le plus gros cashback, c&apos;est le
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
    </>
  );
}
