import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/cookies",
  title: "Politique cookies",
  description:
    "La politique cookies de FILON : nous n'utilisons aucun cookie de suivi publicitaire. Mesure d'audience sans cookie, cookies strictement nécessaires et cookies partenaires, expliqués simplement.",
});

function CookiesFR() {
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
          <p className="upd">Dernière mise à jour : 21 juillet 2026</p>

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

          <h2>Cookies partenaires</h2>
          <p>
            Lorsque vous <b>activez une offre</b> via FILON, un service partenaire peut déposer un <b>cookie technique</b> sur
            votre appareil pour rattacher votre commande. Il est déposé par le partenaire, sous sa propre responsabilité, au
            moment où vous choisissez d&apos;activer l&apos;offre, jamais à votre insu.
          </p>

          <h2>Gérer les cookies</h2>
          <p>
            Vous pouvez à tout moment consulter, bloquer ou supprimer les cookies depuis les réglages de votre navigateur
            (Chrome, Firefox, Edge, Safari…). Bloquer ces cookies peut toutefois empêcher la bonne prise en compte de votre
            commande chez le partenaire concerné.
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

function CookiesNL() {
  return (
    <>
      <ContentHero
        eyebrow="Juridisch"
        title={<>Cookiebeleid</>}
        intro="FILON gebruikt geen enkele advertentie-tracking-cookie. Hier, in klare taal, de enige cookies die geplaatst kunnen worden en waarom."
        breadcrumb={[{ name: "Cookiebeleid", path: "/cookies" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Laatste update : 21 juli 2026</p>

          <h2>Ons principe</h2>
          <p>
            Een cookie is een klein bestand dat bij het bezoek van een website op je toestel wordt geplaatst. Bij FILON
            hebben we een simpele keuze gemaakt&nbsp;: <b>geen enkele advertentie-tracking-cookie, geen profilering</b>. Ons
            model berust niet op de doorverkoop van gegevens, dus verzamelen we er niet meer dan nodig.
          </p>

          <h2>Bezoekersmeting zonder cookie</h2>
          <p>
            Om het gebruik van de website te begrijpen en te verbeteren, gebruiken we <b>Plausible Analytics</b>, een
            oplossing voor bezoekersmeting <b>zonder cookie</b> en zonder identificeerbare persoonsgegevens&nbsp;: geen
            persistente identificator, enkel geaggregeerde en anonieme statistieken. Voor deze meting is dus geen
            cookietoestemming vereist.
          </p>

          <h2>Strikt noodzakelijke cookies</h2>
          <p>
            Sommige zuiver technische cookies kunnen nodig zijn voor de goede werking van de website (bijvoorbeeld een
            weergavevoorkeur onthouden). Ze dienen noch voor tracking noch voor reclame, en zijn door de regelgeving
            vrijgesteld van toestemming.
          </p>

          <h2>Partnercookies</h2>
          <p>
            Wanneer je een aanbod <b>activeert</b> via FILON, kan een partnerdienst een <b>technische cookie</b> op je
            toestel plaatsen om je bestelling te koppelen. Hij wordt geplaatst door de partner, onder diens eigen
            verantwoordelijkheid, op het moment dat je ervoor kiest het aanbod te activeren, nooit buiten je medeweten.
          </p>

          <h2>Cookies beheren</h2>
          <p>
            Je kunt de cookies op elk moment raadplegen, blokkeren of verwijderen via de instellingen van je browser
            (Chrome, Firefox, Edge, Safari…). Deze cookies blokkeren kan echter beletten dat je bestelling goed in
            aanmerking wordt genomen bij de betrokken partner.
          </p>

          <h2>Meer weten</h2>
          <p>
            Dit beleid vult ons <a href="/confidentialite">privacybeleid</a> aan. Voor elke vraag over cookies, schrijf
            ons op <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>.
          </p>
        </div>
      </section>
    </>
  );
}

export default function CookiesPage() {
  return <Localized fr={<CookiesFR />} nl={<CookiesNL />} />;
}
