export type FilonOutfitLocale = "fr" | "nl" | "en";
export type OutfitOccasionCode = "wedding" | "work" | "evening";
export type OutfitSeasonCode = "spring" | "summer" | "autumn" | "winter";
export type OutfitStyleCode = "minimal" | "classic" | "bold";

export type OutfitPublicMessage =
  | { code: "piece.role_inferred" }
  | { code: "piece.role_unconfirmed" }
  | { code: "recommendation.no_eligible_offers" }
  | { code: "recommendation.no_comparable_currency" }
  | { code: "recommendation.budget_exceeded" }
  | { code: "recommendation.evidence_expired" }
  | { code: "score.not_measured" }
  | { code: "constraint.catalogue_current_offers" }
  | { code: "constraint.single_currency"; currency: string }
  | { code: "constraint.budget_unspecified" }
  | { code: "constraint.budget_respected"; amount: number; currency: string }
  | { code: "constraint.context_declared"; occasion: OutfitOccasionCode }
  | { code: "constraint.context_unspecified" }
  | { code: "constraint.season_declared"; season: OutfitSeasonCode }
  | { code: "constraint.season_unspecified" }
  | { code: "constraint.owned_piece"; label: string }
  | { code: "strategy.safe" }
  | { code: "strategy.signature" }
  | { code: "strategy.statement" }
  | { code: "complete.insufficient_current_pieces" }
  | { code: "optimization.invalid_snapshot" }
  | { code: "optimization.no_documented_alternative" }
  | { code: "optimization.unavailable" }
  | { code: "optimization.evidence_expired" }
  | { code: "constraint.optimization_current_offers" }
  | { code: "constraint.saved_price_historical" }
  | { code: "constraint.unknown_costs_excluded" }
  | { code: "ledger.intent"; value: string }
  | { code: "ledger.policy.offer_classification" }
  | { code: "ledger.policy.no_commercial_priority" }
  | { code: "rotation.saved_today" }
  | { code: "rotation.saved_days_ago"; days: number }
  | { code: "recreate.certain" }
  | { code: "recreate.probable" }
  | { code: "recreate.unknown" };

export type OutfitPublicMessageCode = OutfitPublicMessage["code"];

const fr = {
  "piece.role_inferred": "Rôle interprété à partir du nom et de la catégorie fournis par le catalogue FILON.",
  "piece.role_unconfirmed": "Offre du catalogue avec stock renseigné ; son rôle dans la tenue reste à confirmer.",
  "recommendation.no_eligible_offers": "Aucune offre du catalogue avec relevé récent, stock disponible et lien sûr ne permet de composer une proposition responsable.",
  "recommendation.no_comparable_currency": "FILON ne dispose pas d’une base et de chaussures actuelles dans une même devise ; aucun total comparable ne peut être présenté.",
  "recommendation.budget_exceeded": "Les pièces disponibles dépassent votre budget total. FILON préfère ne pas présenter une solution qui ne respecte pas votre contrainte.",
  "recommendation.evidence_expired": "Les données de prix ou de stock sont trop anciennes. Relancez la recherche pour obtenir de nouveaux relevés.",
  "score.not_measured": "Non mesuré : FILON ne publie aucun score de style ou de confiance tant qu’une méthode calibrée et validée n’est pas disponible.",
  "constraint.catalogue_current_offers": "Offres du catalogue avec relevé récent, stock disponible et lien sûr uniquement",
  "constraint.single_currency": "Composition mono-devise : {currency}",
  "constraint.budget_unspecified": "Budget non précisé",
  "constraint.budget_respected": "Budget respecté : {amount}",
  "constraint.context_declared": "Contexte déclaré : {occasion}",
  "constraint.context_unspecified": "Contexte à préciser",
  "constraint.season_declared": "Saison déclarée : {season}",
  "constraint.season_unspecified": "Saison à préciser",
  "constraint.owned_piece": "Pièce possédée déclarée par l’utilisateur : {label}",
  "strategy.safe": "La solution la plus directe autour de votre pièce.",
  "strategy.signature": "Une alternative construite avec une autre pièce du même rôle, lorsque le catalogue le permet.",
  "strategy.statement": "Une troisième variation réservée à une direction audacieuse déclarée ; son caractère reste limité aux signaux du catalogue.",
  "complete.insufficient_current_pieces": "FILON ne trouve pas suffisamment de pièces actuelles dans une même devise pour compléter votre pièce tout en respectant les contraintes déclarées.",
  "optimization.invalid_snapshot": "La tenue sauvegardée ne possède pas un instantané local cohérent et mono-devise ; aucune économie comparable ne peut être calculée.",
  "optimization.no_documented_alternative": "Aucune offre du catalogue avec relevé récent ne permet de proposer une alternative documentée pour cette tenue sauvegardée.",
  "optimization.unavailable": "Aucune amélioration documentée n’est disponible pour cette tenue.",
  "optimization.evidence_expired": "Les relevés des alternatives sont trop anciens. Relancez l’optimisation pour obtenir de nouvelles données.",
  "constraint.optimization_current_offers": "Comparaison mono-devise avec des offres du catalogue à relevé récent, stock disponible et lien sûr uniquement",
  "constraint.saved_price_historical": "Le prix sauvegardé reste un instantané historique et n’est pas réaffiché comme prix courant",
  "constraint.unknown_costs_excluded": "Aucune livraison, promotion ou cashback n’est déduit lorsqu’il est inconnu",
  "ledger.intent": "Intention : {value}",
  "ledger.policy.offer_classification": "Chaque offre est classée une seule fois selon la sécurité du lien, la preuve actuelle de prix et de stock, puis la compatibilité de devise avec le budget déclaré.",
  "ledger.policy.no_commercial_priority": "Les décisions n’utilisent ni commission, ni priorité commerciale, ni prix inventé.",
  "rotation.saved_today": "Sauvegardée aujourd’hui : à garder en repère.",
  "rotation.saved_days_ago": "Sauvegardée il y a {days} {day} : à reconsidérer pour une prochaine occasion.",
  "recreate.certain": "Élément clairement observable sur l’inspiration fournie.",
  "recreate.probable": "Interprétation visuelle plausible ; à confirmer dans une pièce réelle.",
  "recreate.unknown": "Élément insuffisamment visible ou ambigu ; FILON ne l’utilise pas comme contrainte forte.",
} satisfies Record<OutfitPublicMessageCode, string>;

const nl = {
  "piece.role_inferred": "Rol geïnterpreteerd op basis van de naam en categorie uit de FILON-catalogus.",
  "piece.role_unconfirmed": "Catalogusaanbieding met vermelde voorraad; de rol ervan in de outfit moet nog worden bevestigd.",
  "recommendation.no_eligible_offers": "Geen catalogusaanbieding met een recente meting, beschikbare voorraad en een veilige link maakt een verantwoord voorstel mogelijk.",
  "recommendation.no_comparable_currency": "FILON beschikt niet over een basisitem en schoenen in dezelfde valuta met actuele gegevens; er kan geen vergelijkbaar totaal worden getoond.",
  "recommendation.budget_exceeded": "De beschikbare items overschrijden uw totale budget. FILON toont liever geen oplossing die uw beperking niet respecteert.",
  "recommendation.evidence_expired": "De prijs- of voorraadgegevens zijn te oud. Zoek opnieuw om nieuwe metingen op te halen.",
  "score.not_measured": "Niet gemeten: FILON publiceert geen stijl- of vertrouwensscore zolang er geen gekalibreerde en gevalideerde methode beschikbaar is.",
  "constraint.catalogue_current_offers": "Alleen catalogusaanbiedingen met een recente meting, beschikbare voorraad en een veilige link",
  "constraint.single_currency": "Samenstelling in één valuta: {currency}",
  "constraint.budget_unspecified": "Budget niet opgegeven",
  "constraint.budget_respected": "Budget gerespecteerd: {amount}",
  "constraint.context_declared": "Opgegeven context: {occasion}",
  "constraint.context_unspecified": "Context nog op te geven",
  "constraint.season_declared": "Opgegeven seizoen: {season}",
  "constraint.season_unspecified": "Seizoen nog op te geven",
  "constraint.owned_piece": "Door de gebruiker opgegeven eigen item: {label}",
  "strategy.safe": "De meest directe oplossing rond uw item.",
  "strategy.signature": "Een alternatief met een ander item in dezelfde rol, wanneer de catalogus dit toelaat.",
  "strategy.statement": "Een derde variant voor een uitgesproken opgegeven richting; het karakter ervan blijft beperkt tot signalen uit de catalogus.",
  "complete.insufficient_current_pieces": "FILON vindt onvoldoende items met actuele gegevens in dezelfde valuta om uw item aan te vullen binnen de opgegeven beperkingen.",
  "optimization.invalid_snapshot": "De bewaarde outfit heeft geen consistente lokale momentopname in één valuta; er kan geen vergelijkbare besparing worden berekend.",
  "optimization.no_documented_alternative": "Geen catalogusaanbieding met een recente meting biedt een gedocumenteerd alternatief voor deze bewaarde outfit.",
  "optimization.unavailable": "Voor deze outfit is geen gedocumenteerde verbetering beschikbaar.",
  "optimization.evidence_expired": "De metingen van de alternatieven zijn te oud. Optimaliseer opnieuw om nieuwe gegevens op te halen.",
  "constraint.optimization_current_offers": "Vergelijking in één valuta, uitsluitend met catalogusaanbiedingen met een recente meting, beschikbare voorraad en een veilige link",
  "constraint.saved_price_historical": "De bewaarde prijs blijft een historische momentopname en wordt niet als huidige prijs weergegeven",
  "constraint.unknown_costs_excluded": "Levering, promoties of cashback worden niet afgetrokken wanneer ze onbekend zijn",
  "ledger.intent": "Intentie: {value}",
  "ledger.policy.offer_classification": "Elke aanbieding wordt één keer ingedeeld op basis van linkveiligheid, actuele prijs- en voorraadgegevens en vervolgens de verenigbaarheid van de valuta met het opgegeven budget.",
  "ledger.policy.no_commercial_priority": "Beslissingen gebruiken geen commissie, commerciële prioriteit of verzonnen prijs.",
  "rotation.saved_today": "Vandaag bewaard: behouden als referentie.",
  "rotation.saved_days_ago": "{days} {day} geleden bewaard: opnieuw overwegen voor een volgende gelegenheid.",
  "recreate.certain": "Element duidelijk zichtbaar in de aangeleverde inspiratie.",
  "recreate.probable": "Aannemelijke visuele interpretatie; te bevestigen met een echt item.",
  "recreate.unknown": "Element onvoldoende zichtbaar of dubbelzinnig; FILON gebruikt het niet als sterke beperking.",
} satisfies Record<OutfitPublicMessageCode, string>;

const en = {
  "piece.role_inferred": "Role inferred from the name and category provided by the FILON catalogue.",
  "piece.role_unconfirmed": "Catalogue offer with stated stock; its role in the outfit remains to be confirmed.",
  "recommendation.no_eligible_offers": "No catalogue offer with a recent reading, available stock and a safe link supports a responsible proposal.",
  "recommendation.no_comparable_currency": "FILON does not have a base piece and footwear with current data in the same currency, so no comparable total can be shown.",
  "recommendation.budget_exceeded": "The available pieces exceed your total budget. FILON will not show a solution that does not respect your constraint.",
  "recommendation.evidence_expired": "The price or stock data is too old. Search again to retrieve new readings.",
  "score.not_measured": "Not measured: FILON does not publish a style or confidence score until a calibrated and validated method is available.",
  "constraint.catalogue_current_offers": "Catalogue offers with a recent reading, available stock and a safe link only",
  "constraint.single_currency": "Single-currency composition: {currency}",
  "constraint.budget_unspecified": "Budget not specified",
  "constraint.budget_respected": "Budget respected: {amount}",
  "constraint.context_declared": "Declared context: {occasion}",
  "constraint.context_unspecified": "Context to be specified",
  "constraint.season_declared": "Declared season: {season}",
  "constraint.season_unspecified": "Season to be specified",
  "constraint.owned_piece": "User-declared owned piece: {label}",
  "strategy.safe": "The most direct solution around your piece.",
  "strategy.signature": "An alternative built with another piece in the same role, when the catalogue allows it.",
  "strategy.statement": "A third variation reserved for a declared bold direction; its character remains limited to catalogue signals.",
  "complete.insufficient_current_pieces": "FILON cannot find enough pieces with current data in the same currency to complete your piece while respecting the declared constraints.",
  "optimization.invalid_snapshot": "The saved outfit does not have a consistent local single-currency snapshot, so no comparable saving can be calculated.",
  "optimization.no_documented_alternative": "No catalogue offer with a recent reading provides a documented alternative for this saved outfit.",
  "optimization.unavailable": "No documented improvement is available for this outfit.",
  "optimization.evidence_expired": "The alternative readings are too old. Optimise again to retrieve new data.",
  "constraint.optimization_current_offers": "Single-currency comparison using only catalogue offers with a recent reading, available stock and a safe link",
  "constraint.saved_price_historical": "The saved price remains a historical snapshot and is not displayed as a current price",
  "constraint.unknown_costs_excluded": "Delivery, promotions and cashback are not deducted when they are unknown",
  "ledger.intent": "Intent: {value}",
  "ledger.policy.offer_classification": "Each offer is classified once by link safety, current price and stock evidence, then currency compatibility with the declared budget.",
  "ledger.policy.no_commercial_priority": "Decisions use no commission, commercial priority or invented price.",
  "rotation.saved_today": "Saved today: keep as a reference.",
  "rotation.saved_days_ago": "Saved {days} {day} ago: consider again for a future occasion.",
  "recreate.certain": "Element clearly observable in the provided inspiration.",
  "recreate.probable": "Plausible visual interpretation; confirm it with a real piece.",
  "recreate.unknown": "Element insufficiently visible or ambiguous; FILON does not use it as a strong constraint.",
} satisfies Record<OutfitPublicMessageCode, string>;

export const OUTFIT_PUBLIC_MESSAGE_TEMPLATES = { fr, nl, en } satisfies Record<FilonOutfitLocale, Record<OutfitPublicMessageCode, string>>;
export const OUTFIT_PUBLIC_MESSAGE_CODES = Object.keys(fr) as OutfitPublicMessageCode[];

const localeTags: Record<FilonOutfitLocale, string> = { fr: "fr-BE", nl: "nl-BE", en: "en-BE" };
const dayLabels: Record<FilonOutfitLocale, { one: string; other: string }> = {
  fr: { one: "jour", other: "jours" },
  nl: { one: "dag", other: "dagen" },
  en: { one: "day", other: "days" },
};
const occasionLabels: Record<FilonOutfitLocale, Record<OutfitOccasionCode, string>> = {
  fr: { wedding: "Mariage", work: "Travail", evening: "Soirée" },
  nl: { wedding: "Huwelijk", work: "Werk", evening: "Avond" },
  en: { wedding: "Wedding", work: "Work", evening: "Evening" },
};
const seasonLabels: Record<FilonOutfitLocale, Record<OutfitSeasonCode, string>> = {
  fr: { spring: "Printemps", summer: "Été", autumn: "Automne", winter: "Hiver" },
  nl: { spring: "Lente", summer: "Zomer", autumn: "Herfst", winter: "Winter" },
  en: { spring: "Spring", summer: "Summer", autumn: "Autumn", winter: "Winter" },
};

export function localizeOutfitOccasion(occasion: OutfitOccasionCode, locale: FilonOutfitLocale) {
  return occasionLabels[locale][occasion];
}

export function localizeOutfitSeason(season: OutfitSeasonCode, locale: FilonOutfitLocale) {
  return seasonLabels[locale][season];
}

function formatAmount(amount: number, currency: string, locale: FilonOutfitLocale) {
  try {
    return new Intl.NumberFormat(localeTags[locale], { style: "currency", currency }).format(amount);
  } catch {
    return `${new Intl.NumberFormat(localeTags[locale], { maximumFractionDigits: 2 }).format(amount)} ${currency}`;
  }
}

/** Résout uniquement à la frontière UI : les bibliothèques métier conservent des messages structurés et indépendants de la langue. */
export function resolveOutfitPublicMessage(message: OutfitPublicMessage, locale: FilonOutfitLocale) {
  const template = OUTFIT_PUBLIC_MESSAGE_TEMPLATES[locale][message.code];
  const params = message as unknown as Record<string, string | number>;
  return template.replace(/\{([a-z]+)\}/gi, (_, key: string) => {
    if (key === "amount" && "amount" in message && "currency" in message) return formatAmount(message.amount, message.currency, locale);
    if (key === "days" && "days" in message) return new Intl.NumberFormat(localeTags[locale]).format(message.days);
    if (key === "day" && "days" in message) return dayLabels[locale][message.days === 1 ? "one" : "other"];
    if (key === "occasion" && message.code === "constraint.context_declared") return localizeOutfitOccasion(message.occasion, locale);
    if (key === "season" && message.code === "constraint.season_declared") return localizeOutfitSeason(message.season, locale);
    const value = params[key];
    return value === undefined ? `{${key}}` : String(value);
  });
}
