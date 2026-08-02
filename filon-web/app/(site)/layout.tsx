import "@/components/editorial/editorial.css";
// Chargé après editorial.css : à spécificité égale, la refonte gagne.
import "@/components/filon/filon.css";
import { EditorialNav } from "@/components/editorial/EditorialNav";
import { EditorialFooter } from "@/components/editorial/EditorialFooter";
import { StickyCta } from "@/components/editorial/StickyCta";
import { SmoothScroll } from "@/components/editorial/SmoothScroll";
import { LocaleProvider } from "@/lib/i18n";

// Editorial (SmartWave) chrome for the whole marketing site.
export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <LocaleProvider>
      <SmoothScroll />
      <EditorialNav />
      <main id="top">{children}</main>
      <EditorialFooter />
      <StickyCta />
    </LocaleProvider>
  );
}
