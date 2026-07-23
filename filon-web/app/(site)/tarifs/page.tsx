import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Reveal } from "@/components/editorial/Reveal";

export const metadata: Metadata = buildMetadata({
  path: "/tarifs",
  title: "Tarifs",
  description:
    "FILON est gratuit, pour tout le monde, pour toujours. Sans abonnement, sans carte bancaire, sans revente de vos données.",
});

const INCLUS = [
  "Le meilleur prix réel, trouvé pour vous",
  "Un verdict clair : acheter maintenant, ou attendre",
  "Le bon moment pour passer commande",
  "Des alternatives fiables, quand elles existent",
  "L'extension, présente au bon moment",
  "Des alertes quand le prix baisse",
  "Vos données restent chez vous · RGPD",
];

const FAQ = [
  { q: "FILON est-il vraiment 100 % gratuit ?", a: "Oui. Tout est gratuit, pour tout le monde, sans abonnement ni carte bancaire. Il n'y a pas de version payante." },
  { q: "La recommandation est-elle neutre ?", a: "Oui. Elle est calculée sur votre seul intérêt. Aucune marque ne peut acheter sa place dans un conseil FILON." },
  { q: "Vais-je devoir payer un jour ?", a: "Non. FILON est gratuit, et le restera." },
  { q: "Mes données sont-elles revendues ?", a: "Jamais. Pas de profil publicitaire, pas de revente à des tiers. Conforme RGPD par défaut." },
];

export default function TarifsPage() {
  return (
    <>
      <ContentHero
        eyebrow="Tarifs"
        title={<>Gratuit. Pour tout le monde. <span className="it">Pour toujours.</span></>}
        intro="Pas d'abonnement, pas de version premium, pas de carte bancaire. FILON est entièrement gratuit, et le restera."
        breadcrumb={[{ name: "Tarifs", path: "/tarifs" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <Reveal>
            <div className="ed-plan featured" style={{ maxWidth: 620, margin: "0 auto" }}>
              <span className="tag">Le seul plan qui existe</span>
              <div className="name">Filon</div>
              <div className="price">0€ <small>/ pour toujours · sans carte bancaire</small></div>
              <p className="lede">Tout FILON. Décrivez un besoin, obtenez le meilleur prix réel et le verdict « acheter ou attendre », à chaque achat.</p>
              <ul>
                {INCLUS.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
              <div className="cta-wrap">
                <a className="ed-btn wave" href="/#installer" style={{ textDecoration: "none" }}>Ajouter gratuitement</a>
              </div>
            </div>
          </Reveal>
          <p style={{ textAlign: "center", color: "var(--ink-3)", fontSize: 13.5, marginTop: 22 }}>
            Le prix chez le marchand est le même avec ou sans FILON. Vous ne payez jamais.
          </p>
        </div>
      </section>

      <ProseBlock heading={<>Gratuit, sans <span className="it">arrière-pensée</span>.</>} alt>
        <p>
          Gratuit ne veut pas dire au rabais. FILON est complet, sans version payante cachée, sans publicité. Vous ne
          payez jamais.
        </p>
        <p>
          Et vos données ne sont pas à vendre. Le conseil que vous recevez ne sert qu&apos;une chose : votre intérêt.
        </p>
      </ProseBlock>

      <FaqBlock items={FAQ} eyebrow="Tarifs · FAQ" title="Ce que « gratuit » veut vraiment dire." />
      <ClosingCta title={<>Commencez, c&apos;est <span className="it">gratuit</span>.</>} sub="Sans abonnement ni carte bancaire. Vraiment." />
    </>
  );
}
