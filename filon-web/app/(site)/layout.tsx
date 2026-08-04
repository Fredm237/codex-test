import "@/components/editorial/editorial.css";
// Chargé après editorial.css : à spécificité égale, la refonte gagne.
import "@/components/filon/filon.css";
import { EditorialNav } from "@/components/editorial/EditorialNav";
import { EditorialFooter } from "@/components/editorial/EditorialFooter";
import { StickyCta } from "@/components/editorial/StickyCta";
import { SmoothScroll } from "@/components/editorial/SmoothScroll";
import { MotionProvider } from "@/components/filon/MotionProvider";
import { PageTransition } from "@/components/filon/PageTransition";
import { ScrollToTop } from "@/components/filon/ScrollToTop";
import { LocaleProvider } from "@/lib/i18n";
import { getDepartments } from "@/lib/catalogue";

// Editorial (SmartWave) chrome for the whole marketing site.
//
// La taxonomie du méga-menu est lue ici, côté serveur, avec la même fonction que
// les pages rayon (cache d'une heure). Le menu la récupérait auparavant par un
// appel depuis le navigateur, sans revalidation : il dépendait du réseau du
// visiteur, n'était pas dans le HTML servi, et disparaissait sans un mot quand
// l'appel échouait.
export default async function SiteLayout({ children }: { children: React.ReactNode }) {
  const departments = await getDepartments();

  return (
    <LocaleProvider>
      <MotionProvider>
        <SmoothScroll />
        <EditorialNav departments={departments} />
        <main id="top">
          <PageTransition>{children}</PageTransition>
        </main>
        <EditorialFooter />
        <StickyCta />
        <ScrollToTop />
      </MotionProvider>
    </LocaleProvider>
  );
}
