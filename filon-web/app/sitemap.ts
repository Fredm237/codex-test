export const dynamic = "force-static";

import type { MetadataRoute } from "next";
import { site } from "@/lib/site";

const routes = [
  "",
  "/recherche",
  "/comment-ca-marche",
  "/cashback",
  "/reconditionne",
  "/codes-promo",
  "/blog",
  "/a-propos",
  "/contact",
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