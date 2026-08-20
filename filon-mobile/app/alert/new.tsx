import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, View } from "react-native";

import { TactileButton } from "@/components/filon/filon-ui";
import { ScreenContainer } from "@/components/screen-container";
import { saveLocalPriceAlert } from "@/lib/alerts";
import { formatFilonPrice } from "@/lib/filon-api";
import { haptic } from "@/lib/haptics";
import { recordFollowUpEvent } from "@/lib/follow-up-timeline";
import { useLocale } from "@/lib/locale";
import { recordIntentDecision } from "@/lib/intent-decision-journal";

const copy = {
  fr: { title: "Prix à surveiller", back: "Retour", label: "M’avertir sous", helper: "Cette première version enregistre le seuil sur votre appareil. Les notifications et le suivi continu seront activés lorsque les alertes seront liées à un compte FILON.", save: "Enregistrer le seuil", saved: "Seuil enregistré sur cet appareil" },
  nl: { title: "Prijs volgen", back: "Terug", label: "Waarschuw mij onder", helper: "Deze eerste versie bewaart de drempel op je apparaat. Meldingen en permanente opvolging worden geactiveerd zodra waarschuwingen aan een FILON-account gekoppeld zijn.", save: "Drempel bewaren", saved: "Drempel opgeslagen op dit apparaat" },
  en: { title: "Watch a price", back: "Back", label: "Notify me below", helper: "This first version saves the threshold on your device. Notifications and continuous tracking will be enabled once alerts are linked to a FILON account.", save: "Save threshold", saved: "Threshold saved on this device" },
};

export default function NewAlertScreen() {
  const params = useLocalSearchParams<{ id: string; name: string; price: string; currency: string; intentId?: string }>();
  const { locale } = useLocale();
  const text = copy[locale];
  const [threshold, setThreshold] = useState(params.price ?? "");
  const [saved, setSaved] = useState(false);
  const current = Number(params.price);
  const submit = async () => { const value = Number(threshold.replace(",", ".")); if (!Number.isFinite(value) || value <= 0) return; const name = params.name || "FILON"; await saveLocalPriceAlert({ offerId: Number(params.id), name, threshold: value, currency: params.currency || "EUR", createdAt: new Date().toISOString() }); await recordFollowUpEvent("alert-created", name); if (params.intentId) await recordIntentDecision(params.intentId, "alert-created", name); haptic.success(); setSaved(true); };
  return <ScreenContainer className="" containerClassName="bg-background" edges={["top", "left", "right", "bottom"]}><KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}><View style={styles.content}><TactileButton accessibilityLabel={text.back} onPress={() => router.back()} style={styles.back}><MaterialIcons name="arrow-back" size={20} color="#E4DED4" /><Text style={styles.backText}>{text.back}</Text></TactileButton><Text style={styles.title}>{text.title}</Text><Text numberOfLines={2} style={styles.name}>{params.name}</Text><View style={styles.current}><Text style={styles.currentLabel}>Prix actuellement affiché</Text><Text style={styles.currentPrice}>{Number.isFinite(current) ? formatFilonPrice(current, locale, params.currency || "EUR") : "—"}</Text></View><Text style={styles.label}>{text.label}</Text><View style={styles.inputShell}><TextInput value={threshold} onChangeText={setThreshold} keyboardType="decimal-pad" selectTextOnFocus style={styles.input} accessibilityLabel={text.label} /><Text style={styles.currency}>{params.currency || "EUR"}</Text></View><Text style={styles.helper}>{text.helper}</Text>{saved ? <View style={styles.saved}><MaterialIcons name="check-circle" size={19} color="#A9CB8E" /><Text style={styles.savedText}>{text.saved}</Text></View> : <TactileButton accessibilityLabel={text.save} onPress={() => void submit()} style={styles.save}><Text style={styles.saveText}>{text.save}</Text><MaterialIcons name="bookmark-add" size={19} color="#0E0C0B" /></TactileButton>}</View></KeyboardAvoidingView></ScreenContainer>;
}

const styles = StyleSheet.create({ flex: { flex: 1 }, content: { flex: 1, padding: 20 }, back: { alignSelf: "flex-start", minHeight: 44, paddingHorizontal: 10, borderRadius: 14, flexDirection: "row", gap: 8 }, backText: { color: "#E4DED4", fontSize: 14, fontWeight: "700" }, title: { color: "#E4DED4", fontSize: 32, fontWeight: "800", letterSpacing: -0.7, marginTop: 30 }, name: { color: "#9D958C", fontSize: 14, lineHeight: 20, marginTop: 10 }, current: { padding: 17, marginTop: 28, borderRadius: 20, backgroundColor: "#1A1714", borderWidth: 1, borderColor: "#332D28" }, currentLabel: { color: "#C89544", fontSize: 12, fontWeight: "800" }, currentPrice: { color: "#E4DED4", fontSize: 26, fontWeight: "800", marginTop: 4 }, label: { color: "#E4DED4", fontSize: 15, fontWeight: "800", marginTop: 25, marginBottom: 9 }, inputShell: { minHeight: 58, paddingHorizontal: 17, flexDirection: "row", alignItems: "center", borderRadius: 17, backgroundColor: "#1A1714", borderWidth: 1, borderColor: "#4A4037" }, input: { flex: 1, minHeight: 52, color: "#E4DED4", fontSize: 20, fontWeight: "800" }, currency: { color: "#C89544", fontSize: 13, fontWeight: "800" }, helper: { color: "#9D958C", fontSize: 12, lineHeight: 18, marginTop: 12 }, save: { minHeight: 52, marginTop: 24, borderRadius: 17, paddingHorizontal: 18, backgroundColor: "#C89544", flexDirection: "row", gap: 10 }, saveText: { flex: 1, color: "#0E0C0B", fontSize: 14, fontWeight: "800" }, saved: { minHeight: 52, marginTop: 24, paddingHorizontal: 16, borderRadius: 17, backgroundColor: "rgba(143,176,114,0.12)", borderWidth: 1, borderColor: "rgba(143,176,114,0.3)", flexDirection: "row", alignItems: "center", gap: 10 }, savedText: { color: "#A9CB8E", fontSize: 13, fontWeight: "800" } });
