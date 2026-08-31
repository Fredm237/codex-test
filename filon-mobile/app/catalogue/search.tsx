import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { NativeCatalogueHeader, NativeOfferResults } from "@/components/filon/native-catalogue";
import { ScreenContainer } from "@/components/screen-container";
import { useLocale } from "@/lib/locale";

const copy = {
  fr: { title: "Rechercher", placeholder: "Produit, marque ou besoin", emptyTitle: "Que cherchez-vous ?", emptyText: "Saisissez un produit ou une marque. FILON cherchera uniquement parmi les offres indexées dans son catalogue." },
  nl: { title: "Zoeken", placeholder: "Product, merk of behoefte", emptyTitle: "Waar ben je naar op zoek?", emptyText: "Voer een product of merk in. FILON zoekt alleen in aanbiedingen die in zijn catalogus zijn geïndexeerd." },
  en: { title: "Search", placeholder: "Product, brand, or need", emptyTitle: "What are you looking for?", emptyText: "Enter a product or brand. FILON searches only offers indexed in its catalogue." },
};

export default function CatalogueSearchScreen() {
  const router = useRouter();
  const { locale } = useLocale();
  const text = copy[locale];
  const params = useLocalSearchParams<{ q?: string }>();
  const [draft, setDraft] = useState(params.q ?? "");
  const [query, setQuery] = useState(params.q ?? "");
  useEffect(() => { if (params.q) { setDraft(params.q); setQuery(params.q); } }, [params.q]);
  const submit = () => setQuery(draft.trim());
  return <ScreenContainer className="" containerClassName="bg-background"><NativeCatalogueHeader title={text.title} onBack={() => router.back()} /><View style={styles.search}><MaterialIcons name="search" size={19} color="#C89544" /><TextInput autoFocus accessibilityLabel={text.title} value={draft} onChangeText={setDraft} onSubmitEditing={submit} returnKeyType="search" placeholder={text.placeholder} placeholderTextColor="#817A72" style={styles.input} /><Pressable accessibilityRole="button" accessibilityLabel={text.title} onPress={submit} style={({ pressed }) => [styles.submit, pressed && styles.pressed]}><MaterialIcons name="arrow-forward" size={20} color="#0E0C0B" /></Pressable></View>{query.length >= 2 ? <NativeOfferResults title={query} query={query} /> : <View style={styles.empty}><Text style={styles.emptyTitle}>{text.emptyTitle}</Text><Text style={styles.emptyText}>{text.emptyText}</Text></View>}</ScreenContainer>;
}
const styles = StyleSheet.create({ search: { minHeight: 58, margin: 20, marginBottom: 4, paddingLeft: 15, flexDirection: "row", alignItems: "center", gap: 10, borderRadius: 18, backgroundColor: "#1A1714", borderWidth: 1, borderColor: "#40362B" }, input: { flex: 1, minHeight: 54, color: "#E4DED4", fontSize: 15 }, submit: { width: 48, height: 48, marginRight: 5, borderRadius: 15, justifyContent: "center", alignItems: "center", backgroundColor: "#C89544" }, empty: { padding: 28, gap: 9 }, emptyTitle: { color: "#E4DED4", fontSize: 21, fontWeight: "800" }, emptyText: { color: "#9D958C", fontSize: 14, lineHeight: 20 }, pressed: { opacity: 0.75, transform: [{ scale: 0.98 }] } });
