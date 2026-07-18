import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { Reveal } from "@/components/editorial/Reveal";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/partenaires",
  title: "Partenaires & marchands",
  description:
    "FILON connecte plateformes de cashback, marchands et acteurs du reconditionné à une audience de consommateurs à forte intention d'achat. Devenez partenaire et touchez des acheteurs au moment de la décision.",
});

const SOURCES = [
  "iGraal", "Poulpeo", "Widilo", "Joko", "eBuyClub",
  "Back Market", "Refurbed", "Amazon", "Fnac", "Cdiscount", "Rakuten",
];

export default function PartenairesPage() {
  return (
    <>
      <ContentHero
        eyebrow="Partenaires"
        title={<>Touchez l&apos;acheteur au <span className="it">moment</span> décisif.</>}
        intro="FILON accompagne le consommateur juste avant l'achat — l'instant où l'intention est la plus forte. Pour les plateformes, marchands et acteurs du reconditionné, c'est un canal d'acquisition qualifié, transparent et mesurable."
        breadcrumb={[{ name: "Partenaires", path: "/partenaires" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <Reveal>
            <div className="ed-prose" style={{ marginBottom: 20 }}>
              <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>Écosystème</span>
              <h2 style={{ maxWidth: "22ch" }}>Les sources que FILON compare déjà.</h2>
            </div>
            <div className="ed-partners">
              <div className="track" aria-hidden="true">
                {[...SOURCES, ...SOURCES].map((s, i) => (
                  <span key={i}>{s}</span>
                ))}
              </div>
            </div>
            <p style={{ color: "var(--ink-3)", fontSize: 13, marginTop: 12 }}>
              Marques citées à titre indicatif d&apos;écosystème comparé. Les intégrations évoluent au fil des versions.
            </p>
          </Reveal>
        </div>
      </section>

      <ProseBlock heading={<>Pourquoi devenir <span className="it">partenaire</span>.</>}>
        <p>
          FILON n&apos;envoie pas du trafic au hasard : il oriente vers l&apos;offre qui gagne réellement pour l&apos;utilisateur.
          Résultat, les acheteurs que vous recevez arrivent <b>convaincus et prêts à convertir</b>, avec un coût d&apos;acquisition
          maîtrisé et une attribution nette.
        </p>
        <p>
          Notre différence, c&apos;est la <b>transparence</b> : nous affichons notre rémunération et respectons une attribution
          honnête. Dans un secteur marqué par les dérives (affaires Honey, Phia), c&apos;est un gage de confiance autant pour
          l&apos;utilisateur que pour le partenaire.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Ce que nous proposons aux partenaires.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Trafic à forte intention", p: "Des acheteurs au moment précis de la décision, pas des curieux." },
              { n: "02", h: "Attribution transparente", p: "Un suivi honnête et lisible, sans détournement de commission." },
              { n: "03", h: "Audience francophone", p: "Belgique d'abord, puis France et francophonie européenne." },
              { n: "04", h: "Deals mis en avant", p: "Vos meilleures offres exposées quand elles gagnent vraiment pour l'utilisateur." },
              { n: "05", h: "Reconditionné valorisé", p: "Un canal dédié pour les acteurs du reconditionné garanti." },
              { n: "06", h: "Marque de confiance", p: "Être associé à un tiers reconnu pour sa transparence." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Travaillons <span className="it">ensemble</span>.</>} alt>
        <p>
          Plateforme de cashback, marchand, spécialiste du reconditionné ou marque&nbsp;? Écrivez-nous à{" "}
          <a href={`mailto:partenaires@${site.domain}`}>partenaires@{site.domain}</a> — nous vous présentons les formats de
          collaboration et les modalités d&apos;intégration.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Rejoignez l&apos;écosystème <span className="it">FILON</span>.</>} sub="Un canal d'acquisition qualifié, transparent et aligné sur l'intérêt de l'acheteur." />
    </>
  );
}
