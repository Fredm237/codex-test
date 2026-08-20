import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { useFilonOfferDetail } from "@/hooks/use-filon-offer-detail";
import { formatFilonPrice } from "@/lib/filon-api";
import { deriveObservedPriceSignal } from "@/lib/observed-price";

const copy = {
  fr: { down: "Baisse observée depuis le relevé précédent", up: "Hausse observée depuis le relevé précédent", stable: "Prix inchangé entre les deux derniers relevés", insufficient: "Historique insuffisant pour signaler une variation" },
  nl: { down: "Daling waargenomen sinds de vorige meting", up: "Stijging waargenomen sinds de vorige meting", stable: "Prijs ongewijzigd tussen de laatste twee metingen", insufficient: "Onvoldoende historiek om een verandering te tonen" },
  en: { down: "Decrease observed since the previous reading", up: "Increase observed since the previous reading", stable: "Price unchanged between the last two readings", insufficient: "Insufficient history to show a change" },
};

export function ObservedPriceSignal({ offerId, locale, currency }: { offerId: number; locale: "fr" | "nl" | "en"; currency: string }) {
  const detail = useFilonOfferDetail(offerId);
  if (detail.isLoading) return <View style={styles.shell}><ActivityIndicator size="small" color="#C89544" /></View>;
  if (detail.isError || !detail.data) return null;
  const signal = deriveObservedPriceSignal(detail.data.history);
  const text = copy[locale];
  const tone = signal.kind === "down" ? styles.down : signal.kind === "up" ? styles.up : styles.neutral;
  const icon = signal.kind === "down" ? "south" : signal.kind === "up" ? "north" : signal.kind === "stable" ? "horizontal-rule" : "history";
  return <View style={[styles.shell, tone]}><MaterialIcons name={icon} size={15} color={signal.kind === "down" ? "#A9C58F" : signal.kind === "up" ? "#E9B0A0" : "#C89544"} /><Text style={styles.text}>{text[signal.kind]}{signal.delta !== null ? ` · ${formatFilonPrice(signal.delta, locale, currency)}` : ""}</Text></View>;
}

const styles = StyleSheet.create({ shell: { minHeight: 39, paddingHorizontal: 12, marginTop: -2, flexDirection: "row", alignItems: "center", gap: 7, borderWidth: 1, borderTopWidth: 0, borderColor: "#40362B", backgroundColor: "#171411" }, down: { backgroundColor: "rgba(143,176,114,0.08)" }, up: { backgroundColor: "rgba(229,148,128,0.08)" }, neutral: { backgroundColor: "#171411" }, text: { flex: 1, color: "#B9B1A6", fontSize: 10, lineHeight: 14, fontWeight: "600" } });
