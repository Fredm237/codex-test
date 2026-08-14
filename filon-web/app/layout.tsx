import type { Metadata, Viewport } from "next";
import "./globals.css";
import { fraunces, outfit, inter } from "./fonts";
import { buildMetadata, organizationSchema, websiteSchema, JsonLd } from "@/lib/seo";
import { site } from "@/lib/site";

// S’exécute avant l’hydratation : le premier pixel respecte le choix
// enregistré, ou le réglage système si l’utilisateur n’a encore rien choisi.
const themeBootstrap = `(() => {
  try {
    const stored = localStorage.getItem("filon-tone");
    const tone = stored === "light" || stored === "dark"
      ? stored
      : window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
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
  themeColor: "#0e0c0b",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={`${fraunces.variable} ${outfit.variable} ${inter.variable}`} suppressHydrationWarning>
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
