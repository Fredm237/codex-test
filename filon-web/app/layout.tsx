import type { Metadata, Viewport } from "next";
import "./globals.css";
import { fraunces, outfit, inter } from "./fonts";
import { buildMetadata, organizationSchema, websiteSchema, JsonLd } from "@/lib/seo";
import { site } from "@/lib/site";

// S’exécute avant l’hydratation : le premier pixel respecte le choix
// enregistré. La première visite ouvre FILON en lumière éditoriale ;
// le mode sombre reste un choix explicite, jamais une surprise système.
const themeBootstrap = `(() => {
  try {
    const stored = localStorage.getItem("filon-tone");
    const tone = stored === "light" || stored === "dark"
      ? stored
      : "light";
    const root = document.documentElement;
    root.dataset.tone = tone;
    root.style.colorScheme = tone;
  } catch (_) {}
})();`;

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  ...buildMetadata({}),
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#efe7da",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="fr"
      className={`${fraunces.variable} ${outfit.variable} ${inter.variable}`}
      data-scroll-behavior="smooth"
      data-tone="light"
      suppressHydrationWarning
    >
      <head>
        <meta name="color-scheme" content="dark light" />
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
        <JsonLd data={organizationSchema()} />
        <JsonLd data={websiteSchema()} />
        {site.plausibleDomain ? (
          // Privacy-first, cookieless analytics — no consent banner needed.
          <script defer data-domain={site.plausibleDomain} src="https://plausible.io/js/script.js" />
        ) : null}
      </head>
      <body>{children}</body>
    </html>
  );
}
