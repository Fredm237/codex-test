import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Image } from "expo-image";
import { router, useLocalSearchParams } from "expo-router";
import { ActivityIndicator, Modal, Pressable, ScrollView, Share, StyleSheet, Text, View } from "react-native";

import { TactileButton } from "@/components/filon/filon-ui";
import { DataReveal } from "@/components/filon/data-motion";
import { LivingSurface } from "@/components/filon/living-surface";
import { ScreenContainer } from "@/components/screen-container";
import { useColors } from "@/hooks/use-colors";
import { useFavorites } from "@/hooks/use-favorites";
import { useFilonOfferDetail } from "@/hooks/use-filon-offer-detail";
import { currentFilonStock, formatFilonPrice, isFilonOfferActionable, isFilonOfferPriceCurrent, normalizeFilonCurrency, normalizeFilonObservedAt, type FilonOffer } from "@/lib/filon-api";
import { selectVerifiedDetailOffer } from "@/lib/filon-offer-evidence";
import { useLocale } from "@/lib/locale";
import { openPartnerOffer } from "@/lib/open-partner-offer";
import { isSafePartnerOfferUrl } from "@/lib/partner-offer";
import { usePurchaseIntents } from "@/hooks/use-purchase-intents";
import { useIntentOfferEvidence } from "@/hooks/use-intent-offer-evidence";
import { haptic } from "@/lib/haptics";
import { useState } from "react";
import { recordIntentDecision } from "@/lib/intent-decision-journal";
import { useFilonEvidenceNow } from "@/hooks/use-filon-evidence-now";

const copy = {
  fr: { back: "Retour", source: "Offre indexée dans le catalogue FILON", sourceUnknown: "Provenance catalogue non confirmée", availability: "Disponibilité", available: "En stock", unavailable: "Indisponible", unknown: "Stock non renseigné", buy: "Continuer chez", unavailableLink: "Achat indisponible : prix positif, devise prise en charge, stock disponible, lien sûr et relevé de moins de 72 h sont requis.", checking: "Contrôle des faits de l’offre…", note: "Le prix et le stock ne sont considérés actuels que si le relevé affiché date de moins de 72 h. Le marchand confirme la livraison et les conditions.", noImage: "Aucune image disponible", save: "Enregistrer", watching: "Suivi activé", alert: "Créer une alerte", share: "Partager l’offre", priceAt: "Prix transmis par", observed: "Prix relevé", priceUnknown: "Prix non confirmé", fresh: "Relevé récent", stale: "Relevé absent ou ancien", observedAt: "Relevé le", linkIntent: "Lier à une intention", chooseIntent: "Choisir une intention", noIntent: "Créez d’abord une intention pour relier cette offre." },
  nl: { back: "Terug", source: "Aanbieding in de FILON-catalogus", sourceUnknown: "Catalogusherkomst niet bevestigd", availability: "Beschikbaarheid", available: "Op voorraad", unavailable: "Niet beschikbaar", unknown: "Voorraad niet opgegeven", buy: "Verder bij", unavailableLink: "Aankoop niet beschikbaar: een positieve prijs, ondersteunde valuta, beschikbare voorraad, veilige link en meting van minder dan 72 uur oud zijn vereist.", checking: "Aanbiedingsfeiten controleren…", note: "Prijs en voorraad gelden alleen als actueel wanneer de getoonde meting minder dan 72 uur oud is. De handelaar bevestigt levering en voorwaarden.", noImage: "Geen afbeelding beschikbaar", save: "Bewaren", watching: "Volgen actief", alert: "Waarschuwing maken", share: "Aanbieding delen", priceAt: "Prijs aangeleverd door", observed: "Gemeten prijs", priceUnknown: "Prijs niet bevestigd", fresh: "Recente meting", stale: "Meting ontbreekt of is verouderd", observedAt: "Gemeten op", linkIntent: "Aan intentie koppelen", chooseIntent: "Kies een intentie", noIntent: "Maak eerst een intentie om dit aanbod te koppelen." },
  en: { back: "Back", source: "Offer indexed in the FILON catalogue", sourceUnknown: "Catalogue provenance not confirmed", availability: "Availability", available: "In stock", unavailable: "Unavailable", unknown: "Stock not provided", buy: "Continue to", unavailableLink: "Purchase unavailable: a positive price, supported currency, available stock, safe link and observation from the last 72 hours are required.", checking: "Checking offer facts…", note: "Price and stock are treated as current only when the displayed observation is less than 72 hours old. The merchant confirms delivery and terms.", noImage: "No image available", save: "Save", watching: "Watching", alert: "Create alert", share: "Share offer", priceAt: "Price supplied by", observed: "Observed price", priceUnknown: "Price not confirmed", fresh: "Recent observation", stale: "Observation missing or stale", observedAt: "Observed on", linkIntent: "Link to an intent", chooseIntent: "Choose an intent", noIntent: "Create an intent first to link this offer." },
};

export default function ProductScreen() {
  const params = useLocalSearchParams<ProductParams>();
  const { locale } = useLocale();
  const text = copy[locale];
  const colors = useColors();
  const styles = createStyles(colors);
  const favorites = useFavorites();
  const intents = usePurchaseIntents();
  const evidence = useIntentOfferEvidence();
  const [intentPickerOpen, setIntentPickerOpen] = useState(false);
  const parsedOfferId = Number(params.id);
  const offerId = Number.isInteger(parsedOfferId) && parsedOfferId > 0 ? parsedOfferId : undefined;
  const routedHint = offerFromParams(params);
  const detail = useFilonOfferDetail(offerId);
  const detailedOffer = detail.data?.offer ?? null;
  const evidenceNow = useFilonEvidenceNow([detailedOffer?.observedAt]);
  // Les paramètres routés peuvent provenir d'un lien profond externe. Ils
  // restent des indices visuels; seule une réponse Core actuelle, sûre et
  // rapprochée peut autoriser une action.
  const trustedOffer = selectVerifiedDetailOffer(params, detailedOffer, evidenceNow);
  const availability = detailedOffer ? currentFilonStock(detailedOffer, evidenceNow) : null;
  const actionable = trustedOffer !== null && isFilonOfferActionable(trustedOffer, evidenceNow);
  const freshObservation = detailedOffer !== null && isFilonOfferPriceCurrent(detailedOffer, evidenceNow);
  const merchantLink = actionable && trustedOffer && isSafePartnerOfferUrl(trustedOffer.link) ? trustedOffer.link : null;
  const name = detailedOffer?.name ?? routedHint?.name ?? cleanText(params.name) ?? "FILON";
  const category = detailedOffer?.category ?? routedHint?.category ?? cleanText(params.category);
  // Une URL d'image issue d'un deep link ne doit pas déclencher de requête
  // locale ou distante avant validation du détail catalogue.
  const imageUrl = detailedOffer?.imageUrl ?? null;
  const merchant = detailedOffer?.merchantName ?? null;
  const displayedPrice = freshObservation && detailedOffer ? formatFilonPrice(detailedOffer.price, locale, detailedOffer.currency) : "—";
  const observedAt = detailedOffer?.observedAt ? new Intl.DateTimeFormat(locale === "en" ? "en-BE" : `${locale}-BE`, { dateStyle: "medium", timeStyle: "short" }).format(new Date(detailedOffer.observedAt)) : null;
  const canStore = trustedOffer !== null;
  const canLinkIntent = actionable && merchantLink !== null;
  const saved = trustedOffer !== null && favorites.isSaved(trustedOffer.id);
  const readAuthoritativeOffer = () => selectVerifiedDetailOffer(params, detail.data?.offer ?? null, Date.now());
  const openMerchant = () => { const currentOffer = readAuthoritativeOffer(); if (currentOffer && isFilonOfferActionable(currentOffer) && isSafePartnerOfferUrl(currentOffer.link)) void openPartnerOffer(currentOffer.link); };
  const shareOffer = () => { const currentOffer = readAuthoritativeOffer(); if (!currentOffer) return; const priceFact = formatFilonPrice(currentOffer.price, locale, currentOffer.currency); const facts = ` — ${priceFact} · ${currentOffer.merchantName}`; void Share.share({ title: currentOffer.name, message: `${currentOffer.name}${facts}` }); };
  const toggleSaved = () => { const currentOffer = readAuthoritativeOffer(); if (!currentOffer) return; void favorites.toggle({ id: currentOffer.id, name: currentOffer.name, price: currentOffer.price, currency: currentOffer.currency, imageUrl: currentOffer.imageUrl, merchantName: currentOffer.merchantName, link: currentOffer.link, inStock: currentOffer.inStock, observedAt: currentOffer.observedAt ?? null, evidenceCurrent: currentOffer.evidenceCurrent === true, category: currentOffer.category }); };
  const createAlert = () => { const currentOffer = readAuthoritativeOffer(); if (!currentOffer) return; router.push({ pathname: "/alert/new", params: { id: String(currentOffer.id), name: currentOffer.name, price: String(currentOffer.price), currency: currentOffer.currency, observedAt: currentOffer.observedAt ?? "", evidenceCurrent: currentOffer.evidenceCurrent === true ? "1" : "0" } } as never); };
  const linkIntent = async (intentId: string) => { const currentOffer = readAuthoritativeOffer(); if (!currentOffer || !isFilonOfferActionable(currentOffer) || !isSafePartnerOfferUrl(currentOffer.link)) return; await evidence.link({ intentId, offerId: currentOffer.id, name: currentOffer.name, price: currentOffer.price, currency: currentOffer.currency, merchantName: currentOffer.merchantName, link: currentOffer.link, imageUrl: currentOffer.imageUrl, inStock: true, observedAt: currentOffer.observedAt ?? null, evidenceCurrent: currentOffer.evidenceCurrent === true, linkedAt: new Date().toISOString() }); await recordIntentDecision(intentId, "offer-linked", currentOffer.name); haptic.success(); setIntentPickerOpen(false); };
  return (
    <ScreenContainer className="" containerClassName="bg-background" edges={["top", "left", "right", "bottom"]}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <DataReveal><View style={styles.topbar}><TactileButton accessibilityLabel={text.back} onPress={() => router.back()} style={styles.back}><MaterialIcons name="arrow-back" size={20} color={colors.foreground} /><Text style={styles.backText}>{text.back}</Text></TactileButton><TactileButton accessibilityLabel={text.share} onPress={shareOffer} disabled={!trustedOffer} style={[styles.share, !trustedOffer && styles.actionDisabled]}><MaterialIcons name="ios-share" size={19} color={colors.primary} /></TactileButton></View></DataReveal>
        <DataReveal index={1}><View style={styles.imageShell}><LivingSurface variant="catalogue" style={styles.imageMotion} />{imageUrl ? <Image source={{ uri: imageUrl }} style={styles.image} contentFit="contain" transition={180} /> : <View style={styles.imageFallback}><MaterialIcons name="image-not-supported" size={30} color={colors.primary} /><Text style={styles.imageFallbackText}>{text.noImage}</Text></View>}</View></DataReveal>
        <DataReveal index={2}><View style={styles.eyebrow}><View style={[styles.dot, { backgroundColor: detailedOffer ? colors.primary : colors.warning }]} /><Text style={[styles.eyebrowText, { color: detailedOffer ? colors.primary : colors.warning }]}>{detailedOffer ? text.source : text.sourceUnknown}</Text></View><Text style={styles.name}>{name}</Text>{category ? <Text style={styles.category}>{category}</Text> : null}</DataReveal>
        <DataReveal index={3}><View style={styles.pricePanel}><View><Text style={[styles.priceLabel, !freshObservation && { color: colors.warning }]}>{freshObservation ? text.observed : text.priceUnknown}</Text><Text style={styles.price}>{displayedPrice}</Text>{merchant ? <View style={styles.merchantProof}><MaterialIcons name="storefront" size={13} color={colors.primary} /><Text style={styles.merchantProofText}>{text.priceAt} {merchant}</Text></View> : null}{observedAt && freshObservation ? <Text style={styles.observedAt}>{text.observedAt} {observedAt}</Text> : <Text style={[styles.observedAt, { color: colors.warning }]}>{text.priceUnknown} · {text.stale}</Text>}</View><View style={styles.proofRight}><View style={styles.sourceProof}><MaterialIcons name="schedule" size={14} color={freshObservation ? colors.success : colors.warning} /><Text style={[styles.sourceProofText, { color: freshObservation ? colors.success : colors.warning }]}>{freshObservation ? text.fresh : text.stale}</Text></View><View style={[styles.stock, availability === false ? styles.stockUnavailable : availability === null ? styles.stockUnknown : null]}><Text style={[styles.stockText, availability === false ? styles.stockTextUnavailable : availability === null ? styles.stockTextUnknown : null]}>{availability === true ? text.available : availability === false ? text.unavailable : text.unknown}</Text></View></View></View></DataReveal>
        <DataReveal index={4}><View style={styles.followActions}><TactileButton hapticFeedback={false} accessibilityLabel={text.save} onPress={toggleSaved} disabled={!canStore} style={[styles.followAction, saved && styles.followActionActive, !canStore && styles.actionDisabled]}><MaterialIcons name={saved ? "bookmark" : "bookmark-border"} size={19} color={saved ? colors.background : colors.primary} /><Text style={[styles.followActionText, saved && styles.followActionTextActive]}>{saved ? text.watching : text.save}</Text></TactileButton><TactileButton accessibilityLabel={text.alert} onPress={createAlert} disabled={!canStore} style={[styles.followAction, !canStore && styles.actionDisabled]}><MaterialIcons name="notifications-none" size={19} color={colors.primary} /><Text style={styles.followActionText}>{text.alert}</Text></TactileButton></View><TactileButton accessibilityLabel={text.linkIntent} onPress={() => setIntentPickerOpen(true)} disabled={!canLinkIntent} style={[styles.intentAction, !canLinkIntent && styles.actionDisabled]}><MaterialIcons name="track-changes" size={18} color={colors.primary} /><Text style={styles.intentActionText}>{text.linkIntent}</Text></TactileButton></DataReveal>
        <View style={styles.divider} />
        <Text style={styles.availability}>{text.availability}</Text><Text style={styles.note}>{text.note}</Text>
      </ScrollView>
      <DataReveal index={5} style={styles.footer}>{merchantLink && trustedOffer && merchant ? <TactileButton accessibilityLabel={`${text.buy} ${merchant}`} onPress={openMerchant} style={styles.buy}><View style={styles.buyWords}><Text style={styles.buyCaption}>{formatFilonPrice(trustedOffer.price, locale, trustedOffer.currency)}</Text><Text style={styles.buyText}>{text.buy} {merchant}</Text></View><MaterialIcons name="open-in-new" size={18} color={colors.background} /></TactileButton> : detail.isLoading ? <View style={styles.linkUnavailable}><ActivityIndicator color={colors.primary} /><Text style={[styles.linkUnavailableText, { color: colors.muted }]}>{text.checking}</Text></View> : <View style={styles.linkUnavailable}><MaterialIcons name="lock-outline" size={18} color={colors.error} /><Text style={styles.linkUnavailableText}>{text.unavailableLink}</Text></View>}</DataReveal>
      <Modal visible={intentPickerOpen} transparent animationType="slide" onRequestClose={() => setIntentPickerOpen(false)}><View style={styles.scrim}><Pressable style={StyleSheet.absoluteFill} onPress={() => setIntentPickerOpen(false)} /><View style={styles.intentSheet}><View style={styles.grabber} /><Text style={styles.intentSheetTitle}>{text.chooseIntent}</Text>{intents.ready && intents.items.length === 0 ? <Text style={styles.intentSheetEmpty}>{text.noIntent}</Text> : intents.items.map((intent) => <Pressable key={intent.id} accessibilityRole="button" accessibilityLabel={`${text.linkIntent}: ${intent.need}`} onPress={() => void linkIntent(intent.id)} style={({ pressed }) => [styles.intentChoice, pressed && styles.pressed]}><View style={styles.intentChoiceIcon}><MaterialIcons name="track-changes" size={18} color={colors.primary} /></View><Text style={styles.intentChoiceText}>{intent.need}</Text><MaterialIcons name="arrow-forward" size={18} color={colors.primary} /></Pressable>)}</View></View></Modal>
    </ScreenContainer>
  );
}

type ProductParams = { id?: string; name?: string; price?: string; currency?: string; merchant?: string; image?: string; link?: string; stock?: string; observedAt?: string; observed_at?: string; evidenceCurrent?: string; category?: string };

function cleanText(value: string | undefined) {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null;
}

function offerFromParams(params: ProductParams): FilonOffer | null {
  const id = Number(params.id);
  const price = Number(params.price);
  const currency = normalizeFilonCurrency(params.currency);
  const name = cleanText(params.name);
  const merchantName = cleanText(params.merchant);
  if (!Number.isInteger(id) || id <= 0 || !Number.isFinite(price) || price <= 0 || currency === null || name === null || merchantName === null) return null;
  return {
    id,
    name,
    brand: null,
    category: cleanText(params.category),
    price,
    currency,
    inStock: params.stock === "1" ? true : params.stock === "0" ? false : null,
    observedAt: normalizeFilonObservedAt(params.observedAt ?? params.observed_at),
    evidenceCurrent: params.evidenceCurrent === "1",
    imageUrl: cleanText(params.image),
    merchantName,
    merchantSlug: null,
    link: cleanText(params.link) ?? "",
  };
}

function createStyles(colors: ReturnType<typeof useColors>) { return StyleSheet.create({
  content: { padding: 20, paddingBottom: 112 }, topbar: { minHeight: 44, flexDirection: "row", justifyContent: "space-between", alignItems: "center" }, back: { minHeight: 44, flexDirection: "row", gap: 8, paddingHorizontal: 10, borderRadius: 14, backgroundColor: colors.surface }, share: { width: 44, minHeight: 44, borderRadius: 14, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, backText: { color: colors.foreground, fontSize: 14, fontWeight: "700" }, imageShell: { height: 260, marginTop: 14, borderRadius: 24, overflow: "hidden", backgroundColor: colors.surface, justifyContent: "center", alignItems: "center", borderWidth: 1, borderColor: colors.border }, imageMotion: { opacity: 0.58 }, image: { height: "100%", width: "100%" }, imageFallback: { alignItems: "center", gap: 8 }, imageFallbackText: { color: colors.muted, fontSize: 13 }, eyebrow: { flexDirection: "row", alignItems: "center", gap: 7, marginTop: 20 }, dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.success }, eyebrowText: { color: colors.success, fontSize: 11, fontWeight: "800", letterSpacing: 0.5 }, name: { color: colors.foreground, fontSize: 25, lineHeight: 32, fontWeight: "800", letterSpacing: -0.5, marginTop: 10 }, category: { color: colors.muted, fontSize: 12, lineHeight: 18, marginTop: 6 }, pricePanel: { minHeight: 105, marginTop: 22, padding: 17, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderRadius: 20, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, priceLabel: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.35, textTransform: "uppercase" }, price: { color: colors.foreground, fontSize: 28, fontWeight: "800", letterSpacing: -0.7, marginTop: 3 }, merchantProof: { marginTop: 6, flexDirection: "row", alignItems: "center", gap: 4 }, merchantProofText: { color: colors.muted, fontSize: 11, fontWeight: "700", flexShrink: 1 }, observedAt: { color: colors.muted, fontSize: 10, lineHeight: 14, fontWeight: "700", marginTop: 5 }, proofRight: { alignItems: "flex-end", gap: 8 }, sourceProof: { flexDirection: "row", alignItems: "center", gap: 4 }, sourceProofText: { color: colors.success, fontSize: 10, fontWeight: "900", textTransform: "uppercase", letterSpacing: 0.3 }, stock: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, backgroundColor: `${colors.success}20` }, stockUnavailable: { backgroundColor: `${colors.error}20` }, stockUnknown: { backgroundColor: `${colors.warning}20` }, stockText: { color: colors.success, fontSize: 11, fontWeight: "700" }, stockTextUnavailable: { color: colors.error }, stockTextUnknown: { color: colors.warning }, followActions: { flexDirection: "row", gap: 10, marginTop: 11 }, followAction: { flex: 1, minHeight: 62, paddingHorizontal: 12, flexDirection: "row", gap: 8, borderRadius: 17, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, followActionActive: { backgroundColor: colors.primary, borderColor: colors.primary }, followActionText: { flex: 1, color: colors.foreground, fontSize: 12, fontWeight: "800" }, followActionTextActive: { color: colors.background }, intentAction: { minHeight: 48, marginTop: 10, paddingHorizontal: 14, flexDirection: "row", gap: 8, borderRadius: 15, backgroundColor: `${colors.primary}12`, borderWidth: 1, borderColor: `${colors.primary}34` }, intentActionText: { flex: 1, color: colors.primary, fontSize: 12, fontWeight: "900" }, actionDisabled: { opacity: 0.38 }, divider: { height: 1, backgroundColor: colors.border, marginTop: 24, marginBottom: 20 }, availability: { color: colors.foreground, fontSize: 15, fontWeight: "800" }, note: { color: colors.muted, fontSize: 13, lineHeight: 20, marginTop: 8 }, footer: { padding: 16, borderTopWidth: 1, borderTopColor: colors.border, backgroundColor: colors.background }, buy: { minHeight: 56, paddingHorizontal: 18, borderRadius: 17, flexDirection: "row", gap: 10, backgroundColor: colors.primary }, buyWords: { flex: 1 }, buyCaption: { color: colors.background, fontSize: 10, fontWeight: "800", opacity: 0.74 }, buyText: { color: colors.background, fontSize: 14, fontWeight: "900", marginTop: 2 }, linkUnavailable: { minHeight: 52, flexDirection: "row", alignItems: "center", gap: 10, paddingHorizontal: 14, borderRadius: 17, backgroundColor: `${colors.error}16`, borderWidth: 1, borderColor: `${colors.error}44` }, linkUnavailableText: { flex: 1, color: colors.error, fontSize: 12, lineHeight: 17, fontWeight: "700" }, scrim: { flex: 1, justifyContent: "flex-end", backgroundColor: "rgba(0,0,0,0.52)" }, intentSheet: { padding: 20, paddingBottom: 32, borderTopLeftRadius: 28, borderTopRightRadius: 28, backgroundColor: colors.surface, borderTopWidth: 1, borderColor: colors.border }, grabber: { width: 38, height: 4, alignSelf: "center", borderRadius: 3, backgroundColor: colors.muted, marginBottom: 16 }, intentSheetTitle: { color: colors.foreground, fontSize: 19, fontWeight: "900", marginBottom: 12 }, intentSheetEmpty: { color: colors.muted, fontSize: 13, lineHeight: 19, paddingVertical: 14 }, intentChoice: { minHeight: 58, padding: 10, flexDirection: "row", alignItems: "center", gap: 10, borderRadius: 15, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border, marginTop: 8 }, intentChoiceIcon: { width: 34, height: 34, alignItems: "center", justifyContent: "center", borderRadius: 11, backgroundColor: `${colors.primary}12` }, intentChoiceText: { flex: 1, color: colors.foreground, fontSize: 13, fontWeight: "800" }, pressed: { opacity: 0.75, transform: [{ scale: 0.985 }] },
}); }
