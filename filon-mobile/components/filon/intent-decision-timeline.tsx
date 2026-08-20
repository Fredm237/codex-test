import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useColors } from "@/hooks/use-colors";
import type { IntentDecisionEvent } from "@/lib/intent-decision-journal";

const copy = {
  fr: { title: "Décisions sur cet appareil", clear: "Effacer", "intent-defined": "Intention créée", "intent-revised": "Intention modifiée", "catalogue-explored": "Catalogue exploré", "assistant-opened": "Assistant ouvert", "offer-linked": "Offre reliée", "offer-unlinked": "Offre retirée", "alert-created": "Seuil enregistré" },
  nl: { title: "Beslissingen op dit apparaat", clear: "Wissen", "intent-defined": "Intentie gemaakt", "intent-revised": "Intentie gewijzigd", "catalogue-explored": "Catalogus verkend", "assistant-opened": "Assistent geopend", "offer-linked": "Aanbod gekoppeld", "offer-unlinked": "Aanbod verwijderd", "alert-created": "Drempel opgeslagen" },
  en: { title: "Decisions on this device", clear: "Clear", "intent-defined": "Intent created", "intent-revised": "Intent revised", "catalogue-explored": "Catalogue explored", "assistant-opened": "Assistant opened", "offer-linked": "Offer linked", "offer-unlinked": "Offer removed", "alert-created": "Threshold saved" },
};

export function IntentDecisionTimeline({ events, locale, onClear }: { events: IntentDecisionEvent[]; locale: keyof typeof copy; onClear: () => void }) {
  if (!events.length) return null;
  const colors = useColors();
  const styles = createStyles(colors);
  const text = copy[locale];
  return <View style={styles.wrap}><View style={styles.header}><Text style={styles.title}>{text.title}</Text><Pressable accessibilityRole="button" accessibilityLabel={text.clear} onPress={onClear} style={({ pressed }) => [styles.clear, pressed && styles.pressed]}><Text style={styles.clearText}>{text.clear}</Text></Pressable></View>{events.map((event) => <View key={event.id} style={styles.row}><MaterialIcons name={event.kind === "alert-created" ? "notifications-none" : event.kind.includes("offer") ? "verified" : event.kind === "assistant-opened" ? "auto-awesome" : "track-changes"} size={16} color={colors.primary} /><View style={styles.words}><Text style={styles.event}>{text[event.kind]}</Text><Text numberOfLines={1} style={styles.label}>{event.label}</Text></View><Text style={styles.date}>{new Intl.DateTimeFormat(locale, { day: "2-digit", month: "short" }).format(new Date(event.occurredAt))}</Text></View>)}</View>;
}

function createStyles(colors: ReturnType<typeof useColors>) { return StyleSheet.create({ wrap: { marginTop: 3, padding: 11, borderRadius: 15, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border }, header: { minHeight: 25, flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 5 }, title: { color: colors.foreground, fontSize: 11, fontWeight: "900" }, clear: { minHeight: 30, paddingHorizontal: 7, justifyContent: "center" }, clearText: { color: colors.primary, fontSize: 10, fontWeight: "800" }, row: { minHeight: 39, flexDirection: "row", alignItems: "center", gap: 8, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border }, words: { flex: 1 }, event: { color: colors.foreground, fontSize: 10, fontWeight: "800" }, label: { color: colors.muted, marginTop: 1, fontSize: 9 }, date: { color: colors.muted, fontSize: 9 }, pressed: { opacity: 0.58 } }); }
