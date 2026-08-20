import { type PropsWithChildren } from "react";
import { Pressable, StyleSheet, Text, View, type PressableProps, type ViewStyle } from "react-native";

import { useColors } from "@/hooks/use-colors";
import { haptic } from "@/lib/haptics";

export function TactileButton({ children, style, onPress, accessibilityLabel, hapticFeedback = true, ...props }: PropsWithChildren<PressableProps & { hapticFeedback?: boolean }>) {
  const styles = createStyles(useColors());
  return (
    <Pressable
      {...props}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={(event) => {
        if (hapticFeedback) haptic.light();
        onPress?.(event);
      }}
      style={({ pressed }) => [styles.button, style as ViewStyle, pressed && styles.pressed]}
    >
      {children}
    </Pressable>
  );
}

export function Eyebrow({ children }: PropsWithChildren) {
  const styles = createStyles(useColors());
  return <Text style={styles.eyebrow}>{children}</Text>;
}

export function StatusChip({ children, tone = "neutral" }: PropsWithChildren<{ tone?: "neutral" | "good" | "amber" }>) {
  const styles = createStyles(useColors());
  return <View style={[styles.chip, tone === "good" && styles.goodChip, tone === "amber" && styles.amberChip]}><Text style={[styles.chipText, tone === "good" && styles.goodText, tone === "amber" && styles.amberText]}>{children}</Text></View>;
}

function createStyles(colors: ReturnType<typeof useColors>) { return StyleSheet.create({
  button: { minHeight: 46, justifyContent: "center", alignItems: "center" },
  pressed: { opacity: 0.82, transform: [{ scale: 0.98 }] },
  eyebrow: { color: colors.primary, fontSize: 11, fontWeight: "800", letterSpacing: 1.4, textTransform: "uppercase" },
  chip: { alignSelf: "flex-start", paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  chipText: { color: colors.muted, fontSize: 11, fontWeight: "700" },
  goodChip: { backgroundColor: `${colors.success}20`, borderColor: `${colors.success}66` },
  goodText: { color: colors.success },
  amberChip: { backgroundColor: `${colors.primary}20`, borderColor: `${colors.primary}66` },
  amberText: { color: colors.primary },
}); }
