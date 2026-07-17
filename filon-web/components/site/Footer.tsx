import { footerNav, site } from "@/lib/site";
import { Container } from "@/components/ui/Container";
import { Logo } from "./Logo";

export function Footer() {
  return (
    <footer style={{ borderTop: "1px solid var(--border)", padding: "60px 0 40px", marginTop: 40 }}>
      <Container>
        <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr 1fr", gap: 32 }} className="filon-footgrid">
          <div>
            <a href="/" style={{ display: "flex", alignItems: "center", gap: 11, fontWeight: 600, fontSize: 19, letterSpacing: "-0.04em" }}>
              <Logo />
              {site.name}
            </a>
            <p style={{ color: "var(--text-dim)", fontSize: 14.5, maxWidth: 280, marginTop: 14 }}>
              {site.tagline} L&apos;assistant qui trouve le meilleur prix réel — cashback, reconditionné et promos réunis.
            </p>
          </div>
          {footerNav.map((col) => (
            <div key={col.title}>
              <h4 style={{ fontSize: 12.5, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-mute)", margin: "0 0 16px", fontWeight: 600 }}>
                {col.title}
              </h4>
              {col.items.map((it) => (
                <a key={it.href} href={it.href} style={{ display: "block", color: "var(--text-dim)", fontSize: 14.5, padding: "5px 0" }}>
                  {it.label}
                </a>
              ))}
            </div>
          ))}
        </div>

        <p style={{ fontSize: 12.5, color: "var(--text-mute)", maxWidth: 760, marginTop: 36, lineHeight: 1.6 }}>
          <b style={{ color: "var(--text-dim)" }}>Transparence :</b> FILON est gratuit. Certains liens sont affiliés — lorsque vous
          activez un cashback ou une offre via FILON, la plateforme partenaire nous reverse une part de sa commission d&apos;apport.
          Cela n&apos;augmente jamais votre prix. Nous ne revendons aucune donnée de navigation.
        </p>
        <div style={{ marginTop: 26, paddingTop: 26, borderTop: "1px solid var(--border)", fontSize: 13, color: "var(--text-mute)" }}>
          © {new Date().getFullYear()} {site.name}. Conçu à {site.city}, pour la francophonie. Tous droits réservés.
        </div>
      </Container>
    </footer>
  );
}
