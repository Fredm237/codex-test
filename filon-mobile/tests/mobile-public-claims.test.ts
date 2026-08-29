import { readdirSync, readFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import * as ts from "typescript";
import { describe, expect, it } from "vitest";

const mobileRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const publicRoots = ["app", "components", "lib"] as const;

function collectPublicSurfaces(directory: string): string[] {
  return readdirSync(join(mobileRoot, directory), { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return collectPublicSurfaces(path);
    return /\.(?:ts|tsx)$/u.test(entry.name) ? [path] : [];
  });
}

const surfaces = publicRoots.flatMap(collectPublicSurfaces).sort();
const sources = Object.fromEntries(
  surfaces.map((path) => [path, readFileSync(join(mobileRoot, path), "utf8")]),
);

const technicalLiterals = new Set([
  "catalogue_partner",
  "verified-user",
]);

function normalizedPublicText(value: string) {
  return value.trim().replace(/\s+/gu, " ").toLocaleLowerCase("fr");
}

function publicStringLiterals(source: string): string[] {
  return [...source.matchAll(/(["'`])((?:\\.|(?!\1)[\s\S])*)\1/g)]
    .map((match) => normalizedPublicText(match[2]))
    .filter((literal) => literal.length > 0)
    .filter((literal) => !literal.startsWith("@/") && !literal.startsWith("./") && !literal.startsWith("../"))
    .filter((literal) => !technicalLiterals.has(literal));
}

function parsePublicSource(path: string, source: string) {
  return ts.createSourceFile(
    path,
    source,
    ts.ScriptTarget.Latest,
    true,
    path.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );
}

function rawJsxText(path: string, source: string): string[] {
  const sourceFile = parsePublicSource(path, source);
  const literals: string[] = [];
  const visit = (node: ts.Node) => {
    if (ts.isJsxText(node)) {
      const literal = normalizedPublicText(node.getText(sourceFile));
      if (literal) literals.push(literal);
    }
    ts.forEachChild(node, visit);
  };
  visit(sourceFile);
  return literals;
}

function isInsideCopyDeclaration(node: ts.Node, sourceFile: ts.SourceFile) {
  let current: ts.Node | undefined = node.parent;
  while (current && !ts.isSourceFile(current)) {
    if (ts.isVariableDeclaration(current) && ts.isIdentifier(current.name) && /copy$/iu.test(current.name.text)) return true;
    current = current.parent;
  }
  return false;
}

function isMaterialIconName(node: ts.Node, sourceFile: ts.SourceFile) {
  let current: ts.Node | undefined = node.parent;
  while (current && !ts.isSourceFile(current)) {
    if (ts.isJsxAttribute(current)) {
      const attributeName = current.name.getText(sourceFile);
      const attributes = current.parent;
      const element = attributes.parent;
      const tagName = (ts.isJsxOpeningElement(element) || ts.isJsxSelfClosingElement(element))
        ? element.tagName.getText(sourceFile)
        : "";
      return attributeName === "name" && tagName.endsWith("MaterialIcons");
    }
    current = current.parent;
  }
  return false;
}

function isRequiredTechnicalStandalone(node: ts.Node, sourceFile: ts.SourceFile) {
  if (isMaterialIconName(node, sourceFile)) return true;
  const insideCopy = isInsideCopyDeclaration(node, sourceFile);
  let current: ts.Node | undefined = node.parent;
  while (current && !ts.isSourceFile(current)) {
    if (ts.isLiteralTypeNode(current)) return true;
    if (!insideCopy && ts.isPropertyAssignment(current) && /^(?:status|tone)$/u.test(current.name.getText(sourceFile))) return true;
    if (!insideCopy && ts.isVariableDeclaration(current) && ts.isIdentifier(current.name) && current.name.text === "status") return true;
    if (ts.isBinaryExpression(current) && /\.(?:status|tone)$/u.test(current.left.getText(sourceFile))) return true;
    current = current.parent;
  }
  return false;
}

function standalonePublicLiterals(path: string, source: string): string[] {
  const sourceFile = parsePublicSource(path, source);
  const literals: string[] = [];
  const visit = (node: ts.Node) => {
    if (ts.isJsxText(node)) {
      const literal = normalizedPublicText(node.getText(sourceFile));
      if (literal) literals.push(literal);
    } else if ((ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) && !isRequiredTechnicalStandalone(node, sourceFile)) {
      const literal = normalizedPublicText(node.text);
      if (literal && !technicalLiterals.has(literal)) literals.push(literal);
    }
    ts.forEachChild(node, visit);
  };
  visit(sourceFile);
  return literals;
}

const unsupportedClaims = [
  /\boffres?\s+partenaires?\b/u,
  /\bcatalogue\s+partenaire\b/u,
  /\bmarchands?\s+partenaires?\b/u,
  /\bpartneraanbied/u,
  /\bpartnercatalog/u,
  /\bpartnerhandelaar/u,
  /\bpartner\s+(?:offers?|catalog(?:ue)?|merchants?)\b/u,
  /\b(?:offres?|prix|produits?|lectures?|propositions?)\s+(?:vérifié(?:e|es|s)?|vérifiable(?:s)?)\b/u,
  /\bgeverifieerde?\s+(?:aanbiedingen?|prijzen?|producten?|metingen?|voorstellen?)\b/u,
  /\b(?:verified|verifiable)\s+(?:offers?|prices?|products?|readings?|proposals?|catalog(?:ue)?)\b/u,
  /\b(?:catalogue|données|prix)\s+en\s+direct\b/u,
  /\b(?:live|real-time)\s+(?:catalog(?:ue)?|data|prices?|offers?)\b/u,
  /\blive\s+catalogus\b/u,
  /\b(?:prix réels?|echte prij(?:s|zen)|real prices?)\b/u,
  /\b(?:réellement disponibles?|werkelijk beschikbare?|actually available)\b/u,
];

const unsupportedStandaloneClaims = [
  /^(?:vérifié(?:e|es|s)?|vérifiable|geverifieerd(?:e)?|verified|verifiable|live|en direct)$/u,
];

function unsupportedPublicClaims(path: string, source: string) {
  const violations: string[] = [];
  for (const literal of [...publicStringLiterals(source), ...rawJsxText(path, source)]) {
    for (const claim of unsupportedClaims) {
      if (claim.test(literal)) violations.push(`${claim} in “${literal}”`);
    }
  }
  for (const literal of standalonePublicLiterals(path, source)) {
    for (const claim of unsupportedStandaloneClaims) {
      if (claim.test(literal)) violations.push(`${claim} in “${literal}”`);
    }
  }
  return violations;
}

describe("mobile public claims gate", () => {
  it("discovers every TypeScript public mobile surface", () => {
    expect(surfaces.length).toBeGreaterThanOrEqual(106);
    for (const root of publicRoots) expect(surfaces.some((path) => path.startsWith(`${root}/`))).toBe(true);
    expect(surfaces).toContain("app/product/[id].tsx");
    expect(surfaces).toContain("components/filon/offer-card.tsx");
    expect(surfaces).toContain("lib/filon-api.ts");
    expect(relative(mobileRoot, join(mobileRoot, surfaces[0]))).not.toMatch(/^\.\./u);
  });

  it.each(surfaces)("keeps %s free of unsupported public claims", (path) => {
    expect(unsupportedPublicClaims(path, sources[path]), path).toEqual([]);
  });

  it("scans raw JSX and standalone claims without blocking required technical tokens", () => {
    expect(unsupportedPublicClaims("fixture.tsx", "const Screen = () => <Text>Partner offers</Text>;")).not.toEqual([]);
    expect(unsupportedPublicClaims("fixture.tsx", "const Screen = () => <Text>Verified</Text>;")).not.toEqual([]);
    expect(unsupportedPublicClaims("fixture.tsx", "const copy = { badge: 'Live' };")).not.toEqual([]);
    expect(unsupportedPublicClaims("fixture.tsx", "const Icon = () => <MaterialIcons name=\"verified\" />;")).toEqual([]);
    expect(unsupportedPublicClaims("fixture.ts", "const state = { tone: 'live' as const };")).toEqual([]);
  });

  it("describes catalogue provenance consistently in French, Dutch, and English", () => {
    const product = sources["app/product/[id].tsx"];
    expect(sources["lib/locale.tsx"]).toContain("Données indexées du catalogue");
    expect(sources["lib/locale.tsx"]).toContain("Geïndexeerde catalogusgegevens");
    expect(sources["lib/locale.tsx"]).toContain("Indexed catalogue data");
    expect(sources["app/(tabs)/profile.tsx"]).toContain("Confirmez le prix et les conditions auprès du marchand");
    expect(sources["app/(tabs)/profile.tsx"]).toContain("Bevestig prijs en voorwaarden bij de handelaar");
    expect(sources["app/(tabs)/profile.tsx"]).toContain("Confirm the price and conditions with the merchant");
    expect(product).toContain("Provenance catalogue non confirmée");
    expect(product).toContain("Catalogusherkomst niet bevestigd");
    expect(product).toContain("Catalogue provenance not confirmed");
    expect(product).toContain("{detailedOffer ? text.source : text.sourceUnknown}");
    expect(product).not.toContain("{text.source}</Text></View><Text style={styles.name}>{name}");
  });

  it("keeps the 24-hour drop metric distinct from comparable-history headings", () => {
    const catalogue = sources["app/(tabs)/catalogue.tsx"];
    expect(catalogue).toContain('movements: "Historiques comparables", drops24h: "baisses sur 24 h"');
    expect(catalogue).toContain('movements: "Vergelijkbare historiek", drops24h: "dalingen in 24 uur"');
    expect(catalogue).toContain('movements: "Comparable history", drops24h: "drops in 24h"');
    expect(catalogue).toContain("label: text.drops24h");
    expect(catalogue).not.toContain("label: text.movements }] : [])");
  });

  it("localizes catalogue search, back navigation, and the global category filter", () => {
    const search = sources["app/catalogue/search.tsx"];
    const catalogue = sources["components/filon/native-catalogue.tsx"];
    expect(search).toContain('fr: { title: "Rechercher"');
    expect(search).toContain('nl: { title: "Zoeken"');
    expect(search).toContain('en: { title: "Search"');
    expect(search).toContain("accessibilityLabel={text.title}");
    expect(search).toContain("<Text style={styles.emptyTitle}>{text.emptyTitle}</Text>");
    expect(catalogue).toContain('fr: { back: "Retour", all: "Tout"');
    expect(catalogue).toContain('nl: { back: "Terug", all: "Alles"');
    expect(catalogue).toContain('en: { back: "Back", all: "All"');
    expect(catalogue).toContain("accessibilityLabel={copy[locale].back}");
    expect(catalogue).toContain("label={text.all}");
  });

  it("resolves structured Outfit messages only at the localized UI boundary", () => {
    const studio = sources["app/outfit-studio.tsx"];
    expect(sources["lib/filon-intelligence.ts"]).toContain('{ code: "score.not_measured" }');
    expect(sources["lib/filon-complete.ts"]).toContain('{ code: "complete.insufficient_current_pieces" }');
    expect(sources["lib/filon-outfit-optimize.ts"]).toContain('{ code: "optimization.no_documented_alternative" }');
    expect(sources["lib/filon-outfit-rotation.ts"]).toContain('{ code: "rotation.saved_days_ago", days: daysSinceSaved }');
    expect(sources["lib/recreate-contract.ts"]).toContain('{ code: "recreate.unknown" }');
    expect(studio).toContain("resolveOutfitPublicMessage(displayedRecommendation.reason, locale)");
    expect(studio).toContain("solution.constraints.map((message) => resolveOutfitPublicMessage(message, locale))");
    expect(studio).toContain("resolveOutfitPublicMessage(explanationForConfidence(observation.confidence), locale)");
  });

  it("masks offer prices unless their evidence is current", () => {
    const card = sources["components/filon/offer-card.tsx"];
    const catalogue = sources["components/filon/native-catalogue.tsx"];
    const product = sources["app/product/[id].tsx"];
    const saved = sources["app/(tabs)/saved.tsx"];
    expect(card).toContain("const qualifiedPrice = priceCurrent ? price : priceToCheckLabel;");
    expect(card).not.toContain("`${price} · ${priceToCheckLabel}`");
    expect(catalogue).toContain("const qualifiedPrice = priceCurrent ? price : text.priceUnknown;");
    expect(product).toContain("const displayedPrice = freshObservation && detailedOffer ? formatFilonPrice(detailedOffer.price, locale, detailedOffer.currency) : \"—\";");
    expect(product).not.toContain("const displayedOffer = detailedOffer ?? routedHint;");
    expect(saved).toContain("const linkedPrice = linked && alertIsCurrent ? formatFilonPrice(linked.price, locale, linked.currency) : evidenceCopy.priceUnknown;");
  });

  it("never exposes a routed alert price before or after evidence qualification", () => {
    const alert = sources["app/alert/new.tsx"];
    expect(alert).toContain("const [threshold, setThreshold] = useState(\"\");");
    expect(alert).toContain("setThreshold(verifiedPrice === null ? \"\" : String(verifiedPrice))");
    expect(alert).toContain("verifiedOffer ? formatFilonPrice(verifiedOffer.price, locale, verifiedOffer.currency) : \"—\"");
    expect(alert).toContain("verifiedOffer?.currency ?? \"—\"");
    expect(alert).not.toContain("routedCurrent !== null ? formatFilonPrice");
  });

  it("dates historical amounts and suppresses undated derived amounts", () => {
    const signal = sources["components/filon/observed-price-signal.tsx"];
    const observedPrice = sources["lib/observed-price.ts"];
    const productHistory = sources["app/product/ean/[ean].tsx"];
    const catalogue = sources["app/(tabs)/catalogue.tsx"];
    const studio = sources["app/outfit-studio.tsx"];
    expect(signal).toContain("signal.comparedAt");
    expect(signal).not.toContain("formatFilonPrice(signal.delta");
    expect(observedPrice).toContain("comparedAt: latest.at");
    expect(productHistory).toContain("historyPeriod !== null");
    expect(productHistory).toContain("{historyPeriod}");
    expect(catalogue).toContain("new Date(item.observedAt)");
    expect(catalogue).not.toContain("formatFilonPrice(item.high");
    expect(catalogue).not.toContain("item.dropPercentage.toFixed");
    expect(studio).not.toContain("formatFilonPrice(result.savings");
    expect(studio).not.toContain("formatFilonPrice(result.originalTotal");
    expect(studio).not.toContain("formatFilonPrice(result.optimizedTotal");
  });
});
