import { site } from "@/lib/site";
import { Newsletter } from "./Forms";

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
              <span className="it">Le Filon</span> — la newsletter.
            </h3>
            <p style={{ color: "var(--ink-2)", fontSize: 14.5, marginTop: 6 }}>
              Chaque semaine : les vraies bonnes affaires, les erreurs d&apos;achat à éviter et les produits qui valent le coup.
              Zéro spam — et le signal du lancement en avant-première.
            </p>
          </div>
          <Newsletter />
        </div>
        <div className="ed-foot">
          <span className="ed-brand" style={{ fontSize: 16 }}>{site.name}</span>
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
          FILON est gratuit. Certains liens sont affiliés — lorsque vous activez une offre via FILON, la plateforme
          partenaire nous reverse une part de sa commission d&apos;apport. Cela n&apos;augmente jamais votre prix. Nous ne
          revendons aucune donnée de navigation.
        </p>
      </div>
    </footer>
  );
}
