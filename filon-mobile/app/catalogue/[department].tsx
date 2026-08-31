import { useLocalSearchParams, useRouter } from "expo-router";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";

import { NativeCatalogueHeader } from "@/components/filon/native-catalogue";
import { ScreenContainer } from "@/components/screen-container";
import { useFilonCatalogueNavigation } from "@/hooks/use-filon-catalogue-navigation";
import { useLocale } from "@/lib/locale";
import { localizedTaxonomyLabel } from "@/lib/taxonomy-presentation";

const copy = {
  fr: { choose: "Choisissez une catégorie", offer: "offre", offers: "offres", indexedOffer: "offre indexée", indexedOffers: "offres indexées", subcategory: "sous-catégorie", subcategories: "sous-catégories" },
  nl: { choose: "Kies een categorie", offer: "aanbieding", offers: "aanbiedingen", indexedOffer: "geïndexeerde aanbieding", indexedOffers: "geïndexeerde aanbiedingen", subcategory: "subcategorie", subcategories: "subcategorieën" },
  en: { choose: "Choose a category", offer: "offer", offers: "offers", indexedOffer: "indexed offer", indexedOffers: "indexed offers", subcategory: "subcategory", subcategories: "subcategories" },
};

export default function DepartmentScreen() {
  const router = useRouter();
  const { department } = useLocalSearchParams<{ department: string }>();
  const { locale, t } = useLocale();
  const text = copy[locale];
  const navigation = useFilonCatalogueNavigation();
  const item = navigation.data?.departments.find((candidate) => candidate.slug === department);
  const numberLocale = locale === "en" ? "en-BE" : `${locale}-BE`;
  const departmentName = item ? localizedTaxonomyLabel(item, locale) : t.catalogue;
  const subtitle = item
    ? `${item.count.toLocaleString(numberLocale)} ${item.count === 1 ? text.indexedOffer : text.indexedOffers}`
    : undefined;

  return <ScreenContainer className="" containerClassName="bg-background"><NativeCatalogueHeader title={departmentName} subtitle={subtitle} onBack={() => router.back()} />{navigation.isLoading ? <ActivityIndicator color="#C89544" style={styles.loader} /> : <FlatList data={item?.categories ?? []} keyExtractor={(category) => category.slug} contentContainerStyle={styles.content} ListHeaderComponent={<Text style={styles.hint}>{text.choose}</Text>} renderItem={({ item: category }) => { const categoryName = localizedTaxonomyLabel(category, locale); const offerCount = `${category.count.toLocaleString(numberLocale)} ${category.count === 1 ? text.offer : text.offers}`; const subcategoryCount = category.subcategories.length ? ` · ${category.subcategories.length} ${category.subcategories.length === 1 ? text.subcategory : text.subcategories}` : ""; const meta = `${offerCount}${subcategoryCount}`; return <Pressable accessibilityRole="button" accessibilityLabel={`${categoryName}, ${meta}`} onPress={() => router.push({ pathname: "/catalogue/[department]/[category]", params: { department: item?.slug ?? "", category: category.slug } } as never)} style={({ pressed }) => [styles.row, pressed && styles.pressed]}><View style={styles.words}><Text style={styles.name}>{categoryName}</Text><Text style={styles.meta}>{meta}</Text></View><MaterialIcons name="chevron-right" size={23} color="#C89544" /></Pressable>; }} ItemSeparatorComponent={() => <View style={{ height: 9 }} />} />}</ScreenContainer>;
}
const styles = StyleSheet.create({ loader: { marginTop: 48 }, content: { padding: 20, paddingBottom: 112 }, hint: { color: "#817A72", fontSize: 13, fontWeight: "700", marginBottom: 13 }, row: { minHeight: 78, paddingHorizontal: 16, flexDirection: "row", alignItems: "center", gap: 12, borderRadius: 18, backgroundColor: "#1A1714", borderWidth: 1, borderColor: "#332D28" }, words: { flex: 1 }, name: { color: "#E4DED4", fontSize: 16, fontWeight: "800" }, meta: { color: "#817A72", fontSize: 11, fontWeight: "700", marginTop: 6 }, pressed: { opacity: 0.72, transform: [{ scale: 0.98 }] } });
