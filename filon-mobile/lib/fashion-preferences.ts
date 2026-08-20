import AsyncStorage from "@react-native-async-storage/async-storage";

export type FashionPreferences = {
  declaredStyle: "minimal" | "classic" | "bold" | null;
  updatedAt: string | null;
};

const STORAGE_KEY = "filon.intelligence.fashion-preferences.v1";
export const defaultFashionPreferences: FashionPreferences = { declaredStyle: null, updatedAt: null };

function isStyle(value: unknown): value is FashionPreferences["declaredStyle"] {
  return value === "minimal" || value === "classic" || value === "bold" || value === null;
}

export async function readFashionPreferences(): Promise<FashionPreferences> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultFashionPreferences;
    const parsed = JSON.parse(raw) as Partial<FashionPreferences>;
    if (!isStyle(parsed.declaredStyle)) return defaultFashionPreferences;
    return { declaredStyle: parsed.declaredStyle, updatedAt: typeof parsed.updatedAt === "string" ? parsed.updatedAt : null };
  } catch {
    return defaultFashionPreferences;
  }
}

export async function saveFashionPreferences(next: Pick<FashionPreferences, "declaredStyle">): Promise<FashionPreferences> {
  const value: FashionPreferences = { declaredStyle: next.declaredStyle, updatedAt: new Date().toISOString() };
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  return value;
}

export async function resetFashionPreferences() {
  await AsyncStorage.removeItem(STORAGE_KEY);
  return defaultFashionPreferences;
}
