import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/a-propos",
  title: "À propos",
  description:
    "FILON veut devenir la référence francophone de l'optimisation d'achat en ligne — le premier réflexe du consommateur malin, avec la transparence pour boussole. Notre vision, notre mission, notre fondateur.",
});

const VALUES = [
  { n: "01", h: "Transparence", p: "Nous affichons notre rémunération. Toujours. C'est notre modèle, pas un argument." },
  { n: "02", h: "Intelligence", p: "La bonne information, au bon moment, sans effort pour vous." },
  { n: "03", h: "Simplicité", p: "Une seule expérience à la place de dix onglets." },
  { n: "04", h: "Innovation", p: "Un assistant qui anticipe, pas un énième comparateur." },
  { n: "05", h: "Confiance", p: "Vos données restent les vôtres. Sans exception." },
];

export default function AProposPage() {
  return (
    <>
      <ContentHero
        eyebrow="À propos"
        title={<>Ne jamais payer le <span className="it">prix fort</span>.</>}
        intro="FILON réunit en une interface unique ce qui est aujourd'hui éclaté entre des dizaines de services concurrents. Notre ambition : devenir la référence francophone de l'optimisation d'achat en ligne, en commençant par la Belgique, avec la transparence pour boussole."
        breadcrumb={[{ name: "À propos", path: "/a-propos" }]}
      />

      <ProseBlock heading={<>Le problème que nous <span className="it">réglons</span>.</>}>
        <p>
          Pour vraiment optimiser un achat, il faut aujourd&apos;hui vérifier plusieurs plateformes de cashback, chercher un
          équivalent reconditionné, tester des codes promo, comparer les marchands… C&apos;est long, et la plupart des gens
          abandonnent en payant plein tarif.
        </p>
        <p>
          FILON automatise ce parcours. En une seconde, il croise <b>cashback, reconditionné et codes promo</b> et vous donne
          un seul chiffre : votre prix réel le plus bas. Vous ne changez rien à vos habitudes — vous payez simplement moins.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Nos cinq valeurs.</h2>
          </div>
          <div className="ed-infogrid" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            {VALUES.map((v) => (
              <div className="ed-info" key={v.h}>
                <div className="n mono">{v.n}</div>
                <h3>{v.h}</h3>
                <p>{v.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <ProseBlock heading={<>Le <span className="it">fondateur</span>.</>}>
        <p>
          FILON est porté par <b>{site.founder}</b>, à {site.city}. Un profil à la croisée du digital, de la gestion de projet
          et de l&apos;entrepreneuriat technologique.
        </p>
        <p>
          Coordinateur social au CPAS de Woluwe-Saint-Pierre, il pilote des projets et une communication bilingue FR/NL. Il est
          aussi le fondateur de <b>SmartWave FX</b> (plateforme SaaS de trading algorithmique et d&apos;éducation), où il a
          construit l&apos;infrastructure technique, le marketing de contenu et le playbook commercial. Création de communautés,
          production de contenu multi-format, storytelling de marque : c&apos;est précisément ce qui fait la force d&apos;un
          projet comme FILON, où la marque et l&apos;audience sont le vrai actif.
        </p>
      </ProseBlock>

      <ProseBlock heading={<>Pourquoi la <span className="it">Belgique</span> d&apos;abord.</>} alt>
        <p>
          Le marché belge francophone est nettement moins servi que la France par les acteurs historiques du cashback.
          C&apos;est une opportunité : y établir une position de référent, avec une exécution soignée et une marque de
          confiance, avant d&apos;élargir à la France et au reste de la francophonie européenne.
        </p>
        <p>
          À l&apos;heure où les dérives d&apos;attribution du secteur (affaires Honey, Phia) ont ébranlé la confiance, nous
          faisons de la <b>transparence totale</b> notre différence — pas un slogan, un modèle.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Rejoignez le <span className="it">réflexe</span> malin.</>} sub="Ajoutez FILON et ne payez plus jamais le prix fort." />
    </>
  );
}
