import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";

const PATH = "/blog/black-friday-sans-se-faire-avoir";
const TITLE = "Black Friday : le guide pour ne pas se faire avoir";
const DESC =
  "Le Black Friday, ce sont de vraies affaires… et beaucoup de fausses promos. Comment repérer les vrais rabais, éviter les prix gonflés, et acheter au bon moment.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

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
            💡 <b>Le raccourci&nbsp;:</b> plutôt que de tout surveiller à la main, demandez à FILON. Il compare le prix
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
    </>
  );
}
