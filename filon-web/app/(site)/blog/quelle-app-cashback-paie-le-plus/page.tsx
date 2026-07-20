import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";

const PATH = "/blog/quelle-app-cashback-paie-le-plus";
const TITLE = "Quelle app de cashback paie le plus ? (guide 2026)";
const DESC =
  "iGraal, Poulpeo, Widilo, Joko, eBuyClub : les taux de cashback varient énormément d'une app à l'autre. Voici comment comparer, et comment prendre le meilleur à chaque achat.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

export default function ArticlePage() {
  return (
    <>
      <JsonLd data={articleSchema({ title: TITLE, description: DESC, path: PATH, datePublished: "2026-01-15" })} />
      <JsonLd
        data={breadcrumbSchema([
          { name: "Accueil", path: "/" },
          { name: "Blog", path: "/blog" },
          { name: "Quelle app de cashback paie le plus ?", path: PATH },
        ])}
      />

      <article>
        <div className="ed-article-hero">
          <div className="ed-article">
            <div className="ed-article-meta">Comparatif · 6 min · 2026</div>
            <h1>Quelle app de cashback paie le plus&nbsp;?</h1>
            <p className="lede">
              Spoiler : il n&apos;y a pas de « meilleure app » universelle. Le taux le plus élevé change selon le marchand,
              le jour et les promotions. Voici comment ne plus jamais laisser d&apos;argent sur la table.
            </p>
          </div>
        </div>

        <div className="ed-article" style={{ paddingBottom: 60 }}>
          <p>
            Le cashback est devenu un réflexe pour des millions de consommateurs francophones. Le principe est simple : en
            passant par une plateforme partenaire avant de payer, vous récupérez un pourcentage de votre achat. Mais une
            erreur revient sans cesse : <b>s&apos;inscrire à une seule app et s&apos;y tenir</b>.
          </p>
          <p>
            Or les taux varient énormément. Pour un même marchand, un même jour, vous pouvez trouver 3 % ici, 6 % là, et une
            offre boostée à 8 % ailleurs. Choisir la mauvaise app, c&apos;est souvent diviser votre cashback par deux.
          </p>

          <h2>Les principales apps de cashback francophones</h2>
          <p>Voici les acteurs que l&apos;on retrouve le plus souvent, et leur point fort :</p>
          <div className="ed-tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Plateforme</th>
                  <th>Point fort</th>
                  <th>À surveiller</th>
                </tr>
              </thead>
              <tbody>
                <tr><td><b>iGraal</b></td><td>Couverture large, marchands nombreux</td><td>Taux variables selon promos</td></tr>
                <tr><td><b>Poulpeo</b></td><td>Taux souvent élevés, boosts fréquents</td><td>Seuils de retrait</td></tr>
                <tr><td><b>Widilo</b></td><td>Interface simple, bons taux mode/tech</td><td>Catalogue plus restreint</td></tr>
                <tr><td><b>Joko</b></td><td>Expérience mobile soignée, points</td><td>Logique de points à comprendre</td></tr>
                <tr><td><b>eBuyClub</b></td><td>Ancienneté, offres régulières</td><td>Ergonomie datée</td></tr>
              </tbody>
            </table>
          </div>
          <p>
            Aucune ne gagne sur tous les marchands. C&apos;est mathématique : la « meilleure » dépend de <b>où</b> et{" "}
            <b>quand</b> vous achetez.
          </p>

          <h2>La bonne méthode : comparer avant chaque achat</h2>
          <p>Concrètement, pour maximiser votre cashback, il faudrait à chaque fois :</p>
          <ul>
            <li>vérifier le taux du marchand sur <b>chaque</b> plateforme où vous avez un compte&nbsp;;</li>
            <li>repérer les <b>offres boostées</b> temporaires&nbsp;;</li>
            <li>vérifier les conditions (durée de validité, seuil de retrait, délai de validation)&nbsp;;</li>
            <li>et seulement ensuite, cliquer et payer.</li>
          </ul>
          <p>
            Fait à la main, c&apos;est fastidieux, et la plupart des gens abandonnent. C&apos;est exactement le travail que{" "}
            <b>FILON automatise</b>.
          </p>

          <div className="callout">
            💡 <b>Le raccourci :</b> au lieu de comparer les apps une par une, FILON interroge les plateformes partenaires au
            moment de votre achat, repère le <span className="g">taux le plus élevé</span> pour ce marchand et vous y envoie.
            Quand c&apos;est possible, il ajoute un code promo et compare avec une alternative reconditionnée.
          </div>

          <h2>Ne comparez plus le cashback seul</h2>
          <p>
            L&apos;erreur suivante est de raisonner « cashback » alors que la vraie question est <b>le prix réel final</b>. Un
            cashback de 6 % sur un produit neuf peut être battu par un <b>reconditionné équivalent</b> 30 % moins cher, ou par
            un <b>code promo</b> cumulable. Le bon réflexe, c&apos;est de comparer le <b>coût total</b>, pas une seule ligne.
          </p>
          <p>
            C&apos;est la philosophie de FILON : réunir cashback, reconditionné et codes promo en une seule vue, et vous donner
            un seul chiffre, votre prix réel le plus bas.
          </p>

          <h2>En résumé</h2>
          <ul>
            <li>Il n&apos;existe pas d&apos;app de cashback « meilleure » partout&nbsp;: le taux gagnant change selon le marchand.</li>
            <li>Comparer avant chaque achat peut doubler votre cashback, mais c&apos;est chronophage à la main.</li>
            <li>Raisonnez <b>prix réel final</b> (cashback + reconditionné + code promo), pas cashback seul.</li>
            <li>FILON fait cette comparaison pour vous, gratuitement, à chaque achat.</li>
          </ul>

          <p style={{ marginTop: 30 }}>
            <a className="ed-btn wave" href="/recherche" style={{ textDecoration: "none" }}>
              Essayer l&apos;assistant FILON
            </a>
          </p>
        </div>
      </article>
    </>
  );
}
