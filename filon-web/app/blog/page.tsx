import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { PageShell } from "@/components/site/PageShell";
import { Container } from "@/components/ui/Container";

export const metadata: Metadata = buildMetadata({
  path: "/blog",
  title: "Blog — guides d'achat malin",
  description:
    "Comparatifs cashback, guides neuf vs reconditionné, décryptages conso et bons plans. Le contenu qui vous fait économiser, sans jargon.",
});

// Placeholder editorial index — wire to a CMS or MDX in the content phase.
const POSTS = [
  { cat: "Comparatif", title: "Quelle app de cashback paie le plus ce mois-ci ?", excerpt: "iGraal, Poulpeo, Widilo, Joko : le classement chiffré, enseigne par enseigne." },
  { cat: "Guide", title: "Neuf vs reconditionné : l'économie réelle, produit par produit", excerpt: "Combien vous gagnez vraiment en choisissant le reconditionné garanti." },
  { cat: "Décryptage", title: "Honey, Phia : ce que révèlent les scandales d'attribution", excerpt: "Pourquoi la transparence de rémunération devient le vrai critère de confiance." },
];

export default function BlogPage() {
  return (
    <PageShell
      eyebrow="Blog"
      title={<>Acheter malin, ça s&apos;apprend.</>}
      intro="Comparatifs chiffrés, guides neuf vs reconditionné, décryptages conso et bons plans saisonniers. Le contenu qui vous fait économiser — clair, honnête, sans jargon."
      breadcrumb={[{ name: "Blog", path: "/blog" }]}
    >
      <section style={{ padding: "20px 0 70px" }}>
        <Container>
          <div className="filon-steps" style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
            {POSTS.map((p) => (
              <article key={p.title} style={{ padding: 24, borderRadius: "var(--r-lg)", background: "var(--surface)", border: "1px solid var(--border)" }}>
                <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--aqua-2)" }}>{p.cat}</span>
                <h3 style={{ fontSize: 19, margin: "12px 0 8px" }}>{p.title}</h3>
                <p style={{ color: "var(--text-dim)", fontSize: 14.5 }}>{p.excerpt}</p>
              </article>
            ))}
          </div>
        </Container>
      </section>
    </PageShell>
  );
}
