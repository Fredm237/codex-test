import * as WebBrowser from "expo-web-browser";

import { isSafePartnerOfferUrl } from "@/lib/partner-offer";

export async function openPartnerOffer(url: string) {
  if (!isSafePartnerOfferUrl(url)) return { opened: false as const, reason: "invalid" as const };
  await WebBrowser.openBrowserAsync(url, { toolbarColor: "#0E0C0B", controlsColor: "#C89544", presentationStyle: WebBrowser.WebBrowserPresentationStyle.AUTOMATIC, enableBarCollapsing: true });
  return { opened: true as const };
}
