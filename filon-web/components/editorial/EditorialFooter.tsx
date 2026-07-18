import { site } from "@/lib/site";
import { Newsletter } from "./Forms";

const LINKS = [
  { label: "La transformation", href: "/#transform" },
  { label: "La méthode", href: "/#comment" },
  { label: "Transparence", href: "/#transparence" },
  { label: "Installer", href: "/#installer" },
];

export function EditorialFooter() {
  return (
    <footer className="ed-footer">
      <div className="ed-wrap">
        <div className="ed-newsblock">
          <div>
            <h3 style={{ fontFamily: "var(--serif)", fontVariationSettings: '"opsz" 40', fontSize: 24, letterSpacing: "-0.01em" }}>
              Soyez prévenu·e du lancement.
            </h3>
            <p style={{ color: "var(--ink-2)", fontSize: 14.5, marginTop: 6 }}>
              L&apos;extension arrive. Rejoignez la liste — pas de spam, juste le signal du départ.
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
        <p className="ed-disc">
          FILON est gratuit. Certains liens sont affiliés — lorsque vous activez une offre via FILON, la plateforme
          partenaire nous reverse une part de sa commission d&apos;apport. Cela n&apos;augmente jamais votre prix. Nous ne
          revendons aucune donnée de navigation.
        </p>
      </div>
    </footer>
  );
}
