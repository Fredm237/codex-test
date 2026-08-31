import { site } from "./site";

/** URL publique canonique. Avec `trailingSlash`, chaque chemin HTML autre que
 * la racine porte un slash avant sa query ou son fragment. */
export function siteUrl(path = "/"): string {
  const hashIndex = path.indexOf("#");
  const hash = hashIndex >= 0 ? path.slice(hashIndex) : "";
  const withoutHash = hashIndex >= 0 ? path.slice(0, hashIndex) : path;
  const queryIndex = withoutHash.indexOf("?");
  const query = queryIndex >= 0 ? withoutHash.slice(queryIndex) : "";
  const rawPathname = queryIndex >= 0 ? withoutHash.slice(0, queryIndex) : withoutHash;
  const pathname = `/${rawPathname}`.replace(/\/{2,}/g, "/").replace(/\/+$/, "");
  const canonicalPathname = pathname === "" ? "/" : `${pathname}/`;
  return `${site.url.replace(/\/+$/, "")}${canonicalPathname}${query}${hash}`;
}
