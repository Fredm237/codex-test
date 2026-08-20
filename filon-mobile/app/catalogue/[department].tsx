import { useLocalSearchParams, useRouter } from "expo-router";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";

import { NativeCatalogueHeader } from "@/components/filon/native-catalogue";
import { ScreenContainer } from "@/components/screen-container";
import { useFilonCatalogueNavigation } from "@/hooks/use-filon-catalogue-navigation";

export default function DepartmentScreen() {
  const router = useRouter();
  const { department } = useLocalSearchParams<{ department: string }>();
  const navigation = useFilonCatalogueNavigation();
  const item = navigation.data?.departments.find((candidate) => candidate.slug === department);
  return <ScreenContainer className="" containerClassName="bg-background"><NativeCatalogueHeader title={item?.name ?? "Catalogue"} subtitle={item ? `${item.count.toLocaleString("fr-BE")} offres indexées` : undefined} onBack={() => router.back()} />{navigation.isLoading ? <ActivityIndicator color="#C89544" style={styles.loader} /> : <FlatList data={item?.categories ?? []} keyExtractor={(category) => category.slug} contentContainerStyle={styles.content} ListHeaderComponent={<Text style={styles.hint}>Choisissez un rayon</Text>} renderItem={({ item: category }) => <Pressable accessibilityRole="button" onPress={() => router.push({ pathname: "/catalogue/[department]/[category]", params: { department: item?.slug ?? "", category: category.slug, title: category.name } } as never)} style={({ pressed }) => [styles.row, pressed && styles.pressed]}><View style={styles.words}><Text style={styles.name}>{category.name}</Text><Text style={styles.meta}>{category.count.toLocaleString("fr-BE")} offres{category.subcategories.length ? ` · ${category.subcategories.length} sous-catégories` : ""}</Text></View><MaterialIcons name="chevron-right" size={23} color="#C89544" /></Pressable>} ItemSeparatorComponent={() => <View style={{ height: 9 }} />} />}</ScreenContainer>;
}
const styles = StyleSheet.create({ loader: { marginTop: 48 }, content: { padding: 20, paddingBottom: 112 }, hint: { color: "#817A72", fontSize: 13, fontWeight: "700", marginBottom: 13 }, row: { minHeight: 78, paddingHorizontal: 16, flexDirection: "row", alignItems: "center", gap: 12, borderRadius: 18, backgroundColor: "#1A1714", borderWidth: 1, borderColor: "#332D28" }, words: { flex: 1 }, name: { color: "#E4DED4", fontSize: 16, fontWeight: "800" }, meta: { color: "#817A72", fontSize: 11, fontWeight: "700", marginTop: 6 }, pressed: { opacity: 0.72, transform: [{ scale: 0.98 }] } });
