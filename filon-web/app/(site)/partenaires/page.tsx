import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/partenaires",
  title: "Partenaires",
  description:
    "Vous êtes une marque, un marchand ou un média ? Travaillons ensemble. Écrivez à l'équipe FILON.",
});

export default function PartenairesPage() {
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
