import type { Metadata, Viewport } from "next";
import "./globals.css";
import { fraunces, outfit, inter } from "./fonts";
import { buildMetadata, organizationSchema, websiteSchema, JsonLd } from "@/lib/seo";
import { site } from "@/lib/site";

// FILON adopte un univers clair chaud par défaut : aucun réglage système ni
// ancien choix sombre ne doit assombrir le premier pixel de l’expérience.
const themeBootstrap = `(() => {
  try {
    const root = document.documentElement;
    root.dataset.tone = "light";
    root.style.colorScheme = "light";
    localStorage.setItem("filon-tone", "light");
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
  themeColor: "#e8e2d7",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={`${fraunces.variable} ${outfit.variable} ${inter.variable}`} suppressHydrationWarning>
      <head>
        <meta name="color-scheme" content="light" />
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
