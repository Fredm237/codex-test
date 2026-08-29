import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FollowUpEvent } from "@/lib/follow-up-timeline";
import { useColors } from "@/hooks/use-colors";

const copy = {
  fr: { title: "Activité sur cet appareil", clear: "Effacer", favoriteAdded: "Offre enregistrée", favoriteRemoved: "Offre retirée", alertCreated: "Seuil enregistré", alertRemoved: "Seuil retiré", syncSucceeded: "Suivis synchronisés" },
  nl: { title: "Activiteit op dit apparaat", clear: "Wissen", favoriteAdded: "Aanbieding opgeslagen", favoriteRemoved: "Aanbieding verwijderd", alertCreated: "Drempel opgeslagen", alertRemoved: "Drempel verwijderd", syncSucceeded: "Gevolgde items gesynchroniseerd" },
  en: { title: "Activity on this device", clear: "Clear", favoriteAdded: "Offer saved", favoriteRemoved: "Offer removed", alertCreated: "Threshold saved", alertRemoved: "Threshold removed", syncSucceeded: "Saved items synchronized" },
};

function eventTitle(event: FollowUpEvent, locale: keyof typeof copy) {
  const text = copy[locale];
  return event.kind === "favorite-added" ? text.favoriteAdded : event.kind === "favorite-removed" ? text.favoriteRemoved : event.kind === "alert-created" ? text.alertCreated : event.kind === "alert-removed" ? text.alertRemoved : text.syncSucceeded;
}

export function FollowUpTimeline({ events, locale, onClear }: { events: FollowUpEvent[]; locale: keyof typeof copy; onClear: () => void }) {
  const colors = useColors();
  const styles = createStyles(colors);
  if (!events.length) return null;
  const text = copy[locale];
  return <View style={styles.wrap}><View style={styles.header}><Text style={styles.title}>{text.title}</Text><Pressable accessibilityRole="button" accessibilityLabel={text.clear} onPress={onClear} style={({ pressed }) => [styles.clear, pressed && styles.pressed]}><Text style={styles.clearText}>{text.clear}</Text></Pressable></View>{events.map((event) => <View key={event.id} style={styles.row}><MaterialIcons name={event.kind === "sync-succeeded" ? "cloud-done" : event.kind.includes("alert") ? "notifications-none" : "bookmark-border"} size={16} color={colors.primary} /><View style={styles.meta}><Text style={styles.event}>{eventTitle(event, locale)}</Text><Text numberOfLines={1} style={styles.label}>{event.label}</Text></View><Text style={styles.date}>{new Intl.DateTimeFormat(locale, { day: "2-digit", month: "short" }).format(new Date(event.occurredAt))}</Text></View>)}</View>;
}

function createStyles(colors: ReturnType<typeof useColors>) { return StyleSheet.create({ wrap: { marginTop: 22, padding: 14, borderRadius: 18, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, header: { minHeight: 26, flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }, title: { color: colors.foreground, fontSize: 13, fontWeight: "800" }, clear: { minHeight: 32, paddingHorizontal: 9, justifyContent: "center" }, clearText: { color: colors.primary, fontSize: 11, fontWeight: "800" }, row: { minHeight: 46, flexDirection: "row", alignItems: "center", gap: 9, borderTopWidth: 1, borderTopColor: colors.border }, meta: { flex: 1 }, event: { color: colors.foreground, fontSize: 11, fontWeight: "700" }, label: { color: colors.muted, fontSize: 10, marginTop: 2 }, date: { color: colors.muted, fontSize: 10 }, pressed: { opacity: 0.58 } }); }
