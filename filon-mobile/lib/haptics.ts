import * as Haptics from "expo-haptics";
import { Platform } from "react-native";

export { hapticActionFor, type HapticAction } from "./haptic-rules";

function canHaptic() { return Platform.OS !== "web"; }

export const haptic = {
  light: () => { if (canHaptic()) void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); },
  medium: () => { if (canHaptic()) void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); },
  success: () => { if (canHaptic()) void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); },
  error: () => { if (canHaptic()) void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error); },
};
