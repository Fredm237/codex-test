import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { buildFilonOfferSearchParams } from "../lib/filon-api";
import {
  FILON_CATEGORY_LABELS,
  FILON_DEPARTMENT_LABELS,
  FILON_SUBCATEGORY_LABELS,
  FILON_TAXONOMY_LABELS,
  localizedTaxonomyLabel,
  localizedTaxonomyOption,
  taxonomySlug,
  type TaxonomyLocale,
} from "../lib/taxonomy-presentation";

const locales = ["fr", "nl", "en"] as const satisfies readonly TaxonomyLocale[];
const mobileRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const source = (path: string) => readFileSync(join(mobileRoot, path), "utf8");
const backendTaxonomy = readFileSync(join(mobileRoot, "..", "filon-backend", "app", "services", "taxonomy.py"), "utf8");

function quotedLabelsBetween(start: string, end: string) {
  const block = backendTaxonomy.slice(backendTaxonomy.indexOf(start), backendTaxonomy.indexOf(end));
  return [...block.matchAll(/^\s*\("([^"]+)"/gmu)].map((match) => match[1]);
}

function categoryLabelsFromBackend() {
  const block = backendTaxonomy.slice(
    backendTaxonomy.indexOf("# Catégories FILON"),
    backendTaxonomy.indexOf("# Nature transactionnelle"),
  );
  return [...block.matchAll(/^[A-Z_]+ = "([^"]+)"$/gmu)].map((match) => match[1]);
}

function expectBackendParity(entries: Record<string, { fr: string }>, canonicalNames: string[]) {
  const expected = [...new Set(canonicalNames)].sort();
  const translated = Object.values(entries).map(({ fr }) => fr).sort();
  expect(translated).toEqual(expected);
  for (const name of expected) {
    const slug = taxonomySlug(name);
    expect(entries[slug]?.fr, `${name} -> ${slug}`).toBe(name);
  }
}

describe("localisation de la taxonomie catalogue", () => {
  it("couvre les 7 départements, 27 catégories et 130 sous-catégories publiés", () => {
    expect(Object.keys(FILON_DEPARTMENT_LABELS)).toHaveLength(7);
    expect(Object.keys(FILON_CATEGORY_LABELS)).toHaveLength(27);
    expect(Object.keys(FILON_SUBCATEGORY_LABELS)).toHaveLength(130);
    expect(Object.keys(FILON_TAXONOMY_LABELS)).toHaveLength(164);
  });

  it("reste en parité exhaustive avec chaque slug canonique du backend", () => {
    expectBackendParity(FILON_DEPARTMENT_LABELS, quotedLabelsBetween("DEPARTMENTS:", "_DEPARTMENT_OF"));
    expectBackendParity(FILON_CATEGORY_LABELS, categoryLabelsFromBackend());
    expectBackendParity(FILON_SUBCATEGORY_LABELS, quotedLabelsBetween("SUBCATEGORIES:", "def classify_subcategory"));
  });

  it.each([
    ["department", FILON_DEPARTMENT_LABELS],
    ["category", FILON_CATEGORY_LABELS],
    ["subcategory", FILON_SUBCATEGORY_LABELS],
  ] as const)("conserve une clé stable et trois libellés pour chaque %s", (_kind, entries) => {
    for (const [slug, labels] of Object.entries(entries)) {
      expect(taxonomySlug(labels.fr), labels.fr).toBe(slug);
      for (const locale of locales) {
        expect(labels[locale].trim(), `${slug}:${locale}`).not.toBe("");
        expect(localizedTaxonomyLabel({ name: labels.fr, slug }, locale)).toBe(labels[locale]);
        // Les sous-catégories actuelles ne publient pas toujours leur slug.
        expect(localizedTaxonomyLabel({ name: labels.fr }, locale)).toBe(labels[locale]);
      }
    }
  });

  it("utilise le slug comme autorité d'affichage et le nom canonique comme valeur de filtre", () => {
    expect(localizedTaxonomyLabel({ name: "Ancien libellé", slug: "mode-femme" }, "nl")).toBe("Damesmode");
    expect(localizedTaxonomyOption({ name: "Mode femme", slug: "mode-femme" }, "en")).toEqual({
      label: "Women's Fashion",
      canonicalName: "Mode femme",
    });
  });

  it("sérialise les noms canoniques de catégorie et sous-catégorie dans la requête", () => {
    const category = localizedTaxonomyOption({ name: "Mode femme", slug: "mode-femme" }, "en");
    const subcategory = localizedTaxonomyOption({ name: "Manteaux & Vestes" }, "nl");
    const params = buildFilonOfferSearchParams({
      category: category.canonicalName,
      subcategory: subcategory.canonicalName,
    });

    expect(category.label).toBe("Women's Fashion");
    expect(subcategory.label).toBe("Jassen & Mantels");
    expect(params.get("category")).toBe("Mode femme");
    expect(params.get("subcategory")).toBe("Manteaux & Vestes");
    expect(params.toString()).not.toContain("Women%27s+Fashion");
    expect(params.toString()).not.toContain("Jassen+%26+Mantels");
  });

  it("laisse une future entrée inconnue lisible au lieu d'inventer une traduction", () => {
    expect(localizedTaxonomyLabel({ name: "Nouvelle catégorie", slug: "nouvelle-categorie" }, "nl")).toBe("Nouvelle catégorie");
  });

  it("localise chaque niveau visible sans traduire les paramètres de requête", () => {
    const home = source("app/(tabs)/catalogue.tsx");
    const department = source("app/catalogue/[department].tsx");
    const category = source("app/catalogue/[department]/[category].tsx");
    const results = source("components/filon/native-catalogue.tsx");

    expect(home).toContain("localizedTaxonomyLabel(item, locale)");
    expect(home).toContain("{departmentName}</Text>");
    expect(department).toContain("localizedTaxonomyLabel(category, locale)");
    expect(category).toContain("localizedTaxonomyLabel(selected, locale)");
    expect(category).toContain("localizedTaxonomyLabel(parent, locale)");
    expect(category).toContain("category={selected?.name}");
    expect(results).toContain("localizedTaxonomyOption(sub, locale)");
    expect(results).toContain("setActiveSubcategory(option.canonicalName)");
    expect(results).toContain("subcategory: activeSubcategory");
  });

  it("nomme les commandes du panneau de filtres pour les lecteurs d'écran", () => {
    const results = source("components/filon/native-catalogue.tsx");
    const search = source("app/catalogue/search.tsx");
    expect(search).toContain("<TextInput autoFocus accessibilityLabel={text.title}");
    expect(results).toContain("accessibilityLabel={text.closeFilters}");
    expect(results).toContain("accessibilityLabel={text.clear}");
    expect(results).toContain("<Switch accessibilityLabel={text.stock}");
    expect(results).toContain("<TextInput accessibilityLabel={label}");
  });
});
