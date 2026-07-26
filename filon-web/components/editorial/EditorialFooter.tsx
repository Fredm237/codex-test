import { site } from "@/lib/site";
import { Newsletter } from "./Forms";
import { BrandLogo } from "./Brand";

const LINKS = [
  { label: "Assistant IA", href: "/recherche" },
  { label: "Tarifs", href: "/tarifs" },
  { label: "Extension", href: "/extension" },
  { label: "Intelligence", href: "/intelligence" },
  { label: "La méthode", href: "/comment-ca-marche" },
  { label: "Blog", href: "/blog" },
  { label: "FAQ", href: "/faq" },
  { label: "Aide", href: "/aide" },
  { label: "Partenaires", href: "/partenaires" },
  { label: "Presse", href: "/presse" },
  { label: "Carrières", href: "/carrieres" },
  { label: "À propos", href: "/a-propos" },
  { label: "Contact", href: "/contact" },
];

const LEGAL = [
  { label: "Transparence & affiliation", href: "/transparence" },
  { label: "Mentions légales", href: "/mentions-legales" },
  { label: "Confidentialité", href: "/confidentialite" },
  { label: "Politique cookies", href: "/cookies" },
  { label: "CGU", href: "/cgu" },
  { label: "Sécurité", href: "/securite" },
];

export function EditorialFooter() {
  return (
    <footer className="ed-footer">
      <div className="ed-wrap">
        <div className="ed-newsblock">
          <div>
            <h3 style={{ fontFamily: "var(--serif)", fontVariationSettings: '"opsz" 40', fontSize: 24, letterSpacing: "-0.01em" }}>
              La newsletter <span className="it">Le Filon</span>.
            </h3>
            <p style={{ color: "var(--ink-2)", fontSize: 14.5, marginTop: 6 }}>
              Chaque semaine, les bonnes affaires du moment et les pièges à éviter. Rien de plus. Vous serez aussi prévenu du lancement avant tout le monde.
            </p>
          </div>
          <Newsletter />
        </div>
        <div className="ed-foot">
          <BrandLogo as="span" markSize={26} />
          <div className="ed-foot-links">
            {LINKS.map((l) => (
              <a key={l.href} href={l.href}>{l.label}</a>
            ))}
          </div>
          <span className="cr">© {new Date().getFullYear()} · Conçu à {site.city}</span>
        </div>
        <div className="ed-foot-links" style={{ marginTop: 18 }}>
          {LEGAL.map((l) => (
            <a key={l.href} href={l.href} style={{ fontSize: 12.5, color: "var(--ink-3)" }}>
              {l.label}
            </a>
          ))}
        </div>
        <p className="ed-disc">
          FILON est gratuit et le restera. Aucune publicité, aucune revente de vos données. Vous ne payez jamais.{" "}
          Certains liens sont affiliés&nbsp;: acheter via FILON peut nous rémunérer, sans surcoût pour vous et sans
          jamais fausser un conseil (<a href="/transparence" style={{ color: "inherit", textDecoration: "underline" }}>en savoir plus</a>).
        </p>
      </div>
    </footer>
  );
}
