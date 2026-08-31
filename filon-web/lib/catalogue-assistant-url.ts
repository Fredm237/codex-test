import { href, type CatalogueQuery } from "@/lib/catalogue";

// Une demande conversationnelle (« un casque sous 300 € ») ne doit pas être
// envoyée telle quelle au moteur catalogue. Cette extraction courte préserve
// l'intention sans promettre de compréhension artificielle.
export function catalogueSearchTerm(input: string) {
  const normalized = input
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  const concepts: Array<[RegExp, string]> = [
    [/casque|headphone|koptelefoon|noise.?cancell?/, "casque"],
    [/ecouteur|earbud|oortje/, "ecouteurs"],
    [/smartphone|telephone|telefoon|iphone|android/, "smartphone"],
    [/ordinateur|laptop|portable|pc\b|computer/, "ordinateur"],
    [/montre|watch|horloge/, "montre"],
    [/television|televiseur|tv\b/, "television"],
    [/aspirateur|vacuum|stofzuiger/, "aspirateur"],
    [/sneaker|basket|chaussure|shoe/, "chaussures"],
  ];
  const match = concepts.find(([pattern]) => pattern.test(normalized));
  if (match) return match[1];

  const terms = normalized
    .replace(/\b(?:un|une|des|le|la|les|de|du|pour|avec|sous|moins|budget|euro|euros|eur|a|au|en|the|a|an|and|with|under|voor|met|onder)\b/g, " ")
    .replace(/\b\d+[\d\s,.]*\b/g, " ")
    .split(/[^a-z0-9]+/)
    .filter((term) => term.length > 2)
    .slice(0, 3);
  return terms.join(" ") || input.trim();
}

const ROUTES: ReadonlyArray<[RegExp, Partial<CatalogueQuery>]> = [
  [
    /casque|headphone|koptelefoon|noise.?cancell?/,
    { dept: "high-tech", cat: "tv-son", sub: "Casques audio" },
  ],
  [
    /ecouteur|earbud|oortje/,
    { dept: "high-tech", cat: "telephonie", sub: "Écouteurs" },
  ],
  [
    /smartphone|telephone|telefoon|iphone|android/,
    { dept: "high-tech", cat: "telephonie", sub: "Smartphones" },
  ],
  [
    /ordinateur|laptop|portable|pc\b|computer/,
    { dept: "high-tech", cat: "informatique", sub: "Ordinateurs portables" },
  ],
  [
    /television|televiseur|tv\b/,
    { dept: "high-tech", cat: "tv-son", sub: "Téléviseurs" },
  ],
  [
    /aspirateur|vacuum|stofzuiger/,
    { dept: "maison", cat: "electromenager", sub: "Aspirateurs" },
  ],
  [
    /sneaker|basket|chaussure|shoe/,
    {
      dept: "mode-accessoires",
      cat: "chaussures",
      sub: "Baskets & Sneakers",
    },
  ],
];

/**
 * Produit l'unique URL canonique utilisée par l'Assistant pour revenir au
 * catalogue. Le même constructeur que la navigation catalogue fixe le chemin,
 * l'ordre des paramètres, l'encodage et la suppression des filtres interdits.
 */
export function catalogueAssistantHref(input: string) {
  const normalized = input
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
  const route = ROUTES.find(([pattern]) => pattern.test(normalized))?.[1];
  return href({}, route ?? { q: catalogueSearchTerm(input) });
}
