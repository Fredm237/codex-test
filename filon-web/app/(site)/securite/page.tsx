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
    "Comment FILON protège vos données et votre navigation : minimisation des données, aucune revente, chiffrement, conformité RGPD. La confiance n'est pas une option.",
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
              { n: <IcLock />, h: "Minimisation des données", p: "FILON n'analyse que ce qui est strictement nécessaire à la comparaison. Rien de plus." },
              { n: <IcNoResale />, h: "Aucune revente", p: "Pas de profil publicitaire, pas de revente à des tiers. Vos données restent les vôtres." },
              { n: <IcEncrypted />, h: "Connexions chiffrées", p: "Les échanges avec nos services sont chiffrés (HTTPS/TLS) de bout en bout." },
              { n: <IcShieldCheck />, h: "Conforme RGPD", p: "Traitement conforme au RGPD par défaut, avec des droits que vous pouvez exercer à tout moment." },
              { n: <IcChartNoCookie />, h: "Mesure sans cookie", p: "Notre audience est mesurée sans cookie et de façon anonyme (Plausible)." },
              { n: <IcEye />, h: "Sans arrière-pensée", p: "Pas de publicité. La recommandation sert votre intérêt, pas le nôtre." },
            ]}
          />
        </div>
      </section>
      <ProseBlock heading={<>Ce que FILON ne fait <span className="it">jamais</span>.</>} alt>
        <p>
          FILON ne revend pas votre navigation, ne construit pas de profil publicitaire, et ne modifie jamais le prix que vous
          payez chez le marchand. Il ne stocke pas non plus vos moyens de paiement : l&apos;achat se fait chez le marchand,
          comme d&apos;habitude, FILON vous a seulement mené·e à la meilleure décision.
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
      <ClosingCta title={<>Un copilote en qui vous pouvez avoir <span className="it">confiance</span>.</>} sub="Minimisation des données, zéro revente, aucune publicité." />
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
              { n: <IcLock />, h: "Gegevensminimalisatie", p: "FILON analyseert alleen wat strikt nodig is voor de vergelijking. Niets meer." },
              { n: <IcNoResale />, h: "Geen doorverkoop", p: "Geen advertentieprofiel, geen doorverkoop aan derden. Je gegevens blijven van jou." },
              { n: <IcEncrypted />, h: "Versleutelde verbindingen", p: "De uitwisselingen met onze diensten zijn end-to-end versleuteld (HTTPS/TLS)." },
              { n: <IcShieldCheck />, h: "AVG-conform", p: "Verwerking standaard AVG-conform, met rechten die je op elk moment kunt uitoefenen." },
              { n: <IcChartNoCookie />, h: "Meting zonder cookies", p: "Ons bereik wordt gemeten zonder cookies en anoniem (Plausible)." },
              { n: <IcEye />, h: "Zonder bijbedoeling", p: "Geen reclame. De aanbeveling dient jouw belang, niet het onze." },
            ]}
          />
        </div>
      </section>
      <ProseBlock heading={<>Wat FILON <span className="it">nooit</span> doet.</>} alt>
        <p>
          FILON verkoopt je browsegedrag niet door, bouwt geen advertentieprofiel op, en wijzigt nooit de prijs die je bij
          de winkel betaalt. Het bewaart ook je betaalmiddelen niet : de aankoop gebeurt bij de winkel, zoals gewoonlijk —
          FILON heeft je enkel naar de beste beslissing geleid.
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
      <ClosingCta title={<>Een copiloot die je kunt <span className="it">vertrouwen</span>.</>} sub="Gegevensminimalisatie, nul doorverkoop, geen reclame." />
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
              { n: <IcLock />, h: "Data minimisation", p: "FILON analyses only what's strictly necessary for the comparison. Nothing more." },
              { n: <IcNoResale />, h: "No reselling", p: "No advertising profile, no reselling to third parties. Your data stays yours." },
              { n: <IcEncrypted />, h: "Encrypted connections", p: "Exchanges with our services are end-to-end encrypted (HTTPS/TLS)." },
              { n: <IcShieldCheck />, h: "GDPR-compliant", p: "Processing GDPR-compliant by default, with rights you can exercise at any time." },
              { n: <IcChartNoCookie />, h: "Cookie-free measurement", p: "Our audience is measured cookie-free and anonymously (Plausible)." },
              { n: <IcEye />, h: "No ulterior motive", p: "No advertising. The recommendation serves your interest, not ours." },
            ]}
          />
        </div>
      </section>
      <ProseBlock heading={<>What FILON <span className="it">never</span> does.</>} alt>
        <p>
          FILON doesn&apos;t resell your browsing, doesn&apos;t build an advertising profile, and never changes the
          price you pay at the merchant. Nor does it store your payment methods: the purchase happens at the
          merchant, as usual — FILON only led you to the best decision.
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
      <ClosingCta title={<>A copilot you can <span className="it">trust</span>.</>} sub="Data minimisation, zero reselling, no advertising." />
    </>
  );
}

export default function SecuritePage() {
  return <Localized fr={<SecuriteFR />} nl={<SecuriteNL />} en={<SecuriteEN />} />;
}
