import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, AppState, FlatList, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { TactileButton } from "@/components/filon/filon-ui";
import { ScreenContainer } from "@/components/screen-container";
import { useColors } from "@/hooks/use-colors";
import { readFashionPreferences, resetFashionPreferences, saveFashionPreferences, type FashionPreferences } from "@/lib/fashion-preferences";
import { buildOutfitRecommendation, getOutfitSolutionEvidenceExpiry, isOutfitSolutionCurrent, isOutfitStudioEnabled, type OutfitPiece, type OutfitRecommendation, type OutfitSolution } from "@/lib/filon-intelligence";
import { buildCompleteRecommendation, filterCurrentOutfitStrategies, type CompleteRecommendation, type OutfitStrategyId, type OwnedPiece } from "@/lib/filon-complete";
import { formatFilonPrice, searchFilonOffers } from "@/lib/filon-api";
import { useLocale } from "@/lib/locale";
import { buildOutfitFeedbackKey, readOutfitFeedback, saveOutfitFeedback, type OutfitFeedbackValue } from "@/lib/outfit-feedback";
import { appendStyleSignal, getDiscoverDirections, readStyleSignals, resolveStyleDna, type DiscoverDirection, type StyleDirectionId, type StyleDna } from "@/lib/style-dna";
import { explanationForConfidence, isRecreateAnalysisForLocale, type RecreateAnalysis, type RecreateObservation } from "@/lib/recreate-contract";
import { trpc } from "@/lib/trpc";
import { readWardrobe, removeWardrobeItem, saveWardrobeItem, type WardrobeItem } from "@/lib/filon-wardrobe";
import { makeSavedOutfit, readSavedOutfits, removeSavedOutfit, saveOutfit, type SavedOutfit } from "@/lib/filon-outfit-journal";
import { buildDecisionLedger } from "@/lib/filon-decision-ledger";
import { localizedDiscoverCapsuleQuery, selectDiscoverCapsules, type DiscoverCapsule } from "@/lib/filon-discover-capsules";
import { calculateBudget } from "@/lib/filon-budget";
import { readPlannedOccasions, removePlannedOccasion, savePlannedOccasion, updatePlannedOccasionReminder, type PlannedOccasion } from "@/lib/filon-occasion-planner";
import { compareOutfitStrategies } from "@/lib/filon-strategy-comparison";
import { buildOutfitRotation, type OutfitRotationSuggestion } from "@/lib/filon-outfit-rotation";
import { cancelLocalOccasionReminder, scheduleLocalOccasionReminder } from "@/lib/filon-reminder-scheduler";
import { getOutfitOptimizationEvidenceExpiry, isOutfitOptimizationCurrent, optimizeSavedOutfit, type OutfitOptimization } from "@/lib/filon-outfit-optimize";
import { resolveOutfitPublicMessage, type OutfitPublicMessage } from "@/lib/filon-outfit-i18n";
import { saveFashionCorrection } from "@/lib/filon-fashion-corrections";
import type { FashionErrorCode } from "@/lib/filon-fashion-quality";

const copy = {
  fr: { back: "Retour", lookbook: "Lookbook", preview: "APERÇU", eyebrow: "FILON Intelligence · Fashion Expert", title: "Décrivez la tenue qui vous ferait dire : c’est exactement ça.", placeholder: "Ex. un mariage civil, élégant mais simple", occasion: "Occasion", season: "Saison", budget: "Budget total", style: "Votre direction", create: "Créer une solution", loading: "FILON analyse les offres indexées du catalogue…", noResult: "Décrivez une intention, puis FILON cherchera dans le catalogue et s’abstiendra sans données suffisantes.", reset: "Réinitialiser", minimal: "Minimal", classic: "Classique", bold: "Audacieux", wedding: "Mariage", work: "Travail", evening: "Soirée", spring: "Printemps", summer: "Été", autumn: "Automne", winter: "Hiver", solution: "Proposition du catalogue", total: "Total des pièces", styleScore: "Cohérence", confidence: "Confiance", notMeasured: "Non mesuré", verified: "disponible", piece: "Voir l’offre", unavailable: "Outfit Studio est désactivé dans cette version de FILON.", error: "Le catalogue est momentanément indisponible. Aucune recommandation n’a été fabriquée.", constraints: "Contraintes appliquées", why: "Pourquoi cette pièce ?", abstain: "FILON s’abstient", scoreNote: "Statut des mesures", critique: "Relecture FILON", relations: "Relations analysées", coherent: "Les contraintes disponibles sont cohérentes avec cette proposition.", feedback: "Cette proposition vous aide ?", helpful: "Oui, utile", review: "À revoir", thanks: "Votre retour est enregistré localement pour affiner vos prochains briefs.", finding: { MISSING_STRUCTURE: "Une pièce de structure renforcerait cette occasion.", MISSING_ACCESSORY: "Un accessoire pourrait compléter l’ensemble.", CONTEXT_UNSPECIFIED: "Précisez l’occasion pour calibrer davantage la proposition.", SEASON_UNSPECIFIED: "Précisez la saison pour mieux adapter les pièces.", LOW_RELATION_COVERAGE: "Les relations entre pièces restent partielles." }, role: { base: "Base", structure: "Structure", footwear: "Chaussures", accessory: "Accessoire" } },
  nl: { back: "Terug", lookbook: "Lookbook", preview: "VOORBEELD", eyebrow: "FILON Intelligence · Fashion Expert", title: "Beschrijf de outfit die precies goed voelt.", placeholder: "Bijv. een eenvoudige, elegante burgerlijke bruiloft", occasion: "Gelegenheid", season: "Seizoen", budget: "Totaalbudget", style: "Jouw richting", create: "Een oplossing maken", loading: "FILON analyseert de geïndexeerde catalogusaanbiedingen…", noResult: "Beschrijf een intentie. FILON zoekt daarna in de catalogus en onthoudt zich bij onvoldoende gegevens.", reset: "Reset", minimal: "Minimal", classic: "Klassiek", bold: "Gedurfd", wedding: "Huwelijk", work: "Werk", evening: "Avond", spring: "Lente", summer: "Zomer", autumn: "Herfst", winter: "Winter", solution: "Voorstel uit de catalogus", total: "Totaal van items", styleScore: "Samenhang", confidence: "Vertrouwen", notMeasured: "Niet gemeten", verified: "beschikbaar", piece: "Bekijk aanbieding", unavailable: "Outfit Studio is uitgeschakeld in deze FILON-versie.", error: "De catalogus is tijdelijk niet beschikbaar. Er is geen aanbeveling gemaakt.", constraints: "Toegepaste beperkingen", why: "Waarom dit item?", abstain: "FILON onthoudt zich", scoreNote: "Meetstatus", critique: "FILON-controle", relations: "Geanalyseerde relaties", coherent: "De beschikbare beperkingen zijn in overeenstemming met dit voorstel.", feedback: "Helpt dit voorstel u?", helpful: "Ja, nuttig", review: "Herzien", thanks: "Uw feedback wordt lokaal opgeslagen om volgende briefs te verfijnen.", finding: { MISSING_STRUCTURE: "Een structurerend item zou bij deze gelegenheid passen.", MISSING_ACCESSORY: "Een accessoire kan de look aanvullen.", CONTEXT_UNSPECIFIED: "Geef de gelegenheid op voor een betere afstemming.", SEASON_UNSPECIFIED: "Geef het seizoen op om items beter aan te passen.", LOW_RELATION_COVERAGE: "De relaties tussen items blijven gedeeltelijk." }, role: { base: "Basis", structure: "Structuur", footwear: "Schoenen", accessory: "Accessoire" } },
  en: { back: "Back", lookbook: "Lookbook", preview: "PREVIEW", eyebrow: "FILON Intelligence · Fashion Expert", title: "Describe the outfit that would feel exactly right.", placeholder: "E.g. elegant but simple civil wedding", occasion: "Occasion", season: "Season", budget: "Total budget", style: "Your direction", create: "Create a solution", loading: "FILON is analysing indexed catalogue offers…", noResult: "Describe an intent and FILON will search the catalogue, abstaining when data is insufficient.", reset: "Reset", minimal: "Minimal", classic: "Classic", bold: "Bold", wedding: "Wedding", work: "Work", evening: "Evening", spring: "Spring", summer: "Summer", autumn: "Autumn", winter: "Winter", solution: "Catalogue proposal", total: "Pieces total", styleScore: "Coherence", confidence: "Confidence", notMeasured: "Not measured", verified: "available", piece: "View offer", unavailable: "Outfit Studio is disabled in this FILON version.", error: "The catalogue is temporarily unavailable. No recommendation was fabricated.", constraints: "Applied constraints", why: "Why this piece?", abstain: "FILON abstains", scoreNote: "Measurement status", critique: "FILON review", relations: "Analysed relations", coherent: "The available constraints are consistent with this proposal.", feedback: "Does this proposal help?", helpful: "Yes, useful", review: "Needs review", thanks: "Your feedback is stored locally to refine your next briefs.", finding: { MISSING_STRUCTURE: "A structured layer would reinforce this occasion.", MISSING_ACCESSORY: "An accessory could complete the set.", CONTEXT_UNSPECIFIED: "Specify the occasion to calibrate the proposal further.", SEASON_UNSPECIFIED: "Specify the season to adapt the pieces better.", LOW_RELATION_COVERAGE: "The relations between pieces remain partial." }, role: { base: "Base", structure: "Structure", footwear: "Footwear", accessory: "Accessory" } },
};

const outfitStudioName = { fr: "Outfit Studio", nl: "Outfit Studio", en: "Outfit Studio" };

const completeCopy = {
  fr: { createMode: "Créer", completeMode: "Compléter", owned: "Votre pièce", ownedPlaceholder: "Ex. mon blazer bleu marine", ownedRole: "Type de pièce", base: "Haut / bas", structure: "Veste", footwear: "Chaussures", accessory: "Accessoire", complete: "Compléter ma tenue", safe: "Safe", signature: "Signature", statement: "Statement", ownedNotice: "Pièce possédée déclarée par vous. Elle n’est pas une offre FILON.", strategy: "Stratégie", abstain: "FILON ne peut pas compléter cette pièce", solution: "Tenue autour de votre pièce" },
  nl: { createMode: "Maken", completeMode: "Aanvullen", owned: "Jouw item", ownedPlaceholder: "Bijv. mijn marineblauwe blazer", ownedRole: "Type item", base: "Boven / onder", structure: "Jasje", footwear: "Schoenen", accessory: "Accessoire", complete: "Mijn outfit aanvullen", safe: "Safe", signature: "Signature", statement: "Statement", ownedNotice: "Dit is jouw verklaarde item, geen FILON-aanbieding.", strategy: "Strategie", abstain: "FILON kan dit item niet aanvullen", solution: "Outfit rond jouw item" },
  en: { createMode: "Create", completeMode: "Complete", owned: "Your piece", ownedPlaceholder: "E.g. my navy blazer", ownedRole: "Piece type", base: "Top / bottom", structure: "Jacket", footwear: "Footwear", accessory: "Accessory", complete: "Complete my outfit", safe: "Safe", signature: "Signature", statement: "Statement", ownedNotice: "This is your declared piece, not a FILON offer.", strategy: "Strategy", abstain: "FILON cannot complete this piece", solution: "Outfit around your piece" },
};

const dnaCopy = {
  fr: { title: "Style DNA", unknown: "En apprentissage conscient", declared: "Préférence déclarée", repeated: "Signaux répétés", signal: "signal", signals: "signaux", explore: "Discover", apply: "Utiliser", minimal: "Minimal", classic: "Classique", bold: "Audacieux", minimalDescription: "Des lignes nettes, peu de bruit visuel et des pièces polyvalentes.", classicDescription: "Des repères intemporels, structurés et faciles à réemployer.", boldDescription: "Un accent plus assumé, sans dégrader la cohérence de la tenue." },
  nl: { title: "Style DNA", unknown: "Bewust in opbouw", declared: "Verklaarde voorkeur", repeated: "Herhaalde signalen", signal: "signaal", signals: "signalen", explore: "Discover", apply: "Gebruiken", minimal: "Minimal", classic: "Klassiek", bold: "Gedurfd", minimalDescription: "Heldere lijnen, weinig visuele ruis en veelzijdige items.", classicDescription: "Tijdloze, gestructureerde houvast die gemakkelijk te hergebruiken is.", boldDescription: "Een meer uitgesproken accent zonder de samenhang te verliezen." },
  en: { title: "Style DNA", unknown: "Learning consciously", declared: "Declared preference", repeated: "Repeated signals", signal: "signal", signals: "signals", explore: "Discover", apply: "Use", minimal: "Minimal", classic: "Classic", bold: "Bold", minimalDescription: "Clean lines, low visual noise and versatile pieces.", classicDescription: "Timeless, structured anchors that are easy to reuse.", boldDescription: "A more expressive accent without compromising outfit coherence." },
};

const recreateCopy = {
  fr: { mode: "Recreate", title: "Décrivez une image avec précision, sans inventer le reste.", url: "URL d’une image publique HTTPS", placeholder: "https://…/inspiration.jpg", choose: "Choisir une image", localImage: "Image locale sélectionnée", privacy: "L’image choisie est compressée et envoyée uniquement à l’analyse Recreate demandée ; elle n’est pas ajoutée au catalogue.", analyze: "Analyser l’inspiration", analyzing: "FILON lit les signaux visuels…", results: "Lecture de l’inspiration", silhouette: "Silhouette", palette: "Palette", visiblePiece: "Pièce visible", limits: "Limites de l’analyse", certain: "Certain", probable: "Probable", unknown: "Inconnu", search: "Rechercher ces pièces", error: "FILON ne peut pas analyser cette inspiration pour le moment.", guidance: "Seuls les éléments visuellement observables sont utilisés. Marques, prix et disponibilité ne sont jamais déduits d’une image." },
  nl: { mode: "Recreate", title: "Lees een beeld nauwkeurig, zonder de rest te verzinnen.", url: "HTTPS-URL van een openbare afbeelding", placeholder: "https://…/inspiration.jpg", choose: "Afbeelding kiezen", localImage: "Lokale afbeelding geselecteerd", privacy: "De gekozen afbeelding wordt gecomprimeerd en alleen naar de gevraagde Recreate-analyse gestuurd; ze wordt niet aan de catalogus toegevoegd.", analyze: "Inspiratie analyseren", analyzing: "FILON leest visuele signalen…", results: "Lezing van de inspiratie", silhouette: "Silhouet", palette: "Palet", visiblePiece: "Zichtbaar item", limits: "Analysebeperkingen", certain: "Zeker", probable: "Waarschijnlijk", unknown: "Onbekend", search: "Zoek deze items", error: "FILON kan deze inspiratie nu niet analyseren.", guidance: "Alleen visueel waarneembare elementen worden gebruikt. Merken, prijzen en beschikbaarheid worden nooit uit een afbeelding afgeleid." },
  en: { mode: "Recreate", title: "Read an image precisely, without inventing the rest.", url: "Public HTTPS image URL", placeholder: "https://…/inspiration.jpg", choose: "Choose an image", localImage: "Local image selected", privacy: "The selected image is compressed and sent only to the requested Recreate analysis; it is not added to the catalogue.", analyze: "Analyse inspiration", analyzing: "FILON is reading visual signals…", results: "Inspiration reading", silhouette: "Silhouette", palette: "Palette", visiblePiece: "Visible piece", limits: "Analysis limits", certain: "Certain", probable: "Probable", unknown: "Unknown", search: "Search these pieces", error: "FILON cannot analyse this inspiration right now.", guidance: "Only visually observable elements are used. Brands, prices and availability are never inferred from an image." },
};

const wardrobeCopy = {
  fr: { title: "Mon dressing", save: "Ajouter au dressing", empty: "Enregistrez vos pièces pour les réutiliser dans Complete.", use: "Utiliser", remove: "Retirer" },
  nl: { title: "Mijn garderobe", save: "Aan garderobe toevoegen", empty: "Bewaar uw items om ze later in Complete te gebruiken.", use: "Gebruiken", remove: "Verwijderen" },
  en: { title: "My wardrobe", save: "Add to wardrobe", empty: "Save your pieces to reuse them in Complete.", use: "Use", remove: "Remove" },
};

const journalCopy = {
  fr: { title: "Journal de tenues", save: "Sauvegarder cette tenue", saved: "Tenue sauvegardée", empty: "Vos propositions sauvegardées apparaîtront ici.", remove: "Retirer", plan: "Planifier", create: "Créée", complete: "Complétée", piece: "pièce", pieces: "pièces", notMeasured: "Confiance non mesurée" },
  nl: { title: "Outfitdagboek", save: "Deze outfit bewaren", saved: "Outfit bewaard", empty: "Uw bewaarde voorstellen verschijnen hier.", remove: "Verwijderen", plan: "Plannen", create: "Gemaakt", complete: "Aangevuld", piece: "item", pieces: "items", notMeasured: "Vertrouwen niet gemeten" },
  en: { title: "Outfit journal", save: "Save this outfit", saved: "Outfit saved", empty: "Your saved proposals will appear here.", remove: "Remove", plan: "Plan", create: "Created", complete: "Completed", piece: "piece", pieces: "pieces", notMeasured: "Confidence not measured" },
};

const ledgerCopy = {
  fr: { title: "Registre de décision", reviewed: "offres examinées", eligible: "éligibles", nonEligible: "autres non éligibles", unsafe: "liens écartés", constraints: "Contraintes", policy: "Règles de décision" },
  nl: { title: "Beslisregister", reviewed: "bekeken aanbiedingen", eligible: "geschikt", nonEligible: "overige niet geschikt", unsafe: "uitgesloten links", constraints: "Beperkingen", policy: "Beslisregels" },
  en: { title: "Decision ledger", reviewed: "offers reviewed", eligible: "eligible", nonEligible: "other ineligible", unsafe: "links excluded", constraints: "Constraints", policy: "Decision rules" },
};

const capsuleCopy = {
  fr: { title: "Capsules Discover", use: "Essayer", note: "Ces capsules sont des briefs de départ ; FILON cherche ensuite dans le catalogue et s’abstient sans données suffisantes.", minimalWorkTitle: "Lignes claires", minimalWorkDescription: "Une base nette pour une journée de travail, sans surcharge visuelle.", minimalEveningTitle: "Soirée épurée", minimalEveningDescription: "Quelques pièces cohérentes, laissées respirer.", classicWeddingTitle: "Cérémonie intemporelle", classicWeddingDescription: "Des repères structurés pour une occasion formelle.", classicWorkTitle: "Bureau réemployable", classicWorkDescription: "Une tenue ancrée, pensée pour être portée à nouveau.", boldEveningTitle: "Accent assumé", boldEveningDescription: "Une base lisible et une pièce plus expressive.", boldWeddingTitle: "Célébration vivante", boldWeddingDescription: "Une direction festive sans compromis sur la cohérence." },
  nl: { title: "Discover-capsules", use: "Proberen", note: "Deze capsules zijn startbriefs; FILON zoekt daarna in de catalogus en onthoudt zich bij onvoldoende gegevens.", minimalWorkTitle: "Heldere lijnen", minimalWorkDescription: "Een strakke basis voor een werkdag, zonder visuele drukte.", minimalEveningTitle: "Ingetogen avond", minimalEveningDescription: "Enkele samenhangende items die ruimte krijgen.", classicWeddingTitle: "Tijdloze ceremonie", classicWeddingDescription: "Gestructureerde ankerpunten voor een formele gelegenheid.", classicWorkTitle: "Herbruikbare kantoorlook", classicWorkDescription: "Een stevige outfit, bedoeld om opnieuw te dragen.", boldEveningTitle: "Uitgesproken accent", boldEveningDescription: "Een heldere basis met een expressiever item.", boldWeddingTitle: "Levendig feest", boldWeddingDescription: "Een feestelijke richting zonder de samenhang te verliezen." },
  en: { title: "Discover capsules", use: "Try", note: "These capsules are starting briefs; FILON then searches the catalogue and abstains when data is insufficient.", minimalWorkTitle: "Clean lines", minimalWorkDescription: "A clean base for a workday, without visual clutter.", minimalEveningTitle: "Refined evening", minimalEveningDescription: "A few coherent pieces with room to breathe.", classicWeddingTitle: "Timeless ceremony", classicWeddingDescription: "Structured anchors for a formal occasion.", classicWorkTitle: "Reusable office look", classicWorkDescription: "A grounded outfit designed to be worn again.", boldEveningTitle: "Expressive accent", boldEveningDescription: "A clear base with one more expressive piece.", boldWeddingTitle: "Vibrant celebration", boldWeddingDescription: "A festive direction without compromising coherence." },
};

const budgetCopy = {
  fr: { title: "Lecture budget", spent: "Total des pièces", remaining: "Reste", noBudget: "Aucun budget déclaré", under: "Sous la contrainte déclarée", near: "Proche de la limite déclarée", over: "Au-delà de la contrainte déclarée" },
  nl: { title: "Budgetlezing", spent: "Totaal van items", remaining: "Resterend", noBudget: "Geen budget opgegeven", under: "Onder de opgegeven limiet", near: "Dicht bij de opgegeven limiet", over: "Boven de opgegeven limiet" },
  en: { title: "Budget reading", spent: "Pieces total", remaining: "Remaining", noBudget: "No budget declared", under: "Under the declared constraint", near: "Near the declared limit", over: "Above the declared constraint" },
};

const plannerCopy = {
  fr: { title: "Planifier une occasion", date: "Date (AAAA-MM-JJ)", event: "Occasion", plan: "Planifier cette tenue", planned: "Occasions planifiées", noPlanned: "Aucune occasion planifiée.", remove: "Retirer", choose: "Choisissez une tenue du journal pour la planifier.", invalid: "Utilisez une date au format AAAA-MM-JJ.", enableReminder: "Activer le rappel", disableReminder: "Annuler le rappel", reminderScheduled: "Rappel programmé localement pour la veille à 18 h.", reminderCancelled: "Rappel annulé.", reminderUnavailable: "Ce rappel ne peut pas être programmé sur cet appareil ou cette date." },
  nl: { title: "Een gelegenheid plannen", date: "Datum (JJJJ-MM-DD)", event: "Gelegenheid", plan: "Deze outfit plannen", planned: "Geplande gelegenheden", noPlanned: "Geen geplande gelegenheden.", remove: "Verwijderen", choose: "Kies een outfit uit het dagboek om te plannen.", invalid: "Gebruik een datum in het formaat JJJJ-MM-DD.", enableReminder: "Herinnering inschakelen", disableReminder: "Herinnering annuleren", reminderScheduled: "Herinnering lokaal ingepland voor de dag ervoor om 18.00 uur.", reminderCancelled: "Herinnering geannuleerd.", reminderUnavailable: "Deze herinnering kan niet worden ingepland op dit apparaat of voor deze datum." },
  en: { title: "Plan an occasion", date: "Date (YYYY-MM-DD)", event: "Occasion", plan: "Plan this outfit", planned: "Planned occasions", noPlanned: "No planned occasions.", remove: "Remove", choose: "Choose an outfit from the journal to plan it.", invalid: "Use a date in YYYY-MM-DD format.", enableReminder: "Enable reminder", disableReminder: "Cancel reminder", reminderScheduled: "Reminder scheduled locally for 6 PM on the previous day.", reminderCancelled: "Reminder cancelled.", reminderUnavailable: "This reminder cannot be scheduled on this device or for this date." },
};

const comparisonCopy = {
  fr: { title: "Comparer les stratégies", safe: "Safe", signature: "Signature", total: "Total", confidence: "Confiance", coverage: "Pièces", difference: "Écart Signature vs Safe", notMeasured: "Non mesuré" },
  nl: { title: "Strategieën vergelijken", safe: "Safe", signature: "Signature", total: "Totaal", confidence: "Vertrouwen", coverage: "Items", difference: "Signature versus Safe", notMeasured: "Niet gemeten" },
  en: { title: "Compare strategies", safe: "Safe", signature: "Signature", total: "Total", confidence: "Confidence", coverage: "Pieces", difference: "Signature versus Safe", notMeasured: "Not measured" },
};

const rotationCopy = {
  fr: { title: "À reconsidérer", plan: "Planifier", empty: "Sauvegardez quelques tenues pour voir des idées de réemploi." },
  nl: { title: "Opnieuw overwegen", plan: "Plannen", empty: "Bewaar enkele outfits om hergebruikideeën te zien." },
  en: { title: "Consider again", plan: "Plan", empty: "Save a few outfits to see reuse ideas." },
};

const optimizeCopy = {
  fr: { title: "Optimiser une tenue", action: "Optimiser", empty: "Sauvegardez une tenue pour comparer les alternatives documentées du catalogue.", loading: "FILON analyse les offres du catalogue…", saving: "Alternatives documentées", replace: "Alternative proposée", unavailable: "Aucune amélioration documentée n’est disponible pour cette tenue." },
  nl: { title: "Een outfit optimaliseren", action: "Optimaliseren", empty: "Bewaar een outfit om gedocumenteerde alternatieven uit de catalogus te vergelijken.", loading: "FILON analyseert de catalogusaanbiedingen…", saving: "Gedocumenteerde alternatieven", replace: "Voorgesteld alternatief", unavailable: "Voor deze outfit is geen gedocumenteerde verbetering beschikbaar." },
  en: { title: "Optimise an outfit", action: "Optimise", empty: "Save an outfit to compare documented catalogue alternatives.", loading: "FILON is analysing catalogue offers…", saving: "Documented alternatives", replace: "Suggested alternative", unavailable: "No documented improvement is available for this outfit." },
};

const qualityCopy = {
  fr: { title: "Signaler une correction", prompt: "Ce retour reste local et ne modifie jamais les données du catalogue.", save: "Enregistrer la correction", saved: "Correction enregistrée localement.", note: "Précisez si nécessaire", style: "Style", context: "Contexte", confidence: "Confiance", hallucination: "Information à confirmer" },
  nl: { title: "Een correctie melden", prompt: "Deze feedback blijft lokaal en wijzigt de catalogusgegevens nooit.", save: "Correctie opslaan", saved: "Correctie lokaal opgeslagen.", note: "Voeg indien nodig details toe", style: "Stijl", context: "Context", confidence: "Vertrouwen", hallucination: "Te bevestigen informatie" },
  en: { title: "Report a correction", prompt: "This feedback stays local and never changes catalogue data.", save: "Save correction", saved: "Correction saved locally.", note: "Add details if needed", style: "Style", context: "Context", confidence: "Confidence", hallucination: "Information to confirm" },
};

type Occasion = "wedding" | "work" | "evening" | null;
type Season = "spring" | "summer" | "autumn" | "winter" | null;
type OutfitMode = "create" | "complete" | "recreate";

export default function OutfitStudioScreen() {
  const router = useRouter();
  const { occasionId } = useLocalSearchParams<{ occasionId?: string }>();
  const highlightedOccasionId = typeof occasionId === "string" ? occasionId : undefined;
  const { locale } = useLocale();
  const colors = useColors();
  const text = copy[locale];
  const completeText = completeCopy[locale];
  const dnaText = dnaCopy[locale];
  const recreateText = recreateCopy[locale];
  const wardrobeText = wardrobeCopy[locale];
  const journalText = journalCopy[locale];
  const ledgerText = ledgerCopy[locale];
  const capsuleText = capsuleCopy[locale];
  const budgetText = budgetCopy[locale];
  const plannerText = plannerCopy[locale];
  const comparisonText = comparisonCopy[locale];
  const rotationText = rotationCopy[locale];
  const optimizeText = optimizeCopy[locale];
  const qualityText = qualityCopy[locale];
  const styles = useMemo(() => createStyles(colors), [colors]);
  const [request, setRequest] = useState("");
  const [occasion, setOccasion] = useState<Occasion>(null);
  const [season, setSeason] = useState<Season>(null);
  const [budgetInput, setBudgetInput] = useState("");
  const [preferences, setPreferences] = useState<FashionPreferences>({ declaredStyle: null, updatedAt: null });
  const [recommendation, setRecommendation] = useState<OutfitRecommendation | null>(null);
  const [completeRecommendation, setCompleteRecommendation] = useState<CompleteRecommendation | null>(null);
  const [mode, setMode] = useState<OutfitMode>("create");
  const [ownedLabel, setOwnedLabel] = useState("");
  const [ownedRole, setOwnedRole] = useState<OwnedPiece["role"]>("structure");
  const [selectedStrategy, setSelectedStrategy] = useState<OutfitStrategyId>("safe");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<OutfitFeedbackValue | null>(null);
  const [styleDna, setStyleDna] = useState<StyleDna>({ primary: null, confidence: "low", evidenceCount: 0, source: "unknown" });
  const [inspirationUrl, setInspirationUrl] = useState("");
  const [recreateAnalysis, setRecreateAnalysis] = useState<RecreateAnalysis | null>(null);
  const [wardrobe, setWardrobe] = useState<WardrobeItem[]>([]);
  const [savedOutfits, setSavedOutfits] = useState<SavedOutfit[]>([]);
  const [plannedOccasions, setPlannedOccasions] = useState<PlannedOccasion[]>([]);
  const [planningOutfit, setPlanningOutfit] = useState<SavedOutfit | null>(null);
  const [plannedTitle, setPlannedTitle] = useState("");
  const [plannedDate, setPlannedDate] = useState("");
  const [plannerError, setPlannerError] = useState<string | null>(null);
  const [reminderStatus, setReminderStatus] = useState<string | null>(null);
  const [optimization, setOptimization] = useState<OutfitOptimization | null>(null);
  const [optimizingOutfitId, setOptimizingOutfitId] = useState<string | null>(null);
  const [correctionCode, setCorrectionCode] = useState<FashionErrorCode>("WRONG_STYLE");
  const [correctionNote, setCorrectionNote] = useState("");
  const [correctionSaved, setCorrectionSaved] = useState(false);
  const [evidenceNow, setEvidenceNow] = useState(() => Date.now());
  const recreateMutation = trpc.recreate.analyze.useMutation();

  useEffect(() => { void Promise.all([readFashionPreferences(), readStyleSignals()]).then(([nextPreferences, signals]) => { setPreferences(nextPreferences); setStyleDna(resolveStyleDna(nextPreferences.declaredStyle, signals)); }); }, []);
  useEffect(() => { void readWardrobe().then(setWardrobe); }, []);
  useEffect(() => { void readSavedOutfits().then(setSavedOutfits); }, []);
  useEffect(() => { void readPlannedOccasions().then(setPlannedOccasions); }, []);
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (state) => { if (state === "active") setEvidenceNow(Date.now()); });
    return () => subscription.remove();
  }, []);
  useEffect(() => {
    const solutions = [
      recommendation?.status === "solution" ? recommendation.solution : null,
      ...(completeRecommendation?.status === "solution" ? completeRecommendation.strategies.map((strategy) => strategy.solution) : []),
    ].filter((solution): solution is OutfitSolution => solution !== null);
    const expiries = [...solutions.map(getOutfitSolutionEvidenceExpiry), optimization ? getOutfitOptimizationEvidenceExpiry(optimization) : null];
    const nextExpiry = expiries.filter((expiry): expiry is number => expiry !== null && expiry > evidenceNow).sort((left, right) => left - right)[0];
    if (nextExpiry === undefined) return;
    const timeout = setTimeout(() => setEvidenceNow(Date.now()), Math.max(0, nextExpiry - Date.now() + 1));
    return () => clearTimeout(timeout);
  }, [completeRecommendation, evidenceNow, optimization, recommendation]);

  const budget = Number(budgetInput.replace(",", "."));
  const parsedBudget = Number.isFinite(budget) && budget > 0 ? budget : null;
  const setStyle = async (declaredStyle: FashionPreferences["declaredStyle"]) => { const next = await saveFashionPreferences({ declaredStyle }); setPreferences(next); const signals = await readStyleSignals(); setStyleDna(resolveStyleDna(next.declaredStyle, signals)); };
  const resetStyle = async () => { const next = await resetFashionPreferences(); setPreferences(next); const signals = await readStyleSignals(); setStyleDna(resolveStyleDna(next.declaredStyle, signals)); };
  const applyDiscoverDirection = async (direction: StyleDirectionId) => { const signals = await appendStyleSignal(direction, "affirmed"); const next = await saveFashionPreferences({ declaredStyle: direction }); setPreferences(next); setStyleDna(resolveStyleDna(next.declaredStyle, signals)); };
  const solutionKey = useMemo(() => recommendation?.status === "solution" ? buildOutfitFeedbackKey(recommendation.trace.intent.request, recommendation.solution.pieces.map((piece) => piece.offer.id)) : null, [recommendation]);
  useEffect(() => { if (!solutionKey) { setFeedback(null); return; } void readOutfitFeedback(solutionKey).then(setFeedback); }, [solutionKey]);
  const recordFeedback = async (value: OutfitFeedbackValue) => { if (!solutionKey) return; setFeedback(value); await saveOutfitFeedback(solutionKey, value); };
  const recordCorrection = async () => { if (!solutionKey) return; await saveFashionCorrection({ recommendationKey: solutionKey, code: correctionCode, note: correctionNote }); setCorrectionNote(""); setCorrectionSaved(true); };
  const analyzeInspiration = async () => { if (!inspirationUrl.trim() || recreateMutation.isPending) return; setError(null); setRecommendation(null); setCompleteRecommendation(null); setRecreateAnalysis(null); try { setRecreateAnalysis(await recreateMutation.mutateAsync({ imageUrl: inspirationUrl.trim(), locale })); } catch { setError(recreateText.error); } };
  const pickInspiration = async () => { const permission = await ImagePicker.requestMediaLibraryPermissionsAsync(); if (!permission.granted) { setError(recreateText.error); return; } const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.55, base64: true, allowsEditing: false, selectionLimit: 1 }); if (result.canceled || !result.assets[0]?.base64) return; const mime = result.assets[0].mimeType === "image/png" ? "image/png" : result.assets[0].mimeType === "image/webp" ? "image/webp" : "image/jpeg"; setInspirationUrl(`data:${mime};base64,${result.assets[0].base64}`); setError(null); };
  const useInspirationForSearch = () => { if (!recreateAnalysis || !isRecreateAnalysisForLocale(recreateAnalysis, locale)) return; const labels = [...recreateAnalysis.visiblePieces, ...recreateAnalysis.silhouette].filter((item) => item.confidence !== "unknown").slice(0, 5).map((item) => item.label); setRequest(labels.join(" ")); setMode("create"); };
  const saveOwnedPiece = async () => { if (!ownedLabel.trim()) return; setWardrobe(await saveWardrobeItem({ label: ownedLabel, role: ownedRole })); };
  const selectWardrobePiece = (item: WardrobeItem) => { setOwnedLabel(item.label); setOwnedRole(item.role); };
  const deleteWardrobePiece = async (item: WardrobeItem) => setWardrobe(await removeWardrobeItem(item.id));
  const saveSolution = async (title: string, mode: "create" | "complete", solution: OutfitSolution) => setSavedOutfits(await saveOutfit(makeSavedOutfit(title, mode, solution)));
  const deleteSavedSolution = async (item: SavedOutfit) => setSavedOutfits(await removeSavedOutfit(item.id));
  const beginPlanning = (item: SavedOutfit) => { setPlanningOutfit(item); setPlannedTitle(item.title); setPlannerError(null); };
  const savePlanning = async () => { if (!planningOutfit || !/^\d{4}-\d{2}-\d{2}$/.test(plannedDate) || !plannedTitle.trim()) { setPlannerError(plannerText.invalid); return; } setPlannedOccasions(await savePlannedOccasion({ title: plannedTitle, date: plannedDate, outfitId: planningOutfit.id })); setPlanningOutfit(null); setPlannedDate(""); setPlannerError(null); };
  const deletePlanning = async (item: PlannedOccasion) => { await cancelLocalOccasionReminder(item.reminderId); setPlannedOccasions(await removePlannedOccasion(item.id)); };
  const togglePlanningReminder = async (item: PlannedOccasion) => {
    setReminderStatus(null);
    if (item.reminderId) { await cancelLocalOccasionReminder(item.reminderId); setPlannedOccasions(await updatePlannedOccasionReminder(item.id, undefined)); setReminderStatus(plannerText.reminderCancelled); return; }
    const result = await scheduleLocalOccasionReminder(item);
    if (result.status === "scheduled") { setPlannedOccasions(await updatePlannedOccasionReminder(item.id, result.notificationId)); setReminderStatus(plannerText.reminderScheduled); return; }
    setReminderStatus(plannerText.reminderUnavailable);
  };
  const optimizeOutfit = async (item: SavedOutfit) => {
    if (optimizingOutfitId) return;
    setOptimization(null);
    setOptimizingOutfitId(item.id);
    try {
      const response = await searchFilonOffers({ query: item.pieces.map((piece) => piece.name).join(" "), limit: 48, sort: "relevance" });
      setOptimization(optimizeSavedOutfit(item, response.items));
    } catch {
      setOptimization({ status: "abstain", sourceOutfitId: item.id, checkedOffers: 0, reason: { code: "optimization.unavailable" } });
    } finally {
      setOptimizingOutfitId(null);
    }
  };
  const applyCapsule = (capsule: DiscoverCapsule) => { setRequest(localizedDiscoverCapsuleQuery(capsule.id, locale)); setOccasion(capsule.occasion); setMode("create"); };

  const submit = async () => {
    if (!request.trim() || (mode === "complete" && !ownedLabel.trim()) || mode === "recreate" || loading) return;
    setLoading(true);
    setError(null);
    setRecommendation(null);
    setCompleteRecommendation(null);
    try {
      const response = await searchFilonOffers({ query: request.trim(), limit: 48, sort: "relevance" });
      const intent = { request: request.trim(), occasion, season, budget: parsedBudget, declaredStyle: preferences.declaredStyle };
      const evaluationNow = Date.now();
      setEvidenceNow(evaluationNow);
      if (mode === "complete") {
        setSelectedStrategy("safe");
        setCompleteRecommendation(buildCompleteRecommendation(intent, { label: ownedLabel.trim(), role: ownedRole }, response.items, evaluationNow));
      } else {
        setRecommendation(buildOutfitRecommendation(intent, response.items, evaluationNow));
      }
    } catch {
      setError(text.error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOutfitStudioEnabled()) {
    return <ScreenContainer className="p-5" edges={["top", "left", "right", "bottom"]}><View style={styles.disabled}><MaterialIcons name="lock-outline" size={25} color={colors.primary} /><Text style={styles.disabledTitle}>{outfitStudioName[locale]}</Text><Text style={styles.disabledBody}>{text.unavailable}</Text><TactileButton accessibilityLabel={text.back} onPress={() => router.back()} style={styles.primaryButton}><Text style={styles.primaryButtonText}>{text.back}</Text></TactileButton></View></ScreenContainer>;
  }

  const displayedRecommendation: OutfitRecommendation | null = recommendation?.status === "solution" && !isOutfitSolutionCurrent(recommendation.solution, evidenceNow)
    ? { status: "abstain", reason: { code: "recommendation.evidence_expired" }, trace: recommendation.trace }
    : recommendation;
  const displayedCompleteRecommendation: CompleteRecommendation | null = completeRecommendation?.status === "solution"
    ? (() => {
      const strategies = filterCurrentOutfitStrategies(completeRecommendation.strategies, evidenceNow);
      return strategies.length > 0 ? { ...completeRecommendation, strategies } : { status: "abstain", ownedPiece: completeRecommendation.ownedPiece, reason: { code: "recommendation.evidence_expired" }, trace: completeRecommendation.trace };
    })()
    : completeRecommendation;
  const displayedOptimization: OutfitOptimization | null = optimization?.status === "solution" && !isOutfitOptimizationCurrent(optimization, evidenceNow)
    ? { status: "abstain", sourceOutfitId: optimization.sourceOutfitId, checkedOffers: optimization.checkedOffers, reason: { code: "optimization.evidence_expired" } }
    : optimization;
  const activeCompleteStrategy = displayedCompleteRecommendation?.status === "solution" ? displayedCompleteRecommendation.strategies.find((strategy) => strategy.id === selectedStrategy) ?? displayedCompleteRecommendation.strategies[0] : null;
  const displayedStrategyId = activeCompleteStrategy?.id ?? selectedStrategy;
  const pieces = displayedRecommendation?.status === "solution" ? displayedRecommendation.solution.pieces : activeCompleteStrategy?.solution.pieces ?? [];
  return (
    <ScreenContainer className="" containerClassName="bg-background" edges={["top", "left", "right", "bottom"]}>
      <FlatList
        data={pieces}
        keyExtractor={(item) => String(item.offer.id)}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        ListHeaderComponent={<>
          <View style={styles.topbar}><TactileButton accessibilityLabel={text.back} onPress={() => router.back()} style={styles.back}><MaterialIcons name="arrow-back" size={20} color={colors.foreground} /><Text style={styles.backText}>{text.back}</Text></TactileButton><Pressable accessibilityRole="button" accessibilityLabel={text.lookbook} onPress={() => router.push("/lookbook" as never)} style={({ pressed }) => [styles.lookbookButton, pressed && styles.pressed]}><MaterialIcons name="collections-bookmark" size={17} color={colors.primary} /><Text style={styles.lookbookText}>{text.lookbook}</Text></Pressable><View style={styles.live}><View style={styles.liveDot} /><Text style={styles.liveText}>{text.preview}</Text></View></View>
          <View style={styles.hero}><Text style={styles.eyebrow}>{text.eyebrow}</Text><Text style={styles.title}>{mode === "recreate" ? recreateText.title : text.title}</Text><View style={styles.orbit} /><View style={styles.spark} /></View>
          <View style={styles.modeRow}><Choice label={completeText.createMode} active={mode === "create"} onPress={() => setMode("create")} styles={styles} /><Choice label={completeText.completeMode} active={mode === "complete"} onPress={() => setMode("complete")} styles={styles} /><Choice label={recreateText.mode} active={mode === "recreate"} onPress={() => setMode("recreate")} styles={styles} /></View>
          {mode === "recreate" ? <View style={styles.recreatePanel}><Text style={styles.recreateGuidance}>{recreateText.guidance}</Text><TextInput value={inspirationUrl.startsWith("data:") ? recreateText.localImage : inspirationUrl} onChangeText={setInspirationUrl} autoCapitalize="none" keyboardType="url" placeholder={recreateText.placeholder} placeholderTextColor={colors.muted} style={styles.recreateInput} accessibilityLabel={recreateText.url} /><Pressable accessibilityRole="button" accessibilityLabel={recreateText.choose} onPress={() => void pickInspiration()} style={({ pressed }) => [styles.recreatePicker, pressed && styles.pressed]}><MaterialIcons name="photo-library" size={16} color={colors.primary} /><Text style={styles.recreatePickerText}>{recreateText.choose}</Text></Pressable>{inspirationUrl.startsWith("data:") ? <Image source={{ uri: inspirationUrl }} style={styles.recreatePreview} contentFit="cover" /> : null}<Text style={styles.recreatePrivacy}>{recreateText.privacy}</Text><TactileButton accessibilityLabel={recreateText.analyze} onPress={() => void analyzeInspiration()} disabled={!inspirationUrl.trim() || recreateMutation.isPending} style={[styles.recreateButton, (!inspirationUrl.trim() || recreateMutation.isPending) && styles.disabledButton]}>{recreateMutation.isPending ? <ActivityIndicator color={colors.background} /> : <><Text style={styles.primaryButtonText}>{recreateText.analyze}</Text><MaterialIcons name="center-focus-strong" size={18} color={colors.background} /></>}</TactileButton></View> : <View style={styles.composer}><TextInput value={request} onChangeText={setRequest} onSubmitEditing={() => void submit()} returnKeyType="search" placeholder={text.placeholder} placeholderTextColor={colors.muted} style={styles.input} multiline accessibilityLabel={text.placeholder} /><TextInput value={budgetInput} onChangeText={setBudgetInput} keyboardType="decimal-pad" placeholder={`${text.budget} €`} placeholderTextColor={colors.muted} style={styles.budgetInput} accessibilityLabel={text.budget} /></View>}
          {mode === "complete" ? <><View style={styles.ownedPanel}><Text style={styles.ownedTitle}>{completeText.owned}</Text><TextInput value={ownedLabel} onChangeText={setOwnedLabel} placeholder={completeText.ownedPlaceholder} placeholderTextColor={colors.muted} style={styles.ownedInput} accessibilityLabel={completeText.owned} /><Text style={styles.ownedCaption}>{completeText.ownedNotice}</Text><SectionLabel label={completeText.ownedRole} /><View style={styles.chipRow}><Choice label={completeText.base} active={ownedRole === "base"} onPress={() => setOwnedRole("base")} styles={styles} /><Choice label={completeText.structure} active={ownedRole === "structure"} onPress={() => setOwnedRole("structure")} styles={styles} /><Choice label={completeText.footwear} active={ownedRole === "footwear"} onPress={() => setOwnedRole("footwear")} styles={styles} /><Choice label={completeText.accessory} active={ownedRole === "accessory"} onPress={() => setOwnedRole("accessory")} styles={styles} /></View><Pressable accessibilityRole="button" accessibilityLabel={wardrobeText.save} onPress={() => void saveOwnedPiece()} style={({ pressed }) => [styles.wardrobeSave, !ownedLabel.trim() && styles.disabledButton, pressed && styles.pressed]}><MaterialIcons name="add" size={16} color={colors.primary} /><Text style={styles.wardrobeSaveText}>{wardrobeText.save}</Text></Pressable></View><WardrobePanel items={wardrobe} text={wardrobeText} styles={styles} onSelect={selectWardrobePiece} onRemove={deleteWardrobePiece} /></> : null}
          {mode !== "recreate" ? <><SectionLabel label={text.occasion} /><View style={styles.chipRow}><Choice label={text.wedding} active={occasion === "wedding"} onPress={() => setOccasion(occasion === "wedding" ? null : "wedding")} styles={styles} /><Choice label={text.work} active={occasion === "work"} onPress={() => setOccasion(occasion === "work" ? null : "work")} styles={styles} /><Choice label={text.evening} active={occasion === "evening"} onPress={() => setOccasion(occasion === "evening" ? null : "evening")} styles={styles} /></View></> : null}
          <SectionLabel label={text.season} /><View style={styles.chipRow}><Choice label={text.spring} active={season === "spring"} onPress={() => setSeason(season === "spring" ? null : "spring")} styles={styles} /><Choice label={text.summer} active={season === "summer"} onPress={() => setSeason(season === "summer" ? null : "summer")} styles={styles} /><Choice label={text.autumn} active={season === "autumn"} onPress={() => setSeason(season === "autumn" ? null : "autumn")} styles={styles} /><Choice label={text.winter} active={season === "winter"} onPress={() => setSeason(season === "winter" ? null : "winter")} styles={styles} /></View>
          <View style={styles.preferenceHeader}><SectionLabel label={text.style} /><Pressable accessibilityRole="button" accessibilityLabel={text.reset} onPress={() => void resetStyle()} style={({ pressed }) => [styles.reset, pressed && styles.pressed]}><Text style={styles.resetText}>{text.reset}</Text></Pressable></View>
          <View style={styles.chipRow}><Choice label={text.minimal} active={preferences.declaredStyle === "minimal"} onPress={() => void setStyle(preferences.declaredStyle === "minimal" ? null : "minimal")} styles={styles} /><Choice label={text.classic} active={preferences.declaredStyle === "classic"} onPress={() => void setStyle(preferences.declaredStyle === "classic" ? null : "classic")} styles={styles} /><Choice label={text.bold} active={preferences.declaredStyle === "bold"} onPress={() => void setStyle(preferences.declaredStyle === "bold" ? null : "bold")} styles={styles} /></View>
          <StyleDnaPanel dna={styleDna} directions={getDiscoverDirections(styleDna)} text={dnaText} styles={styles} onApply={applyDiscoverDirection} />
          <DiscoverCapsulesPanel capsules={selectDiscoverCapsules(styleDna)} text={capsuleText} styles={styles} onApply={applyCapsule} />
          <JournalPanel items={savedOutfits} text={journalText} styles={styles} onRemove={deleteSavedSolution} onPlan={beginPlanning} />
          <OptimizePanel items={savedOutfits} result={displayedOptimization} loadingId={optimizingOutfitId} locale={locale} text={optimizeText} styles={styles} onOptimize={optimizeOutfit} />
          <RotationPanel suggestions={buildOutfitRotation(savedOutfits)} locale={locale} text={rotationText} styles={styles} onPlan={(suggestion) => beginPlanning(suggestion.outfit)} />
          <PlannerPanel selected={planningOutfit} title={plannedTitle} date={plannedDate} error={plannerError} reminderStatus={reminderStatus} highlightedId={highlightedOccasionId} items={plannedOccasions} text={plannerText} styles={styles} onTitle={setPlannedTitle} onDate={setPlannedDate} onSave={() => void savePlanning()} onRemove={deletePlanning} onToggleReminder={togglePlanningReminder} />
          {mode !== "recreate" ? <TactileButton accessibilityLabel={mode === "complete" ? completeText.complete : text.create} onPress={() => void submit()} disabled={!request.trim() || (mode === "complete" && !ownedLabel.trim()) || loading} style={[styles.primaryButton, (!request.trim() || (mode === "complete" && !ownedLabel.trim()) || loading) && styles.disabledButton]}>{loading ? <ActivityIndicator color={colors.background} /> : <><Text style={styles.primaryButtonText}>{mode === "complete" ? completeText.complete : text.create}</Text><MaterialIcons name="auto-awesome" size={18} color={colors.background} /></>}</TactileButton> : null}
          {loading ? <StatusCard title={text.loading} body="" icon="hourglass-top" styles={styles} /> : null}
          {error ? <StatusCard title={mode === "recreate" ? recreateText.error : text.error} body="" icon="cloud-off" styles={styles} error /> : null}
          {displayedRecommendation?.status === "abstain" ? <StatusCard title={text.abstain} body={resolveOutfitPublicMessage(displayedRecommendation.reason, locale)} icon="verified-user" styles={styles} error /> : null}
          {displayedRecommendation?.status === "solution" ? <><SolutionHeader recommendation={displayedRecommendation} text={text} locale={locale} styles={styles} feedback={feedback} onFeedback={recordFeedback} onSave={(solution) => void saveSolution(request, "create", solution)} saveLabel={journalText.save} /><CorrectionPanel code={correctionCode} note={correctionNote} saved={correctionSaved} text={qualityText} styles={styles} onCode={setCorrectionCode} onNote={setCorrectionNote} onSave={() => void recordCorrection()} /><BudgetPanel spent={displayedRecommendation.solution.total} budget={displayedRecommendation.trace.intent.budget} currency={displayedRecommendation.solution.currency} locale={locale} text={budgetText} styles={styles} /><DecisionLedgerPanel trace={displayedRecommendation.trace} constraints={displayedRecommendation.solution.constraints} locale={locale} text={ledgerText} styles={styles} /></> : null}
          {displayedCompleteRecommendation?.status === "abstain" ? <StatusCard title={completeText.abstain} body={resolveOutfitPublicMessage(displayedCompleteRecommendation.reason, locale)} icon="verified-user" styles={styles} error /> : null}
          {displayedCompleteRecommendation?.status === "solution" && activeCompleteStrategy ? <View style={styles.completeWrap}><View style={styles.strategyHeading}><Text style={styles.strategyLabel}>{completeText.strategy}</Text><Text style={styles.ownedNotice}>{completeText.solution}</Text></View><View style={styles.strategyRow}>{displayedCompleteRecommendation.strategies.some((strategy) => strategy.id === "safe") ? <Choice label={completeText.safe} active={displayedStrategyId === "safe"} onPress={() => setSelectedStrategy("safe")} styles={styles} /> : null}{displayedCompleteRecommendation.strategies.some((strategy) => strategy.id === "signature") ? <Choice label={completeText.signature} active={displayedStrategyId === "signature"} onPress={() => setSelectedStrategy("signature")} styles={styles} /> : null}{displayedCompleteRecommendation.strategies.some((strategy) => strategy.id === "statement") ? <Choice label={completeText.statement} active={displayedStrategyId === "statement"} onPress={() => setSelectedStrategy("statement")} styles={styles} /> : null}</View><StrategyComparisonPanel strategies={displayedCompleteRecommendation.strategies} locale={locale} text={comparisonText} styles={styles} /><Text style={styles.strategyDescription}>{resolveOutfitPublicMessage(activeCompleteStrategy.description, locale)}</Text><SolutionHeader recommendation={{ status: "solution", solution: activeCompleteStrategy.solution, trace: displayedCompleteRecommendation.trace }} text={text} locale={locale} styles={styles} feedback={null} onFeedback={recordFeedback} showFeedback={false} onSave={(solution) => void saveSolution(ownedLabel || request, "complete", solution)} saveLabel={journalText.save} /><BudgetPanel spent={activeCompleteStrategy.solution.total} budget={displayedCompleteRecommendation.trace.intent.budget} currency={activeCompleteStrategy.solution.currency} locale={locale} text={budgetText} styles={styles} /><DecisionLedgerPanel trace={displayedCompleteRecommendation.trace} constraints={activeCompleteStrategy.solution.constraints} locale={locale} text={ledgerText} styles={styles} /></View> : null}
          {recreateAnalysis && isRecreateAnalysisForLocale(recreateAnalysis, locale) ? <RecreatePanel analysis={recreateAnalysis} locale={locale} text={recreateText} styles={styles} onUse={useInspirationForSearch} /> : null}
          {!displayedRecommendation && !displayedCompleteRecommendation && !loading && !error ? <View style={styles.empty}><MaterialIcons name="auto-awesome" size={22} color={colors.primary} /><Text style={styles.emptyText}>{text.noResult}</Text></View> : null}
        </>}
        renderItem={({ item }) => <PieceCard item={item} text={text} locale={locale} styles={styles} onPress={() => router.push({ pathname: "/product/[id]", params: { id: String(item.offer.id), name: item.offer.name, price: String(item.offer.price), currency: item.offer.currency, merchant: item.offer.merchantName, image: item.offer.imageUrl ?? "", link: item.offer.link, stock: item.offer.inStock === true ? "1" : item.offer.inStock === false ? "0" : "", observedAt: item.offer.observedAt ?? "", evidenceCurrent: item.offer.evidenceCurrent === true ? "1" : "", category: item.offer.category ?? "" } } as never)} />}
        ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
        ListFooterComponent={displayedRecommendation?.status === "solution" || displayedCompleteRecommendation?.status === "solution" ? <View style={styles.footerSpace} /> : null}
      />
    </ScreenContainer>
  );
}

function SectionLabel({ label }: { label: string }) { return <Text style={localStyles.sectionLabel}>{label}</Text>; }
function Choice({ label, active, onPress, styles }: { label: string; active: boolean; onPress: () => void; styles: ReturnType<typeof createStyles> }) { return <Pressable accessibilityRole="button" accessibilityState={{ selected: active }} accessibilityLabel={label} onPress={onPress} style={({ pressed }) => [styles.choice, active && styles.choiceActive, pressed && styles.pressed]}><Text style={[styles.choiceText, active && styles.choiceTextActive]}>{label}</Text></Pressable>; }
function StatusCard({ title, body, icon, styles, error = false }: { title: string; body: string; icon: keyof typeof MaterialIcons.glyphMap; styles: ReturnType<typeof createStyles>; error?: boolean }) { return <View style={[styles.status, error && styles.statusError]}><MaterialIcons name={icon} size={20} color={error ? "#E59480" : "#8FB072"} /><View style={styles.statusWords}><Text style={styles.statusTitle}>{title}</Text>{body ? <Text style={styles.statusBody}>{body}</Text> : null}</View></View>; }
function SolutionHeader({ recommendation, text, locale, styles, feedback, onFeedback, showFeedback = true, onSave, saveLabel }: { recommendation: Extract<OutfitRecommendation, { status: "solution" }>; text: typeof copy.fr; locale: "fr" | "nl" | "en"; styles: ReturnType<typeof createStyles>; feedback: OutfitFeedbackValue | null; onFeedback: (value: OutfitFeedbackValue) => Promise<void>; showFeedback?: boolean; onSave?: (solution: OutfitSolution) => void; saveLabel?: string }) { const solution = recommendation.solution; return <View style={styles.solution}><View style={styles.solutionTop}><View><Text style={styles.solutionLabel}>{text.solution}</Text><Text style={styles.total}>{formatFilonPrice(solution.total, locale, solution.currency)}</Text><Text style={styles.totalCaption}>{text.total}</Text></View><View style={styles.confidence}><Text style={styles.confidenceValue}>{text.notMeasured}</Text><Text style={styles.confidenceLabel}>{text.confidence}</Text></View></View><View style={styles.scoreRow}><Metric label={text.styleScore} value={text.notMeasured} styles={styles} /><Metric label={text.confidence} value={text.notMeasured} styles={styles} /></View><Text style={styles.constraintsTitle}>{text.constraints}</Text><Text style={styles.constraints}>{solution.constraints.map((message) => resolveOutfitPublicMessage(message, locale)).join(" · ")}</Text><View style={styles.critique}><View style={styles.critiqueTop}><Text style={styles.critiqueTitle}>{text.critique}</Text><Text style={styles.relations}>{solution.relations.length} {text.relations}</Text></View><Text style={styles.critiqueBody}>{describeFindings(solution.critique.findings, text)}</Text></View><Text style={styles.scoreNoteTitle}>{text.scoreNote}</Text><Text style={styles.scoreNote}>{resolveOutfitPublicMessage(solution.scoreExplanation, locale)}</Text>{onSave && saveLabel ? <Pressable accessibilityRole="button" accessibilityLabel={saveLabel} onPress={() => onSave(solution)} style={({ pressed }) => [styles.journalSave, pressed && styles.pressed]}><MaterialIcons name="bookmark-add" size={16} color="#C89544" /><Text style={styles.journalSaveText}>{saveLabel}</Text></Pressable> : null}{showFeedback ? <View style={styles.feedback}><Text style={styles.feedbackTitle}>{text.feedback}</Text><View style={styles.feedbackActions}><Pressable accessibilityRole="button" accessibilityState={{ selected: feedback === "helpful" }} accessibilityLabel={text.helpful} onPress={() => void onFeedback("helpful")} style={({ pressed }) => [styles.feedbackButton, feedback === "helpful" && styles.feedbackButtonActive, pressed && styles.pressed]}><MaterialIcons name="thumb-up-off-alt" size={16} color={feedback === "helpful" ? colorsForFeedback : "#C89544"} /><Text style={[styles.feedbackButtonText, feedback === "helpful" && styles.feedbackButtonTextActive]}>{text.helpful}</Text></Pressable><Pressable accessibilityRole="button" accessibilityState={{ selected: feedback === "needs_review" }} accessibilityLabel={text.review} onPress={() => void onFeedback("needs_review")} style={({ pressed }) => [styles.feedbackButton, feedback === "needs_review" && styles.feedbackButtonActive, pressed && styles.pressed]}><MaterialIcons name="thumb-down-off-alt" size={16} color={feedback === "needs_review" ? colorsForFeedback : "#C89544"} /><Text style={[styles.feedbackButtonText, feedback === "needs_review" && styles.feedbackButtonTextActive]}>{text.review}</Text></Pressable></View>{feedback ? <Text style={styles.feedbackThanks}>{text.thanks}</Text> : null}</View> : null}</View>; }
function CorrectionPanel({ code, note, saved, text, styles, onCode, onNote, onSave }: { code: FashionErrorCode; note: string; saved: boolean; text: typeof qualityCopy.fr; styles: ReturnType<typeof createStyles>; onCode: (value: FashionErrorCode) => void; onNote: (value: string) => void; onSave: () => void }) { const choices: [FashionErrorCode, string][] = [["WRONG_STYLE", text.style], ["WRONG_CONTEXT", text.context], ["LOW_CONFIDENCE", text.confidence], ["HALLUCINATION", text.hallucination]]; return <View style={styles.correction}><Text style={styles.correctionTitle}>{text.title}</Text><Text style={styles.correctionPrompt}>{text.prompt}</Text><View style={styles.correctionChoices}>{choices.map(([value, label]) => <Choice key={value} label={label} active={code === value} onPress={() => onCode(value)} styles={styles} />)}</View><TextInput value={note} onChangeText={onNote} placeholder={text.note} placeholderTextColor="#817A72" style={styles.correctionInput} accessibilityLabel={text.note} /><Pressable accessibilityRole="button" accessibilityLabel={text.save} onPress={onSave} style={({ pressed }) => [styles.correctionAction, pressed && styles.pressed]}><Text style={styles.correctionActionText}>{text.save}</Text></Pressable>{saved ? <Text style={styles.correctionSaved}>{text.saved}</Text> : null}</View>; }
const colorsForFeedback = "#0E0C0B";
function describeFindings(findings: Extract<OutfitRecommendation, { status: "solution" }> ["solution"]["critique"]["findings"], text: typeof copy.fr) { if (findings.length === 0) return text.coherent; const labels: string[] = []; for (const finding of findings) labels.push(text.finding[finding.code]); return labels.join(" "); }
function Metric({ label, value, styles }: { label: string; value: string; styles: ReturnType<typeof createStyles> }) { return <View style={styles.metric}><Text style={styles.metricValue}>{value}</Text><Text style={styles.metricLabel}>{label}</Text></View>; }
function PieceCard({ item, text, locale, styles, onPress }: { item: OutfitPiece; text: typeof copy.fr; locale: "fr" | "nl" | "en"; styles: ReturnType<typeof createStyles>; onPress: () => void }) { return <Pressable accessibilityRole="button" accessibilityLabel={`${text.piece} ${item.offer.name}`} onPress={onPress} style={({ pressed }) => [styles.piece, pressed && styles.pressed]}>{item.offer.imageUrl ? <Image source={{ uri: item.offer.imageUrl }} style={styles.pieceImage} contentFit="contain" transition={180} /> : <View style={styles.pieceImageFallback}><MaterialIcons name="checkroom" size={22} color="#C89544" /></View>}<View style={styles.pieceWords}><Text style={styles.pieceRole}>{text.role[item.role]}</Text><Text style={styles.pieceName} numberOfLines={2}>{item.offer.name}</Text><Text style={styles.pieceExplanation} numberOfLines={2}>{resolveOutfitPublicMessage(item.explanation, locale)}</Text><View style={styles.pieceBottom}><Text style={styles.piecePrice}>{formatFilonPrice(item.offer.price, locale, item.offer.currency)}</Text><Text style={styles.pieceMerchant}>{item.offer.merchantName}</Text></View></View><MaterialIcons name="chevron-right" size={21} color="#C89544" /></Pressable>; }
function StyleDnaPanel({ dna, directions, text, styles, onApply }: { dna: StyleDna; directions: DiscoverDirection[]; text: typeof dnaCopy.fr; styles: ReturnType<typeof createStyles>; onApply: (direction: StyleDirectionId) => Promise<void> }) { const source = dna.source === "declared" ? text.declared : dna.source === "repeated_signals" ? text.repeated : text.unknown; return <View style={styles.dnaPanel}><View style={styles.dnaTop}><View><Text style={styles.dnaTitle}>{text.title}</Text><Text style={styles.dnaSource}>{source}</Text></View><View style={styles.dnaConfidence}><Text style={styles.dnaConfidenceValue}>{dna.evidenceCount}</Text><Text style={styles.dnaConfidenceCaption}>{dna.evidenceCount === 1 ? text.signal : text.signals}</Text></View></View><Text style={styles.discoverTitle}>{text.explore}</Text><DiscoverCard direction={directions[0]} text={text} styles={styles} onApply={onApply} /><DiscoverCard direction={directions[1]} text={text} styles={styles} onApply={onApply} /><DiscoverCard direction={directions[2]} text={text} styles={styles} onApply={onApply} /></View>; }
function DiscoverCard({ direction, text, styles, onApply }: { direction: DiscoverDirection; text: typeof dnaCopy.fr; styles: ReturnType<typeof createStyles>; onApply: (direction: StyleDirectionId) => Promise<void> }) { const label = direction.id === "minimal" ? text.minimal : direction.id === "classic" ? text.classic : text.bold; const description = direction.id === "minimal" ? text.minimalDescription : direction.id === "classic" ? text.classicDescription : text.boldDescription; return <View style={styles.discoverCard}><View style={styles.discoverWords}><Text style={styles.discoverName}>{label}</Text><Text style={styles.discoverDescription}>{description}</Text></View><Pressable accessibilityRole="button" accessibilityLabel={`${text.apply} ${label}`} onPress={() => void onApply(direction.id)} style={({ pressed }) => [styles.discoverAction, pressed && styles.pressed]}><Text style={styles.discoverActionText}>{text.apply}</Text></Pressable></View>; }
function RecreatePanel({ analysis, locale, text, styles, onUse }: { analysis: RecreateAnalysis; locale: "fr" | "nl" | "en"; text: typeof recreateCopy.fr; styles: ReturnType<typeof createStyles>; onUse: () => void }) { return <View style={styles.recreateResult}><Text style={styles.recreateResultTitle}>{text.results}</Text><Text style={styles.recreateSummary}>{analysis.summary}</Text><ObservationLine title={text.silhouette} observation={analysis.silhouette[0]} locale={locale} text={text} styles={styles} /><ObservationLine title={text.palette} observation={analysis.palette[0]} locale={locale} text={text} styles={styles} /><ObservationLine title={text.visiblePiece} observation={analysis.visiblePieces[0]} locale={locale} text={text} styles={styles} /><Text style={styles.recreateLimitsTitle}>{text.limits}</Text><Text style={styles.recreateLimits}>{analysis.limits.join(" · ")}</Text><TactileButton accessibilityLabel={text.search} onPress={onUse} style={styles.recreateButton}><Text style={styles.primaryButtonText}>{text.search}</Text><MaterialIcons name="search" size={18} color="#0E0C0B" /></TactileButton></View>; }
function ObservationLine({ title, observation, locale, text, styles }: { title: string; observation: RecreateObservation | undefined; locale: "fr" | "nl" | "en"; text: typeof recreateCopy.fr; styles: ReturnType<typeof createStyles> }) { if (!observation) return null; const confidence = observation.confidence === "certain" ? text.certain : observation.confidence === "probable" ? text.probable : text.unknown; return <View style={styles.observation}><View style={styles.observationTop}><Text style={styles.observationTitle}>{title}</Text><Text style={styles.observationConfidence}>{confidence}</Text></View><Text style={styles.observationLabel}>{observation.label}</Text><Text style={styles.observationExplanation}>{resolveOutfitPublicMessage(explanationForConfidence(observation.confidence), locale)}</Text></View>; }
function WardrobePanel({ items, text, styles, onSelect, onRemove }: { items: WardrobeItem[]; text: typeof wardrobeCopy.fr; styles: ReturnType<typeof createStyles>; onSelect: (item: WardrobeItem) => void; onRemove: (item: WardrobeItem) => Promise<void> }) { return <View style={styles.wardrobePanel}><Text style={styles.wardrobeTitle}>{text.title}</Text>{items.length === 0 ? <Text style={styles.wardrobeEmpty}>{text.empty}</Text> : <><WardrobeRow item={items[0]} text={text} styles={styles} onSelect={onSelect} onRemove={onRemove} /><WardrobeRow item={items[1]} text={text} styles={styles} onSelect={onSelect} onRemove={onRemove} /><WardrobeRow item={items[2]} text={text} styles={styles} onSelect={onSelect} onRemove={onRemove} /></>}</View>; }
function WardrobeRow({ item, text, styles, onSelect, onRemove }: { item: WardrobeItem | undefined; text: typeof wardrobeCopy.fr; styles: ReturnType<typeof createStyles>; onSelect: (item: WardrobeItem) => void; onRemove: (item: WardrobeItem) => Promise<void> }) { if (!item) return null; return <View style={styles.wardrobeRow}><Pressable accessibilityRole="button" accessibilityLabel={`${text.use} ${item.label}`} onPress={() => onSelect(item)} style={({ pressed }) => [styles.wardrobeSelect, pressed && styles.pressed]}><MaterialIcons name="checkroom" size={16} color="#C89544" /><Text style={styles.wardrobeItemName} numberOfLines={1}>{item.label}</Text></Pressable><Pressable accessibilityRole="button" accessibilityLabel={`${text.remove} ${item.label}`} onPress={() => void onRemove(item)} style={({ pressed }) => [styles.wardrobeRemove, pressed && styles.pressed]}><MaterialIcons name="close" size={15} color="#E59480" /></Pressable></View>; }
function JournalPanel({ items, text, styles, onRemove, onPlan }: { items: SavedOutfit[]; text: typeof journalCopy.fr; styles: ReturnType<typeof createStyles>; onRemove: (item: SavedOutfit) => Promise<void>; onPlan: (item: SavedOutfit) => void }) { return <View style={styles.journalPanel}><Text style={styles.journalTitle}>{text.title}</Text>{items.length === 0 ? <Text style={styles.journalEmpty}>{text.empty}</Text> : <><JournalRow item={items[0]} text={text} styles={styles} onRemove={onRemove} onPlan={onPlan} /><JournalRow item={items[1]} text={text} styles={styles} onRemove={onRemove} onPlan={onPlan} /></>}</View>; }
function JournalRow({ item, text, styles, onRemove, onPlan }: { item: SavedOutfit | undefined; text: typeof journalCopy.fr; styles: ReturnType<typeof createStyles>; onRemove: (item: SavedOutfit) => Promise<void>; onPlan: (item: SavedOutfit) => void }) { if (!item) return null; const type = item.mode === "create" ? text.create : text.complete; const pieceLabel = item.pieces.length === 1 ? text.piece : text.pieces; return <View style={styles.journalRow}><Pressable accessibilityRole="button" accessibilityLabel={`${text.plan} ${item.title}`} onPress={() => onPlan(item)} style={({ pressed }) => [styles.journalWords, pressed && styles.pressed]}><Text style={styles.journalItemTitle} numberOfLines={1}>{item.title}</Text><Text style={styles.journalMeta}>{type} · {item.pieces.length} {pieceLabel} · {text.notMeasured}</Text></Pressable><Pressable accessibilityRole="button" accessibilityLabel={`${text.remove} ${item.title}`} onPress={() => void onRemove(item)} style={({ pressed }) => [styles.wardrobeRemove, pressed && styles.pressed]}><MaterialIcons name="close" size={15} color="#E59480" /></Pressable></View>; }
function OptimizePanel({ items, result, loadingId, locale, text, styles, onOptimize }: { items: SavedOutfit[]; result: OutfitOptimization | null; loadingId: string | null; locale: "fr" | "nl" | "en"; text: typeof optimizeCopy.fr; styles: ReturnType<typeof createStyles>; onOptimize: (item: SavedOutfit) => Promise<void> }) { return <View style={styles.optimize}><Text style={styles.optimizeTitle}>{text.title}</Text>{items.length === 0 ? <Text style={styles.optimizeEmpty}>{text.empty}</Text> : <><OptimizeRow item={items[0]} loading={loadingId === items[0]?.id} text={text} styles={styles} onOptimize={onOptimize} /><OptimizeRow item={items[1]} loading={loadingId === items[1]?.id} text={text} styles={styles} onOptimize={onOptimize} />{result?.status === "solution" ? <View style={styles.optimizeResult}><Text style={styles.optimizeSaving}>{text.saving}</Text>{result.replacements.slice(0, 2).map((replacement) => <Text key={replacement.previous.offerId} style={styles.optimizeReplacement}>{text.replace} · {replacement.previous.name} → {replacement.next.name}</Text>)}<Text style={styles.optimizeNote}>{result.constraints.map((message) => resolveOutfitPublicMessage(message, locale)).join(" · ")}</Text></View> : null}{result?.status === "abstain" ? <Text style={styles.optimizeEmpty}>{resolveOutfitPublicMessage(result.reason, locale)}</Text> : null}</>}</View>; }
function OptimizeRow({ item, loading, text, styles, onOptimize }: { item: SavedOutfit | undefined; loading: boolean; text: typeof optimizeCopy.fr; styles: ReturnType<typeof createStyles>; onOptimize: (item: SavedOutfit) => Promise<void> }) { if (!item) return null; return <View style={styles.optimizeRow}><Text style={styles.optimizeName} numberOfLines={1}>{item.title}</Text><Pressable accessibilityRole="button" accessibilityLabel={`${text.action} ${item.title}`} onPress={() => void onOptimize(item)} style={({ pressed }) => [styles.optimizeAction, pressed && styles.pressed]}>{loading ? <ActivityIndicator size="small" color="#C89544" /> : <><Text style={styles.optimizeActionText}>{text.action}</Text><MaterialIcons name="tune" size={14} color="#C89544" /></>}</Pressable></View>; }
function PlannerPanel({ selected, title, date, error, reminderStatus, highlightedId, items, text, styles, onTitle, onDate, onSave, onRemove, onToggleReminder }: { selected: SavedOutfit | null; title: string; date: string; error: string | null; reminderStatus: string | null; highlightedId?: string; items: PlannedOccasion[]; text: typeof plannerCopy.fr; styles: ReturnType<typeof createStyles>; onTitle: (value: string) => void; onDate: (value: string) => void; onSave: () => void; onRemove: (item: PlannedOccasion) => Promise<void>; onToggleReminder: (item: PlannedOccasion) => Promise<void> }) { const rows = highlightedId ? [...items].sort((left, right) => Number(right.id === highlightedId) - Number(left.id === highlightedId)) : items; return <View style={styles.planner}><Text style={styles.plannerTitle}>{text.title}</Text>{selected ? <><Text style={styles.plannerSelected}>{selected.title}</Text><TextInput value={title} onChangeText={onTitle} placeholder={text.event} placeholderTextColor="#817A72" style={styles.plannerInput} accessibilityLabel={text.event} /><TextInput value={date} onChangeText={onDate} placeholder={text.date} placeholderTextColor="#817A72" style={styles.plannerInput} accessibilityLabel={text.date} keyboardType="numbers-and-punctuation" /><TactileButton accessibilityLabel={text.plan} onPress={onSave} style={styles.plannerButton}><Text style={styles.primaryButtonText}>{text.plan}</Text><MaterialIcons name="event" size={17} color="#0E0C0B" /></TactileButton>{error ? <Text style={styles.plannerError}>{error}</Text> : null}</> : <Text style={styles.plannerEmpty}>{text.choose}</Text>}<Text style={styles.plannedTitle}>{text.planned}</Text>{reminderStatus ? <Text style={styles.plannerStatus}>{reminderStatus}</Text> : null}{rows.length === 0 ? <Text style={styles.plannerEmpty}>{text.noPlanned}</Text> : <><PlannedRow item={rows[0]} highlighted={rows[0]?.id === highlightedId} text={text} styles={styles} onRemove={onRemove} onToggleReminder={onToggleReminder} /><PlannedRow item={rows[1]} highlighted={rows[1]?.id === highlightedId} text={text} styles={styles} onRemove={onRemove} onToggleReminder={onToggleReminder} /></>}</View>; }
function PlannedRow({ item, highlighted = false, text, styles, onRemove, onToggleReminder }: { item: PlannedOccasion | undefined; highlighted?: boolean; text: typeof plannerCopy.fr; styles: ReturnType<typeof createStyles>; onRemove: (item: PlannedOccasion) => Promise<void>; onToggleReminder: (item: PlannedOccasion) => Promise<void> }) { if (!item) return null; const reminderLabel = item.reminderId ? text.disableReminder : text.enableReminder; return <View style={[styles.plannedRow, highlighted && styles.plannedRowHighlighted]}><View style={styles.plannedWords}><Text style={styles.plannedName}>{item.title}</Text><Text style={styles.plannedDate}>{item.date}</Text></View><Pressable accessibilityRole="button" accessibilityLabel={`${reminderLabel} ${item.title}`} onPress={() => void onToggleReminder(item)} style={({ pressed }) => [styles.plannerReminder, pressed && styles.pressed]}><MaterialIcons name={item.reminderId ? "notifications-off" : "notifications-none"} size={15} color="#C89544" /><Text style={styles.plannerReminderText}>{item.reminderId ? text.disableReminder : text.enableReminder}</Text></Pressable><Pressable accessibilityRole="button" accessibilityLabel={`${text.remove} ${item.title}`} onPress={() => void onRemove(item)} style={({ pressed }) => [styles.wardrobeRemove, pressed && styles.pressed]}><MaterialIcons name="close" size={15} color="#E59480" /></Pressable></View>; }
function StrategyComparisonPanel({ strategies, locale, text, styles }: { strategies: import("@/lib/filon-complete").OutfitStrategy[]; locale: "fr" | "nl" | "en"; text: typeof comparisonCopy.fr; styles: ReturnType<typeof createStyles> }) { const comparison = compareOutfitStrategies(strategies); if (comparison.items.length < 2) return null; const safe = comparison.items.find((item) => item.id === "safe"); const signature = comparison.items.find((item) => item.id === "signature"); if (!safe || !signature) return null; return <View style={styles.comparison}><Text style={styles.comparisonTitle}>{text.title}</Text><View style={styles.comparisonGrid}><ComparisonColumn title={text.safe} item={safe} locale={locale} text={text} styles={styles} /><ComparisonColumn title={text.signature} item={signature} locale={locale} text={text} styles={styles} /></View><Text style={styles.comparisonDifference}>{text.difference} · {comparison.totalDifference !== null ? formatFilonPrice(Math.abs(comparison.totalDifference), locale, safe.currency) : "—"} · {text.confidence} : {text.notMeasured}</Text></View>; }
function ComparisonColumn({ title, item, locale, text, styles }: { title: string; item: { total: number; currency: string; confidenceScore: null; pieceCount: number }; locale: "fr" | "nl" | "en"; text: typeof comparisonCopy.fr; styles: ReturnType<typeof createStyles> }) { return <View style={styles.comparisonColumn}><Text style={styles.comparisonName}>{title}</Text><Text style={styles.comparisonValue}>{formatFilonPrice(item.total, locale, item.currency)}</Text><Text style={styles.comparisonLabel}>{text.total}</Text><Text style={styles.comparisonValue}>{text.notMeasured}</Text><Text style={styles.comparisonLabel}>{text.confidence}</Text><Text style={styles.comparisonValue}>{item.pieceCount}</Text><Text style={styles.comparisonLabel}>{text.coverage}</Text></View>; }
function RotationPanel({ suggestions, locale, text, styles, onPlan }: { suggestions: OutfitRotationSuggestion[]; locale: "fr" | "nl" | "en"; text: typeof rotationCopy.fr; styles: ReturnType<typeof createStyles>; onPlan: (suggestion: OutfitRotationSuggestion) => void }) { return <View style={styles.rotation}><Text style={styles.rotationTitle}>{text.title}</Text>{suggestions.length === 0 ? <Text style={styles.rotationEmpty}>{text.empty}</Text> : <><RotationRow suggestion={suggestions[0]} locale={locale} text={text} styles={styles} onPlan={onPlan} /><RotationRow suggestion={suggestions[1]} locale={locale} text={text} styles={styles} onPlan={onPlan} /><RotationRow suggestion={suggestions[2]} locale={locale} text={text} styles={styles} onPlan={onPlan} /></>}</View>; }
function RotationRow({ suggestion, locale, text, styles, onPlan }: { suggestion: OutfitRotationSuggestion | undefined; locale: "fr" | "nl" | "en"; text: typeof rotationCopy.fr; styles: ReturnType<typeof createStyles>; onPlan: (suggestion: OutfitRotationSuggestion) => void }) { if (!suggestion) return null; return <View style={styles.rotationRow}><View style={styles.rotationWords}><Text style={styles.rotationName} numberOfLines={1}>{suggestion.outfit.title}</Text><Text style={styles.rotationReason}>{resolveOutfitPublicMessage(suggestion.reason, locale)}</Text></View><Pressable accessibilityRole="button" accessibilityLabel={`${text.plan} ${suggestion.outfit.title}`} onPress={() => onPlan(suggestion)} style={({ pressed }) => [styles.rotationAction, pressed && styles.pressed]}><Text style={styles.rotationActionText}>{text.plan}</Text></Pressable></View>; }
function DecisionLedgerPanel({ trace, constraints, locale, text, styles }: { trace: import("@/lib/filon-intelligence").RecommendationTrace; constraints: OutfitPublicMessage[]; locale: "fr" | "nl" | "en"; text: typeof ledgerCopy.fr; styles: ReturnType<typeof createStyles> }) { const ledger = buildDecisionLedger(trace, constraints); return <View style={styles.ledger}><Text style={styles.ledgerTitle}>{text.title}</Text><View style={styles.ledgerMetrics}><LedgerMetric value={ledger.catalogue.considered} label={text.reviewed} styles={styles} /><LedgerMetric value={ledger.catalogue.eligible} label={text.eligible} styles={styles} /><LedgerMetric value={ledger.catalogue.nonEligible} label={text.nonEligible} styles={styles} /><LedgerMetric value={ledger.catalogue.unsafe} label={text.unsafe} styles={styles} /></View><Text style={styles.ledgerLabel}>{text.constraints}</Text><Text style={styles.ledgerBody}>{ledger.constraints.map((message) => resolveOutfitPublicMessage(message, locale)).join(" · ")}</Text><Text style={styles.ledgerLabel}>{text.policy}</Text><Text style={styles.ledgerBody}>{ledger.policy.map((message) => resolveOutfitPublicMessage(message, locale)).join(" ")}</Text></View>; }
function LedgerMetric({ value, label, styles }: { value: number; label: string; styles: ReturnType<typeof createStyles> }) { return <View style={styles.ledgerMetric}><Text style={styles.ledgerValue}>{value}</Text><Text style={styles.ledgerMetricLabel}>{label}</Text></View>; }
function DiscoverCapsulesPanel({ capsules, text, styles, onApply }: { capsules: DiscoverCapsule[]; text: typeof capsuleCopy.fr; styles: ReturnType<typeof createStyles>; onApply: (capsule: DiscoverCapsule) => void }) { return <View style={styles.capsules}><Text style={styles.capsulesTitle}>{text.title}</Text><Text style={styles.capsulesNote}>{text.note}</Text><CapsuleRow capsule={capsules[0]} text={text} styles={styles} onApply={onApply} /><CapsuleRow capsule={capsules[1]} text={text} styles={styles} onApply={onApply} /><CapsuleRow capsule={capsules[2]} text={text} styles={styles} onApply={onApply} /></View>; }
function localizeCapsule(capsule: DiscoverCapsule, text: typeof capsuleCopy.fr) {
  if (capsule.id === "minimal-work") return { title: text.minimalWorkTitle, description: text.minimalWorkDescription };
  if (capsule.id === "minimal-evening") return { title: text.minimalEveningTitle, description: text.minimalEveningDescription };
  if (capsule.id === "classic-wedding") return { title: text.classicWeddingTitle, description: text.classicWeddingDescription };
  if (capsule.id === "classic-work") return { title: text.classicWorkTitle, description: text.classicWorkDescription };
  if (capsule.id === "bold-evening") return { title: text.boldEveningTitle, description: text.boldEveningDescription };
  if (capsule.id === "bold-wedding") return { title: text.boldWeddingTitle, description: text.boldWeddingDescription };
  return { title: text.title, description: text.note };
}
function CapsuleRow({ capsule, text, styles, onApply }: { capsule: DiscoverCapsule | undefined; text: typeof capsuleCopy.fr; styles: ReturnType<typeof createStyles>; onApply: (capsule: DiscoverCapsule) => void }) { if (!capsule) return null; const localized = localizeCapsule(capsule, text); return <View style={styles.capsuleRow}><View style={styles.capsuleWords}><Text style={styles.capsuleTitle}>{localized.title}</Text><Text style={styles.capsuleDescription}>{localized.description}</Text></View><Pressable accessibilityRole="button" accessibilityLabel={`${text.use} ${localized.title}`} onPress={() => onApply(capsule)} style={({ pressed }) => [styles.capsuleAction, pressed && styles.pressed]}><Text style={styles.capsuleActionText}>{text.use}</Text><MaterialIcons name="arrow-forward" size={14} color="#C89544" /></Pressable></View>; }
function BudgetPanel({ spent, budget, currency, locale, text, styles }: { spent: number; budget: number | null; currency: string; locale: "fr" | "nl" | "en"; text: typeof budgetCopy.fr; styles: ReturnType<typeof createStyles> }) { const summary = calculateBudget(spent, budget); const message = summary.status === "no_budget" ? text.noBudget : summary.status === "under" ? text.under : summary.status === "near_limit" ? text.near : text.over; return <View style={styles.budgetPanel}><View style={styles.budgetTop}><Text style={styles.budgetTitle}>{text.title}</Text><Text style={styles.budgetStatus}>{message}</Text></View><View style={styles.budgetMetrics}><View><Text style={styles.budgetValue}>{formatFilonPrice(summary.spent, locale, currency)}</Text><Text style={styles.budgetLabel}>{text.spent}</Text></View>{summary.remaining !== null ? <View><Text style={styles.budgetValue}>{formatFilonPrice(Math.abs(summary.remaining), locale, currency)}</Text><Text style={styles.budgetLabel}>{summary.remaining >= 0 ? text.remaining : text.over}</Text></View> : null}</View>{summary.ratio !== null ? <View style={styles.budgetTrack}><View style={[styles.budgetFill, { width: `${Math.min(100, Math.round(summary.ratio * 100))}%` }]} /></View> : null}</View>; }

const localStyles = StyleSheet.create({ sectionLabel: { color: "#A9A197", fontSize: 11, fontWeight: "800", letterSpacing: 0.6, textTransform: "uppercase", marginTop: 18, marginBottom: 9 } });
function createStyles(colors: ReturnType<typeof useColors>): Record<string, any> {
  const defined = StyleSheet.create({
    content: { padding: 20, paddingBottom: 42 },
    topbar: { minHeight: 44, flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 14 },
    lookbookButton: { minHeight: 36, paddingHorizontal: 8, flexDirection: "row", alignItems: "center", gap: 4, borderRadius: 11, backgroundColor: `${colors.primary}18` },
    lookbookText: { color: colors.primary, fontSize: 10, fontWeight: "900" },
    back: { minHeight: 44, flexDirection: "row", gap: 8, paddingHorizontal: 10, borderRadius: 14, backgroundColor: colors.surface },
    backText: { color: colors.foreground, fontSize: 14, fontWeight: "700" },
    live: { flexDirection: "row", alignItems: "center", gap: 6 },
    liveDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.primary },
    liveText: { color: colors.muted, fontSize: 10, fontWeight: "900", letterSpacing: 0.8 },
    hero: { minHeight: 176, padding: 20, borderRadius: 26, overflow: "hidden", backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, justifyContent: "flex-end" },
    eyebrow: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.65, textTransform: "uppercase", marginBottom: 10 },
    title: { color: colors.foreground, maxWidth: 294, fontSize: 24, lineHeight: 30, fontWeight: "800", letterSpacing: -0.6 },
    orbit: { position: "absolute", top: -78, right: -38, width: 192, height: 192, borderRadius: 96, borderWidth: 1, borderColor: `${colors.primary}66` },
    spark: { position: "absolute", top: 54, right: 55, width: 8, height: 8, borderRadius: 2, backgroundColor: colors.primary },
    modeRow: { flexDirection: "row", gap: 8, marginTop: 14 },
    composer: { marginTop: 14, padding: 10, gap: 9, borderRadius: 20, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    input: { minHeight: 74, paddingHorizontal: 7, paddingTop: 7, color: colors.foreground, fontSize: 15, lineHeight: 21 },
    budgetInput: { height: 44, paddingHorizontal: 12, color: colors.foreground, fontSize: 14, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    ownedPanel: { marginTop: 14, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    ownedTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" },
    ownedInput: { minHeight: 46, marginTop: 9, paddingHorizontal: 12, color: colors.foreground, fontSize: 14, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    ownedCaption: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 7 },
    wardrobeSave: { minHeight: 38, marginTop: 12, paddingHorizontal: 10, alignSelf: "flex-start", flexDirection: "row", alignItems: "center", gap: 5, borderRadius: 11, backgroundColor: `${colors.primary}18` },
    wardrobeSaveText: { color: colors.primary, fontSize: 11, fontWeight: "900" },
    wardrobePanel: { marginTop: 14, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    wardrobeTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" },
    wardrobeEmpty: { color: colors.muted, fontSize: 11, lineHeight: 16, marginTop: 6 },
    wardrobeRow: { minHeight: 44, marginTop: 9, paddingLeft: 9, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    wardrobeSelect: { flex: 1, minHeight: 42, flexDirection: "row", alignItems: "center", gap: 8 },
    wardrobeItemName: { flex: 1, color: colors.foreground, fontSize: 12, fontWeight: "800" },
    wardrobeRemove: { minHeight: 42, width: 38, alignItems: "center", justifyContent: "center" },
    journalPanel: { marginTop: 18, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    journalTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" },
    journalEmpty: { color: colors.muted, fontSize: 11, lineHeight: 16, marginTop: 6 },
    journalRow: { minHeight: 48, marginTop: 9, paddingLeft: 10, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    journalWords: { flex: 1 },
    journalItemTitle: { color: colors.foreground, fontSize: 12, fontWeight: "800" },
    journalMeta: { color: colors.muted, fontSize: 10, marginTop: 3 },
    journalSave: { minHeight: 40, marginTop: 14, paddingHorizontal: 10, alignSelf: "flex-start", flexDirection: "row", gap: 6, alignItems: "center", borderRadius: 11, backgroundColor: `${colors.primary}18` },
    journalSaveText: { color: colors.primary, fontSize: 11, fontWeight: "900" },
    ledger: { marginTop: 12, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    ledgerTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" },
    ledgerMetrics: { flexDirection: "row", gap: 6, marginTop: 10 },
    ledgerMetric: { flex: 1, minHeight: 48, padding: 7, borderRadius: 10, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    ledgerValue: { color: colors.primary, fontSize: 15, fontWeight: "900" },
    ledgerMetricLabel: { color: colors.muted, fontSize: 8, lineHeight: 11, marginTop: 2 },
    ledgerLabel: { color: colors.foreground, fontSize: 10, fontWeight: "900", marginTop: 12, textTransform: "uppercase" },
    ledgerBody: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 4 },
    capsules: { marginTop: 18, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    capsulesTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" },
    capsulesNote: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 5 },
    capsuleRow: { minHeight: 62, marginTop: 9, padding: 10, flexDirection: "row", alignItems: "center", gap: 8, borderRadius: 13, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    capsuleWords: { flex: 1 },
    capsuleTitle: { color: colors.foreground, fontSize: 12, fontWeight: "900" },
    capsuleDescription: { color: colors.muted, fontSize: 10, lineHeight: 14, marginTop: 3 },
    capsuleAction: { minHeight: 34, paddingHorizontal: 8, flexDirection: "row", alignItems: "center", gap: 3, borderRadius: 10, backgroundColor: `${colors.primary}18` },
    capsuleActionText: { color: colors.primary, fontSize: 10, fontWeight: "900" },
    budgetPanel: { marginTop: 12, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    budgetTop: { flexDirection: "row", justifyContent: "space-between", gap: 10 },
    budgetTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" },
    budgetStatus: { color: colors.primary, flex: 1, fontSize: 10, fontWeight: "800", textAlign: "right" },
    budgetMetrics: { flexDirection: "row", justifyContent: "space-between", gap: 12, marginTop: 10 },
    budgetValue: { color: colors.foreground, fontSize: 16, fontWeight: "900" },
    budgetLabel: { color: colors.muted, fontSize: 10, marginTop: 2 },
    budgetTrack: { height: 5, marginTop: 12, overflow: "hidden", borderRadius: 3, backgroundColor: colors.background },
    budgetFill: { height: "100%", borderRadius: 3, backgroundColor: colors.primary },
    planner: { marginTop: 18, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    plannerTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" },
    plannerSelected: { color: colors.primary, fontSize: 11, fontWeight: "800", marginTop: 7 },
    plannerInput: { minHeight: 42, marginTop: 8, paddingHorizontal: 10, color: colors.foreground, fontSize: 12, borderRadius: 11, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    plannerButton: { minHeight: 44, marginTop: 10, paddingHorizontal: 12, flexDirection: "row", justifyContent: "space-between", alignItems: "center", borderRadius: 12, backgroundColor: colors.primary },
    plannerError: { color: "#E59480", fontSize: 10, lineHeight: 14, marginTop: 7 },
    plannerEmpty: { color: colors.muted, fontSize: 11, lineHeight: 16, marginTop: 7 },
    plannedTitle: { color: colors.foreground, fontSize: 11, fontWeight: "900", marginTop: 14, textTransform: "uppercase" },
    plannedRow: { minHeight: 46, marginTop: 8, paddingLeft: 10, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    plannedRowHighlighted: { borderColor: colors.primary, backgroundColor: `${colors.primary}12` },
    plannedWords: { flex: 1 },
    plannedName: { color: colors.foreground, fontSize: 12, fontWeight: "800" },
    plannedDate: { color: colors.muted, fontSize: 10, marginTop: 2 },
    plannerStatus: { color: colors.primary, fontSize: 10, lineHeight: 14, marginTop: 7 },
    plannerReminder: { minHeight: 42, maxWidth: 106, paddingHorizontal: 7, flexDirection: "row", alignItems: "center", gap: 4 },
    plannerReminderText: { color: colors.primary, flexShrink: 1, fontSize: 9, lineHeight: 12, fontWeight: "900" },
    comparison: { marginTop: 12, padding: 13, borderRadius: 16, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    comparisonTitle: { color: colors.foreground, fontSize: 12, fontWeight: "900" },
    comparisonGrid: { flexDirection: "row", gap: 8, marginTop: 9 },
    comparisonColumn: { flex: 1, padding: 10, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    comparisonName: { color: colors.primary, fontSize: 11, fontWeight: "900" },
    comparisonValue: { color: colors.foreground, fontSize: 13, fontWeight: "900", marginTop: 6 },
    comparisonLabel: { color: colors.muted, fontSize: 9, marginTop: 1 },
    comparisonDifference: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 10 },
    rotation: { marginTop: 18, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    rotationTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" },
    rotationEmpty: { color: colors.muted, fontSize: 11, lineHeight: 16, marginTop: 7 },
    rotationRow: { minHeight: 58, marginTop: 8, padding: 9, flexDirection: "row", alignItems: "center", gap: 8, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    rotationWords: { flex: 1 },
    rotationName: { color: colors.foreground, fontSize: 12, fontWeight: "900" },
    rotationReason: { color: colors.muted, fontSize: 9, lineHeight: 13, marginTop: 3 },
    rotationAction: { minHeight: 34, paddingHorizontal: 8, justifyContent: "center", borderRadius: 10, backgroundColor: `${colors.primary}18` },
    rotationActionText: { color: colors.primary, fontSize: 10, fontWeight: "900" },
    optimize: { marginTop: 18, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: `${colors.primary}55` },
    optimizeTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" },
    optimizeEmpty: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 7 },
    optimizeRow: { minHeight: 46, marginTop: 8, paddingLeft: 10, flexDirection: "row", alignItems: "center", gap: 8, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    optimizeName: { color: colors.foreground, flex: 1, fontSize: 11, fontWeight: "800" },
    optimizeAction: { minHeight: 42, minWidth: 92, paddingHorizontal: 9, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4 },
    optimizeActionText: { color: colors.primary, fontSize: 10, fontWeight: "900" },
    optimizeResult: { marginTop: 9, padding: 10, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: `${colors.primary}55` },
    optimizeSaving: { color: colors.primary, fontSize: 11, fontWeight: "900" },
    optimizeTotal: { color: colors.foreground, fontSize: 12, fontWeight: "900", marginTop: 4 },
    optimizeReplacement: { color: colors.muted, fontSize: 10, lineHeight: 14, marginTop: 6 },
    optimizeNote: { color: colors.muted, fontSize: 9, lineHeight: 13, marginTop: 8 },
    chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
    choice: { minHeight: 40, justifyContent: "center", paddingHorizontal: 13, borderRadius: 13, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    choiceActive: { backgroundColor: `${colors.primary}22`, borderColor: `${colors.primary}88` },
    choiceText: { color: colors.muted, fontSize: 12, fontWeight: "800" },
    choiceTextActive: { color: colors.primary },
    preferenceHeader: { flexDirection: "row", alignItems: "flex-end", justifyContent: "space-between" },
    reset: { minHeight: 32, justifyContent: "center", paddingHorizontal: 5 },
    resetText: { color: colors.primary, fontSize: 12, fontWeight: "800" },
    primaryButton: { minHeight: 58, marginTop: 22, paddingHorizontal: 18, flexDirection: "row", justifyContent: "space-between", borderRadius: 18, backgroundColor: colors.primary },
    primaryButtonText: { color: colors.background, fontSize: 15, fontWeight: "900" },
    disabledButton: { opacity: 0.38 },
    dnaPanel: { marginTop: 18, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: `${colors.primary}55` },
    dnaTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
    dnaTitle: { color: colors.foreground, fontSize: 14, fontWeight: "900" },
    dnaSource: { color: colors.muted, fontSize: 10, marginTop: 3 },
    dnaConfidence: { minWidth: 46, alignItems: "center", padding: 7, borderRadius: 12, backgroundColor: `${colors.success}18` },
    dnaConfidenceValue: { color: colors.success, fontSize: 16, fontWeight: "900" },
    dnaConfidenceCaption: { color: colors.success, fontSize: 9, fontWeight: "800" },
    discoverTitle: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.6, textTransform: "uppercase", marginTop: 16, marginBottom: 8 },
    discoverCard: { minHeight: 58, padding: 10, marginTop: 7, flexDirection: "row", alignItems: "center", gap: 9, borderRadius: 14, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    discoverWords: { flex: 1 },
    discoverName: { color: colors.foreground, fontSize: 12, fontWeight: "900" },
    discoverDescription: { color: colors.muted, fontSize: 10, lineHeight: 14, marginTop: 2 },
    discoverAction: { minHeight: 34, justifyContent: "center", paddingHorizontal: 10, borderRadius: 10, backgroundColor: `${colors.primary}20` },
    discoverActionText: { color: colors.primary, fontSize: 10, fontWeight: "900" },
    recreatePanel: { marginTop: 14, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: `${colors.primary}55` },
    recreateGuidance: { color: colors.muted, fontSize: 11, lineHeight: 16 },
    recreateInput: { minHeight: 46, marginTop: 11, paddingHorizontal: 12, color: colors.foreground, fontSize: 13, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    recreatePicker: { minHeight: 42, marginTop: 9, paddingHorizontal: 11, alignSelf: "flex-start", flexDirection: "row", alignItems: "center", gap: 6, borderRadius: 11, backgroundColor: `${colors.primary}18` },
    recreatePickerText: { color: colors.primary, fontSize: 11, fontWeight: "900" },
    recreatePreview: { width: "100%", height: 134, marginTop: 10, borderRadius: 12, backgroundColor: colors.background },
    recreatePrivacy: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 9 },
    recreateButton: { minHeight: 48, marginTop: 11, paddingHorizontal: 14, flexDirection: "row", justifyContent: "space-between", alignItems: "center", borderRadius: 14, backgroundColor: colors.primary },
    recreateResult: { marginTop: 16, padding: 15, borderRadius: 19, backgroundColor: colors.surface, borderWidth: 1, borderColor: `${colors.primary}66` },
    recreateResultTitle: { color: colors.primary, fontSize: 11, fontWeight: "900", textTransform: "uppercase", letterSpacing: 0.6 },
    recreateSummary: { color: colors.foreground, fontSize: 14, lineHeight: 20, fontWeight: "700", marginTop: 7 },
    observation: { marginTop: 12, padding: 10, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    observationTop: { flexDirection: "row", justifyContent: "space-between", gap: 8 },
    observationTitle: { color: colors.muted, fontSize: 10, fontWeight: "800", textTransform: "uppercase" },
    observationConfidence: { color: colors.primary, fontSize: 10, fontWeight: "900" },
    observationLabel: { color: colors.foreground, fontSize: 12, fontWeight: "900", marginTop: 4 },
    observationExplanation: { color: colors.muted, fontSize: 10, lineHeight: 14, marginTop: 3 },
    recreateLimitsTitle: { color: colors.foreground, fontSize: 12, fontWeight: "900", marginTop: 14 },
    recreateLimits: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 4 },
    solution: { marginTop: 16, padding: 17, borderRadius: 20, backgroundColor: colors.surface, borderWidth: 1, borderColor: `${colors.primary}66` },
    correction: { marginTop: 12, padding: 13, borderRadius: 17, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    correctionTitle: { color: colors.foreground, fontSize: 12, fontWeight: "900" },
    correctionPrompt: { color: colors.muted, fontSize: 10, lineHeight: 14, marginTop: 4 },
    correctionChoices: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 9 },
    correctionInput: { minHeight: 40, marginTop: 9, paddingHorizontal: 10, color: colors.foreground, fontSize: 11, borderRadius: 11, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border },
    correctionAction: { minHeight: 38, marginTop: 9, paddingHorizontal: 10, alignSelf: "flex-start", justifyContent: "center", borderRadius: 11, backgroundColor: `${colors.primary}18` },
    correctionActionText: { color: colors.primary, fontSize: 10, fontWeight: "900" },
    correctionSaved: { color: colors.success, fontSize: 10, marginTop: 7 },
    piece: { minHeight: 130, padding: 12, marginTop: 12, flexDirection: "row", alignItems: "center", gap: 12, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    pieceImage: { width: 78, height: 102, borderRadius: 13, backgroundColor: colors.background },
    pieceImageFallback: { width: 78, height: 102, borderRadius: 13, justifyContent: "center", alignItems: "center", backgroundColor: colors.background },
    footerSpace: { height: 26 },
    pressed: { opacity: 0.74, transform: [{ scale: 0.985 }] },
  });
  return new Proxy(defined, { get: (target, property) => (typeof property === "string" && property in target ? target[property as keyof typeof target] : {}) }) as Record<string, any>;
} /*
  content: { padding: 20, paddingBottom: 42 }, topbar: { minHeight: 44, flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }, back: { minHeight: 44, flexDirection: "row", gap: 8, paddingHorizontal: 10, borderRadius: 14, backgroundColor: colors.surface }, backText: { color: colors.foreground, fontSize: 14, fontWeight: "700" }, live: { flexDirection: "row", alignItems: "center", gap: 6 }, liveDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: "#8FB072" }, liveText: { color: colors.muted, fontSize: 10, fontWeight: "900", letterSpacing: 0.8 }, hero: { minHeight: 176, padding: 20, borderRadius: 26, overflow: "hidden", backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, justifyContent: "flex-end" }, modeRow: { flexDirection: "row", gap: 8, marginTop: 14 }, ownedPanel: { marginTop: 14, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, ownedTitle: { color: colors.foreground, fontSize: 13, fontWeight: "900" }, ownedInput: { minHeight: 46, marginTop: 9, paddingHorizontal: 12, color: colors.foreground, fontSize: 14, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border }, ownedCaption: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: 7 }, eyebrow: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.65, textTransform: "uppercase", marginBottom: 10 }, title: { color: colors.foreground, maxWidth: 294, fontSize: 24, lineHeight: 30, fontWeight: "800", letterSpacing: -0.6 }, orbit: { position: "absolute", top: -78, right: -38, width: 192, height: 192, borderRadius: 96, borderWidth: 1, borderColor: `${colors.primary}66` }, spark: { position: 
*/
