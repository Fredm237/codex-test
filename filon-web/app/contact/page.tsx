import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { PageShell } from "@/components/site/PageShell";
import { ContactForm } from "@/components/site/ContactForm";

export const metadata: Metadata = buildMetadata({
  path: "/contact",
  title: "Contact",
  description: "Une question, un partenariat, une idée ? Écrivez à l'équipe FILON.",
});

export default function ContactPage() {
  return (
    <PageShell
      eyebrow="Contact"
      title={<>Parlons-en.</>}
      intro="Une question, une idée, un partenariat cashback ou reconditionné ? Laissez-nous un message — nous répondons vite."
      breadcrumb={[{ name: "Contact", path: "/contact" }]}
    >
      <ContactForm />
    </PageShell>
  );
}
