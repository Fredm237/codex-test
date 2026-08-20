import { Image } from "expo-image";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { FilonOffer } from "@/lib/filon-api";
import { openPartnerOffer } from "@/lib/open-partner-offer";
import { useColors } from "@/hooks/use-colors";

type OfferCardProps = { offer: FilonOffer; price: string; openLabel: string; inStockLabel: string; unavailableLabel: string; unknownLabel?: string; comparisonLabel?: string; onPress?: () => void };

export function OfferCard({ offer, price, openLabel, inStockLabel, unavailableLabel, unknownLabel = unavailableLabel, comparisonLabel, onPress }: OfferCardProps) {
  const openMerchant = () => { void openPartnerOffer(offer.link); };
  const colors = useColors();
  const styles = createStyles(colors);
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={`${openLabel} ${offer.merchantName}`} onPress={onPress ?? openMerchant} style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
      <View style={styles.imageShell}>{offer.imageUrl ? <Image source={{ uri: offer.imageUrl }} style={styles.image} contentFit="contain" transition={160} accessibilityLabel="" /> : <View style={styles.imageFallback}><Text style={styles.imageFallbackText}>F</Text></View>}</View>
      <View style={styles.content}>
        <View style={styles.merchantLine}><Text numberOfLines={1} style={styles.merchant}>{offer.merchantName}</Text>{comparisonLabel ? <Text style={styles.comparison}>{comparisonLabel}</Text> : null}</View>
        <Text numberOfLines={2} style={styles.name}>{offer.name}</Text>
        <View style={styles.bottom}><View><Text style={styles.price}>{price}</Text><Text style={[styles.stock, offer.inStock === false ? styles.unavailable : offer.inStock === null ? styles.unknown : null]}>{offer.inStock === true ? inStockLabel : offer.inStock === false ? unavailableLabel : unknownLabel}</Text></View><MaterialIcons name="open-in-new" size={18} color={colors.primary} /></View>
      </View>
    </Pressable>
  );
}

function createStyles(colors: ReturnType<typeof useColors>) {
  return StyleSheet.create({
    card: { minHeight: 142, padding: 10, flexDirection: "row", gap: 12, borderRadius: 19, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
    imageShell: { width: 102, height: 120, overflow: "hidden", borderRadius: 13, backgroundColor: colors.background, alignItems: "center", justifyContent: "center" }, image: { width: "100%", height: "100%" }, imageFallback: { alignItems: "center", justifyContent: "center", width: "100%", height: "100%", backgroundColor: `${colors.primary}12` }, imageFallbackText: { color: colors.primary, fontSize: 30, fontWeight: "800" },
    content: { flex: 1, paddingTop: 4, paddingRight: 3, justifyContent: "space-between" }, merchantLine: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 6 }, merchant: { flex: 1, color: colors.primary, fontSize: 11, fontWeight: "800", letterSpacing: 0.4 }, comparison: { color: colors.success, fontSize: 9, fontWeight: "800", textTransform: "uppercase", letterSpacing: 0.45 }, name: { color: colors.foreground, fontSize: 13, lineHeight: 18, fontWeight: "700", marginTop: 5 }, bottom: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-end", gap: 8 }, price: { color: colors.foreground, fontSize: 20, fontWeight: "800", letterSpacing: -0.4 }, stock: { color: colors.success, fontSize: 11, fontWeight: "600", marginTop: 2 }, unavailable: { color: colors.error }, unknown: { color: colors.warning }, pressed: { opacity: 0.73, transform: [{ scale: 0.987 }] },
  });
}
