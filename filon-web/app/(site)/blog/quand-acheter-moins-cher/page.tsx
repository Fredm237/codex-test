import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";

const PATH = "/blog/quand-acheter-moins-cher";
const TITLE = "Quand acheter pour payer moins cher : le calendrier des bons moments";
const DESC =
  "Le même produit ne coûte pas le même prix en janvier et en octobre. Soldes belges, Black Friday, rentrée, fin de cycle : voici quand les prix baissent vraiment.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

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
            💡 <b>Le bon réflexe :</b> avant d&apos;acheter, demandez-vous si le prix est bas <span className="g">dans son
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
    </>
  );
}
