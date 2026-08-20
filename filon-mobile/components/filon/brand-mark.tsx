import { StyleSheet, Text, View, type ViewStyle } from "react-native";

export function BrandMark({ compact = false, style }: { compact?: boolean; style?: ViewStyle }) {
  return (
    <View style={[styles.wrap, compact && styles.compact, style]} accessibilityLabel="FILON">
      <View style={styles.vertical} />
      <View style={styles.top} />
      <View style={styles.middle} />
      {!compact && <Text style={styles.word}>FILON</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { height: 30, flexDirection: "row", alignItems: "center", position: "relative", paddingLeft: 18 },
  compact: { width: 24, paddingLeft: 0 },
  vertical: { position: "absolute", left: 0, top: 2, width: 4, height: 26, backgroundColor: "#C89544", borderRadius: 2 },
  top: { position: "absolute", left: 4, top: 2, width: 13, height: 4, backgroundColor: "#E4DED4", borderRadius: 2 },
  middle: { position: "absolute", left: 4, top: 12, width: 10, height: 4, backgroundColor: "#E4DED4", borderRadius: 2 },
  word: { color: "#E4DED4", fontSize: 15, fontWeight: "800", letterSpacing: 3.2, marginLeft: 7 },
});
