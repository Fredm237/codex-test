import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { Reveal } from "@/components/editorial/Reveal";

export const metadata: Metadata = buildMetadata({
  path: "/intelligence",
  title: "Filon Intelligence Graph",
  description:
    "Sous le copilote FILON, une base de connaissance produit propriétaire : prix historiques, fiabilité des marques, réparabilité, durée de vie, coût total de possession. C'est ce qui transforme « voici les prix » en « voici ce que vous devriez acheter ».",
});

const PHASES = [
  {
    n: "Phase 1 · aujourd'hui",
    status: "En cours",
    live: true,
    h: "Le copilote conversationnel",
    p: "Vous décrivez un besoin, FILON analyse le marché et recommande la meilleure décision, quoi acheter, où, et quand.",
    items: ["Analyse besoin + budget", "Cashback, reconditionné, codes promo", "Verdict acheter / attendre"],
  },
  {
    n: "Phase 2 · prochainement",
    status: "À venir",
    live: false,
    h: "L'extension, partout",
    p: "Le copilote présent sur chaque site marchand, le vrai avantage durable. Sur chaque fiche produit, la meilleure alternative en un coup d'œil.",
    items: ["Prix ailleurs en direct", "Alternative reconditionnée", "Historique de prix contextuel"],
  },
  {
    n: "Phase 3 · l'ambition",
    status: "En construction",
    live: false,
    h: "L'Intelligence Graph",
    p: "La base de connaissance produit propriétaire qui alimente tout le reste, et qui, à terme, vaut bien plus que l'affiliation.",
    items: ["Durée de vie & réparabilité", "Fiabilité des marques", "Coût total de possession"],
  },
];

export default function IntelligencePage() {
  return (
    <>
      <ContentHero
        eyebrow="Technologie"
        title={<>Sous le copilote, une <span className="it">intelligence</span> propriétaire.</>}
        intro="Un comparateur affiche des prix. FILON recommande une décision. La différence tient en une chose : le Filon Intelligence Graph, une base de connaissance produit que nous construisons, et qui apprend à chaque analyse."
        breadcrumb={[{ name: "Intelligence", path: "/intelligence" }]}
      />

      <ProseBlock heading={<>De « voici les prix » à <span className="it">« voici quoi acheter »</span>.</>}>
        <p>
          Trouver le prix le plus bas est utile, mais ce n&apos;est que la surface. La vraie question d&apos;un achat, c&apos;est :
          <b> est-ce le bon produit, au bon moment, qui durera&nbsp;?</b> Y répondre demande bien plus qu&apos;un flux de prix.
        </p>
        <p>
          C&apos;est le rôle de l&apos;Intelligence Graph : croiser, pour chaque produit, ses caractéristiques, son historique de
          prix, la fiabilité de sa marque, sa réparabilité, sa durée de vie estimée et son coût réel de possession. Cette
          connaissance, accumulée dans le temps, devient l&apos;actif le plus précieux de FILON.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>Ce que le graphe sait de chaque produit</span>
            <h2 style={{ maxWidth: "20ch" }}>Bien plus qu&apos;un prix.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "◷", h: "Historique de prix", p: "Le vrai niveau d'un prix : au plancher, dans la moyenne, ou gonflé." },
              { n: "★", h: "Fiabilité de la marque", p: "Taux de panne, qualité du SAV, satisfaction réelle dans le temps." },
              { n: "🔧", h: "Réparabilité", p: "Indice de réparabilité et disponibilité des pièces détachées." },
              { n: "⌛", h: "Durée de vie estimée", p: "Combien de temps le produit tiendra vraiment, usage réel à l'appui." },
              { n: "€", h: "Coût total de possession", p: "Prix d'achat, consommables, réparations, revente : le coût sur la durée." },
              { n: "💬", h: "Avis analysés", p: "Des milliers d'avis synthétisés pour en extraire le signal, pas le bruit." },
            ]}
          />
        </div>
      </section>

      <section className="ed-band">
        <div className="ed-wrap">
          <Reveal>
            <div className="ed-prose" style={{ marginBottom: 28 }}>
              <span className="eyebrow" style={{ display: "block", marginBottom: 12 }}>Notre trajectoire</span>
              <h2 style={{ maxWidth: "22ch" }}>Là où va FILON.</h2>
            </div>
          </Reveal>
          <Reveal>
            <div className="ed-roadmap">
              {PHASES.map((ph) => (
                <div className={`ed-phase ${ph.live ? "live" : ""}`} key={ph.h}>
                  <div className="ph">
                    <span className="n">{ph.n}</span>
                    <span className={`st ${ph.live ? "now" : ""}`}>{ph.status}</span>
                  </div>
                  <h3>{ph.h}</h3>
                  <p>{ph.p}</p>
                  <ul>
                    {ph.items.map((it) => (
                      <li key={it}>{it}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <ProseBlock heading={<>Pourquoi FILON <span className="it">gagne</span>.</>} alt>
        <p>
          Google, Amazon ou d&apos;autres peuvent afficher des prix. Mais un copilote d&apos;achat de confiance repose sur cinq
          forces difficiles à copier : une <b>spécialisation achat</b> francophone, une <b>base produit locale</b> supérieure,
          une <b>extension ultra-efficace</b> présente partout, une <b>communauté</b> de consommateurs, et des{" "}
          <b>données comportementales propriétaires</b> qui améliorent la recommandation à chaque usage.
        </p>
        <p>
          Le tout avec la <b>transparence</b> comme socle, l&apos;exact opposé des modèles qui ont trahi la confiance du secteur.
          C&apos;est ce cercle vertueux, pas un simple flux de prix, qui construit l&apos;avance de FILON.
        </p>
      </ProseBlock>

      <ClosingCta title={<>L&apos;intelligence au service de <span className="it">votre</span> achat.</>} sub="Un copilote qui apprend, pour des décisions toujours meilleures. Et gratuit." />
    </>
  );
}
