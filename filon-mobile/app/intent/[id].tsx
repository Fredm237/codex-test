import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { TactileButton } from "@/components/filon/filon-ui";
import { ScreenContainer } from "@/components/screen-container";
import { useColors } from "@/hooks/use-colors";
import { haptic } from "@/lib/haptics";
import { useLocale } from "@/lib/locale";
import { describePurchaseIntent, isPurchaseIntentValid, readPurchaseIntent, savePurchaseIntent, type PurchaseIntent } from "@/lib/purchase-intents";
import { recordIntentDecision } from "@/lib/intent-decision-journal";

const copy = {
  fr: { newTitle: "Nouvelle intention", editTitle: "Votre intention", back: "Retour", need: "Ce que vous cherchez", needHint: "Ex. un casque confortable pour le train", budget: "Budget maximum", budgetHint: "Facultatif", deadline: "Délai", deadlineHint: "Ex. avant vendredi", preferences: "Préférences", preferencesHint: "Ex. réparable, sans marketplace inconnue", local: "Cette règle reste sur votre appareil. FILON ne lance aucun achat automatiquement.", save: "Enregistrer l’intention", saved: "Intention enregistrée", catalogue: "Explorer le catalogue", assistant: "Éclairer avec l’Assistant", incomplete: "Décrivez au moins ce que vous cherchez." },
  nl: { newTitle: "Nieuwe intentie", editTitle: "Jouw intentie", back: "Terug", need: "Wat je zoekt", needHint: "Bijv. een comfortabele koptelefoon voor de trein", budget: "Maximumbudget", budgetHint: "Optioneel", deadline: "Deadline", deadlineHint: "Bijv. voor vrijdag", preferences: "Voorkeuren", preferencesHint: "Bijv. herstelbaar, geen onbekende marktplaats", local: "Deze regel blijft op je apparaat. FILON start nooit automatisch een aankoop.", save: "Intentie bewaren", saved: "Intentie opgeslagen", catalogue: "Catalogus verkennen", assistant: "Met Assistent verkennen", incomplete: "Beschrijf ten minste wat je zoekt." },
  en: { newTitle: "New intent", editTitle: "Your intent", back: "Back", need: "What you are looking for", needHint: "E.g. comfortable headphones for the train", budget: "Maximum budget", budgetHint: "Optional", deadline: "Deadline", deadlineHint: "E.g. by Friday", preferences: "Preferences", preferencesHint: "E.g. repairable, no unknown marketplaces", local: "This rule stays on your device. FILON never starts a purchase automatically.", save: "Save intent", saved: "Intent saved", catalogue: "Explore catalogue", assistant: "Explore with Assistant", incomplete: "Describe at least what you are looking for." },
};

export default function PurchaseIntentEditorScreen() {
  const params = useLocalSearchParams<{ id: string }>();
  const { locale } = useLocale();
  const colors = useColors();
  const styles = createStyles(colors);
  const text = copy[locale];
  const isNew = params.id === "new";
  const [existing, setExisting] = useState<PurchaseIntent | undefined>();
  const [loading, setLoading] = useState(!isNew);
  const [need, setNeed] = useState("");
  const [budget, setBudget] = useState("");
  const [deadline, setDeadline] = useState("");
  const [preferences, setPreferences] = useState("");
  const [saved, setSaved] = useState<PurchaseIntent | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isNew) return;
    void readPurchaseIntent(params.id).then((intent) => { if (intent) { setExisting(intent); setNeed(intent.need); setBudget(intent.maxBudget === null ? "" : String(intent.maxBudget)); setDeadline(intent.deadline ?? ""); setPreferences(intent.preferences ?? ""); } setLoading(false); });
  }, [isNew, params.id]);

  const submit = async () => {
    const maxBudget = budget.trim() ? Number(budget.replace(",", ".")) : null;
    const draft = { need, maxBudget, deadline, preferences };
    if (!isPurchaseIntentValid(draft)) { setError(text.incomplete); return; }
    const intent = await savePurchaseIntent(draft, existing);
    await recordIntentDecision(intent.id, existing ? "intent-revised" : "intent-defined", intent.need);
    setExisting(intent); setSaved(intent); setError(null); haptic.success();
  };

  if (loading) return <ScreenContainer className="" containerClassName="bg-background"><View style={styles.loader}><ActivityIndicator color={colors.primary} /></View></ScreenContainer>;
  const active = saved ?? existing;
  return <ScreenContainer className="" containerClassName="bg-background" edges={["top", "left", "right", "bottom"]}><KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}><ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}><Pressable accessibilityRole="button" accessibilityLabel={text.back} onPress={() => router.back()} style={({ pressed }) => [styles.back, pressed && styles.pressed]}><MaterialIcons name="arrow-back" size={21} color={colors.foreground} /><Text style={styles.backText}>{text.back}</Text></Pressable><Text style={styles.title}>{isNew ? text.newTitle : text.editTitle}</Text><Text style={styles.intro}>{text.local}</Text><Field label={text.need} hint={text.needHint} value={need} onChangeText={setNeed} styles={styles} colors={colors} multiline /><Field label={text.budget} hint={text.budgetHint} value={budget} onChangeText={setBudget} styles={styles} colors={colors} keyboardType="decimal-pad" suffix="EUR" /><Field label={text.deadline} hint={text.deadlineHint} value={deadline} onChangeText={setDeadline} styles={styles} colors={colors} /><Field label={text.preferences} hint={text.preferencesHint} value={preferences} onChangeText={setPreferences} styles={styles} colors={colors} multiline />{error ? <Text style={styles.error}>{error}</Text> : null}{saved ? <View style={styles.saved}><View style={styles.savedHeading}><MaterialIcons name="check-circle" size={20} color={colors.success} /><Text style={styles.savedTitle}>{text.saved}</Text></View><Text style={styles.savedSummary}>{describePurchaseIntent(saved, locale)}</Text><TactileButton accessibilityLabel={text.catalogue} onPress={() => { void recordIntentDecision(saved.id, "catalogue-explored", saved.need); router.push({ pathname: "/catalogue/search", params: { q: saved.need, max: saved.maxBudget === null ? "" : String(saved.maxBudget) } } as never); }} style={styles.primaryAction}><Text style={styles.primaryActionText}>{text.catalogue}</Text><MaterialIcons name="arrow-forward" size={18} color={colors.background} /></TactileButton><TactileButton accessibilityLabel={text.assistant} onPress={() => { void recordIntentDecision(saved.id, "assistant-opened", saved.need); router.push({ pathname: "/(tabs)/assistant", params: { intentId: saved.id } } as never); }} style={styles.secondaryAction}><Text style={styles.secondaryActionText}>{text.assistant}</Text><MaterialIcons name="auto-awesome" size={18} color={colors.primary} /></TactileButton></View> : <TactileButton accessibilityLabel={text.save} onPress={() => void submit()} style={styles.save}><Text style={styles.saveText}>{text.save}</Text><MaterialIcons name="track-changes" size={19} color={colors.background} /></TactileButton>}</ScrollView></KeyboardAvoidingView></ScreenContainer>;
}

function Field({ label, hint, value, onChangeText, styles, colors, multiline, keyboardType, suffix }: { label: string; hint: string; value: string; onChangeText: (value: string) => void; styles: ReturnType<typeof createStyles>; colors: ReturnType<typeof useColors>; multiline?: boolean; keyboardType?: "default" | "decimal-pad"; suffix?: string }) { return <View style={styles.field}><View style={styles.fieldTop}><Text style={styles.label}>{label}</Text><Text style={styles.hint}>{hint}</Text></View><View style={[styles.inputShell, multiline && styles.inputMulti]}><TextInput value={value} onChangeText={onChangeText} multiline={multiline} keyboardType={keyboardType} returnKeyType={multiline ? "default" : "done"} placeholder={hint} placeholderTextColor={colors.muted} style={[styles.input, multiline && styles.inputMultiline]} accessibilityLabel={label} />{suffix ? <Text style={styles.suffix}>{suffix}</Text> : null}</View></View>; }

function createStyles(colors: ReturnType<typeof useColors>) { return StyleSheet.create({
  flex: { flex: 1 }, content: { padding: 20, paddingBottom: 34 }, loader: { flex: 1, alignItems: "center", justifyContent: "center" }, back: { alignSelf: "flex-start", minHeight: 44, paddingHorizontal: 10, flexDirection: "row", alignItems: "center", gap: 8, borderRadius: 14, backgroundColor: colors.surface }, backText: { color: colors.foreground, fontSize: 14, fontWeight: "800" }, title: { color: colors.foreground, marginTop: 22, fontSize: 29, lineHeight: 34, fontWeight: "900", letterSpacing: -0.6 }, intro: { color: colors.muted, marginTop: 9, fontSize: 13, lineHeight: 19 },
  field: { marginTop: 22 }, fieldTop: { flexDirection: "row", justifyContent: "space-between", gap: 12, alignItems: "baseline", marginBottom: 8 }, label: { color: colors.foreground, fontSize: 14, fontWeight: "800" }, hint: { color: colors.muted, flex: 1, textAlign: "right", fontSize: 10, fontWeight: "700" }, inputShell: { minHeight: 56, paddingHorizontal: 15, flexDirection: "row", alignItems: "center", gap: 10, borderRadius: 17, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, inputMulti: { minHeight: 84, alignItems: "flex-start", paddingTop: 11 }, input: { flex: 1, minHeight: 54, color: colors.foreground, fontSize: 15, fontWeight: "600" }, inputMultiline: { minHeight: 58, textAlignVertical: "top" }, suffix: { color: colors.primary, fontSize: 11, fontWeight: "900" },
  error: { color: colors.error, marginTop: 12, fontSize: 12, fontWeight: "700" }, save: { minHeight: 54, marginTop: 28, flexDirection: "row", gap: 10, borderRadius: 17, backgroundColor: colors.primary }, saveText: { color: colors.background, fontSize: 14, fontWeight: "900" }, saved: { marginTop: 26, padding: 15, gap: 12, borderRadius: 21, borderWidth: 1, borderColor: `${colors.success}48`, backgroundColor: `${colors.success}10` }, savedHeading: { flexDirection: "row", gap: 8, alignItems: "center" }, savedTitle: { color: colors.foreground, fontSize: 15, fontWeight: "900" }, savedSummary: { color: colors.muted, fontSize: 12, lineHeight: 18 }, primaryAction: { minHeight: 50, flexDirection: "row", justifyContent: "space-between", paddingHorizontal: 15, borderRadius: 15, backgroundColor: colors.primary }, primaryActionText: { color: colors.background, fontSize: 13, fontWeight: "900" }, secondaryAction: { minHeight: 48, flexDirection: "row", justifyContent: "space-between", paddingHorizontal: 15, borderRadius: 15, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, secondaryActionText: { color: colors.primary, fontSize: 13, fontWeight: "900" }, pressed: { opacity: 0.78, transform: [{ scale: 0.985 }] },
}); }
