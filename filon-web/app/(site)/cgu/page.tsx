import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/cgu",
  title: "Conditions générales d'utilisation",
  description:
    "Les conditions générales d'utilisation du service FILON : objet, accès, nature de l'aide à la décision, liens partenaires, responsabilités et droit applicable.",
});

function CguFR() {
  return (
    <>
      <ContentHero
        eyebrow="Légal"
        title={<>Conditions générales d&apos;utilisation</>}
        intro="Les règles qui encadrent l'utilisation du service FILON. En utilisant FILON, vous acceptez les présentes conditions."
        breadcrumb={[{ name: "Conditions générales d'utilisation", path: "/cgu" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Dernière mise à jour : 21 juillet 2026</p>

          <h2>1. Objet</h2>
          <p>
            Les présentes conditions générales d&apos;utilisation (« CGU ») régissent l&apos;accès et l&apos;utilisation du
            service <b>{site.name}</b>, accessible via le site <b>{site.domain}</b> et, à terme, via une extension de navigateur
            et une application. Le service est édité par {site.legalName}, {site.legalForm.toLowerCase()} (BCE{" "}
            {site.bce}), {site.legalAddress}.
          </p>

          <h2>2. Description du service</h2>
          <p>
            FILON est un service d&apos;<b>aide à la décision d&apos;achat</b>. Il analyse le marché, compare des offres et
            estime un coût réel, puis propose une recommandation. FILON ne vend aucun produit&nbsp;: l&apos;achat
            s&apos;effectue toujours directement auprès du marchand ou de la plateforme choisie par l&apos;utilisateur.
          </p>

          <h2>3. Accès et gratuité</h2>
          <p>
            L&apos;accès à FILON est <b>entièrement gratuit</b> pour l&apos;utilisateur, sans abonnement ni frais&nbsp;: voir la
            page <a href="/tarifs">Tarifs</a>. Il n&apos;est jamais facturé à l&apos;utilisateur. L&apos;éditeur s&apos;efforce
            d&apos;assurer la disponibilité du service sans pouvoir la garantir de manière ininterrompue.
          </p>

          <h2>4. Utilisation conforme</h2>
          <p>
            L&apos;utilisateur s&apos;engage à utiliser FILON conformément à sa destination et à la loi. Il s&apos;interdit
            notamment de perturber le fonctionnement du service, d&apos;en extraire massivement les données de manière
            automatisée, ou de porter atteinte aux droits de l&apos;éditeur ou de tiers.
          </p>

          <h2>5. Nature indicative des informations</h2>
          <p>
            Les informations de prix, de disponibilité et d&apos;offres sont fournies à titre <b>indicatif</b>
            {" "}et peuvent évoluer en temps réel chez les marchands. L&apos;éditeur s&apos;efforce
            d&apos;en assurer l&apos;exactitude mais ne garantit pas leur caractère complet ou à jour à chaque instant. La
            décision d&apos;achat relève de la seule responsabilité de l&apos;utilisateur.
          </p>

          <h2>6. Liens partenaires</h2>
          <p>
            FILON peut contenir des <b>liens partenaires</b>. Les activer <b>n&apos;augmente jamais le prix payé par
            l&apos;utilisateur</b> et n&apos;influence pas la recommandation, qui vise le meilleur coût réel pour
            l&apos;utilisateur.
          </p>

          <h2>7. Propriété intellectuelle</h2>
          <p>
            L&apos;ensemble des contenus du service (textes, éléments graphiques, logo, identité visuelle, code) est protégé et
            demeure la propriété de l&apos;éditeur, sauf mention contraire. Toute reproduction ou réutilisation non autorisée
            est interdite.
          </p>

          <h2>8. Données personnelles</h2>
          <p>
            Le traitement des données personnelles est décrit dans notre{" "}
            <a href="/confidentialite">politique de confidentialité</a> et notre{" "}
            <a href="/cookies">politique cookies</a>, conformes au RGPD.
          </p>

          <h2>9. Responsabilité</h2>
          <p>
            FILON est fourni « en l&apos;état ». L&apos;éditeur ne saurait être tenu responsable des décisions d&apos;achat de
            l&apos;utilisateur, des variations de prix ou d&apos;offres, ni d&apos;un préjudice indirect lié à
            l&apos;utilisation du service. La relation commerciale et le service après-vente relèvent du marchand ou de la
            plateforme auprès duquel l&apos;achat est réalisé.
          </p>

          <h2>10. Modification des CGU</h2>
          <p>
            L&apos;éditeur peut faire évoluer les présentes CGU pour les adapter au service ou à la réglementation. La version
            applicable est celle publiée sur cette page à la date d&apos;utilisation.
          </p>

          <h2>11. Droit applicable</h2>
          <p>
            Les présentes CGU sont soumises au <b>droit belge</b>. Tout litige relève, à défaut de résolution amiable, des
            juridictions compétentes de Belgique. Pour toute question&nbsp;:{" "}
            <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>.
          </p>
        </div>
      </section>
    </>
  );
}

function CguNL() {
  return (
    <>
      <ContentHero
        eyebrow="Juridisch"
        title={<>Algemene gebruiksvoorwaarden</>}
        intro="De regels die het gebruik van de dienst FILON omkaderen. Door FILON te gebruiken, aanvaard je deze voorwaarden."
        breadcrumb={[{ name: "Algemene gebruiksvoorwaarden", path: "/cgu" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Laatste update : 21 juli 2026</p>

          <h2>1. Voorwerp</h2>
          <p>
            Deze algemene gebruiksvoorwaarden (« AGV ») regelen de toegang tot en het gebruik van de dienst{" "}
            <b>{site.name}</b>, toegankelijk via de website <b>{site.domain}</b> en, op termijn, via een browserextensie
            en een applicatie. De dienst wordt uitgegeven door {site.legalName}, {site.legalForm.toLowerCase()} (KBO{" "}
            {site.bce}), {site.legalAddress}.
          </p>

          <h2>2. Beschrijving van de dienst</h2>
          <p>
            FILON is een dienst voor <b>hulp bij de aankoopbeslissing</b>. Hij analyseert de markt, vergelijkt
            aanbiedingen en schat een echte kost, en stelt dan een aanbeveling voor. FILON verkoopt geen enkel
            product&nbsp;: de aankoop gebeurt altijd rechtstreeks bij de winkel of het platform gekozen door de gebruiker.
          </p>

          <h2>3. Toegang en kosteloosheid</h2>
          <p>
            De toegang tot FILON is <b>volledig gratis</b> voor de gebruiker, zonder abonnement of kosten&nbsp;: zie de
            pagina <a href="/tarifs">Tarieven</a>. Het wordt nooit aan de gebruiker gefactureerd. De uitgever streeft ernaar
            de beschikbaarheid van de dienst te verzekeren zonder ze ononderbroken te kunnen garanderen.
          </p>

          <h2>4. Conform gebruik</h2>
          <p>
            De gebruiker verbindt zich ertoe FILON te gebruiken conform zijn bestemming en de wet. Hij verbiedt zich
            met name de werking van de dienst te verstoren, er massaal de gegevens op geautomatiseerde wijze uit te
            halen, of de rechten van de uitgever of van derden te schenden.
          </p>

          <h2>5. Indicatieve aard van de informatie</h2>
          <p>
            De informatie over prijzen, beschikbaarheid en aanbiedingen wordt <b>ter indicatie</b> verstrekt
            {" "}en kan in real time evolueren bij de winkels. De uitgever streeft ernaar de juistheid ervan te
            verzekeren maar garandeert niet dat ze op elk moment volledig of actueel is. De aankoopbeslissing valt onder
            de uitsluitende verantwoordelijkheid van de gebruiker.
          </p>

          <h2>6. Partnerlinks</h2>
          <p>
            FILON kan <b>partnerlinks</b> bevatten. Ze activeren <b>verhoogt nooit de prijs die de gebruiker
            betaalt</b> en beïnvloedt de aanbeveling niet, die de beste echte kost voor de gebruiker beoogt.
          </p>

          <h2>7. Intellectuele eigendom</h2>
          <p>
            Het geheel van de inhoud van de dienst (teksten, grafische elementen, logo, visuele identiteit, code) is
            beschermd en blijft eigendom van de uitgever, behoudens andersluidende vermelding. Elke ongeoorloofde
            reproductie of hergebruik is verboden.
          </p>

          <h2>8. Persoonsgegevens</h2>
          <p>
            De verwerking van persoonsgegevens wordt beschreven in ons{" "}
            <a href="/confidentialite">privacybeleid</a> en ons{" "}
            <a href="/cookies">cookiebeleid</a>, GDPR-conform.
          </p>

          <h2>9. Aansprakelijkheid</h2>
          <p>
            FILON wordt geleverd « in de staat waarin hij zich bevindt ». De uitgever kan niet aansprakelijk worden
            gesteld voor de aankoopbeslissingen van de gebruiker, de schommelingen van prijzen of aanbiedingen, noch
            voor onrechtstreekse schade verbonden aan het gebruik van de dienst. De commerciële relatie en de
            dienst-na-verkoop vallen onder de winkel of het platform waarbij de aankoop wordt verricht.
          </p>

          <h2>10. Wijziging van de AGV</h2>
          <p>
            De uitgever kan deze AGV doen evolueren om ze aan te passen aan de dienst of de regelgeving. De toepasselijke
            versie is die welke op deze pagina gepubliceerd is op de datum van gebruik.
          </p>

          <h2>11. Toepasselijk recht</h2>
          <p>
            Deze AGV zijn onderworpen aan het <b>Belgisch recht</b>. Elk geschil valt, bij gebrek aan minnelijke
            oplossing, onder de bevoegde rechtbanken van België. Voor elke vraag&nbsp;:{" "}
            <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>.
          </p>
        </div>
      </section>
    </>
  );
}

function CguEN() {
  return (
    <>
      <ContentHero
        eyebrow="Legal"
        title={<>Terms of use</>}
        intro="The rules that govern the use of the FILON service. By using FILON, you accept these terms."
        breadcrumb={[{ name: "Terms of use", path: "/cgu" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Last updated: 21 July 2026</p>

          <h2>1. Purpose</h2>
          <p>
            These terms of use (« Terms ») govern access to and use of the <b>{site.name}</b> service, accessible via
            the website <b>{site.domain}</b> and, in time, via a browser extension and an application. The service is
            published by {site.legalName}, {site.legalForm.toLowerCase()} (CBE {site.bce}), {site.legalAddress}.
          </p>

          <h2>2. Description of the service</h2>
          <p>
            FILON is a <b>purchase-decision aid</b> service. It analyses the market, compares offers and estimates a
            real cost, then proposes a recommendation. FILON sells no product&nbsp;: the purchase is always made
            directly with the merchant or platform chosen by the user.
          </p>

          <h2>3. Access and free of charge</h2>
          <p>
            Access to FILON is <b>entirely free</b> for the user, with no subscription or fees&nbsp;: see the{" "}
            <a href="/tarifs">Pricing</a> page. It is never billed to the user. The publisher strives to ensure the
            availability of the service without being able to guarantee it uninterrupted.
          </p>

          <h2>4. Compliant use</h2>
          <p>
            The user undertakes to use FILON in accordance with its purpose and the law. In particular, they refrain
            from disrupting the operation of the service, extracting its data en masse in an automated way, or
            infringing the rights of the publisher or of third parties.
          </p>

          <h2>5. Indicative nature of the information</h2>
          <p>
            Information on prices, availability and offers is provided <b>for guidance</b>
            {" "}and may change in real time at the merchants. The publisher strives to ensure its accuracy but does
            not guarantee it is complete or up to date at every moment. The purchase decision is the user&apos;s sole
            responsibility.
          </p>

          <h2>6. Partner links</h2>
          <p>
            FILON may contain <b>partner links</b>. Activating them <b>never increases the price paid by the
            user</b> and does not influence the recommendation, which aims at the best real cost for the user.
          </p>

          <h2>7. Intellectual property</h2>
          <p>
            All the service&apos;s content (texts, graphic elements, logo, visual identity, code) is protected and
            remains the property of the publisher, unless stated otherwise. Any unauthorised reproduction or reuse is
            prohibited.
          </p>

          <h2>8. Personal data</h2>
          <p>
            The processing of personal data is described in our{" "}
            <a href="/confidentialite">privacy policy</a> and our{" "}
            <a href="/cookies">cookie policy</a>, GDPR-compliant.
          </p>

          <h2>9. Liability</h2>
          <p>
            FILON is provided « as is ». The publisher cannot be held liable for the user&apos;s purchase decisions,
            for variations in prices or offers, nor for indirect harm linked to the use of the service. The
            commercial relationship and after-sales service fall under the merchant or platform where the purchase is
            made.
          </p>

          <h2>10. Amendment of the Terms</h2>
          <p>
            The publisher may amend these Terms to adapt them to the service or the regulations. The applicable
            version is the one published on this page on the date of use.
          </p>

          <h2>11. Applicable law</h2>
          <p>
            These Terms are governed by <b>Belgian law</b>. Any dispute falls, failing an amicable resolution, under
            the competent courts of Belgium. For any question&nbsp;:{" "}
            <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>.
          </p>
        </div>
      </section>
    </>
  );
}

export default function CguPage() {
  return <Localized fr={<CguFR />} nl={<CguNL />} en={<CguEN />} />;
}
