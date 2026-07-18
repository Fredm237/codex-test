import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";

export const metadata: Metadata = buildMetadata({
  path: "/cashback",
  title: "Cashback : toujours le meilleur taux",
  description:
    "FILON compare les taux de cashback d'iGraal, Poulpeo, Widilo, Joko et eBuyClub pour chaque marchand et applique automatiquement le plus rémunérateur. Comparateur de cashback francophone, gratuit et transparent.",
});

const FAQ = [
  { q: "Qu'est-ce que le cashback, concrètement ?", a: "Le cashback, c'est un pourcentage de votre achat qui vous est remboursé après validation. En passant par une plateforme partenaire avant de payer, vous récupérez une partie de la commission qu'elle touche du marchand. FILON trouve le taux le plus élevé du moment pour votre boutique." },
  { q: "Pourquoi comparer les plateformes de cashback ?", a: "Parce que les taux varient énormément : un même marchand peut offrir 3 % chez l'une, 6 % chez une autre et 8 % en promotion ailleurs, le tout le même jour. Sans comparer, vous laissez de l'argent sur la table à chaque achat." },
  { q: "Quelles plateformes FILON compare-t-il ?", a: "Les principales plateformes francophones : iGraal, Poulpeo, Widilo, Joko, eBuyClub et d'autres. Nous ajoutons régulièrement de nouveaux partenaires." },
  { q: "Le cashback est-il cumulable avec un code promo ?", a: "Souvent oui. FILON teste la combinaison la plus rentable (cashback + code promo + éventuellement reconditionné) et vous indique le prix réel final." },
  { q: "Combien de temps pour recevoir mon cashback ?", a: "Cela dépend de la plateforme et du marchand : la validation prend généralement de quelques jours à quelques semaines, puis le retrait se fait dès le seuil atteint. FILON affiche ces conditions avant que vous ne cliquiez." },
];

export default function CashbackPage() {
  return (
    <>
      <ContentHero
        eyebrow="Cashback"
        title={<>Le meilleur taux de cashback, sans le chercher.</>}
        intro="Un même marchand peut offrir 5 % sur une plateforme, 7 % sur une autre et 4 % sur une troisième — le même jour. FILON compare iGraal, Poulpeo, Widilo, Joko et eBuyClub en temps réel et vous oriente vers le taux le plus rémunérateur, automatiquement."
        breadcrumb={[{ name: "Cashback", path: "/cashback" }]}
      />

      <ProseBlock heading={<>Le cashback, c'est de l'argent que vous <span className="it">oubliez</span> de récupérer.</>}>
        <p>
          Des millions de francophones utilisent déjà le cashback. Mais la plupart s'inscrivent à <b>une seule</b> plateforme
          et s'y tiennent — alors que les taux changent en permanence d'une plateforme à l'autre.
        </p>
        <p>
          FILON supprime ce travail : à l'instant où vous vous apprêtez à acheter, il interroge les plateformes partenaires,
          repère le taux le plus élevé pour ce marchand, et vous y envoie. Vous gardez vos habitudes ; vous encaissez juste plus.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Comment FILON maximise votre cashback.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Détection du marchand", p: "FILON reconnaît la boutique sur laquelle vous êtes et prépare la comparaison." },
              { n: "02", h: "Comparaison des taux", p: "iGraal, Poulpeo, Widilo, Joko, eBuyClub… le taux le plus élevé du moment est identifié." },
              { n: "03", h: "Activation en un geste", p: "Vous partez sur la bonne plateforme, le cashback est suivi, l'économie est à vous." },
            ]}
          />
        </div>
      </section>

      <FaqBlock items={FAQ} eyebrow="Cashback · FAQ" title="Le cashback, sans zone d'ombre." />
      <ClosingCta title={<>Ne cliquez plus jamais « payer » <span className="it">sans</span> cashback.</>} sub="FILON s'en occupe pour vous, gratuitement, à chaque achat." />
    </>
  );
}
