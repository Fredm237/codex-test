import { formatFilonPrice } from "./filon-api";
import type { FilonProduct } from "./filon-api";

export function buildProductComparisonShareText(product: Pick<FilonProduct, "name" | "ean" | "priceMin" | "currency" | "offersCount" | "merchantsCount">, locale: "fr" | "nl" | "en") {
  const price = formatFilonPrice(product.priceMin, locale, product.currency);
  const lines = {
    fr: [`${product.name}`, `FILON a observé ${product.offersCount} offre${product.offersCount > 1 ? "s" : ""} chez ${product.merchantsCount} marchand${product.merchantsCount > 1 ? "s" : ""} partenaire${product.merchantsCount > 1 ? "s" : ""}.`, `Prix le plus bas observé : ${price}.`, "Prix et disponibilité à confirmer auprès du marchand.", `EAN : ${product.ean}`],
    nl: [`${product.name}`, `FILON observeerde ${product.offersCount} partneraanbieding${product.offersCount > 1 ? "en" : ""} bij ${product.merchantsCount} handelaar${product.merchantsCount > 1 ? "s" : ""}.`, `Laagste waargenomen prijs: ${price}.`, "Prijs en beschikbaarheid bij de handelaar bevestigen.", `EAN: ${product.ean}`],
    en: [`${product.name}`, `FILON observed ${product.offersCount} partner offer${product.offersCount > 1 ? "s" : ""} across ${product.merchantsCount} merchant${product.merchantsCount > 1 ? "s" : ""}.`, `Lowest observed price: ${price}.`, "Confirm price and availability with the merchant.", `EAN: ${product.ean}`],
  }[locale];
  return lines.join("\n");
}
