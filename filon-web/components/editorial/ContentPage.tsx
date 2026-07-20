import type { ReactNode } from "react";
import { JsonLd, breadcrumbSchema } from "@/lib/seo";
import { Reveal } from "./Reveal";

export function ContentHero({
  eyebrow,
  title,
  intro,
  breadcrumb,
}: {
  eyebrow: string;
  title: ReactNode;
  intro: ReactNode;
  breadcrumb: { name: string; path: string }[];
}) {
  return (
    <section className="ed-content-hero">
      <JsonLd data={breadcrumbSchema([{ name: "Accueil", path: "/" }, ...breadcrumb])} />
      <div className="ed-wrap">
        <Reveal>
          <span className="eyebrow">{eyebrow}</span>
          <h1 style={{ marginTop: 18 }}>{title}</h1>
          <p className="intro">{intro}</p>
        </Reveal>
      </div>
    </section>
  );
}

/** Editorial two-column block: a serif heading + prose. */
export function ProseBlock({ heading, children, alt = false }: { heading: ReactNode; children: ReactNode; alt?: boolean }) {
  return (
    <section className={`ed-band ${alt ? "alt" : ""}`}>
      <div className="ed-wrap">
        <div className="ed-mgrid">
          <Reveal>
            <div className="ed-prose">
              <h2>{heading}</h2>
            </div>
          </Reveal>
          <Reveal>
            <div className="ed-prose">{children}</div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

export function InfoGrid({ items }: { items: { n: string; h: string; p: string }[] }) {
  return (
    <div className="ed-infogrid">
      {items.map((it) => (
        <div className="ed-info" key={it.h}>
          <div className="n mono">{it.n}</div>
          <h3>{it.h}</h3>
          <p>{it.p}</p>
        </div>
      ))}
    </div>
  );
}

export function ClosingCta({ title, sub }: { title: ReactNode; sub?: string }) {
  return (
    <section className="ed-closing" id="installer">
      <div className="ed-wrap">
        <Reveal>
          <span className="eyebrow" style={{ display: "block", marginBottom: 26 }}>
            Ne payez plus jamais trop cher
          </span>
          <h2>{title}</h2>
          {sub ? <p style={{ color: "var(--ink-2)", fontSize: 18, margin: "18px auto 0", maxWidth: "42ch" }}>{sub}</p> : null}
          <a className="ed-btn dark" href="/#installer" style={{ marginTop: "clamp(30px,5vw,44px)" }}>
            Ajouter gratuitement
          </a>
        </Reveal>
      </div>
    </section>
  );
}
