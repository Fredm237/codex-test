import type { MetadataRoute } from "next";
import { siteUrl } from "@/lib/site-url";
import { API } from "@/lib/api";

// Revalidé quotidiennement : les rayons apparaissent au rythme du catalogue.
export const revalidate = 86400;

async function categorySlugs(): Promise<string[]> {
  try {
    const res = await fetch(`${API}/api/catalog/categories`, {
      next: { revalidate: 86400 },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) return [];
    return ((await res.json()).items || []).map((c: { slug: string }) => c.slug);
  } catch {
    // Un backend indisponible ne doit pas priver le site de son sitemap.
    return [];
  }
}

const routes = [
  "",
  "/recherche",
  "/catalogue",
  "/marchands",
  "/comment-ca-marche",
  "/cashback",
  "/reconditionne",
  "/codes-promo",
  "/tarifs",
  "/extension",
  "/intelligence",
  "/score",
  "/blog",
  "/blog/cashback-comment-ca-marche",
  "/blog/black-friday-sans-se-faire-avoir",
  "/blog/choisir-ordinateur-portable",
  "/blog/quand-acheter-moins-cher",
  "/blog/quelle-app-cashback-paie-le-plus",
  "/blog/neuf-vs-reconditionne-economie-reelle",
  "/faq",
  "/aide",
  "/a-propos",
  "/partenaires",
  "/presse",
  "/carrieres",
  "/contact",
  "/securite",
  "/transparence",
  "/mentions-legales",
  "/confidentialite",
  "/cookies",
  "/cgu",
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const slugs = await categorySlugs();
  const all = [...routes, ...slugs.map((s) => `/categorie/${s}`)];
  return all.map((path) => ({
    url: siteUrl(path || "/"),
    lastModified: now,
    changeFrequency: path === "" || path === "/blog" ? "daily" : "weekly",
    priority: path === "" ? 1 : 0.7,
  }));
}
