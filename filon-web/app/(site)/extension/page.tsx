import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Reveal } from "@/components/editorial/Reveal";

export const metadata: Metadata = buildMetadata({
  path: "/extension",
  title: "L'extension",
  description:
    "L'extension FILON travaille partout où vous achetez. Sur chaque fiche produit, elle affiche le meilleur prix ailleurs, le cashback disponible, l'alternative reconditionnée et l'historique de prix, sans quitter la page.",
});

const FAQ = [
  { q: "Sur quels navigateurs l'extension fonctionne-t-elle ?", a: "Chrome en premier, puis Edge, Firefox et Safari. L'application mobile et l'assistant conversationnel suivront. Rejoignez la liste pour être prévenu·e du lancement de chaque version." },
  { q: "L'extension ralentit-elle ma navigation ?", a: "Non. Elle ne s'active que sur les pages produit des marchands reconnus, reste invisible le reste du temps, et n'exécute aucune analyse tant que vous ne consultez pas un article." },
  { q: "Quelles données l'extension lit-elle ?", a: "Uniquement ce qui est nécessaire à la comparaison : le produit et le marchand de la page consultée. Pas de profil publicitaire, pas de revente. Le détail figure dans notre politique de confidentialité." },
  { q: "Dois-je créer un compte ?", a: "Non pour l'essentiel. Un compte devient utile pour les alertes de baisse de prix, mais la comparaison et le verdict fonctionnent sans inscription, et c'est gratuit." },
];

export default function ExtensionPage() {
  return (
    <>
      <ContentHero
        eyebrow="Extension"
        title={<>Votre copilote d&apos;achat, <span className="it">partout</span>.</>}
        intro="L'extension FILON est présente sur chaque site marchand. Au moment où vous regardez un produit, elle vous dit s'il est moins cher ailleurs, quel cashback l'accompagne, s'il existe une alternative reconditionnée, et si c'est le bon moment pour acheter."
        breadcrumb={[{ name: "Extension", path: "/extension" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <Reveal>
            <div className="ed-browsers">
              <span className="bw live"><span className="dot" /> Chrome · bientôt</span>
              <span className="bw"><span className="dot" /> Edge</span>
              <span className="bw"><span className="dot" /> Firefox</span>
              <span className="bw"><span className="dot" /> Safari</span>
            </div>
            <p style={{ color: "var(--ink-3)", fontSize: 13.5, marginTop: 4 }}>
              L&apos;extension Chrome arrive en premier. Ajoutez FILON pour être prévenu·e dès sa mise en ligne.
            </p>
          </Reveal>
        </div>
      </section>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Ce qui s&apos;affiche pendant que vous regardez un produit.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Le prix ailleurs", p: "« Vous regardez ce produit à 899€, il est à 799€ chez un autre marchand. »" },
              { n: "%", h: "Le cashback disponible", p: "Le taux le plus élevé du moment, activable en un geste avant de payer." },
              { n: "↻", h: "L'alternative reconditionnée", p: "L'équivalent garanti, souvent 20 à 45 % moins cher, quand il existe." },
              { n: "↧", h: "L'historique de prix", p: "Prix élevé, normal ou au plancher, pour savoir s'il faut acheter ou attendre." },
              { n: "★", h: "La fiabilité du vendeur", p: "Réputation et garanties, pour éviter la fausse bonne affaire." },
              { n: "✓", h: "Le verdict", p: "Un seul message clair : « acheter maintenant » ou « mieux vaut attendre »." },
            ]}
          />
        </div>
      </section>

      <FaqBlock items={FAQ} eyebrow="Extension · FAQ" title="L'extension, sans zone d'ombre." />
      <ClosingCta title={<>Installez le <span className="it">réflexe</span>.</>} sub="Ajoutez FILON à votre navigateur et laissez-le veiller avant chaque achat." />
    </>
  );
}
