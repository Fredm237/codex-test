import { Image } from "expo-image";
import { useEffect } from "react";
import { StyleSheet, View, type StyleProp, type ViewStyle } from "react-native";
import Animated, { Easing, interpolate, useAnimatedStyle, useReducedMotion, useSharedValue, withRepeat, withTiming } from "react-native-reanimated";

import { useColors } from "@/hooks/use-colors";

const MATERIAL_URL = "/manus-storage/filon-amber-material_4159f0c1.png";

export function LivingSurface({ variant = "home", style }: { variant?: "home" | "catalogue" | "intelligence"; style?: StyleProp<ViewStyle> }) {
  const colors = useColors();
  const reducedMotion = useReducedMotion();
  const drift = useSharedValue(0);
  const scan = useSharedValue(0);
  useEffect(() => {
    if (reducedMotion) { drift.value = 0.5; scan.value = 0.4; return; }
    drift.value = withRepeat(withTiming(1, { duration: 12000, easing: Easing.inOut(Easing.quad) }), -1, true);
    scan.value = withRepeat(withTiming(1, { duration: 4200, easing: Easing.inOut(Easing.sin) }), -1, true);
  }, [drift, reducedMotion, scan]);
  const materialStyle = useAnimatedStyle(() => ({ opacity: reducedMotion ? 0.18 : interpolate(scan.value, [0, 1], [0.13, 0.28]), transform: [{ scale: interpolate(drift.value, [0, 1], [1.04, 1.16]) }, { translateX: interpolate(drift.value, [0, 1], [-10, 16]) }, { translateY: interpolate(drift.value, [0, 1], [4, -12]) }] }));
  const beamStyle = useAnimatedStyle(() => ({ opacity: reducedMotion ? 0.36 : interpolate(scan.value, [0, 1], [0.16, 0.72]), transform: [{ translateX: interpolate(scan.value, [0, 1], [-70, 148]) }, { rotate: "-17deg" }] }));
  const markerStyle = useAnimatedStyle(() => ({ opacity: reducedMotion ? 0.55 : interpolate(scan.value, [0, 1], [0.3, 0.95]), transform: [{ scale: interpolate(scan.value, [0, 1], [0.82, 1.14]) }] }));
  return <View pointerEvents="none" accessibilityElementsHidden style={[styles.wrap, style]}><Animated.View style={[styles.material, materialStyle]}><Image source={{ uri: MATERIAL_URL }} contentFit="cover" style={styles.image} /></Animated.View><View style={[styles.vignette, { backgroundColor: colors.surface }]} /><Animated.View style={[styles.beam, { backgroundColor: colors.primary }, beamStyle]} /><Animated.View style={[styles.marker, { backgroundColor: colors.primary, shadowColor: colors.primary }, markerStyle]} /><View style={[styles.gridLine, styles.gridOne, { borderColor: `${colors.primary}40` }]} /><View style={[styles.gridLine, styles.gridTwo, { borderColor: `${colors.primary}25` }]} /></View>;
}

const styles = StyleSheet.create({ wrap: { position: "absolute", inset: 0, overflow: "hidden" }, material: { ...StyleSheet.absoluteFillObject }, image: { width: "100%", height: "100%" }, vignette: { ...StyleSheet.absoluteFillObject, opacity: 0.52 }, beam: { position: "absolute", top: "46%", left: -80, width: 180, height: 1 }, marker: { position: "absolute", top: 31, right: 29, width: 7, height: 7, borderRadius: 2, shadowOpacity: 0.85, shadowRadius: 12, elevation: 5 }, gridLine: { position: "absolute", borderWidth: 1, borderRadius: 17 }, gridOne: { width: 136, height: 82, top: -28, right: -16 }, gridTwo: { width: 118, height: 92, bottom: -50, left: 28 } });
