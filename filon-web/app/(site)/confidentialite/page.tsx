import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/confidentialite",
  title: "Politique de confidentialité",
  description:
    "Comment FILON protège vos données : aucune revente, analytics sans cookie, formulaires, liens affiliés et vos droits RGPD.",
});

export default function ConfidentialitePage() {
  return (
    <>
      <ContentHero
        eyebrow="Confidentialité"
        title={<>Vos données restent les vôtres.</>}
        intro="La transparence est le cœur de FILON — cela vaut aussi pour vos données. Voici, en clair, ce que nous collectons, pourquoi, et vos droits."
        breadcrumb={[{ name: "Confidentialité", path: "/confidentialite" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Dernière mise à jour : 2026</p>

          <h2>En résumé</h2>
          <ul>
            <li>Nous ne construisons <b>aucun profil publicitaire</b> et ne <b>revendons aucune donnée</b>.</li>
            <li>Notre mesure d&apos;audience est <b>sans cookie</b> et anonyme (Plausible).</li>
            <li>Nous ne collectons des données personnelles que si <b>vous nous les fournissez</b> (contact, newsletter).</li>
            <li>Les liens affiliés n&apos;augmentent <b>jamais</b> votre prix.</li>
          </ul>

          <h2>Responsable du traitement</h2>
          <p>
            {site.founder}, éditeur du site {site.domain} ({site.city}, Belgique). Pour toute question :{" "}
            <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>.
          </p>

          <h2>Données que nous traitons</h2>
          <p>
            <b>Formulaire de contact</b> : nom, adresse e-mail et message, pour répondre à votre demande. Base légale :
            votre consentement / notre intérêt légitime à vous répondre.
          </p>
          <p>
            <b>Newsletter</b> : votre adresse e-mail, pour vous informer du lancement et des nouveautés. Base légale : votre
            consentement. Vous pouvez vous désinscrire à tout moment.
          </p>
          <p>
            <b>Mesure d&apos;audience</b> : nous utilisons Plausible Analytics, une solution respectueuse de la vie privée,
            <b> sans cookie</b> et sans donnée personnelle identifiable (pas d&apos;identifiant persistant, statistiques
            agrégées). Aucun bandeau de consentement n&apos;est donc requis pour ce traitement.
          </p>

          <h2>Cookies</h2>
          <p>
            Le site ne dépose <b>pas de cookie de suivi publicitaire</b>. Seuls d&apos;éventuels cookies strictement
            nécessaires au bon fonctionnement peuvent être utilisés. Vous gardez le contrôle via les réglages de votre
            navigateur.
          </p>

          <h2>Liens affiliés</h2>
          <p>
            Lorsque vous activez une offre via FILON, un cookie d&apos;affiliation peut être déposé par la plateforme
            partenaire (iGraal, Poulpeo, Back Market, etc.) afin de rattacher votre achat — c&apos;est ce qui permet le
            cashback et notre rémunération. Ce traitement relève de la politique de confidentialité de chaque partenaire.
          </p>

          <h2>Sous-traitants</h2>
          <ul>
            <li><b>Hostinger</b> — hébergement du site.</li>
            <li><b>Plausible Analytics</b> — mesure d&apos;audience sans cookie.</li>
            <li><b>Formspree</b> (ou équivalent) — acheminement des messages de contact et inscriptions.</li>
          </ul>

          <h2>Durée de conservation</h2>
          <p>
            Les messages de contact sont conservés le temps nécessaire au traitement de votre demande. Les adresses
            newsletter le sont jusqu&apos;à votre désinscription.
          </p>

          <h2>Vos droits (RGPD)</h2>
          <p>
            Vous disposez d&apos;un droit d&apos;accès, de rectification, d&apos;effacement, de limitation, d&apos;opposition
            et de portabilité de vos données. Pour les exercer, écrivez à{" "}
            <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. Vous pouvez également introduire une
            réclamation auprès de l&apos;Autorité de protection des données (APD), en Belgique.
          </p>
        </div>
      </section>
    </>
  );
}
