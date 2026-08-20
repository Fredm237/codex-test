import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { useRouter } from "expo-router";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";

import { ScreenContainer } from "@/components/screen-container";
import { TactileButton } from "@/components/filon/filon-ui";
import { useColors } from "@/hooks/use-colors";
import { usePurchaseIntents } from "@/hooks/use-purchase-intents";
import { useLocale } from "@/lib/locale";
import type { PurchaseIntent } from "@/lib/purchase-intents";

const copy = {
  fr: { title: "Mes intentions", subtitle: "Des règles d’achat claires, sur cet appareil.", create: "Créer une intention", emptyTitle: "Aucune intention active", emptyBody: "Définissez un besoin, un budget ou un délai. FILON vous laissera toujours modifier cette règle.", budget: "Budget", deadline: "Échéance", open: "Modifier l’intention", back: "Retour" },
  nl: { title: "Mijn intenties", subtitle: "Duidelijke aankoopregels, op dit apparaat.", create: "Intentie maken", emptyTitle: "Geen actieve intentie", emptyBody: "Omschrijf een behoefte, budget of deadline. FILON laat je deze regel altijd wijzigen.", budget: "Budget", deadline: "Deadline", open: "Intentie wijzigen", back: "Terug" },
  en: { title: "My intents", subtitle: "Clear buying rules, on this device.", create: "Create an intent", emptyTitle: "No active intent", emptyBody: "Set a need, budget or deadline. FILON will always let you change this rule.", budget: "Budget", deadline: "Deadline", open: "Edit intent", back: "Back" },
};

export default function PurchaseIntentHubScreen() {
  const router = useRouter();
  const { locale } = useLocale();
  const colors = useColors();
  const styles = createStyles(colors);
  const text = copy[locale];
  const intents = usePurchaseIntents();

  return <ScreenContainer className="" containerClassName="bg-background"><View style={styles.header}><Pressable accessibilityRole="button" accessibilityLabel={text.back} onPress={() => router.back()} style={({ pressed }) => [styles.back, pressed && styles.pressed]}><MaterialIcons name="arrow-back" size={21} color={colors.foreground} /></Pressable><View style={styles.headerWords}><Text style={styles.title}>{text.title}</Text><Text style={styles.subtitle}>{text.subtitle}</Text></View></View><FlatList data={intents.items} keyExtractor={(item) => item.id} contentContainerStyle={styles.list} renderItem={({ item }) => <IntentRow item={item} locale={locale} styles={styles} colors={colors} onPress={() => router.push({ pathname: "/intent/[id]", params: { id: item.id } } as never)} />} ListEmptyComponent={intents.ready ? <View style={styles.empty}><View style={styles.emptyIcon}><MaterialIcons name="track-changes" size={24} color={colors.primary} /></View><Text style={styles.emptyTitle}>{text.emptyTitle}</Text><Text style={styles.emptyBody}>{text.emptyBody}</Text></View> : null} ListFooterComponent={<TactileButton accessibilityLabel={text.create} onPress={() => router.push({ pathname: "/intent/[id]", params: { id: "new" } } as never)} style={styles.create}><MaterialIcons name="add" size={21} color={colors.background} /><Text style={styles.createText}>{text.create}</Text></TactileButton>} /></ScreenContainer>;
}

function IntentRow({ item, locale, styles, colors, onPress }: { item: PurchaseIntent; locale: "fr" | "nl" | "en"; styles: ReturnType<typeof createStyles>; colors: ReturnType<typeof useColors>; onPress: () => void }) {
  const text = copy[locale];
  const budget = item.maxBudget === null ? null : `${item.maxBudget.toLocaleString(locale === "nl" ? "nl-BE" : locale === "fr" ? "fr-BE" : "en-BE", { maximumFractionDigits: 2 })} EUR`;
  return <Pressable accessibilityRole="button" accessibilityLabel={`${text.open}: ${item.need}`} onPress={onPress} style={({ pressed }) => [styles.row, pressed && styles.pressed]}><View style={styles.rowSignal}><MaterialIcons name="track-changes" size={20} color={colors.primary} /></View><View style={styles.rowWords}><Text numberOfLines={2} style={styles.rowNeed}>{item.need}</Text><View style={styles.rowMeta}>{budget ? <Text style={styles.metaPill}>{text.budget} · {budget}</Text> : null}{item.deadline ? <Text style={styles.metaPill}>{text.deadline} · {item.deadline}</Text> : null}</View></View><MaterialIcons name="chevron-right" size={22} color={colors.muted} /></Pressable>;
}

function createStyles(colors: ReturnType<typeof useColors>) { return StyleSheet.create({
  header: { minHeight: 92, paddingHorizontal: 20, paddingTop: 12, flexDirection: "row", gap: 12, alignItems: "center", borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
  back: { width: 42, height: 42, alignItems: "center", justifyContent: "center", borderRadius: 14, backgroundColor: colors.surface }, headerWords: { flex: 1 }, title: { color: colors.foreground, fontSize: 24, fontWeight: "900", letterSpacing: -0.5 }, subtitle: { color: colors.muted, fontSize: 12, lineHeight: 17, marginTop: 3 },
  list: { flexGrow: 1, padding: 20, paddingBottom: 116, gap: 10 }, row: { minHeight: 88, padding: 13, flexDirection: "row", alignItems: "center", gap: 12, borderRadius: 21, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface }, rowSignal: { width: 42, height: 42, alignItems: "center", justifyContent: "center", borderRadius: 14, backgroundColor: `${colors.primary}14`, borderWidth: 1, borderColor: `${colors.primary}30` }, rowWords: { flex: 1, minWidth: 0 }, rowNeed: { color: colors.foreground, fontSize: 15, lineHeight: 20, fontWeight: "800" }, rowMeta: { flexDirection: "row", flexWrap: "wrap", gap: 5, marginTop: 7 }, metaPill: { color: colors.muted, fontSize: 10, lineHeight: 14, fontWeight: "700" },
  empty: { flex: 1, minHeight: 280, alignItems: "center", justifyContent: "center", paddingHorizontal: 26 }, emptyIcon: { width: 54, height: 54, alignItems: "center", justifyContent: "center", borderRadius: 18, backgroundColor: `${colors.primary}14` }, emptyTitle: { color: colors.foreground, marginTop: 14, fontSize: 18, fontWeight: "900" }, emptyBody: { color: colors.muted, marginTop: 8, textAlign: "center", fontSize: 13, lineHeight: 19 },
  create: { minHeight: 54, marginTop: 16, flexDirection: "row", gap: 9, borderRadius: 17, backgroundColor: colors.primary }, createText: { color: colors.background, fontSize: 14, fontWeight: "900" }, pressed: { opacity: 0.78, transform: [{ scale: 0.985 }] },
}); }
