import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";

export const metadata: Metadata = buildMetadata({
  path: "/cgu",
  title: "Conditions générales d'utilisation",
  description:
    "Les conditions générales d'utilisation du service FILON : objet, accès, nature de l'aide à la décision, liens affiliés, responsabilités et droit applicable.",
});

export default function CguPage() {
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
          <p className="upd">Dernière mise à jour : 2026</p>

          <h2>1. Objet</h2>
          <p>
            Les présentes conditions générales d&apos;utilisation (« CGU ») régissent l&apos;accès et l&apos;utilisation du
            service <b>{site.name}</b>, accessible via le site <b>{site.domain}</b> et, à terme, via une extension de navigateur
            et une application. Le service est édité par {site.founder}.
          </p>

          <h2>2. Description du service</h2>
          <p>
            FILON est un service d&apos;<b>aide à la décision d&apos;achat</b>. Il analyse et compare des offres (prix,
            cashback, reconditionné, codes promo), estime un coût réel et propose une recommandation. FILON ne vend aucun
            produit&nbsp;: l&apos;achat s&apos;effectue toujours directement auprès du marchand ou de la plateforme partenaire
            choisie par l&apos;utilisateur.
          </p>

          <h2>3. Accès et gratuité</h2>
          <p>
            L&apos;accès aux fonctions essentielles de FILON est <b>gratuit</b>. Une offre payante optionnelle (« Filon Pro »)
            peut donner accès à des fonctionnalités supplémentaires, dans les conditions et au tarif indiqués sur la page{" "}
            <a href="/tarifs">Tarifs</a>. L&apos;éditeur s&apos;efforce d&apos;assurer la disponibilité du service sans pouvoir
            la garantir de manière ininterrompue.
          </p>

          <h2>4. Utilisation conforme</h2>
          <p>
            L&apos;utilisateur s&apos;engage à utiliser FILON conformément à sa destination et à la loi. Il s&apos;interdit
            notamment de perturber le fonctionnement du service, d&apos;en extraire massivement les données de manière
            automatisée, ou de porter atteinte aux droits de l&apos;éditeur ou de tiers.
          </p>

          <h2>5. Nature indicative des informations</h2>
          <p>
            Les informations de prix, taux de cashback, disponibilité, grades et offres sont fournies à titre <b>indicatif</b>
            {" "}et peuvent évoluer en temps réel chez les marchands et plateformes partenaires. L&apos;éditeur s&apos;efforce
            d&apos;en assurer l&apos;exactitude mais ne garantit pas leur caractère complet ou à jour à chaque instant. La
            décision d&apos;achat relève de la seule responsabilité de l&apos;utilisateur.
          </p>

          <h2>6. Liens affiliés</h2>
          <p>
            FILON contient des <b>liens affiliés</b>&nbsp;: lorsqu&apos;un utilisateur active une offre via FILON, la plateforme
            partenaire peut reverser à l&apos;éditeur une part de sa commission d&apos;apport. <b>Cela n&apos;augmente jamais le
            prix payé par l&apos;utilisateur</b> et n&apos;influence pas l&apos;objectivité de la recommandation, qui vise le
            meilleur coût réel pour l&apos;utilisateur.
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
