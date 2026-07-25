import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";

export const metadata: Metadata = buildMetadata({
  path: "/transparence",
  title: "Transparence & affiliation",
  description:
    "Comment FILON gagne de l'argent : liens d'affiliation, sans surcoût pour vous, sans jamais fausser un conseil. Neutralité, gratuité et clarté, expliquées.",
});

export default function TransparencePage() {
  return (
    <>
      <ContentHero
        eyebrow="Transparence"
        title={
          <>
            Comment FILON gagne sa vie, <span className="it">sans jamais vous coûter plus cher</span>.
          </>
        }
        intro={
          <>
            Un service gratuit doit s&apos;expliquer. Voici, sans détour, notre modèle : d&apos;où vient
            l&apos;argent, ce que ça change pour vous (rien), et ce que nous nous interdisons.
          </>
        }
        breadcrumb={[{ name: "Transparence", path: "/transparence" }]}
      />

      <ProseBlock heading={<>Nous sommes rémunérés par <span className="it">l&apos;affiliation</span>.</>}>
        <p>
          Quand vous cliquez sur «&nbsp;Voir l&apos;offre&nbsp;» et que vous achetez chez un marchand, celui-ci peut
          nous verser une <b>commission d&apos;affiliation</b>. C&apos;est notre source de revenus.
        </p>
        <p>
          Point essentiel&nbsp;: cette commission est payée par le <b>marchand</b>, prélevée sur sa marge. Elle
          <b> n&apos;augmente jamais le prix que vous payez</b>. Vous payez exactement le même montant qu&apos;en
          allant directement sur le site du marchand.
        </p>
        <p style={{ color: "var(--ink-3)", fontSize: 14 }}>
          En clair, comme l&apos;exige la réglementation (DGCCRF, ARPP) et nos partenaires&nbsp;: certains liens de
          ce site sont des liens affiliés. Cliquer dessus et acheter peut nous rapporter une commission, sans coût
          supplémentaire pour vous.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-lead">
            <span className="idx">Nos règles</span>
            <h2>
              Ce que la rémunération ne change <span className="it">jamais</span>.
            </h2>
          </div>
          <InfoGrid
            items={[
              {
                n: "01",
                h: "Aucun classement acheté",
                p: "Un marchand qui nous rémunère mieux n'obtient pas une meilleure place, ni un meilleur Score. Le classement suit votre intérêt, point.",
              },
              {
                n: "02",
                h: "Le meilleur prix d'abord",
                p: "Si l'offre la moins chère ne nous rapporte rien, c'est quand même elle que nous vous montrons. Toujours.",
              },
              {
                n: "03",
                h: "Sans publicité",
                p: "Pas de bannières, pas de placements déguisés. Rien ne vient troubler le conseil que vous recevez.",
              },
              {
                n: "04",
                h: "Gratuit, pour de vrai",
                p: "Aucun abonnement, aucune carte bancaire, aucune option payante. Vous ne payez jamais FILON.",
              },
              {
                n: "05",
                h: "Vos données restent à vous",
                p: "Mesure d'audience sans cookie et anonyme (Plausible). Aucun profil publicitaire, aucune revente.",
              },
              {
                n: "06",
                h: "Le raisonnement est ouvert",
                p: "Le Score se décompose critère par critère. Vous voyez pourquoi une offre est recommandée.",
              },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Pendant le lancement, on <span className="it">signale tout</span>.</>} alt>
        <p>
          FILON démarre. Tant que nos partenariats marchands et nos accès aux données (cashback, historique de prix
          long) ne sont pas tous signés, certaines informations reposent sur des <b>estimations</b>.
        </p>
        <p>
          Nous ne les cachons pas&nbsp;: elles sont <b>clairement signalées</b> comme telles («&nbsp;prix
          estimés&nbsp;», «&nbsp;exemple&nbsp;», «&nbsp;chiffres réels à venir&nbsp;»). À mesure que les données
          réelles arrivent, elles remplacent les estimations, sans jamais inventer de chiffre entre-temps.
        </p>
        <p>
          Notre seul actif, c&apos;est votre confiance. La trahir une fois suffirait à tout perdre&nbsp;: nous
          préférons afficher «&nbsp;on ne sait pas encore&nbsp;» plutôt qu&apos;un beau chiffre faux.
        </p>
      </ProseBlock>

      <ClosingCta
        title={<>Un conseil de votre côté, <span className="it">rien d&apos;autre.</span></>}
        sub="Demandez à FILON avant d'acheter. Gratuit, neutre, sans publicité."
      />
    </>
  );
}
