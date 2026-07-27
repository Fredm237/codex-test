import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { ContactForm } from "@/components/editorial/Forms";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/contact",
  title: "Contact",
  description: "Une question, un partenariat cashback ou reconditionné, une idée ? Écrivez à l'équipe FILON.",
});

function ContactFR() {
  return (
    <>
      <ContentHero
        eyebrow="Contact"
        title={<>Parlons-en.</>}
        intro="Une question, une idée, un partenariat cashback ou reconditionné ? Laissez-nous un message, nous répondons vite."
        breadcrumb={[{ name: "Contact", path: "/contact" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <ContactForm />
        </div>
      </section>
    </>
  );
}

function ContactNL() {
  return (
    <>
      <ContentHero
        eyebrow="Contact"
        title={<>Laten we praten.</>}
        intro="Een vraag, een idee, een cashback- of refurbished-partnerschap ? Laat ons een bericht na, we antwoorden snel."
        breadcrumb={[{ name: "Contact", path: "/contact" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <ContactForm />
        </div>
      </section>
    </>
  );
}

export default function ContactPage() {
  return <Localized fr={<ContactFR />} nl={<ContactNL />} />;
}
