import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/cookies",
  title: "Politique cookies",
  description:
    "La politique cookies de FILON : nous n'utilisons aucun cookie de suivi publicitaire. Mesure d'audience sans cookie, cookies strictement nécessaires et cookies d'affiliation déposés par les partenaires — expliqués simplement.",
});

export default function CookiesPage() {
  return (
    <>
      <ContentHero
        eyebrow="Légal"
        title={<>Politique cookies</>}
        intro="FILON n'utilise pas de cookie de suivi publicitaire. Voici, en clair, les seuls cookies susceptibles d'être déposés et pourquoi."
        breadcrumb={[{ name: "Politique cookies", path: "/cookies" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Dernière mise à jour : 2026</p>

          <h2>Notre principe</h2>
          <p>
            Un cookie est un petit fichier déposé sur votre appareil lors de la visite d&apos;un site. Chez FILON, nous avons
            fait un choix simple&nbsp;: <b>aucun cookie de suivi publicitaire, aucun profilage</b>. Notre modèle ne repose pas
            sur la revente de données, donc nous n&apos;en collectons pas plus que nécessaire.
          </p>

          <h2>Mesure d&apos;audience sans cookie</h2>
          <p>
            Pour comprendre l&apos;usage du site et l&apos;améliorer, nous utilisons <b>Plausible Analytics</b>, une solution de
            mesure d&apos;audience <b>sans cookie</b> et sans donnée personnelle identifiable&nbsp;: pas d&apos;identifiant
            persistant, uniquement des statistiques agrégées et anonymes. Aucun consentement cookie n&apos;est donc requis pour
            cette mesure.
          </p>

          <h2>Cookies strictement nécessaires</h2>
          <p>
            Certains cookies purement techniques peuvent être nécessaires au bon fonctionnement du site (par exemple mémoriser
            une préférence d&apos;affichage). Ils ne servent ni au suivi ni à la publicité, et sont exemptés de consentement
            par la réglementation.
          </p>

          <h2>Cookies d&apos;affiliation des partenaires</h2>
          <p>
            Lorsque vous <b>activez une offre</b> via FILON (cashback, reconditionné, code promo), la plateforme ou le marchand
            partenaire peut déposer un <b>cookie d&apos;affiliation</b> sur votre appareil. Ce cookie permet d&apos;attribuer
            correctement l&apos;apport et, le cas échéant, de vous verser votre cashback. Il est déposé par le partenaire, sous
            sa propre responsabilité, au moment où vous choisissez d&apos;activer l&apos;offre — jamais à votre insu.
          </p>

          <h2>Gérer les cookies</h2>
          <p>
            Vous pouvez à tout moment consulter, bloquer ou supprimer les cookies depuis les réglages de votre navigateur
            (Chrome, Firefox, Edge, Safari…). Bloquer les cookies d&apos;affiliation peut toutefois empêcher l&apos;attribution
            de votre cashback chez le partenaire concerné.
          </p>

          <h2>En savoir plus</h2>
          <p>
            Cette politique complète notre <a href="/confidentialite">politique de confidentialité</a>. Pour toute question
            relative aux cookies, écrivez-nous à <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>.
          </p>
        </div>
      </section>
    </>
  );
}
