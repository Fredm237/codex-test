import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { ContactForm } from "@/components/editorial/Forms";

export const metadata: Metadata = buildMetadata({
  path: "/contact",
  title: "Contact",
  description: "Une question, un partenariat cashback ou reconditionné, une idée ? Écrivez à l'équipe FILON.",
});

export default function ContactPage() {
  return (
    <>
      <ContentHero
        eyebrow="Contact"
        title={<>Parlons-en.</>}
        intro="Une question, une idée, un partenariat cashback ou reconditionné ? Laissez-nous un message — nous répondons vite."
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
