import "@/components/editorial/editorial.css";
import { EditorialNav } from "@/components/editorial/EditorialNav";
import { EditorialFooter } from "@/components/editorial/EditorialFooter";
import { StickyCta } from "@/components/editorial/StickyCta";
import { SmoothScroll } from "@/components/editorial/SmoothScroll";

// Editorial (SmartWave) chrome for the whole marketing site.
export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SmoothScroll />
      <EditorialNav />
      <main id="top">{children}</main>
      <EditorialFooter />
      <StickyCta />
    </>
  );
}
