export type FilonColorScheme = "light" | "dark";
export type AppearancePreference = FilonColorScheme | "system";

export function resolveAppearance(preference: AppearancePreference, systemScheme: FilonColorScheme): FilonColorScheme {
  return preference === "system" ? systemScheme : preference;
}
