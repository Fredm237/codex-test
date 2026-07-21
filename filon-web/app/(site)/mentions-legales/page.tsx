import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/mentions-legales",
  title: "Mentions légales",
  description: "Mentions légales du site FILON, éditeur, hébergeur et informations légales.",
});

export default function MentionsLegalesPage() {
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
          <p className="upd">Dernière mise à jour : 2026</p>

          <h2>Éditeur du site</h2>
          <p>
            Le site <b>{site.domain}</b> est édité par <b>{site.founder}</b>.
            <br />
            Forme juridique : <b>Entreprise individuelle</b>
            <br />
            Siège : <b>Chaussée de Stockel 406, 1150 Woluwe-Saint-Pierre, Belgique</b>
            <br />
            Numéro d&apos;entreprise (BCE) : <b>BE 1016.978.286</b>
            <br />
            Numéro de TVA : <b>BE 1016.978.286</b>
            <br />
            Contact : <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>
          </p>

          <h2>Directeur de la publication</h2>
          <p>{site.founder}.</p>

          <h2>Hébergement</h2>
          <p>
            Le site est hébergé par <b>Hostinger International Ltd</b>, 61 Lordou Vironos Street, 6023 Larnaca, Chypre.
            Plus d&apos;informations sur <a href="https://www.hostinger.fr">hostinger.fr</a>.
            {" "}
            {/* Adaptez si vous changez d'hébergeur. */}
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
            Les informations de prix, cashback, disponibilité et offres sont fournies à titre indicatif et peuvent évoluer
            en temps réel chez les marchands et plateformes partenaires. L&apos;éditeur s&apos;efforce d&apos;assurer leur
            exactitude mais ne saurait être tenu responsable d&apos;éventuelles erreurs ou d&apos;un préjudice lié à leur
            utilisation.
          </p>
        </div>
      </section>
    </>
  );
}
