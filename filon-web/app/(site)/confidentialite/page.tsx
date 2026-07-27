import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/confidentialite",
  title: "Politique de confidentialité",
  description:
    "Comment FILON protège vos données : aucune revente, analytics sans cookie, formulaires, liens partenaires et vos droits RGPD.",
});

function ConfidentialiteFR() {
  return (
    <>
      <ContentHero
        eyebrow="Confidentialité"
        title={<>Vos données restent les vôtres.</>}
        intro="La transparence est le cœur de FILON, cela vaut aussi pour vos données. Voici, en clair, ce que nous collectons, pourquoi, et vos droits."
        breadcrumb={[{ name: "Confidentialité", path: "/confidentialite" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Dernière mise à jour : 21 juillet 2026</p>

          <h2>En résumé</h2>
          <ul>
            <li>Nous ne construisons <b>aucun profil publicitaire</b> et ne <b>revendons aucune donnée</b>.</li>
            <li>Notre mesure d&apos;audience est <b>sans cookie</b> et anonyme (Plausible).</li>
            <li>Nous ne collectons des données personnelles que si <b>vous nous les fournissez</b> (contact, newsletter).</li>
            <li>Les liens partenaires n&apos;augmentent <b>jamais</b> votre prix.</li>
          </ul>

          <h2>Responsable du traitement</h2>
          <p>
            {site.legalName}, {site.legalForm.toLowerCase()} (BCE {site.bce}), {site.legalAddress}. Pour toute
            question :{" "}
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

          <h2>L&apos;extension de navigateur FILON</h2>
          <p>
            Sur la fiche produit d&apos;un marchand supporté, l&apos;extension lit uniquement le <b>nom du
            produit affiché</b> (contenu de la page) afin de vous proposer FILON. Ce nom n&apos;est <b>ni
            stocké, ni revendu, ni transmis en arrière-plan</b> : il n&apos;est envoyé à FILON que
            <b> lorsque vous cliquez</b> pour lancer la comparaison, exactement comme si vous tapiez ce produit
            dans une recherche.
          </p>
          <p>
            L&apos;autorisation <b>activeTab</b> n&apos;est utilisée que si vous cliquez sur « Analyser la
            page » (lecture du titre de l&apos;onglet actif). L&apos;autorisation <b>storage</b> sert
            uniquement à mémoriser localement que vous avez fermé le panneau, pour ne pas le rouvrir pendant
            quelques heures. L&apos;extension ne contient <b>aucune télémétrie</b>, ne suit pas votre
            navigation et n&apos;accède qu&apos;aux marchands supportés.
          </p>

          <h2>Cookies</h2>
          <p>
            Le site ne dépose <b>pas de cookie de suivi publicitaire</b>. Seuls d&apos;éventuels cookies strictement
            nécessaires au bon fonctionnement peuvent être utilisés. Vous gardez le contrôle via les réglages de votre
            navigateur.
          </p>

          <h2>Liens partenaires</h2>
          <p>
            Lorsque vous activez une offre via FILON, un service partenaire peut déposer un cookie technique afin de
            rattacher votre commande. Ce traitement relève de la politique de confidentialité de ce partenaire. Cela ne
            modifie jamais le prix que vous payez.
          </p>

          <h2>Sous-traitants</h2>
          <ul>
            <li><b>Vercel</b>, hébergement du site.</li>
            <li><b>Plausible Analytics</b>, mesure d&apos;audience sans cookie.</li>
            <li><b>Formspree</b> (ou équivalent), acheminement des messages de contact et inscriptions.</li>
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

function ConfidentialiteNL() {
  return (
    <>
      <ContentHero
        eyebrow="Privacy"
        title={<>Je gegevens blijven van jou.</>}
        intro="Transparantie is het hart van FILON, dat geldt ook voor je gegevens. Hier, in klare taal, wat we verzamelen, waarom, en je rechten."
        breadcrumb={[{ name: "Privacy", path: "/confidentialite" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Laatste update : 21 juli 2026</p>

          <h2>Samengevat</h2>
          <ul>
            <li>We bouwen <b>geen enkel advertentieprofiel</b> en <b>verkopen geen enkele gegevens door</b>.</li>
            <li>Onze bezoekersmeting is <b>zonder cookie</b> en anoniem (Plausible).</li>
            <li>We verzamelen enkel persoonsgegevens als <b>jij ze ons bezorgt</b> (contact, nieuwsbrief).</li>
            <li>Partnerlinks verhogen <b>nooit</b> je prijs.</li>
          </ul>

          <h2>Verwerkingsverantwoordelijke</h2>
          <p>
            {site.legalName}, {site.legalForm.toLowerCase()} (KBO {site.bce}), {site.legalAddress}. Voor elke
            vraag :{" "}
            <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>.
          </p>

          <h2>Gegevens die we verwerken</h2>
          <p>
            <b>Contactformulier</b> : naam, e-mailadres en bericht, om je aanvraag te beantwoorden. Rechtsgrond :
            jouw toestemming / ons gerechtvaardigd belang om je te antwoorden.
          </p>
          <p>
            <b>Nieuwsbrief</b> : je e-mailadres, om je te informeren over de lancering en de nieuwigheden. Rechtsgrond :
            jouw toestemming. Je kunt je op elk moment uitschrijven.
          </p>
          <p>
            <b>Bezoekersmeting</b> : we gebruiken Plausible Analytics, een privacyvriendelijke oplossing,
            <b> zonder cookie</b> en zonder identificeerbare persoonsgegevens (geen persistente identificator,
            geaggregeerde statistieken). Voor deze verwerking is dus geen toestemmingsbanner vereist.
          </p>

          <h2>De FILON-browserextensie</h2>
          <p>
            Op de productpagina van een ondersteunde winkel leest de extensie enkel de <b>getoonde
            productnaam</b> (inhoud van de pagina) om je FILON voor te stellen. Die naam wordt <b>noch
            opgeslagen, noch doorverkocht, noch op de achtergrond doorgestuurd</b> : hij wordt pas naar FILON
            gestuurd <b>wanneer je klikt</b> om de vergelijking te starten, precies alsof je dat product in een
            zoekopdracht typt.
          </p>
          <p>
            De <b>activeTab</b>-toestemming wordt enkel gebruikt als je op « Pagina analyseren » klikt
            (lezen van de titel van het actieve tabblad). De <b>storage</b>-toestemming dient enkel om lokaal te
            onthouden dat je het paneel gesloten hebt, om het gedurende enkele uren niet opnieuw te openen. De
            extensie bevat <b>geen enkele telemetrie</b>, volgt je surfgedrag niet en heeft enkel toegang tot de
            ondersteunde winkels.
          </p>

          <h2>Cookies</h2>
          <p>
            De website plaatst <b>geen advertentie-tracking-cookie</b>. Enkel eventuele cookies die strikt nodig zijn
            voor de goede werking kunnen gebruikt worden. Je behoudt de controle via de instellingen van je browser.
          </p>

          <h2>Partnerlinks</h2>
          <p>
            Wanneer je een aanbod activeert via FILON, kan een partnerdienst een technische cookie plaatsen om je
            bestelling te koppelen. Deze verwerking valt onder het privacybeleid van die partner. Dit verandert nooit de
            prijs die jij betaalt.
          </p>

          <h2>Verwerkers</h2>
          <ul>
            <li><b>Vercel</b>, hosting van de website.</li>
            <li><b>Plausible Analytics</b>, bezoekersmeting zonder cookie.</li>
            <li><b>Formspree</b> (of gelijkwaardig), verzending van de contactberichten en inschrijvingen.</li>
          </ul>

          <h2>Bewaartermijn</h2>
          <p>
            De contactberichten worden bewaard zolang nodig voor de verwerking van je aanvraag. De
            nieuwsbrief-adressen tot je uitschrijving.
          </p>

          <h2>Je rechten (GDPR)</h2>
          <p>
            Je beschikt over een recht op inzage, verbetering, wissing, beperking, verzet en overdraagbaarheid van je
            gegevens. Om ze uit te oefenen, schrijf naar{" "}
            <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. Je kunt ook een klacht indienen bij de
            Gegevensbeschermingsautoriteit (GBA), in België.
          </p>
        </div>
      </section>
    </>
  );
}

function ConfidentialiteEN() {
  return (
    <>
      <ContentHero
        eyebrow="Privacy"
        title={<>Your data stays yours.</>}
        intro="Transparency is at the heart of FILON, and that goes for your data too. Here, plainly, is what we collect, why, and your rights."
        breadcrumb={[{ name: "Privacy", path: "/confidentialite" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Last updated: 21 July 2026</p>

          <h2>In short</h2>
          <ul>
            <li>We build <b>no advertising profile</b> and <b>resell no data</b>.</li>
            <li>Our audience measurement is <b>cookie-free</b> and anonymous (Plausible).</li>
            <li>We only collect personal data if <b>you provide it</b> (contact, newsletter).</li>
            <li>Partner links <b>never</b> increase your price.</li>
          </ul>

          <h2>Data controller</h2>
          <p>
            {site.legalName}, {site.legalForm.toLowerCase()} (CBE {site.bce}), {site.legalAddress}. For any
            question:{" "}
            <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>.
          </p>

          <h2>Data we process</h2>
          <p>
            <b>Contact form</b>: name, email address and message, to answer your request. Legal basis: your consent
            / our legitimate interest in replying to you.
          </p>
          <p>
            <b>Newsletter</b>: your email address, to inform you of the launch and news. Legal basis: your consent.
            You can unsubscribe at any time.
          </p>
          <p>
            <b>Audience measurement</b>: we use Plausible Analytics, a privacy-friendly solution,
            <b> cookie-free</b> and with no identifiable personal data (no persistent identifier, aggregated
            statistics). No consent banner is therefore required for this processing.
          </p>

          <h2>The FILON browser extension</h2>
          <p>
            On the product page of a supported merchant, the extension only reads the <b>displayed product
            name</b> (page content) in order to offer you FILON. This name is <b>neither stored, resold, nor
            transmitted in the background</b>: it is sent to FILON only <b>when you click</b> to start the
            comparison, exactly as if you typed that product into a search.
          </p>
          <p>
            The <b>activeTab</b> permission is used only if you click « Analyse the page » (reading the title of the
            active tab). The <b>storage</b> permission serves only to remember locally that you closed the panel, so
            as not to reopen it for a few hours. The extension contains <b>no telemetry</b>, does not track your
            browsing and only accesses supported merchants.
          </p>

          <h2>Cookies</h2>
          <p>
            The site sets <b>no advertising tracking cookie</b>. Only any strictly necessary cookies for proper
            functioning may be used. You keep control via your browser settings.
          </p>

          <h2>Partner links</h2>
          <p>
            When you activate an offer via FILON, a partner service may place a technical cookie to attribute your
            order. This processing falls under that partner&apos;s privacy policy. It never changes the price you
            pay.
          </p>

          <h2>Processors</h2>
          <ul>
            <li><b>Vercel</b>, website hosting.</li>
            <li><b>Plausible Analytics</b>, cookie-free audience measurement.</li>
            <li><b>Formspree</b> (or equivalent), routing of contact messages and sign-ups.</li>
          </ul>

          <h2>Retention period</h2>
          <p>
            Contact messages are kept for as long as needed to process your request. Newsletter addresses are kept
            until you unsubscribe.
          </p>

          <h2>Your rights (GDPR)</h2>
          <p>
            You have a right of access, rectification, erasure, restriction, objection and portability of your data.
            To exercise them, write to{" "}
            <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. You may also lodge a complaint with
            the Data Protection Authority (DPA), in Belgium.
          </p>
        </div>
      </section>
    </>
  );
}

export default function ConfidentialitePage() {
  return <Localized fr={<ConfidentialiteFR />} nl={<ConfidentialiteNL />} en={<ConfidentialiteEN />} />;
}
