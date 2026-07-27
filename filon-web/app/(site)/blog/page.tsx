import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { Reveal } from "@/components/editorial/Reveal";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/blog",
  title: "Le blog",
  description:
    "Comparatifs cashback, guides neuf vs reconditionné, décryptages conso et bons plans. Le contenu qui vous fait économiser, sans jargon.",
});

type Post = { cat: string; title: string; excerpt: string; href: string; img: string; read: string };

const POSTS_FR: Post[] = [
  { cat: "Guide", title: "Le cashback expliqué simplement : comment ça marche", excerpt: "D'où vient l'argent, combien récupère-t-on vraiment, et quels pièges éviter ? Le cashback sans jargon.", href: "/blog/cashback-comment-ca-marche", img: "/img/blog-cashback-explique.webp", read: "6 min de lecture" },
  { cat: "Guide", title: "Black Friday : le guide pour ne pas se faire avoir", excerpt: "De vraies affaires, et beaucoup de fausses promos. Comment repérer les vrais rabais et éviter les prix gonflés.", href: "/blog/black-friday-sans-se-faire-avoir", img: "/img/blog-black-friday.webp", read: "7 min de lecture" },
  { cat: "Guide", title: "Bien choisir son ordinateur portable : le guide simple", excerpt: "Quelle RAM, quel stockage, quel processeur ? L'essentiel expliqué simplement, selon votre usage et votre budget.", href: "/blog/choisir-ordinateur-portable", img: "/img/blog-choisir-portable.webp", read: "7 min de lecture" },
  { cat: "Guide", title: "Quand acheter pour payer moins cher", excerpt: "Soldes belges, Black Friday, rentrée, fin de cycle. Le calendrier des vrais bons moments pour acheter.", href: "/blog/quand-acheter-moins-cher", img: "/img/blog-quand-acheter.webp", read: "6 min de lecture" },
  { cat: "Guide", title: "Neuf vs reconditionné : l'économie réelle, produit par produit", excerpt: "Combien économise-t-on vraiment ? Écarts par catégorie, grades et garanties, pour décider sans hésiter.", href: "/blog/neuf-vs-reconditionne-economie-reelle", img: "/img/blog-neuf-vs-reconditionne.webp", read: "5 min de lecture" },
  { cat: "Comparatif", title: "Quelle app de cashback paie le plus ?", excerpt: "Les taux varient énormément d'une app à l'autre. Comment être sûr de prendre le meilleur à chaque achat.", href: "/blog/quelle-app-cashback-paie-le-plus", img: "/img/blog-app-cashback.webp", read: "6 min de lecture" },
];

const POSTS_NL: Post[] = [
  { cat: "Gids", title: "Cashback simpel uitgelegd : hoe het werkt", excerpt: "Waar komt het geld vandaan, hoeveel krijg je echt terug, en welke valkuilen vermijden ? Cashback zonder jargon.", href: "/blog/cashback-comment-ca-marche", img: "/img/blog-cashback-explique.webp", read: "6 min lezen" },
  { cat: "Gids", title: "Black Friday : de gids om je niet te laten beetnemen", excerpt: "Echte koopjes, en veel valse promo's. Hoe je de echte kortingen herkent en opgeblazen prijzen vermijdt.", href: "/blog/black-friday-sans-se-faire-avoir", img: "/img/blog-black-friday.webp", read: "7 min lezen" },
  { cat: "Gids", title: "Je laptop goed kiezen : de simpele gids", excerpt: "Welk RAM, welke opslag, welke processor ? Het essentiële simpel uitgelegd, volgens je gebruik en je budget.", href: "/blog/choisir-ordinateur-portable", img: "/img/blog-choisir-portable.webp", read: "7 min lezen" },
  { cat: "Gids", title: "Wanneer kopen om minder te betalen", excerpt: "Belgische solden, Black Friday, terug naar school, einde levenscyclus. De kalender van de echte koopmomenten.", href: "/blog/quand-acheter-moins-cher", img: "/img/blog-quand-acheter.webp", read: "6 min lezen" },
  { cat: "Gids", title: "Nieuw vs refurbished : de echte besparing, product per product", excerpt: "Hoeveel bespaar je echt ? Verschillen per categorie, grades en garanties, om zonder twijfelen te beslissen.", href: "/blog/neuf-vs-reconditionne-economie-reelle", img: "/img/blog-neuf-vs-reconditionne.webp", read: "5 min lezen" },
  { cat: "Vergelijking", title: "Welke cashback-app betaalt het meest ?", excerpt: "De percentages verschillen enorm van app tot app. Hoe je zeker het beste pakt bij elke aankoop.", href: "/blog/quelle-app-cashback-paie-le-plus", img: "/img/blog-app-cashback.webp", read: "6 min lezen" },
];

function BlogList({ eyebrow, title, intro, posts }: { eyebrow: string; title: string; intro: string; posts: Post[] }) {
  return (
    <>
      <ContentHero eyebrow={eyebrow} title={<>{title}</>} intro={intro} breadcrumb={[{ name: eyebrow, path: "/blog" }]} />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <Reveal>
            <div className="ed-blog">
              {posts.map((p) => (
                <a className="ed-post" href={p.href} key={p.href}>
                  <span className="ed-post-cover">
                    <img src={p.img} alt="" loading="lazy" />
                  </span>
                  <span className="ed-post-body">
                    <span className="cat">{p.cat}</span>
                    <h3>{p.title}</h3>
                    <p>{p.excerpt}</p>
                    <span className="rd">{p.read} →</span>
                  </span>
                </a>
              ))}
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}

export default function BlogPage() {
  return (
    <Localized
      fr={<BlogList eyebrow="Blog" title="Acheter malin, ça s'apprend." intro="Des guides qui vous font vraiment économiser. Clairs, chiffrés, sans jargon." posts={POSTS_FR} />}
      nl={<BlogList eyebrow="Blog" title="Slim kopen kun je leren." intro="Gidsen die je echt doen besparen. Helder, becijferd, zonder jargon." posts={POSTS_NL} />}
    />
  );
}
