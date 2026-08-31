import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, View } from "react-native";

import { TactileButton } from "@/components/filon/filon-ui";
import { ScreenContainer } from "@/components/screen-container";
import { useFilonOfferDetail } from "@/hooks/use-filon-offer-detail";
import { saveLocalPriceAlert } from "@/lib/alerts";
import { formatFilonPrice, normalizeFilonCurrency } from "@/lib/filon-api";
import { selectVerifiedAlertOffer } from "@/lib/filon-offer-evidence";
import { haptic } from "@/lib/haptics";
import { recordFollowUpEvent } from "@/lib/follow-up-timeline";
import { useLocale } from "@/lib/locale";
import { recordIntentDecision } from "@/lib/intent-decision-journal";
import { useFilonEvidenceNow } from "@/hooks/use-filon-evidence-now";

const copy = {
  fr: { title: "Prix à surveiller", back: "Retour", current: "Prix de référence transmis", label: "M’avertir sous", checking: "FILON rapproche l’offre avec le catalogue…", helper: "Le seuil est enregistré sur cet appareil. Une alerte distante devra encore vérifier le prix et la devise auprès de l’offre exacte.", invalid: "Impossible d’enregistrer : l’offre, son prix de référence ou sa devise sont incomplets ou contradictoires.", stale: "Impossible d’enregistrer : le relevé transmis est absent, expiré ou non confirmé par le catalogue. Actualisez d’abord l’offre.", save: "Enregistrer le seuil", saved: "Seuil enregistré sur cet appareil" },
  nl: { title: "Prijs volgen", back: "Terug", current: "Ontvangen referentieprijs", label: "Waarschuw mij onder", checking: "FILON vergelijkt het aanbod met de catalogus…", helper: "De drempel wordt op dit apparaat bewaard. Een externe melding moet prijs en valuta nog controleren bij de exacte aanbieding.", invalid: "Opslaan is niet mogelijk: aanbieding, referentieprijs of valuta is onvolledig of tegenstrijdig.", stale: "Opslaan is niet mogelijk: de ontvangen meting ontbreekt, is verlopen of wordt niet door de catalogus bevestigd. Vernieuw eerst het aanbod.", save: "Drempel bewaren", saved: "Drempel opgeslagen op dit apparaat" },
  en: { title: "Watch a price", back: "Back", current: "Received reference price", label: "Notify me below", checking: "FILON is reconciling the offer with the catalogue…", helper: "The threshold is saved on this device. A remote alert must still verify price and currency against the exact offer.", invalid: "Cannot save: the offer, reference price or currency is incomplete or contradictory.", stale: "Cannot save: the supplied observation is missing, expired or unconfirmed by the catalogue. Refresh the offer first.", save: "Save threshold", saved: "Threshold saved on this device" },
};

export default function NewAlertScreen() {
  const params = useLocalSearchParams<{ id?: string; name?: string; price?: string; currency?: string; intentId?: string; observedAt?: string; evidenceCurrent?: string }>();
  const { locale } = useLocale();
  const text = copy[locale];
  const [threshold, setThreshold] = useState("");
  const [thresholdWasEdited, setThresholdWasEdited] = useState(false);
  const [saved, setSaved] = useState(false);
  const parsedOfferId = Number(params.id);
  const offerId = Number.isInteger(parsedOfferId) && parsedOfferId > 0 ? parsedOfferId : null;
  const routedName = typeof params.name === "string" && params.name.trim() ? params.name.trim() : null;
  const routedCurrency = normalizeFilonCurrency(params.currency);
  const parsedCurrent = Number(params.price);
  const routedCurrent = Number.isFinite(parsedCurrent) && parsedCurrent > 0 ? parsedCurrent : null;
  const detail = useFilonOfferDetail(offerId ?? undefined);
  const evidenceNow = useFilonEvidenceNow([detail.data?.offer.observedAt, params.observedAt]);
  const verifiedOffer = selectVerifiedAlertOffer(params, detail.data?.offer ?? null, evidenceNow);
  const verifiedPrice = verifiedOffer?.price ?? null;
  useEffect(() => {
    if (!thresholdWasEdited) setThreshold(verifiedPrice === null ? "" : String(verifiedPrice));
  }, [thresholdWasEdited, verifiedPrice]);
  const thresholdValue = Number(threshold.replace(",", "."));
  const contractIsValid = verifiedOffer !== null;
  const canSubmit = contractIsValid && !detail.isFetching && Number.isFinite(thresholdValue) && thresholdValue > 0;
  const submit = async () => {
    const nextThreshold = Number(threshold.replace(",", "."));
    if (!Number.isFinite(nextThreshold) || nextThreshold <= 0) return;
    // Une activation exige une nouvelle réponse réseau. Une donnée encore
    // présente dans le cache après un échec ne suffit jamais.
    const refreshed = await detail.refetch();
    if (!refreshed.isSuccess) return;
    const authoritative = selectVerifiedAlertOffer(params, refreshed.data.offer, Date.now());
    const currency = authoritative ? normalizeFilonCurrency(authoritative.currency) : null;
    if (authoritative === null || currency === null) return;
    await saveLocalPriceAlert({ offerId: authoritative.id, name: authoritative.name, threshold: nextThreshold, currency, createdAt: new Date().toISOString() });
    await recordFollowUpEvent("alert-created", authoritative.name);
    if (params.intentId) await recordIntentDecision(params.intentId, "alert-created", authoritative.name);
    haptic.success();
    setSaved(true);
  };
  const helper = detail.isLoading || detail.isFetching ? text.checking : contractIsValid ? text.helper : routedCurrent !== null && routedCurrency !== null ? text.stale : text.invalid;
  return <ScreenContainer className="" containerClassName="bg-background" edges={["top", "left", "right", "bottom"]}><KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}><View style={styles.content}><TactileButton accessibilityLabel={text.back} onPress={() => router.back()} style={styles.back}><MaterialIcons name="arrow-back" size={20} color="#E4DED4" /><Text style={styles.backText}>{text.back}</Text></TactileButton><Text style={styles.title}>{text.title}</Text><Text numberOfLines={2} style={styles.name}>{verifiedOffer?.name ?? routedName ?? "—"}</Text><View style={styles.current}><Text style={styles.currentLabel}>{text.current}</Text><Text style={styles.currentPrice}>{verifiedOffer ? formatFilonPrice(verifiedOffer.price, locale, verifiedOffer.currency) : "—"}</Text></View><Text style={styles.label}>{text.label}</Text><View style={styles.inputShell}><TextInput value={threshold} onChangeText={(value) => { setThresholdWasEdited(true); setThreshold(value); }} keyboardType="decimal-pad" selectTextOnFocus style={styles.input} accessibilityLabel={text.label} editable={contractIsValid} /><Text style={styles.currency}>{verifiedOffer?.currency ?? "—"}</Text></View><Text style={styles.helper}>{helper}</Text>{saved ? <View style={styles.saved}><MaterialIcons name="check-circle" size={19} color="#A9CB8E" /><Text style={styles.savedText}>{text.saved}</Text></View> : <TactileButton accessibilityLabel={text.save} onPress={() => void submit()} disabled={!canSubmit} style={[styles.save, !canSubmit && styles.disabled]}><Text style={styles.saveText}>{text.save}</Text><MaterialIcons name="bookmark-add" size={19} color="#0E0C0B" /></TactileButton>}</View></KeyboardAvoidingView></ScreenContainer>;
}

const styles = StyleSheet.create({ flex: { flex: 1 }, content: { flex: 1, padding: 20 }, back: { alignSelf: "flex-start", minHeight: 44, paddingHorizontal: 10, borderRadius: 14, flexDirection: "row", gap: 8 }, backText: { color: "#E4DED4", fontSize: 14, fontWeight: "700" }, title: { color: "#E4DED4", fontSize: 32, fontWeight: "800", letterSpacing: -0.7, marginTop: 30 }, name: { color: "#9D958C", fontSize: 14, lineHeight: 20, marginTop: 10 }, current: { padding: 17, marginTop: 28, borderRadius: 20, backgroundColor: "#1A1714", borderWidth: 1, borderColor: "#332D28" }, currentLabel: { color: "#C89544", fontSize: 12, fontWeight: "800" }, currentPrice: { color: "#E4DED4", fontSize: 26, fontWeight: "800", marginTop: 4 }, label: { color: "#E4DED4", fontSize: 15, fontWeight: "800", marginTop: 25, marginBottom: 9 }, inputShell: { minHeight: 58, paddingHorizontal: 17, flexDirection: "row", alignItems: "center", borderRadius: 17, backgroundColor: "#1A1714", borderWidth: 1, borderColor: "#4A4037" }, input: { flex: 1, minHeight: 52, color: "#E4DED4", fontSize: 20, fontWeight: "800" }, currency: { color: "#C89544", fontSize: 13, fontWeight: "800" }, helper: { color: "#9D958C", fontSize: 12, lineHeight: 18, marginTop: 12 }, save: { minHeight: 52, marginTop: 24, borderRadius: 17, paddingHorizontal: 18, backgroundColor: "#C89544", flexDirection: "row", gap: 10 }, disabled: { opacity: 0.35 }, saveText: { flex: 1, color: "#0E0C0B", fontSize: 14, fontWeight: "800" }, saved: { minHeight: 52, marginTop: 24, paddingHorizontal: 16, borderRadius: 17, backgroundColor: "rgba(143,176,114,0.12)", borderWidth: 1, borderColor: "rgba(143,176,114,0.3)", flexDirection: "row", alignItems: "center", gap: 10 }, savedText: { color: "#A9CB8E", fontSize: 13, fontWeight: "800" } });
