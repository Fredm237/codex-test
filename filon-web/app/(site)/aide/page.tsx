import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, InfoGrid, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/aide",
  title: "Centre d'aide",
  description:
    "Besoin d'un coup de main avec FILON ? Prise en main, cashback, reconditionné, extension, compte et données : les réponses par thème, et un contact humain quand il vous faut.",
});

export default function AidePage() {
  return (
    <>
      <ContentHero
        eyebrow="Aide"
        title={<>On est là quand vous en avez <span className="it">besoin</span>.</>}
        intro="Choisissez un thème pour trouver rapidement votre réponse. Et si vous ne trouvez pas, un humain vous répond, pas un robot qui tourne en rond."
        breadcrumb={[{ name: "Centre d'aide", path: "/aide" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <InfoGrid
            items={[
              { n: "01", h: "Prise en main", p: "Comment poser un besoin, lire le verdict et activer la meilleure offre. Voir « Comment ça marche »." },
              { n: "02", h: "Cashback", p: "Plateformes comparées, cumul avec un code promo, délais de validation et de retrait." },
              { n: "03", h: "Reconditionné", p: "Grades, garanties, vendeurs certifiés et calcul de l'économie réelle." },
              { n: "04", h: "Extension", p: "Installation, navigateurs pris en charge, ce qui s'affiche sur une fiche produit." },
              { n: "05", h: "Compte & alertes", p: "Créer un compte, gérer les alertes de baisse de prix et vos préférences." },
              { n: "06", h: "Données & confidentialité", p: "Ce que FILON lit, ce qu'il ne fait pas, et comment exercer vos droits RGPD." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Vous ne trouvez pas ? <span className="it">Écrivez-nous</span>.</>} alt>
        <p>
          La plupart des réponses se trouvent dans notre <a href="/faq">FAQ</a> et sur la page{" "}
          <a href="/comment-ca-marche">Comment ça marche</a>. Pour tout le reste, notre équipe répond directement.
        </p>
        <p>
          Contactez-nous à <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a> ou via le{" "}
          <a href="/contact">formulaire de contact</a>. Nous revenons vers vous rapidement, en français ou en néerlandais.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Prêt·e à ne plus <span className="it">surpayer</span> ?</>} sub="Ajoutez FILON et laissez le copilote faire le travail avant chaque achat." />
    </>
  );
}
