import type { Metadata, Viewport } from "next";
import "./globals.css";
import { buildMetadata, organizationSchema, websiteSchema, JsonLd } from "@/lib/seo";
import { site } from "@/lib/site";
import { ThemeScript } from "@/components/site/ThemeScript";
import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { Atmosphere } from "@/components/site/Atmosphere";

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  ...buildMetadata({}),
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#06070c" },
    { media: "(prefers-color-scheme: light)", color: "#fbfcfe" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <head>
        <ThemeScript />
        <JsonLd data={organizationSchema()} />
        <JsonLd data={websiteSchema()} />
      </head>
      <body>
        <Atmosphere />
        <Nav />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
