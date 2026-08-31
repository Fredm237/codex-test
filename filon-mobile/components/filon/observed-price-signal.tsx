import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { useFilonOfferDetail } from "@/hooks/use-filon-offer-detail";
import { deriveObservedPriceSignal } from "@/lib/observed-price";

const copy = {
  fr: { down: "Baisse entre les deux derniers relevés", up: "Hausse entre les deux derniers relevés", stable: "Prix inchangé entre les deux derniers relevés", insufficient: "Historique insuffisant pour signaler une variation", dated: "dernier relevé" },
  nl: { down: "Daling tussen de laatste twee metingen", up: "Stijging tussen de laatste twee metingen", stable: "Prijs ongewijzigd tussen de laatste twee metingen", insufficient: "Onvoldoende historiek om een verandering te tonen", dated: "laatste meting" },
  en: { down: "Decrease between the last two readings", up: "Increase between the last two readings", stable: "Price unchanged between the last two readings", insufficient: "Insufficient history to show a change", dated: "latest reading" },
};

export function ObservedPriceSignal({ offerId, locale }: { offerId: number; locale: "fr" | "nl" | "en" }) {
  const detail = useFilonOfferDetail(offerId);
  if (detail.isLoading) return <View style={styles.shell}><ActivityIndicator size="small" color="#C89544" /></View>;
  if (detail.isError || !detail.data) return null;
  const signal = deriveObservedPriceSignal(detail.data.history);
  const text = copy[locale];
  const tone = signal.kind === "down" ? styles.down : signal.kind === "up" ? styles.up : styles.neutral;
  const icon = signal.kind === "down" ? "south" : signal.kind === "up" ? "north" : signal.kind === "stable" ? "horizontal-rule" : "history";
  const comparedAt = signal.comparedAt ? new Intl.DateTimeFormat(locale === "en" ? "en-BE" : `${locale}-BE`, { dateStyle: "medium" }).format(new Date(signal.comparedAt)) : null;
  return <View style={[styles.shell, tone]}><MaterialIcons name={icon} size={15} color={signal.kind === "down" ? "#A9C58F" : signal.kind === "up" ? "#E9B0A0" : "#C89544"} /><Text style={styles.text}>{text[signal.kind]}{comparedAt ? ` · ${text.dated} ${comparedAt}` : ""}</Text></View>;
}

const styles = StyleSheet.create({ shell: { minHeight: 39, paddingHorizontal: 12, marginTop: -2, flexDirection: "row", alignItems: "center", gap: 7, borderWidth: 1, borderTopWidth: 0, borderColor: "#40362B", backgroundColor: "#171411" }, down: { backgroundColor: "rgba(143,176,114,0.08)" }, up: { backgroundColor: "rgba(229,148,128,0.08)" }, neutral: { backgroundColor: "#171411" }, text: { flex: 1, color: "#B9B1A6", fontSize: 10, lineHeight: 14, fontWeight: "600" } });
