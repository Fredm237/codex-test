import { Tabs } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { HapticTab } from "@/components/haptic-tab";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Platform } from "react-native";
import { useColors } from "@/hooks/use-colors";
import { useLocale } from "@/lib/locale";

export default function TabLayout() {
  const colors = useColors();
  const { t } = useLocale();
  const insets = useSafeAreaInsets();
  const bottomPadding = Platform.OS === "web" ? 12 : Math.max(insets.bottom, 8);
  const tabBarHeight = 56 + bottomPadding;

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.tint,
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarStyle: {
          paddingTop: 8,
          paddingBottom: bottomPadding,
          height: tabBarHeight,
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          borderTopWidth: 0.5,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: t.home,
          tabBarIcon: ({ color }) => <IconSymbol size={28} name="house.fill" color={color} />,
        }}
      />
      <Tabs.Screen name="catalogue" options={{ title: t.catalogue, tabBarIcon: ({ color }) => <IconSymbol size={25} name="square.grid.2x2.fill" color={color} /> }} />
      <Tabs.Screen name="assistant" options={{ title: t.assistant, tabBarIcon: ({ color }) => <IconSymbol size={25} name="sparkles" color={color} /> }} />
      <Tabs.Screen name="saved" options={{ title: t.saved, tabBarIcon: ({ color }) => <IconSymbol size={25} name="bookmark.fill" color={color} /> }} />
      <Tabs.Screen name="profile" options={{ title: t.profile, tabBarIcon: ({ color }) => <IconSymbol size={25} name="slider.horizontal.3" color={color} /> }} />
    </Tabs>
  );
}
