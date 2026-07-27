import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/mentions-legales",
  title: "Mentions légales",
  description: "Mentions légales du site FILON, éditeur, hébergeur et informations légales.",
});

function MentionsFR() {
  return (
    <>
      <ContentHero
        eyebrow="Légal"
        title={<>Mentions légales</>}
        intro="Les informations légales relatives au site FILON et à son éditeur."
        breadcrumb={[{ name: "Mentions légales", path: "/mentions-legales" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Dernière mise à jour : 21 juillet 2026</p>

          <h2>Éditeur du site</h2>
          <p>
            Le site <b>{site.domain}</b> est édité par <b>{site.legalName}</b>.
            <br />
            Forme juridique : <b>{site.legalForm}</b>
            <br />
            Siège : <b>{site.legalAddress}</b>
            <br />
            Numéro d&apos;entreprise (BCE) : <b>{site.bce}</b>
            <br />
            Numéro de TVA : <b>{site.vat}</b>
            <br />
            Contact : <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>
          </p>

          <h2>Directeur de la publication</h2>
          <p>{site.legalName}.</p>

          <h2>Hébergement</h2>
          <p>
            Le site est hébergé par <b>Vercel Inc.</b>, San Francisco, Californie, États-Unis.
            Plus d&apos;informations sur <a href="https://vercel.com">vercel.com</a>.
          </p>

          <h2>Propriété intellectuelle</h2>
          <p>
            L&apos;ensemble des contenus du site (textes, éléments graphiques, logo, identité visuelle, code) est la propriété
            de l&apos;éditeur, sauf mention contraire, et est protégé par le droit de la propriété intellectuelle. Toute
            reproduction sans autorisation est interdite.
          </p>

          <h2>Nature du service et liens partenaires</h2>
          <p>
            FILON est un service gratuit d&apos;aide à la décision d&apos;achat. Le site peut contenir des <b>liens
            partenaires</b>. Les activer <b>ne modifie jamais le prix payé par l&apos;utilisateur.</b>
          </p>

          <h2>Données personnelles</h2>
          <p>
            Le traitement des données personnelles est décrit dans notre{" "}
            <a href="/confidentialite">politique de confidentialité</a>.
          </p>

          <h2>Responsabilité</h2>
          <p>
            Les informations de prix, de disponibilité et d&apos;offres sont fournies à titre indicatif et peuvent évoluer
            en temps réel chez les marchands. L&apos;éditeur s&apos;efforce d&apos;assurer leur
            exactitude mais ne saurait être tenu responsable d&apos;éventuelles erreurs ou d&apos;un préjudice lié à leur
            utilisation.
          </p>
        </div>
      </section>
    </>
  );
}

function MentionsNL() {
  return (
    <>
      <ContentHero
        eyebrow="Juridisch"
        title={<>Juridische vermeldingen</>}
        intro="De juridische informatie met betrekking tot de website FILON en zijn uitgever."
        breadcrumb={[{ name: "Juridische vermeldingen", path: "/mentions-legales" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-legal">
          <p className="upd">Laatste update : 21 juli 2026</p>

          <h2>Uitgever van de website</h2>
          <p>
            De website <b>{site.domain}</b> wordt uitgegeven door <b>{site.legalName}</b>.
            <br />
            Rechtsvorm : <b>{site.legalForm}</b>
            <br />
            Zetel : <b>{site.legalAddress}</b>
            <br />
            Ondernemingsnummer (KBO) : <b>{site.bce}</b>
            <br />
            Btw-nummer : <b>{site.vat}</b>
            <br />
            Contact : <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>
          </p>

          <h2>Verantwoordelijke uitgever</h2>
          <p>{site.legalName}.</p>

          <h2>Hosting</h2>
          <p>
            De website wordt gehost door <b>Vercel Inc.</b>, San Francisco, Californië, Verenigde Staten.
            Meer informatie op <a href="https://vercel.com">vercel.com</a>.
          </p>

          <h2>Intellectuele eigendom</h2>
          <p>
            Het geheel van de inhoud van de website (teksten, grafische elementen, logo, visuele identiteit, code) is
            eigendom van de uitgever, behoudens andersluidende vermelding, en wordt beschermd door het recht van de
            intellectuele eigendom. Elke reproductie zonder toestemming is verboden.
          </p>

          <h2>Aard van de dienst en partnerlinks</h2>
          <p>
            FILON is een gratis dienst voor hulp bij de aankoopbeslissing. De website kan <b>partnerlinks</b> bevatten.
            Ze activeren <b>verandert nooit de prijs die de gebruiker betaalt.</b>
          </p>

          <h2>Persoonsgegevens</h2>
          <p>
            De verwerking van persoonsgegevens wordt beschreven in ons{" "}
            <a href="/confidentialite">privacybeleid</a>.
          </p>

          <h2>Aansprakelijkheid</h2>
          <p>
            De informatie over prijzen, beschikbaarheid en aanbiedingen wordt louter ter indicatie verstrekt en kan in
            real time evolueren bij de winkels. De uitgever streeft ernaar de juistheid ervan te verzekeren maar kan niet
            aansprakelijk worden gesteld voor eventuele fouten of voor schade verbonden aan het gebruik ervan.
          </p>
        </div>
      </section>
    </>
  );
}

export default function MentionsLegalesPage() {
  return <Localized fr={<MentionsFR />} nl={<MentionsNL />} />;
}
