import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { PageShell } from "@/components/site/PageShell";
import { Container } from "@/components/ui/Container";

export const metadata: Metadata = buildMetadata({
  path: "/a-propos",
  title: "À propos",
  description:
    "FILON veut devenir la référence francophone de l'optimisation d'achat en ligne — le premier réflexe du consommateur malin, avec la transparence pour boussole.",
});

const VALUES = [
  ["Transparence", "Nous affichons notre rémunération. Toujours."],
  ["Intelligence", "La bonne info, au bon moment, sans effort pour vous."],
  ["Simplicité", "Une seule expérience à la place de dix onglets."],
  ["Innovation", "Un assistant qui anticipe, pas un énième comparateur."],
  ["Confiance", "Vos données restent les vôtres. Sans exception."],
];

export default function AProposPage() {
  return (
    <PageShell
      eyebrow="À propos"
      title={<>Ne jamais payer le prix fort.</>}
      intro="FILON réunit en une interface unique ce qui est aujourd'hui éclaté entre des dizaines de services concurrents. Notre ambition : devenir la référence francophone de l'optimisation d'achat en ligne, en commençant par la Belgique, avec la transparence pour boussole."
      breadcrumb={[{ name: "À propos", path: "/a-propos" }]}
    >
      <section style={{ padding: "40px 0 60px" }}>
        <Container>
          <div className="filon-grid2" style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 16 }}>
            {VALUES.map(([t, d]) => (
              <div key={t} style={{ padding: 24, borderRadius: "var(--r-lg)", background: "var(--surface)", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 6 }}>{t}</div>
                <div style={{ color: "var(--text-dim)", fontSize: 15 }}>{d}</div>
              </div>
            ))}
          </div>
        </Container>
      </section>
    </PageShell>
  );
}
