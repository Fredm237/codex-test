import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { Reveal } from "@/components/editorial/Reveal";

export const metadata: Metadata = buildMetadata({
  path: "/blog",
  title: "Le blog",
  description:
    "Comparatifs cashback, guides neuf vs reconditionné, décryptages conso et bons plans. Le contenu qui vous fait économiser, sans jargon.",
});

const POSTS = [
  {
    cat: "Guide",
    title: "Bien choisir son ordinateur portable : le guide simple",
    excerpt: "Quelle RAM, quel stockage, quel processeur ? L'essentiel expliqué simplement, selon votre usage et votre budget.",
    href: "/blog/choisir-ordinateur-portable",
    read: "7 min de lecture",
  },
  {
    cat: "Guide",
    title: "Quand acheter pour payer moins cher",
    excerpt: "Soldes belges, Black Friday, rentrée, fin de cycle. Le calendrier des vrais bons moments pour acheter.",
    href: "/blog/quand-acheter-moins-cher",
    read: "6 min de lecture",
  },
  {
    cat: "Guide",
    title: "Neuf vs reconditionné : l'économie réelle, produit par produit",
    excerpt: "Combien économise-t-on vraiment ? Écarts par catégorie, grades et garanties, pour décider sans hésiter.",
    href: "/blog/neuf-vs-reconditionne-economie-reelle",
    read: "5 min de lecture",
  },
  {
    cat: "Comparatif",
    title: "Quelle app de cashback paie le plus ?",
    excerpt: "Les taux varient énormément d'une app à l'autre. Comment être sûr de prendre le meilleur à chaque achat.",
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
        intro="Des guides qui vous font vraiment économiser. Clairs, chiffrés, sans jargon."
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
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
