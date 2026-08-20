import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { CameraView, useCameraPermissions, type BarcodeScanningResult } from "expo-camera";
import { router } from "expo-router";
import { useState } from "react";
import { Platform, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { DataPulseTrack, DataReveal } from "@/components/filon/data-motion";
import { TactileButton } from "@/components/filon/filon-ui";
import { LivingSurface } from "@/components/filon/living-surface";
import { ScreenContainer } from "@/components/screen-container";
import { useColors } from "@/hooks/use-colors";
import { normalizeProductCode } from "@/lib/barcode";
import { getFilonProductByEan } from "@/lib/filon-api";
import { haptic } from "@/lib/haptics";
import { useLocale } from "@/lib/locale";
import { resolveScanLookupState, type ScanLookupState } from "@/lib/scan-status";

const copy = {
  fr: { title: "Scanner un produit", intro: "Visez le code-barres pour retrouver les offres partenaires vérifiées.", back: "Retour", activate: "Autoriser la caméra", denied: "La caméra est désactivée. Vous pouvez autoriser l’accès ou saisir le code manuellement.", manual: "Saisir un code", placeholder: "EAN, UPC ou code produit", search: "Vérifier ce code", invalid: "Saisissez un code EAN, UPC ou produit valide.", unmatched: "Ce code ne correspond pas encore à un produit regroupé vérifié dans FILON.", unavailable: "Le catalogue est momentanément indisponible. Réessayez dans un instant.", frame: "Placez le code-barres dans le cadre", verifying: "Vérification du catalogue partenaire…", verified: "Lecture vérifiée" },
  nl: { title: "Een product scannen", intro: "Richt op de barcode om geverifieerde partneraanbiedingen te vinden.", back: "Terug", activate: "Camera toestaan", denied: "De camera is uitgeschakeld. Sta toegang toe of voer de code handmatig in.", manual: "Een code invoeren", placeholder: "EAN, UPC of productcode", search: "Deze code controleren", invalid: "Voer een geldige EAN-, UPC- of productcode in.", unmatched: "Deze code komt nog niet overeen met een geverifieerd gegroepeerd product in FILON.", unavailable: "De catalogus is tijdelijk niet beschikbaar. Probeer het zo opnieuw.", frame: "Plaats de barcode in het kader", verifying: "Partnercatalogus controleren…", verified: "Geverifieerde lezing" },
  en: { title: "Scan a product", intro: "Point at the barcode to find verified partner offers.", back: "Back", activate: "Allow camera", denied: "The camera is disabled. Allow access or enter the code manually.", manual: "Enter a code", placeholder: "EAN, UPC or product code", search: "Verify this code", invalid: "Enter a valid EAN, UPC, or product code.", unmatched: "This code does not yet match a verified grouped product in FILON.", unavailable: "The catalogue is temporarily unavailable. Please try again shortly.", frame: "Place the barcode inside the frame", verifying: "Checking partner catalogue…", verified: "Verified scan" },
};

export default function ScanScreen() {
  const { locale } = useLocale();
  const text = copy[locale];
  const colors = useColors();
  const styles = createStyles(colors);
  const [permission, requestPermission] = useCameraPermissions();
  const [code, setCode] = useState("");
  const [scanned, setScanned] = useState(false);
  const [status, setStatus] = useState<ScanLookupState>("idle");

  const submit = async (value = code) => {
    const normalized = normalizeProductCode(value);
    if (!normalized) { setStatus("invalid"); return; }
    setStatus("checking");
    setScanned(true);
    try {
      const product = await getFilonProductByEan(normalized);
      if (product) { haptic.success(); router.replace({ pathname: "/product/ean/[ean]", params: { ean: normalized } } as never); return; }
      setStatus(resolveScanLookupState(false, false));
      setScanned(false);
    } catch {
      setStatus(resolveScanLookupState(false, true));
      setScanned(false);
    }
  };

  const onBarcodeScanned = ({ data }: BarcodeScanningResult) => { if (!scanned) void submit(data); };
  const statusMessage = status === "invalid" ? text.invalid : status === "unmatched" ? text.unmatched : status === "unavailable" ? text.unavailable : null;

  return (
    <ScreenContainer className="" containerClassName="bg-background" edges={["top", "left", "right", "bottom"]}>
      <View style={styles.content}>
        <DataReveal>
          <TactileButton accessibilityLabel={text.back} onPress={() => router.back()} style={styles.back}>
            <MaterialIcons name="arrow-back" size={20} color={colors.foreground} />
            <Text style={styles.backText}>{text.back}</Text>
          </TactileButton>
        </DataReveal>
        <DataReveal index={1}>
          <View style={styles.headingRow}>
            <View style={styles.scanMark}><MaterialIcons name="qr-code-scanner" size={20} color={colors.primary} /></View>
            <View style={styles.headingWords}><Text style={styles.title}>{text.title}</Text><Text style={styles.intro}>{text.intro}</Text></View>
          </View>
        </DataReveal>
        <DataReveal index={2}>
          {permission?.granted && Platform.OS !== "web" ? (
            <View style={styles.cameraShell}>
              <CameraView style={styles.camera} facing="back" barcodeScannerSettings={{ barcodeTypes: ["ean13", "ean8", "upc_a", "upc_e", "code128"] }} onBarcodeScanned={scanned ? undefined : onBarcodeScanned} />
              <View style={styles.overlay} pointerEvents="none"><View style={styles.frame} /><Text style={styles.frameText}>{text.frame}</Text></View>
            </View>
          ) : (
            <View style={styles.permission}>
              <LivingSurface variant="catalogue" style={styles.permissionMotion} />
              <View style={styles.permissionIcon}><MaterialIcons name="photo-camera" size={27} color={colors.primary} /></View>
              <Text style={styles.permissionKicker}>{text.verified}</Text>
              <Text style={styles.permissionText}>{permission && !permission.granted ? text.denied : text.intro}</Text>
              <TactileButton accessibilityLabel={text.activate} onPress={() => void requestPermission()} style={styles.permissionButton}><Text style={styles.permissionButtonText}>{text.activate}</Text></TactileButton>
            </View>
          )}
        </DataReveal>
        <DataReveal index={3}>
          <View style={styles.manual}>
            <Text style={styles.manualTitle}>{text.manual}</Text>
            <View style={styles.inputShell}>
              <TextInput value={code} onChangeText={(value) => { setCode(value); setStatus("idle"); }} onSubmitEditing={() => void submit()} returnKeyType="search" keyboardType="number-pad" placeholder={text.placeholder} placeholderTextColor={colors.muted} style={styles.input} accessibilityLabel={text.placeholder} />
              <Pressable disabled={scanned} accessibilityRole="button" accessibilityLabel={text.search} onPress={() => void submit()} style={({ pressed }) => [styles.search, (pressed || scanned) && styles.searchPressed]}><MaterialIcons name={scanned ? "hourglass-empty" : "arrow-forward"} size={20} color={colors.background} /></Pressable>
            </View>
          </View>
        </DataReveal>
        {status === "checking" ? <DataReveal index={4}><View style={styles.checking}><DataPulseTrack percentage={100} color={colors.primary} trackColor={colors.border} /><Text style={styles.verifying}>{text.verifying}</Text></View></DataReveal> : null}
        {statusMessage ? <DataReveal index={4}><View style={styles.status}><MaterialIcons name={status === "unavailable" ? "cloud-off" : "info-outline"} size={17} color={status === "unavailable" ? colors.error : colors.warning} /><Text accessibilityRole="alert" style={[styles.statusText, { color: status === "unavailable" ? colors.error : colors.warning }]}>{statusMessage}</Text></View></DataReveal> : null}
      </View>
    </ScreenContainer>
  );
}

function createStyles(colors: ReturnType<typeof useColors>) {
  return StyleSheet.create({
    content: { flex: 1, padding: 20 }, back: { alignSelf: "flex-start", minHeight: 44, paddingHorizontal: 10, borderRadius: 14, flexDirection: "row", gap: 8, backgroundColor: colors.surface }, backText: { color: colors.foreground, fontSize: 14, fontWeight: "700" }, headingRow: { marginTop: 22, flexDirection: "row", alignItems: "flex-start", gap: 12 }, scanMark: { width: 44, height: 44, alignItems: "center", justifyContent: "center", borderRadius: 15, backgroundColor: `${colors.primary}14`, borderWidth: 1, borderColor: `${colors.primary}34` }, headingWords: { flex: 1 }, title: { color: colors.foreground, fontSize: 27, lineHeight: 32, fontWeight: "900", letterSpacing: -0.6 }, intro: { color: colors.muted, fontSize: 13, lineHeight: 19, marginTop: 5 }, cameraShell: { height: 285, overflow: "hidden", marginTop: 24, borderRadius: 25, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, camera: { flex: 1 }, overlay: { ...StyleSheet.absoluteFillObject, alignItems: "center", justifyContent: "center", backgroundColor: `${colors.background}1A` }, frame: { width: "76%", height: 150, borderRadius: 20, borderWidth: 2, borderColor: colors.primary, shadowColor: colors.primary, shadowOpacity: 0.3, shadowRadius: 16 }, frameText: { color: colors.foreground, fontSize: 12, fontWeight: "800", marginTop: 15, textShadowColor: colors.background, textShadowRadius: 4 }, permission: { minHeight: 285, overflow: "hidden", marginTop: 24, padding: 25, alignItems: "center", justifyContent: "center", borderRadius: 25, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, permissionMotion: { opacity: 0.58 }, permissionIcon: { width: 52, height: 52, alignItems: "center", justifyContent: "center", borderRadius: 17, backgroundColor: `${colors.primary}14`, borderWidth: 1, borderColor: `${colors.primary}36` }, permissionKicker: { color: colors.primary, fontSize: 10, fontWeight: "900", letterSpacing: 0.7, textTransform: "uppercase", marginTop: 14 }, permissionText: { color: colors.muted, textAlign: "center", fontSize: 13, lineHeight: 20, marginTop: 8 }, permissionButton: { minHeight: 48, marginTop: 18, paddingHorizontal: 18, borderRadius: 16, backgroundColor: colors.primary }, permissionButtonText: { color: colors.background, fontSize: 13, fontWeight: "900" }, manual: { marginTop: 22 }, manualTitle: { color: colors.foreground, fontSize: 15, fontWeight: "900", marginBottom: 9 }, inputShell: { minHeight: 54, paddingLeft: 15, flexDirection: "row", alignItems: "center", borderRadius: 17, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, input: { flex: 1, minHeight: 50, color: colors.foreground, fontSize: 15 }, search: { width: 52, alignSelf: "stretch", alignItems: "center", justifyContent: "center", borderRadius: 15, backgroundColor: colors.primary }, searchPressed: { opacity: 0.65 }, checking: { minHeight: 46, marginTop: 12, paddingHorizontal: 13, flexDirection: "row", alignItems: "center", gap: 10, borderRadius: 14, backgroundColor: `${colors.primary}10`, borderWidth: 1, borderColor: `${colors.primary}2B` }, verifying: { flex: 1, color: colors.primary, fontSize: 12, fontWeight: "800" }, status: { minHeight: 56, marginTop: 12, padding: 12, flexDirection: "row", alignItems: "center", gap: 9, borderRadius: 15, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, statusText: { flex: 1, fontSize: 12, lineHeight: 17, fontWeight: "700" },
  });
}
