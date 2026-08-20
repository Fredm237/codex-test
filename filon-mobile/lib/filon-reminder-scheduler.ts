import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

import type { PlannedOccasion } from "./filon-occasion-planner";
import { buildOccasionReminder } from "./filon-occasion-reminders";

export type ReminderScheduleResult = { status: "scheduled"; notificationId: string } | { status: "unsupported" | "permission_denied" | "past_or_invalid" };

/** N’est appelé qu’après un choix explicite de l’utilisateur. Sur le web, aucun rappel n’est programmé. */
export async function scheduleLocalOccasionReminder(occasion: PlannedOccasion): Promise<ReminderScheduleResult> {
  if (Platform.OS === "web") return { status: "unsupported" };
  const reminder = buildOccasionReminder(occasion);
  if (!reminder) return { status: "past_or_invalid" };
  let permission = await Notifications.getPermissionsAsync();
  if (!permission.granted) permission = await Notifications.requestPermissionsAsync();
  if (!permission.granted) return { status: "permission_denied" };
  const notificationId = await Notifications.scheduleNotificationAsync({ content: { title: "FILON · occasion à venir", body: `${occasion.title} approche. Votre tenue est prête à être consultée.`, data: { occasionId: occasion.id } }, trigger: { type: Notifications.SchedulableTriggerInputTypes.DATE, date: reminder.triggerAt } });
  return { status: "scheduled", notificationId };
}

export async function cancelLocalOccasionReminder(reminderId: string | undefined) {
  if (!reminderId || Platform.OS === "web") return;
  await Notifications.cancelScheduledNotificationAsync(reminderId);
}
