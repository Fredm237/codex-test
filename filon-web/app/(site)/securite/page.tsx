import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/securite",
  title: "Sécurité & confiance",
  description:
    "Comment FILON protège vos données et votre navigation : minimisation des données, aucune revente, chiffrement, conformité RGPD. La confiance n'est pas une option.",
});

export default function SecuritePage() {
  return (
    <>
      <ContentHero
        eyebrow="Sécurité"
        title={<>La confiance n&apos;est pas une option. C&apos;est le <span className="it">produit</span>.</>}
        intro="Un copilote d'achat n'a de valeur que si vous pouvez lui faire confiance. Voici concrètement comment FILON protège vos données, votre navigation et votre argent."
        breadcrumb={[{ name: "Sécurité", path: "/securite" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <InfoGrid
            items={[
              { n: "🔒", h: "Minimisation des données", p: "FILON n'analyse que ce qui est strictement nécessaire à la comparaison. Rien de plus." },
              { n: "🚫", h: "Aucune revente", p: "Pas de profil publicitaire, pas de revente à des tiers. Vos données restent les vôtres." },
              { n: "🔐", h: "Connexions chiffrées", p: "Les échanges avec nos services sont chiffrés (HTTPS/TLS) de bout en bout." },
              { n: "🇪🇺", h: "Conforme RGPD", p: "Traitement conforme au RGPD par défaut, avec des droits que vous pouvez exercer à tout moment." },
              { n: "📊", h: "Mesure sans cookie", p: "Notre audience est mesurée sans cookie et de façon anonyme (Plausible)." },
              { n: "👁", h: "Sans arrière-pensée", p: "Pas de publicité. La recommandation sert votre intérêt, pas le nôtre." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Ce que FILON ne fait <span className="it">jamais</span>.</>} alt>
        <p>
          FILON ne revend pas votre navigation, ne construit pas de profil publicitaire, et ne modifie jamais le prix que vous
          payez chez le marchand. Il ne stocke pas non plus vos moyens de paiement : l&apos;achat se fait chez le marchand,
          comme d&apos;habitude, FILON vous a seulement mené·e à la meilleure décision.
        </p>
        <p>
          Le détail complet des traitements figure dans notre <a href="/confidentialite">politique de confidentialité</a> et
          notre <a href="/cookies">politique cookies</a>.
        </p>
      </ProseBlock>

      <ProseBlock heading={<>Signaler une <span className="it">vulnérabilité</span>.</>}>
        <p>
          La sécurité est un travail continu. Si vous pensez avoir identifié une faille ou un comportement anormal, écrivez-nous
          à <a href={`mailto:securite@${site.domain}`}>securite@{site.domain}</a>. Nous étudions chaque signalement sérieux avec
          attention et reconnaissance.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Un copilote en qui vous pouvez avoir <span className="it">confiance</span>.</>} sub="Minimisation des données, zéro revente, aucune publicité." />
    </>
  );
}
