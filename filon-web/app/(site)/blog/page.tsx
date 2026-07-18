import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { Reveal } from "@/components/editorial/Reveal";

export const metadata: Metadata = buildMetadata({
  path: "/blog",
  title: "Blog — guides d'achat malin",
  description:
    "Comparatifs cashback, guides neuf vs reconditionné, décryptages conso et bons plans. Le contenu qui vous fait économiser, sans jargon.",
});

const POSTS = [
  {
    cat: "Comparatif",
    title: "Quelle app de cashback paie le plus ?",
    excerpt: "iGraal, Poulpeo, Widilo, Joko, eBuyClub : comment les taux varient, et comment être sûr de prendre le meilleur à chaque achat.",
    href: "/blog/quelle-app-cashback-paie-le-plus",
    read: "6 min de lecture",
  },
];

export default function BlogPage() {
  return (
    <>
      <ContentHero
        eyebrow="Blog"
        title={<>Acheter malin, ça s&apos;apprend.</>}
        intro="Comparatifs chiffrés, guides neuf vs reconditionné, décryptages conso et bons plans. Le contenu qui vous fait économiser — clair, honnête, sans jargon."
        breadcrumb={[{ name: "Blog", path: "/blog" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <Reveal>
            <div className="ed-blog">
              {POSTS.map((p) => (
                <a className="ed-post" href={p.href} key={p.href}>
                  <span className="cat">{p.cat}</span>
                  <h3>{p.title}</h3>
                  <p>{p.excerpt}</p>
                  <div className="rd">{p.read} →</div>
                </a>
              ))}
              <div className="ed-post" style={{ opacity: 0.6 }}>
                <span className="cat">Bientôt</span>
                <h3>Neuf vs reconditionné : l&apos;économie réelle, produit par produit</h3>
                <p>Combien vous gagnez vraiment en choisissant le reconditionné garanti — chiffres à l&apos;appui.</p>
                <div className="rd">En préparation</div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
