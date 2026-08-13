/** @type {import('next').NextConfig} */
const nextConfig = {
  // Rendu Next.js natif (SSR/ISR) sur Vercel → pages catalogue/produit
  // rendues côté serveur et indexables par Google. Mettre STATIC_EXPORT=1 pour
  // régénérer un export statique (out/) pour un hébergement sans serveur Node
  // — mais les fiches produit dynamiques ne sont pas incluses dans ce mode.
  output: process.env.STATIC_EXPORT === "1" ? "export" : undefined,
  reactStrictMode: true,
  poweredByHeader: false,
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || undefined,
  async headers() {
    return [
      {
        // Les frames sont versionnées avec le build et ne changent pas entre
        // deux déploiements : le navigateur peut les réutiliser immédiatement.
        source: "/seq/hero/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
