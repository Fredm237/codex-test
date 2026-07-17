import { Nav } from "@/components/site/Nav";
import { Footer } from "@/components/site/Footer";
import { Atmosphere } from "@/components/site/Atmosphere";

// Marketing chrome (aurora background, nav, footer) — applies to every page in
// the (site) group but NOT to the full-bleed /experience route.
export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Atmosphere />
      <Nav />
      <main>{children}</main>
      <Footer />
    </>
  );
}
