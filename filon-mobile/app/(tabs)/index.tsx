import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Animated from "react-native-reanimated";

import { BrandMark } from "@/components/filon/brand-mark";
import { LivingSurface } from "@/components/filon/living-surface";
import { ScreenContainer } from "@/components/screen-container";
import { useColors } from "@/hooks/use-colors";
import { haptic } from "@/lib/haptics";
import { useLocale } from "@/lib/locale";

const ArrowRight = ({ size, color }: { size: number; color: string }) => <MaterialIcons name="arrow-forward" size={size} color={color} />;
const Search = ({ size, color }: { size: number; color: string }) => <MaterialIcons name="search" size={size} color={color} />;
const Sparkles = ({ size, color }: { size: number; color: string }) => <MaterialIcons name="auto-awesome" size={size} color={color} />;
const Grid = ({ size, color }: { size: number; color: string }) => <MaterialIcons name="grid-view" size={size} color={color} />;
const Target = ({ size, color }: { size: number; color: string }) => <MaterialIcons name="track-changes" size={size} color={color} />;

export default function HomeScreen() {
  const router = useRouter();
  const { t } = useLocale();
  const colors = useColors();
  return (
    <ScreenContainer className="" containerClassName="bg-background">
      <View style={styles.screen}>
        <View style={styles.top}><BrandMark /><Animated.View style={[styles.liveDot, { opacity: 0.9 }]} /></View>
          <View style={[styles.entry, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <LivingSurface variant="home" style={styles.livingMatter} />
          <Text style={[styles.prompt, { color: colors.foreground }]}>{t.searchPlaceholder}</Text>
          <Pressable accessibilityRole="button" accessibilityLabel={t.startSearch} onPress={() => { haptic.medium(); router.push("/catalogue/search"); }} style={({ pressed }) => [styles.searchAction, pressed && styles.pressed]}>
            <View style={styles.searchIcon}><Search size={22} color="#0E0C0B" /></View>
            <Text style={styles.searchText}>{t.startSearch}</Text>
            <ArrowRight size={20} color="#0E0C0B" />
          </Pressable>
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel={t.defineIntent} onPress={() => { haptic.light(); router.push("/intent" as never); }} style={({ pressed }) => [styles.intentEntry, { backgroundColor: colors.surface, borderColor: colors.border }, pressed && styles.pressed]}><View style={styles.intentIcon}><Target size={20} color="#C89544" /></View><View style={styles.intentWords}><Text style={[styles.intentLabel, { color: colors.foreground }]}>{t.defineIntent}</Text><Text style={[styles.intentHint, { color: colors.muted }]}>{t.intentHint}</Text></View><ArrowRight size={19} color="#C89544" /></Pressable>
        <View style={styles.shortcuts}>
          <Pressable accessibilityRole="button" accessibilityLabel={t.exploreCatalogue} onPress={() => { haptic.light(); router.push("/(tabs)/catalogue"); }} style={({ pressed }) => [styles.shortcut, { backgroundColor: colors.surface, borderColor: colors.border }, pressed && styles.pressed]}>
            <View style={styles.shortcutIcon}><Grid size={23} color="#C89544" /></View>
            <Text style={[styles.shortcutText, { color: colors.foreground }]}>{t.exploreCatalogue}</Text>
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={t.assistant} onPress={() => { haptic.light(); router.push("/(tabs)/assistant"); }} style={({ pressed }) => [styles.shortcut, { backgroundColor: colors.surface, borderColor: colors.border }, pressed && styles.pressed]}>
            <View style={styles.shortcutIcon}><Sparkles size={23} color="#C89544" /></View>
            <Text style={[styles.shortcutText, { color: colors.foreground }]}>{t.assistant}</Text>
          </Pressable>
        </View>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, padding: 20, paddingBottom: 18, justifyContent: "space-between" }, top: { minHeight: 38, flexDirection: "row", alignItems: "center", justifyContent: "space-between" }, liveDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: "#8FB072", shadowColor: "#8FB072", shadowOpacity: 0.75, shadowRadius: 9, elevation: 3 }, entry: { minHeight: 234, padding: 24, overflow: "hidden", justifyContent: "flex-end", borderRadius: 30, backgroundColor: "#1A1714", borderWidth: 1, borderColor: "#332D28" }, livingMatter: { position: "absolute", top: 0, left: 0, right: 0, height: 164 }, prompt: { color: "#E4DED4", fontSize: 26, lineHeight: 32, letterSpacing: -0.7, fontWeight: "800", maxWidth: 280, marginBottom: 20 }, searchAction: { minHeight: 60, paddingHorizontal: 12, flexDirection: "row", alignItems: "center", gap: 10, borderRadius: 19, backgroundColor: "#C89544" }, searchIcon: { width: 36, height: 36, borderRadius: 12, alignItems: "center", justifyContent: "center", backgroundColor: "rgba(14,12,11,0.12)" }, searchText: { flex: 1, color: "#0E0C0B", fontSize: 15, fontWeight: "900" }, intentEntry: { minHeight: 66, paddingHorizontal: 13, flexDirection: "row", alignItems: "center", gap: 10, borderRadius: 20, borderWidth: 1 }, intentIcon: { width: 38, height: 38, borderRadius: 13, alignItems: "center", justifyContent: "center", backgroundColor: "rgba(200,149,68,0.10)" }, intentWords: { flex: 1 }, intentLabel: { fontSize: 14, fontWeight: "900" }, intentHint: { fontSize: 11, fontWeight: "700", marginTop: 3 }, shortcuts: { flexDirection: "row", gap: 12 }, shortcut: { flex: 1, minHeight: 94, padding: 15, borderRadius: 22, justifyContent: "space-between", backgroundColor: "#171411", borderWidth: 1, borderColor: "#332D28" }, shortcutIcon: { width: 42, height: 42, borderRadius: 15, alignItems: "center", justifyContent: "center", backgroundColor: "rgba(200,149,68,0.10)" }, shortcutText: { color: "#E4DED4", fontSize: 14, fontWeight: "800" }, pressed: { opacity: 0.78, transform: [{ scale: 0.98 }] },
});
