import { useEffect, type ReactNode } from "react";
import { StyleSheet, View, type StyleProp, type ViewStyle } from "react-native";
import Animated, { Easing, interpolate, useAnimatedStyle, useReducedMotion, useSharedValue, withDelay, withTiming } from "react-native-reanimated";

export function DataReveal({ children, index = 0, style }: { children: ReactNode; index?: number; style?: StyleProp<ViewStyle> }) {
  const reducedMotion = useReducedMotion();
  const progress = useSharedValue(reducedMotion ? 1 : 0);
  useEffect(() => { progress.value = reducedMotion ? 1 : withDelay(Math.min(index, 5) * 55, withTiming(1, { duration: 260, easing: Easing.out(Easing.cubic) })); }, [index, progress, reducedMotion]);
  const animated = useAnimatedStyle(() => ({ opacity: progress.value, transform: [{ translateY: interpolate(progress.value, [0, 1], [reducedMotion ? 0 : 10, 0]) }] }));
  return <Animated.View style={[animated, style]}>{children}</Animated.View>;
}

export function DataPulseTrack({ percentage, color, trackColor }: { percentage: number; color: string; trackColor: string }) {
  const reducedMotion = useReducedMotion();
  const progress = useSharedValue(reducedMotion ? 1 : 0);
  const target = Math.min(Math.max(percentage, 0), 100);
  useEffect(() => { progress.value = reducedMotion ? 1 : withTiming(1, { duration: 420, easing: Easing.out(Easing.cubic) }); }, [progress, reducedMotion, target]);
  const bar = useAnimatedStyle(() => ({ width: `${interpolate(progress.value, [0, 1], [0, target])}%` }));
  return <View style={[styles.track, { backgroundColor: trackColor }]}><Animated.View style={[styles.fill, { backgroundColor: color }, bar]} /></View>;
}

const styles = StyleSheet.create({ track: { width: 42, height: 3, overflow: "hidden", borderRadius: 2 }, fill: { height: "100%", borderRadius: 2 } });
