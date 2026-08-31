import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { IcLock, IcNoResale, IcEncrypted, IcShieldCheck, IcChartNoCookie, IcEye } from "@/components/editorial/icons";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/securite",
  title: "Sécurité & confiance",
  description:
    "Les mesures de sécurité visibles de FILON, les limites du parcours d'achat et les politiques qui documentent les traitements de données.",
});

function SecuriteFR() {
  return (
    <>
      <ContentHero
        eyebrow="Sécurité"
        title={<>La confiance n&apos;est pas une option. C&apos;est le <span className="it">produit</span>.</>}
        intro="Un copilote d'achat n'a de valeur que si vous pouvez lui faire confiance. Voici concrètement comment FILON protège vos données, votre navigation et votre argent."
        breadcrumb={[{ name: "Sécurité", path: "/securite" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <InfoGrid
            items={[
              { n: <IcLock />, h: "Périmètre documenté", p: "Les politiques publiées décrivent les données traitées, leur finalité et vos droits." },
              { n: <IcNoResale />, h: "Achat chez le marchand", p: "Le parcours public renvoie vers le marchand ; FILON ne demande pas les données de carte bancaire dans ce parcours." },
              { n: <IcEncrypted />, h: "Transport HTTPS", p: "Le site public est servi en HTTPS. Cela protège le transport, sans remplacer la sécurité propre à chaque prestataire." },
              { n: <IcShieldCheck />, h: "Droits publiés", p: "La politique de confidentialité indique comment exercer les droits applicables aux traitements décrits." },
              { n: <IcChartNoCookie />, h: "Mesure configurable", p: "La configuration du site prévoit Plausible ; la politique cookies constitue la référence sur son activation et son périmètre." },
              { n: <IcEye />, h: "Commission hors score actuel", p: "Le taux de commission n'est pas un champ du score de décision actuellement implémenté." },
            ]}
          />
        </div>
      </section>
      <ProseBlock heading={<>Les limites du parcours <span className="it">actuel</span>.</>} alt>
        <p>
          FILON affiche des informations de comparaison puis renvoie vers le marchand. Le prix, les frais, le stock et
          le total final doivent y être confirmés. Le parcours public actuel ne collecte pas de moyen de paiement.
        </p>
        <p>
          Le détail complet des traitements figure dans notre <a href="/confidentialite">politique de confidentialité</a> et
          notre <a href="/cookies">politique cookies</a>.
        </p>
      </ProseBlock>
      <ProseBlock heading={<>Signaler une <span className="it">vulnérabilité</span>.</>}>
        <p>
          La sécurité est un travail continu. Si vous pensez avoir identifié une faille ou un comportement anormal, écrivez-nous
          à <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. Nous étudions chaque signalement sérieux avec
          attention et reconnaissance.
        </p>
      </ProseBlock>
      <ClosingCta title={<>Une sécurité à <span className="it">vérifier</span>.</>} sub="Consultez les politiques publiées et signalez tout comportement anormal." />
    </>
  );
}

function SecuriteNL() {
  return (
    <>
      <ContentHero
        eyebrow="Veiligheid"
        title={<>Vertrouwen is geen optie. Het is het <span className="it">product</span>.</>}
        intro="Een koopcopiloot heeft pas waarde als je hem kunt vertrouwen. Zo beschermt FILON concreet je gegevens, je browsen en je geld."
        breadcrumb={[{ name: "Veiligheid", path: "/securite" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <InfoGrid
            items={[
              { n: <IcLock />, h: "Gedocumenteerde reikwijdte", p: "Gepubliceerde beleidsdocumenten beschrijven verwerkte gegevens, doel en je rechten." },
              { n: <IcNoResale />, h: "Aankoop bij de winkel", p: "De publieke route stuurt door naar de winkel; FILON vraagt daar geen betaalkaartgegevens." },
              { n: <IcEncrypted />, h: "HTTPS-transport", p: "De publieke site gebruikt HTTPS. Dat beschermt het transport, maar vervangt niet de beveiliging van elke dienstverlener." },
              { n: <IcShieldCheck />, h: "Gepubliceerde rechten", p: "Het privacybeleid vermeldt hoe je rechten voor de beschreven verwerkingen kunt uitoefenen." },
              { n: <IcChartNoCookie />, h: "Configureerbare meting", p: "De siteconfiguratie voorziet Plausible; het cookiebeleid is de referentie voor activatie en bereik." },
              { n: <IcEye />, h: "Commissie buiten huidige score", p: "Het commissietarief is geen veld van de momenteel geïmplementeerde beslissingsscore." },
            ]}
          />
        </div>
      </section>
      <ProseBlock heading={<>De grenzen van de <span className="it">huidige route</span>.</>} alt>
        <p>
          FILON toont vergelijkingsinformatie en stuurt daarna door naar de winkel. Bevestig daar prijs, kosten,
          voorraad en eindtotaal. De huidige publieke route verzamelt geen betaalmiddel.
        </p>
        <p>
          De volledige details van de verwerkingen staan in ons <a href="/confidentialite">privacybeleid</a> en ons{" "}
          <a href="/cookies">cookiebeleid</a>.
        </p>
      </ProseBlock>
      <ProseBlock heading={<>Een <span className="it">kwetsbaarheid</span> melden.</>}>
        <p>
          Veiligheid is doorlopend werk. Denk je een lek of afwijkend gedrag te hebben ontdekt, schrijf ons op{" "}
          <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. We bekijken elke ernstige melding met
          aandacht en dankbaarheid.
        </p>
      </ProseBlock>
      <ClosingCta title={<>Beveiliging die je kunt <span className="it">controleren</span>.</>} sub="Raadpleeg het gepubliceerde beleid en meld afwijkend gedrag." />
    </>
  );
}

function SecuriteEN() {
  return (
    <>
      <ContentHero
        eyebrow="Security"
        title={<>Trust isn&apos;t an option. It&apos;s the <span className="it">product</span>.</>}
        intro="A shopping copilot is only worth anything if you can trust it. Here, concretely, is how FILON protects your data, your browsing and your money."
        breadcrumb={[{ name: "Security", path: "/securite" }]}
      />
      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <InfoGrid
            items={[
              { n: <IcLock />, h: "Documented scope", p: "Published policies describe processed data, purpose and your rights." },
              { n: <IcNoResale />, h: "Purchase at the merchant", p: "The public journey redirects to the merchant; FILON does not request payment-card data in that journey." },
              { n: <IcEncrypted />, h: "HTTPS transport", p: "The public site is served over HTTPS. This protects transport but does not replace each provider's security." },
              { n: <IcShieldCheck />, h: "Published rights", p: "The privacy policy explains how to exercise rights applicable to the processing described." },
              { n: <IcChartNoCookie />, h: "Configurable measurement", p: "Site configuration supports Plausible; the cookie policy is the reference for activation and scope." },
              { n: <IcEye />, h: "Commission outside current score", p: "Commission rate is not a field in the currently implemented decision score." },
            ]}
          />
        </div>
      </section>
      <ProseBlock heading={<>Limits of the <span className="it">current journey</span>.</>} alt>
        <p>
          FILON shows comparison information and then redirects to the merchant. Confirm price, fees, stock and final
          total there. The current public journey does not collect a payment method.
        </p>
        <p>
          The full detail of the processing is set out in our <a href="/confidentialite">privacy policy</a> and our{" "}
          <a href="/cookies">cookie policy</a>.
        </p>
      </ProseBlock>
      <ProseBlock heading={<>Report a <span className="it">vulnerability</span>.</>}>
        <p>
          Security is ongoing work. If you think you&apos;ve found a flaw or abnormal behaviour, write to us at{" "}
          <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a>. We study every serious report with
          care and gratitude.
        </p>
      </ProseBlock>
      <ClosingCta title={<>Security you can <span className="it">verify</span>.</>} sub="Consult the published policies and report abnormal behaviour." />
    </>
  );
}

export default function SecuritePage() {
  return <Localized fr={<SecuriteFR />} nl={<SecuriteNL />} en={<SecuriteEN />} />;
}
