import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";

const PATH = "/blog/choisir-ordinateur-portable";
const TITLE = "Bien choisir son ordinateur portable : le guide simple";
const DESC =
  "Quelle RAM, quel stockage, quel processeur ? Le guide clair pour choisir un ordinateur portable selon votre usage et votre budget, sans jargon et sans se faire avoir.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

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
            💡 <b>Le raccourci :</b> décrivez simplement votre besoin («&nbsp;un portable pour la fac à 800&nbsp;€&nbsp;»)
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
    </>
  );
}
