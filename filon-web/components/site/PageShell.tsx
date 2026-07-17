import type { ReactNode } from "react";
import { Container } from "@/components/ui/Container";
import { Eyebrow } from "./Sections";
import { JsonLd, breadcrumbSchema } from "@/lib/seo";

export function PageShell({
  eyebrow,
  title,
  intro,
  breadcrumb,
  children,
}: {
  eyebrow: string;
  title: ReactNode;
  intro: string;
  breadcrumb: { name: string; path: string }[];
  children?: ReactNode;
}) {
  return (
    <>
      <JsonLd data={breadcrumbSchema([{ name: "Accueil", path: "/" }, ...breadcrumb])} />
      <section style={{ padding: "90px 0 40px" }}>
        <Container>
          <div style={{ maxWidth: 760 }}>
            <Eyebrow>{eyebrow}</Eyebrow>
            <h1 style={{ fontSize: "clamp(38px,6vw,68px)", fontWeight: 620, margin: "18px 0 20px" }}>{title}</h1>
            <p style={{ fontSize: "clamp(17px,2vw,20px)", color: "var(--text-dim)", lineHeight: 1.5 }}>{intro}</p>
          </div>
        </Container>
      </section>
      {children}
    </>
  );
}
