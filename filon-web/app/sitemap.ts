export const dynamic = "force-static";

import type { MetadataRoute } from "next";
import { site } from "@/lib/site";

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

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return routes.map((path) => ({
    url: `${site.url}${path}`,
    lastModified: now,
    changeFrequency: path === "" || path === "/blog" ? "daily" : "weekly",
    priority: path === "" ? 1 : 0.7,
  }));
}