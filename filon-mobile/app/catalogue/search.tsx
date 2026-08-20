import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { NativeCatalogueHeader, NativeOfferResults } from "@/components/filon/native-catalogue";
import { ScreenContainer } from "@/components/screen-container";

export default function CatalogueSearchScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ q?: string; max?: string }>();
  const [draft, setDraft] = useState(params.q ?? "");
  const [query, setQuery] = useState(params.q ?? "");
  useEffect(() => { if (params.q) { setDraft(params.q); setQuery(params.q); } }, [params.q]);
  const submit = () => setQuery(draft.trim());
  const priceMax = params.max && Number.isFinite(Number(params.max)) ? Number(params.max) : undefined;
  return <ScreenContainer className="" containerClassName="bg-background"><NativeCatalogueHeader title="Rechercher" onBack={() => router.back()} /><View style={styles.search}><MaterialIcons name="search" size={19} color="#C89544" /><TextInput autoFocus value={draft} onChangeText={setDraft} onSubmitEditing={submit} returnKeyType="search" placeholder="Produit, marque ou besoin" placeholderTextColor="#817A72" style={styles.input} /><Pressable accessibilityRole="button" accessibilityLabel="Rechercher" onPress={submit} style={({ pressed }) => [styles.submit, pressed && styles.pressed]}><MaterialIcons name="arrow-forward" size={20} color="#0E0C0B" /></Pressable></View>{query.length >= 2 ? <NativeOfferResults title={query} query={query} initialPriceMax={priceMax} /> : <View style={styles.empty}><Text style={styles.emptyTitle}>Que cherchez-vous ?</Text><Text style={styles.emptyText}>Saisissez un produit ou une marque. FILON cherchera uniquement parmi les offres partenaires indexées.</Text></View>}</ScreenContainer>;
}
const styles = StyleSheet.create({ search: { minHeight: 58, margin: 20, marginBottom: 4, paddingLeft: 15, flexDirection: "row", alignItems: "center", gap: 10, borderRadius: 18, backgroundColor: "#1A1714", borderWidth: 1, borderColor: "#40362B" }, input: { flex: 1, minHeight: 54, color: "#E4DED4", fontSize: 15 }, submit: { width: 48, height: 48, marginRight: 5, borderRadius: 15, justifyContent: "center", alignItems: "center", backgroundColor: "#C89544" }, empty: { padding: 28, gap: 9 }, emptyTitle: { color: "#E4DED4", fontSize: 21, fontWeight: "800" }, emptyText: { color: "#9D958C", fontSize: 14, lineHeight: 20 }, pressed: { opacity: 0.75, transform: [{ scale: 0.98 }] } });
