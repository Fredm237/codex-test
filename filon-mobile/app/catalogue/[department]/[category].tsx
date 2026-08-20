import { useLocalSearchParams, useRouter } from "expo-router";

import { NativeCatalogueHeader, NativeOfferResults } from "@/components/filon/native-catalogue";
import { ScreenContainer } from "@/components/screen-container";
import { useFilonCatalogueNavigation } from "@/hooks/use-filon-catalogue-navigation";

export default function CategoryScreen() {
  const router = useRouter();
  const { department, category } = useLocalSearchParams<{ department: string; category: string }>();
  const navigation = useFilonCatalogueNavigation();
  const parent = navigation.data?.departments.find((item) => item.slug === department);
  const selected = parent?.categories.find((item) => item.slug === category);
  return <ScreenContainer className="" containerClassName="bg-background"><NativeCatalogueHeader title={selected?.name ?? "Catalogue"} subtitle={parent?.name} onBack={() => router.back()} /><NativeOfferResults title={selected?.name ?? "Offres"} category={selected?.name} subcategories={selected?.subcategories} /></ScreenContainer>;
}
