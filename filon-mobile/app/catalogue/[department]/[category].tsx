import { useLocalSearchParams, useRouter } from "expo-router";

import { NativeCatalogueHeader, NativeOfferResults } from "@/components/filon/native-catalogue";
import { ScreenContainer } from "@/components/screen-container";
import { useFilonCatalogueNavigation } from "@/hooks/use-filon-catalogue-navigation";
import { useLocale } from "@/lib/locale";
import { localizedTaxonomyLabel } from "@/lib/taxonomy-presentation";

const copy = {
  fr: { offers: "Offres" },
  nl: { offers: "Aanbiedingen" },
  en: { offers: "Offers" },
};

export default function CategoryScreen() {
  const router = useRouter();
  const { department, category } = useLocalSearchParams<{ department: string; category: string }>();
  const { locale, t } = useLocale();
  const navigation = useFilonCatalogueNavigation();
  const parent = navigation.data?.departments.find((item) => item.slug === department);
  const selected = parent?.categories.find((item) => item.slug === category);
  const selectedName = selected ? localizedTaxonomyLabel(selected, locale) : copy[locale].offers;
  const parentName = parent ? localizedTaxonomyLabel(parent, locale) : undefined;
  return <ScreenContainer className="" containerClassName="bg-background"><NativeCatalogueHeader title={selected ? selectedName : t.catalogue} subtitle={parentName} onBack={() => router.back()} /><NativeOfferResults title={selectedName} category={selected?.name} subcategories={selected?.subcategories} /></ScreenContainer>;
}
