import type { MetadataRoute } from "next";
import { site } from "@/lib/site";
import {
  SITEMAP_CHUNK,
  countSitemapChunks,
  fetchSitemapProducts,
} from "@/lib/sitemap-products";

// Sitemaps des fiches produit regroupées, servis en /produits/sitemap/N.xml.
// Revalidés une fois par jour : le catalogue bouge au rythme du cron, pas à
// celui des visites.
export const revalidate = 86400;

export async function generateSitemaps(): Promise<{ id: number }[]> {
  const chunks = await countSitemapChunks();
  return Array.from({ length: chunks }, (_, id) => ({ id }));
}

export default async function sitemap({
  id,
}: {
  id: number;
}): Promise<MetadataRoute.Sitemap> {
  const { items } = await fetchSitemapProducts(id * SITEMAP_CHUNK);
  return items.map((p) => ({
    url: `${site.url}/produits/${p.ean}/`,
    lastModified: p.updated ? new Date(p.updated) : new Date(),
    changeFrequency: "daily",
    // Les fiches regroupées comparent plusieurs marchands : elles portent plus
    // de valeur que les pages éditoriales secondaires, sans égaler l'accueil.
    priority: 0.8,
  }));
}
