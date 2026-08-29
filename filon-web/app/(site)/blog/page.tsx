import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { Reveal } from "@/components/editorial/Reveal";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/blog",
  title: "Le blog",
  description:
    "Guides de comparaison sur le cashback, le reconditionné, les prix et les conditions à vérifier avant un achat.",
});

type Post = { cat: string; title: string; excerpt: string; href: string; img: string; read: string };

const POSTS_FR: Post[] = [
  { cat: "Guide", title: "Le cashback expliqué simplement : comment ça marche", excerpt: "Origine de l'avantage, taux, plafond, exclusions et validation : les conditions à lire sans jargon.", href: "/blog/cashback-comment-ca-marche", img: "/img/blog-cashback-explique.webp", read: "6 min de lecture" },
  { cat: "Guide", title: "Black Friday : les conditions à contrôler", excerpt: "Prix de référence, historique disponible et offre exacte : les signaux à examiner sans présumer d'un rabais.", href: "/blog/black-friday-sans-se-faire-avoir", img: "/img/blog-black-friday.webp", read: "7 min de lecture" },
  { cat: "Guide", title: "Bien choisir son ordinateur portable : le guide simple", excerpt: "Quelle RAM, quel stockage, quel processeur ? L'essentiel expliqué simplement, selon votre usage et votre budget.", href: "/blog/choisir-ordinateur-portable", img: "/img/blog-choisir-portable.webp", read: "7 min de lecture" },
  { cat: "Guide", title: "Quand comparer les prix observés", excerpt: "Soldes, Black Friday, rentrée et changements de gamme : des périodes à surveiller, sans garantie de baisse.", href: "/blog/quand-acheter-moins-cher", img: "/img/blog-quand-acheter.webp", read: "6 min de lecture" },
  { cat: "Guide", title: "Neuf vs reconditionné : comparer les écarts et conditions", excerpt: "Prix affiché, état, garantie et retour : les champs à comparer pour une offre donnée.", href: "/blog/neuf-vs-reconditionne-economie-reelle", img: "/img/blog-neuf-vs-reconditionne.webp", read: "5 min de lecture" },
  { cat: "Comparatif", title: "Comment comparer les apps de cashback ?", excerpt: "Taux, plafonds, exclusions et délais peuvent varier : voici les champs à vérifier pour l'offre concernée.", href: "/blog/quelle-app-cashback-paie-le-plus", img: "/img/blog-app-cashback.webp", read: "6 min de lecture" },
];

const POSTS_NL: Post[] = [
  { cat: "Gids", title: "Cashback simpel uitgelegd : hoe het werkt", excerpt: "Herkomst van het voordeel, tarief, plafond, uitsluitingen en validatie: voorwaarden zonder jargon.", href: "/blog/cashback-comment-ca-marche", img: "/img/blog-cashback-explique.webp", read: "6 min lezen" },
  { cat: "Gids", title: "Black Friday : voorwaarden om te controleren", excerpt: "Referentieprijs, beschikbare historiek en exact aanbod: signalen om te bekijken zonder korting te veronderstellen.", href: "/blog/black-friday-sans-se-faire-avoir", img: "/img/blog-black-friday.webp", read: "7 min lezen" },
  { cat: "Gids", title: "Je laptop goed kiezen : de simpele gids", excerpt: "Welk RAM, welke opslag, welke processor ? Het essentiële simpel uitgelegd, volgens je gebruik en je budget.", href: "/blog/choisir-ordinateur-portable", img: "/img/blog-choisir-portable.webp", read: "7 min lezen" },
  { cat: "Gids", title: "Wanneer waargenomen prijzen vergelijken", excerpt: "Solden, Black Friday, schoolstart en modelwissels: periodes om te volgen, zonder prijsdaling te garanderen.", href: "/blog/quand-acheter-moins-cher", img: "/img/blog-quand-acheter.webp", read: "6 min lezen" },
  { cat: "Gids", title: "Nieuw vs refurbished : prijsverschillen en voorwaarden", excerpt: "Getoonde prijs, staat, garantie en retour: velden om voor een concrete aanbieding te vergelijken.", href: "/blog/neuf-vs-reconditionne-economie-reelle", img: "/img/blog-neuf-vs-reconditionne.webp", read: "5 min lezen" },
  { cat: "Vergelijking", title: "Hoe vergelijk je cashback-apps ?", excerpt: "Tarieven, plafonds, uitsluitingen en termijnen kunnen verschillen: controleer ze voor de betrokken aanbieding.", href: "/blog/quelle-app-cashback-paie-le-plus", img: "/img/blog-app-cashback.webp", read: "6 min lezen" },
];

const POSTS_EN: Post[] = [
  { cat: "Guide", title: "Cashback simply explained : how it works", excerpt: "Benefit source, rate, cap, exclusions and validation: the terms explained without jargon.", href: "/blog/cashback-comment-ca-marche", img: "/img/blog-cashback-explique.webp", read: "6 min read" },
  { cat: "Guide", title: "Black Friday : terms to check", excerpt: "Reference price, available history and exact offer: signals to examine without assuming a discount.", href: "/blog/black-friday-sans-se-faire-avoir", img: "/img/blog-black-friday.webp", read: "7 min read" },
  { cat: "Guide", title: "Choosing your laptop well : the simple guide", excerpt: "Which RAM, which storage, which processor ? The essentials explained simply, by your use and your budget.", href: "/blog/choisir-ordinateur-portable", img: "/img/blog-choisir-portable.webp", read: "7 min read" },
  { cat: "Guide", title: "When to compare observed prices", excerpt: "Sales, Black Friday, back to school and model changes: periods to watch, without guaranteeing a price drop.", href: "/blog/quand-acheter-moins-cher", img: "/img/blog-quand-acheter.webp", read: "6 min read" },
  { cat: "Guide", title: "New vs refurbished : price gaps and terms", excerpt: "Displayed price, condition, warranty and returns: fields to compare for a specific offer.", href: "/blog/neuf-vs-reconditionne-economie-reelle", img: "/img/blog-neuf-vs-reconditionne.webp", read: "5 min read" },
  { cat: "Comparison", title: "How should cashback apps be compared ?", excerpt: "Rates, caps, exclusions and timing may vary: check them for the offer concerned.", href: "/blog/quelle-app-cashback-paie-le-plus", img: "/img/blog-app-cashback.webp", read: "6 min read" },
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
      fr={<BlogList eyebrow="Blog" title="Acheter malin, ça s'apprend." intro="Des guides pour comparer les prix, les conditions et les preuves disponibles, sans jargon." posts={POSTS_FR} />}
      nl={<BlogList eyebrow="Blog" title="Slim kopen kun je leren." intro="Gidsen om prijzen, voorwaarden en beschikbaar bewijs te vergelijken, zonder jargon." posts={POSTS_NL} />}
      en={<BlogList eyebrow="Blog" title="Buying smart is a skill." intro="Guides for comparing prices, terms and available evidence, without jargon." posts={POSTS_EN} />}
    />
  );
}
