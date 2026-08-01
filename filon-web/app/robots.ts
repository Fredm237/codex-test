import type { MetadataRoute } from "next";
import { site } from "@/lib/site";
import { countSitemapChunks } from "@/lib/sitemap-products";

// Revalidé quotidiennement, comme les sitemaps produits : le nombre de fichiers
// grandit avec le catalogue et doit rester annoncé correctement.
export const revalidate = 86400;

export default async function robots(): Promise<MetadataRoute.Robots> {
  const chunks = await countSitemapChunks();
  const productSitemaps = Array.from(
    { length: chunks },
    (_, i) => `${site.url}/produits/sitemap/${i}.xml`
  );

  return {
    rules: { userAgent: "*", allow: "/" },
    // Les fiches produit sont trop nombreuses pour un seul fichier : on annonce
    // le sitemap éditorial, puis chaque tranche de produits.
    sitemap: [`${site.url}/sitemap.xml`, ...productSitemaps],
    host: site.url,
  };
}
