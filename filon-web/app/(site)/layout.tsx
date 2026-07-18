import "@/components/editorial/editorial.css";
import { EditorialNav } from "@/components/editorial/EditorialNav";
import { EditorialFooter } from "@/components/editorial/EditorialFooter";

// Editorial (SmartWave) chrome for the whole marketing site.
export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <EditorialNav />
      <main id="top">{children}</main>
      <EditorialFooter />
    </>
  );
}
