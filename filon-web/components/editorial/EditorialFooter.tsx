import { site } from "@/lib/site";

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
