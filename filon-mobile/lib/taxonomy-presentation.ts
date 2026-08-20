import type MaterialIcons from "@expo/vector-icons/MaterialIcons";
import type { ComponentProps } from "react";

type IconName = ComponentProps<typeof MaterialIcons>["name"];

const RULES: Array<{ terms: string[]; icon: IconName }> = [
  { terms: ["tech", "informat", "telephon", "gaming"], icon: "memory" },
  { terms: ["maison", "deco", "jardin", "bricol"], icon: "home" },
  { terms: ["mode", "chauss", "bijoux"], icon: "checkroom" },
  { terms: ["beaute", "parfum", "sante"], icon: "spa" },
  { terms: ["sport", "plein air"], icon: "directions-run" },
  { terms: ["auto", "moto"], icon: "directions-car" },
  { terms: ["bebe", "puériculture"], icon: "child-care" },
  { terms: ["animal"], icon: "pets" },
  { terms: ["voyage", "sejour"], icon: "flight" },
];

const FALLBACKS: IconName[] = ["category", "explore", "auto-awesome", "widgets", "hub"];

function normalized(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function stableIndex(value: string) {
  return Array.from(value).reduce((hash, char) => ((hash * 31) + char.charCodeAt(0)) >>> 0, 17) % FALLBACKS.length;
}

export function taxonomyPresentation(name: string) {
  const key = normalized(name);
  const rule = RULES.find(({ terms }) => terms.some((term) => key.includes(term)));
  return { icon: rule?.icon ?? FALLBACKS[stableIndex(key)], variation: stableIndex(key) };
}
