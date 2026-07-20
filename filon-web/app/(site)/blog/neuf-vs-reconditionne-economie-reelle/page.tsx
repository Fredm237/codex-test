import type { Metadata } from "next";
import { buildMetadata, articleSchema, breadcrumbSchema, JsonLd } from "@/lib/seo";

const PATH = "/blog/neuf-vs-reconditionne-economie-reelle";
const TITLE = "Neuf vs reconditionné : l'économie réelle, produit par produit";
const DESC =
  "Combien économise-t-on vraiment en choisissant le reconditionné ? Écarts de prix, grades, garanties, et le cumul avec le cashback, le guide clair pour décider.";

export const metadata: Metadata = buildMetadata({ path: PATH, title: TITLE, description: DESC });

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
            💡 <b>Le vrai calcul :</b> l&apos;économie ne s&apos;arrête pas au prix reconditionné. En ajoutant un{" "}
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
    </>
  );
}
