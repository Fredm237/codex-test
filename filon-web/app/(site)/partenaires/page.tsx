import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/partenaires",
  title: "Partenaires",
  description:
    "Vous êtes une marque, un marchand ou un média ? Travaillons ensemble. Écrivez à l'équipe FILON.",
});

function PartenairesFR() {
  return (
    <>
      <ContentHero
        eyebrow="Partenaires"
        title={<>Travaillons <span className="it">ensemble</span>.</>}
        intro="FILON aide chaque jour des personnes à mieux acheter. Vous êtes une marque, un marchand ou un média ? Parlons de ce qu'on peut faire ensemble."
        breadcrumb={[{ name: "Partenaires", path: "/partenaires" }]}
      />

      <ProseBlock heading={<>Une audience qui <span className="it">décide</span>.</>}>
        <p>
          Nos utilisateurs viennent sur FILON au moment précis où ils s&apos;apprêtent à acheter. C&apos;est le meilleur
          moment pour rencontrer une belle marque.
        </p>
        <p>
          Si vous pensez avoir votre place, écrivez-nous à{" "}
          <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. On revient vers vous rapidement.
        </p>
      </ProseBlock>

      <ClosingCta title={<>On en <span className="it">parle</span> ?</>} sub="Écrivez-nous. Une bonne collaboration commence par une conversation." />
    </>
  );
}

function PartenairesNL() {
  return (
    <>
      <ContentHero
        eyebrow="Partners"
        title={<>Laten we <span className="it">samenwerken</span>.</>}
        intro="FILON helpt elke dag mensen om beter te kopen. Ben je een merk, een winkel of een medium ? Laten we praten over wat we samen kunnen doen."
        breadcrumb={[{ name: "Partners", path: "/partenaires" }]}
      />

      <ProseBlock heading={<>Een publiek dat <span className="it">beslist</span>.</>}>
        <p>
          Onze gebruikers komen op FILON op het precieze moment dat ze op het punt staan te kopen. Dat is het beste
          moment om een mooi merk te ontmoeten.
        </p>
        <p>
          Als je denkt dat je hier je plaats hebt, schrijf ons op{" "}
          <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. We komen snel bij je terug.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Erover <span className="it">praten</span> ?</>} sub="Schrijf ons. Een goede samenwerking begint met een gesprek." />
    </>
  );
}

export default function PartenairesPage() {
  return <Localized fr={<PartenairesFR />} nl={<PartenairesNL />} />;
}
