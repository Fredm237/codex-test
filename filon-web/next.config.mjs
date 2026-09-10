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
  async rewrites() {
    // Le développement local a besoin du même relais que Vercel. Lors d'un
    // export statique, vercel.json assure le relais car Next n'émet pas de
    // serveur applicatif.
    if (process.env.STATIC_EXPORT === "1") return [];
    return [
      {
        source: "/api/catalog/offers/",
        destination: "https://web-production-c6842.up.railway.app/api/catalog/offers",
      },
    ];
  },
  async headers() {
    return [
      {
        // Le chemin versionné rend chaque frame immuable. Une future séquence
        // prendra un nouveau dossier au lieu d'invalider des centaines d'images.
        source: "/cinematic/filon-scroll-story/desktop-v7-sprites4/:path*",
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
