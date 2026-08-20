import Constants from "expo-constants";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

export type PushRegistration = { status: "granted"; token: string; platform: "ios" | "android" } | { status: "denied" | "unavailable" | "failed" };

export async function requestPushRegistration(): Promise<PushRegistration> {
  if (Platform.OS !== "ios" && Platform.OS !== "android") return { status: "unavailable" };
  const projectId = (Constants.expoConfig?.extra as { eas?: { projectId?: string } } | undefined)?.eas?.projectId;
  if (!projectId) return { status: "unavailable" };
  if (Platform.OS === "android") await Notifications.setNotificationChannelAsync("price-alerts", { name: "Price alerts", importance: Notifications.AndroidImportance.DEFAULT, lightColor: "#C89544" });
  const existing = await Notifications.getPermissionsAsync();
  const permission = existing.status === "granted" ? existing : await Notifications.requestPermissionsAsync();
  if (permission.status !== "granted") return { status: "denied" };
  try {
    const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
    return { status: "granted", token, platform: Platform.OS };
  } catch {
    return { status: "failed" };
  }
}
