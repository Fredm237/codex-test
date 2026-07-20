import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Reveal } from "@/components/editorial/Reveal";

export const metadata: Metadata = buildMetadata({
  path: "/tarifs",
  title: "Tarifs",
  description:
    "FILON est gratuit, pour tout le monde, pour toujours. Le copilote d'achat qui trouve le meilleur prix réel avant chaque commande, sans abonnement, sans carte bancaire, sans revente de vos données. Voici pourquoi c'est possible.",
});

const INCLUS = [
  "Analyse d'achat par l'IA, décrivez un besoin, obtenez la meilleure décision",
  "Comparaison cashback, reconditionné et codes promo en temps réel",
  "Verdict clair : « acheter maintenant » ou « attendre »",
  "Meilleur vendeur et prix réel le plus bas",
  "Historique de prix pour savoir si c'est le bon moment",
  "Extension navigateur, présente sur chaque site marchand",
  "Alertes de baisse de prix",
  "Aucune revente de données · conforme RGPD",
];

const FAQ = [
  { q: "FILON est-il vraiment 100 % gratuit ?", a: "Oui. Toutes les fonctions de FILON sont gratuites, pour tout le monde, sans abonnement ni carte bancaire. Il n'y a pas de version « premium » payante : ce que vous voyez est ce que vous obtenez, gratuitement." },
  { q: "Comment FILON gagne-t-il de l'argent, alors ?", a: "Via une part de la commission d'apport que les plateformes partenaires nous reversent quand vous activez une offre (cashback, reconditionné, code promo). C'est le marchand qui paie cette commission, jamais vous. Le prix que vous payez est identique, que vous passiez par FILON ou non." },
  { q: "Est-ce que la recommandation est biaisée par ce que FILON gagne ?", a: "Non. Le verdict est calculé sur votre seul intérêt : le coût réel le plus bas et la fiabilité du vendeur. Notre rémunération est affichée en toute transparence, c'est notre modèle, pas un argument." },
  { q: "Vais-je devoir payer un jour ?", a: "Non. Le modèle de FILON repose sur la commission d'apport des partenaires, pas sur votre portefeuille. Le copilote d'achat restera gratuit." },
  { q: "Mes données sont-elles revendues pour compenser ?", a: "Jamais. Pas de profil publicitaire, pas de revente à des tiers. FILON n'analyse que ce qui est nécessaire à la comparaison, conforme RGPD par défaut." },
];

export default function TarifsPage() {
  return (
    <>
      <ContentHero
        eyebrow="Tarifs"
        title={<>Gratuit. Pour tout le monde. <span className="it">Pour toujours.</span></>}
        intro="Pas d'abonnement, pas de version premium, pas de carte bancaire. FILON est un copilote d'achat entièrement gratuit, et le modèle est pensé pour qu'il le reste."
        breadcrumb={[{ name: "Tarifs", path: "/tarifs" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <Reveal>
            <div className="ed-plan featured" style={{ maxWidth: 620, margin: "0 auto" }}>
              <span className="tag">Le seul plan qui existe</span>
              <div className="name">Filon</div>
              <div className="price">0€ <small>/ pour toujours · sans carte bancaire</small></div>
              <p className="lede">Le copilote d&apos;achat complet. Décrivez un besoin, obtenez le meilleur coût réel et le verdict « acheter ou attendre », gratuitement, à chaque achat.</p>
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
            Le prix chez le marchand est le même avec ou sans FILON. Nous ne facturons jamais l&apos;utilisateur.
          </p>
        </div>
      </section>

      <ProseBlock heading={<>Pourquoi c&apos;est <span className="it">gratuit</span>, et honnête.</>} alt>
        <p>
          Quand vous activez une offre via FILON, la plateforme partenaire nous reverse une part de sa{" "}
          <b>commission d&apos;apport</b>. C&apos;est cette commission, payée par le marchand, jamais par vous, qui finance FILON.
          Votre prix ne change pas d&apos;un centime.
        </p>
        <p>
          Nous refusons le modèle inverse, celui qui a miné la confiance du secteur (affaires Honey, Phia) : détourner
          l&apos;attribution ou revendre vos données. Chez FILON, la rémunération est <b>affichée</b> et la recommandation sert
          <b> votre</b> intérêt. La transparence, c&apos;est le produit, pas une option payante.
        </p>
      </ProseBlock>

      <FaqBlock items={FAQ} eyebrow="Tarifs · FAQ" title="Ce que « gratuit » veut vraiment dire." />
      <ClosingCta title={<>Commencez, c&apos;est <span className="it">gratuit</span>.</>} sub="Le copilote d'achat, sans abonnement ni carte bancaire. Vraiment." />
    </>
  );
}
