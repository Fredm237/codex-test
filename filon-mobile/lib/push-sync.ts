import type { PushRegistration } from "./push-registration";

export type PushDeviceRegistrationInput = {
  expoToken: string;
  platform: "ios" | "android";
  permission: "granted";
};

export async function confirmPushRegistration(
  registration: PushRegistration,
  registerDevice: (input: PushDeviceRegistrationInput) => Promise<unknown>,
): Promise<PushRegistration["status"]> {
  if (registration.status !== "granted") return registration.status;
  await registerDevice({
    expoToken: registration.token,
    platform: registration.platform,
    permission: "granted",
  });
  return "granted";
}
