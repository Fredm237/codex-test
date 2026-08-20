import AsyncStorage from "@react-native-async-storage/async-storage";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Appearance, View, useColorScheme as useSystemColorScheme } from "react-native";
import { colorScheme as nativewindColorScheme, vars } from "nativewind";

import { SchemeColors, type ColorScheme } from "@/constants/theme";
import { resolveAppearance, type AppearancePreference } from "@/lib/theme-preference";

export type { AppearancePreference } from "@/lib/theme-preference";

type ThemeContextValue = {
  colorScheme: ColorScheme;
  appearancePreference: AppearancePreference;
  setColorScheme: (scheme: ColorScheme) => void;
  setAppearancePreference: (preference: AppearancePreference) => void;
};

const THEME_STORAGE_KEY = "filon.appearance.v1";
const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const systemScheme = (useSystemColorScheme() ?? "light") as ColorScheme;
  const [appearancePreference, setAppearancePreferenceState] = useState<AppearancePreference>("system");
  const resolvedScheme = resolveAppearance(appearancePreference, systemScheme);

  const applyScheme = useCallback((scheme: ColorScheme) => {
    nativewindColorScheme.set(scheme);
    if (typeof document !== "undefined") {
      const root = document.documentElement;
      root.dataset.theme = scheme;
      root.classList.toggle("dark", scheme === "dark");
      Object.entries(SchemeColors[scheme]).forEach(([token, value]) => root.style.setProperty(`--color-${token}`, value));
    }
  }, []);

  useEffect(() => {
    void AsyncStorage.getItem(THEME_STORAGE_KEY).then((stored) => {
      if (stored === "light" || stored === "dark" || stored === "system") setAppearancePreferenceState(stored);
    });
  }, []);

  useEffect(() => {
    applyScheme(resolvedScheme);
  }, [applyScheme, resolvedScheme]);

  const setAppearancePreference = useCallback((preference: AppearancePreference) => {
    setAppearancePreferenceState(preference);
    void AsyncStorage.setItem(THEME_STORAGE_KEY, preference);
    Appearance.setColorScheme?.(preference === "system" ? null : preference);
  }, []);

  const themeVariables = useMemo(() => vars(Object.fromEntries(Object.entries(SchemeColors[resolvedScheme]).map(([token, value]) => [`color-${token}`, value]))), [resolvedScheme]);
  const value = useMemo(() => ({ colorScheme: resolvedScheme, appearancePreference, setColorScheme: (scheme: ColorScheme) => setAppearancePreference(scheme), setAppearancePreference }), [appearancePreference, resolvedScheme, setAppearancePreference]);

  return <ThemeContext.Provider value={value}><View style={[{ flex: 1 }, themeVariables]}>{children}</View></ThemeContext.Provider>;
}

export function useThemeContext(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useThemeContext must be used within ThemeProvider");
  return ctx;
}
