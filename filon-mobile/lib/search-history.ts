import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "filon.search-history.v1";
const LIMIT = 6;

export type RecentSearch = { query: string; at: string };

export function normalizeSearchQuery(value: string) { return value.trim().replace(/\s+/g, " "); }

export function applyRecentSearch(current: RecentSearch[], value: string, now = new Date().toISOString()): RecentSearch[] {
  const query = normalizeSearchQuery(value);
  if (query.length < 2) return current;
  const key = query.toLocaleLowerCase();
  return [{ query, at: now }, ...current.filter((item) => item.query.toLocaleLowerCase() !== key)].slice(0, LIMIT);
}

export async function readRecentSearches(): Promise<RecentSearch[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter((item): item is RecentSearch => Boolean(item && typeof item === "object" && typeof (item as RecentSearch).query === "string" && typeof (item as RecentSearch).at === "string")).slice(0, LIMIT) : [];
  } catch { return []; }
}

export async function saveRecentSearch(value: string) {
  const current = await readRecentSearches();
  const next = applyRecentSearch(current, value);
  if (next !== current) await AsyncStorage.setItem(KEY, JSON.stringify(next));
  return next;
}

export async function clearRecentSearches() { await AsyncStorage.removeItem(KEY); }
