import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ClosingCta, InfoGrid } from "@/components/editorial/ContentPage";
import { Method } from "@/components/editorial/EditorialSections";
import { IcHeart } from "@/components/editorial/icons";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/comment-ca-marche",
  title: "Comment ça marche",
  description:
    "FILON montre les offres indexées, leur fraîcheur et les preuves disponibles ; il s'abstient lorsque ces données ne suffisent pas.",
});

function CommentFR() {
  return (
    <>
      <ContentHero
        eyebrow="Comment ça marche"
        title={<>Les offres observées, avec leur <span className="it">contexte</span>.</>}
        intro="FILON compare son catalogue indexé, indique le périmètre et rend les inconnues visibles. Si la preuve manque, il ne force pas une conclusion."
        breadcrumb={[{ name: "Comment ça marche", path: "/comment-ca-marche" }]}
      />
      <Method />
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Ce que vous obtenez.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Prix observé", p: "Le montant du dernier relevé, sans inventer les frais de livraison absents." },
              { n: "◷", h: "Historique borné", p: "Nombre de relevés, durée suivie et conclusion seulement si l'historique suffit." },
              { n: "✓", h: "Périmètre visible", p: "Nombre d'offres et de marchands comparables actuellement indexés." },
              { n: "★", h: "Fraîcheur", p: "Date du relevé disponible et avertissement lorsque la donnée vieillit." },
              { n: "?", h: "Inconnues explicites", p: "Stock, livraison, retour ou garantie restent inconnus sans source." },
              { n: <IcHeart />, h: "Abstention", p: "FILON peut demander une vérification au lieu de recommander sans preuve." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Consultez l&apos;accès <span className="it">actuel</span>.</>} sub="Comparez les offres indexées et gardez les inconnues visibles avant de choisir." />
    </>
  );
}

function CommentNL() {
  return (
    <>
      <ContentHero
        eyebrow="Hoe het werkt"
        title={<>Bekeken aanbiedingen, met hun <span className="it">context</span>.</>}
        intro="FILON vergelijkt zijn geïndexeerde catalogus, toont het bereik en maakt onbekenden zichtbaar. Als bewijs ontbreekt, forceert het geen conclusie."
        breadcrumb={[{ name: "Hoe het werkt", path: "/comment-ca-marche" }]}
      />
      <Method />
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Wat je krijgt.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Bekeken prijs", p: "Het bedrag van de laatste meting, zonder ontbrekende verzendkosten te verzinnen." },
              { n: "◷", h: "Afgebakende historiek", p: "Aantal metingen, gevolgde duur en alleen een conclusie als de historiek volstaat." },
              { n: "✓", h: "Zichtbaar bereik", p: "Aantal vergelijkbare aanbiedingen en winkels die momenteel geïndexeerd zijn." },
              { n: "★", h: "Actualiteit", p: "Datum van de beschikbare meting en een waarschuwing wanneer gegevens verouderen." },
              { n: "?", h: "Expliciete onbekenden", p: "Voorraad, levering, retour of garantie blijven onbekend zonder bron." },
              { n: <IcHeart />, h: "Onthouding", p: "FILON kan om controle vragen in plaats van zonder bewijs aan te bevelen." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>Bekijk de huidige <span className="it">toegang</span>.</>} sub="Vergelijk geïndexeerde aanbiedingen en houd onbekenden zichtbaar voordat je kiest." />
    </>
  );
}

function CommentEN() {
  return (
    <>
      <ContentHero
        eyebrow="How it works"
        title={<>Observed offers, with their <span className="it">context</span>.</>}
        intro="FILON compares its indexed catalogue, states the scope and exposes unknowns. When evidence is missing, it does not force a conclusion."
        breadcrumb={[{ name: "How it works", path: "/comment-ca-marche" }]}
      />
      <Method />
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>What you get.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "€", h: "Observed price", p: "The latest reading, without inventing missing delivery costs." },
              { n: "◷", h: "Bounded history", p: "Reading count, tracking duration and a conclusion only when history is sufficient." },
              { n: "✓", h: "Visible scope", p: "The number of comparable offers and merchants currently indexed." },
              { n: "★", h: "Freshness", p: "The available reading date and a warning when data grows stale." },
              { n: "?", h: "Explicit unknowns", p: "Stock, shipping, returns or warranty stay unknown without a source." },
              { n: <IcHeart />, h: "Abstention", p: "FILON can ask for verification instead of recommending without evidence." },
            ]}
          />
        </div>
      </section>
      <ClosingCta title={<>See the current <span className="it">access</span>.</>} sub="Compare indexed offers and keep unknowns visible before choosing." />
    </>
  );
}

export default function CommentCaMarchePage() {
  return <Localized fr={<CommentFR />} nl={<CommentNL />} en={<CommentEN />} />;
}
