import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, InfoGrid, ProseBlock, ClosingCta } from "@/components/editorial/ContentPage";
import { site } from "@/lib/site";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/aide",
  title: "Centre d'aide",
  description:
    "Besoin d'un coup de main avec FILON ? Prise en main, cashback, reconditionné, extension, compte et données : les réponses par thème, et un contact humain quand il vous faut.",
});

function AideFR() {
  return (
    <>
      <ContentHero
        eyebrow="Aide"
        title={<>On est là quand vous en avez <span className="it">besoin</span>.</>}
        intro="Choisissez un thème pour trouver rapidement votre réponse. Et si vous ne trouvez pas, un humain vous répond, pas un robot qui tourne en rond."
        breadcrumb={[{ name: "Centre d'aide", path: "/aide" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <InfoGrid
            items={[
              { n: "01", h: "Prise en main", p: "Comment poser un besoin, lire les preuves et ouvrir une offre observée. Voir « Comment ça marche »." },
              { n: "02", h: "Cashback", p: "Plateformes comparées, cumul avec un code promo, délais de validation et de retrait." },
              { n: "03", h: "Reconditionné", p: "Grades indiqués, garantie lorsqu'elle est fournie et conditions à vérifier chez le vendeur." },
              { n: "04", h: "Extension", p: "Installation, navigateurs pris en charge, ce qui s'affiche sur une fiche produit." },
              { n: "05", h: "Compte & alertes", p: "Créer un compte, gérer les alertes de baisse de prix et vos préférences." },
              { n: "06", h: "Données & confidentialité", p: "Ce que FILON lit, ce qu'il ne fait pas, et comment exercer vos droits RGPD." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Vous ne trouvez pas ? <span className="it">Écrivez-nous</span>.</>} alt>
        <p>
          La plupart des réponses se trouvent dans notre <a href="/faq">FAQ</a> et sur la page{" "}
          <a href="/comment-ca-marche">Comment ça marche</a>. Pour tout le reste, notre équipe répond directement.
        </p>
        <p>
          Contactez-nous à <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a> ou via le{" "}
          <a href="/contact">formulaire de contact</a>. Nous revenons vers vous rapidement, en français ou en néerlandais.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Prêt·e à mieux <span className="it">comparer</span> ?</>} sub="Utilisez FILON sur les offres indexées et confirmez le total chez le marchand." />
    </>
  );
}

function AideNL() {
  return (
    <>
      <ContentHero
        eyebrow="Hulp"
        title={<>We zijn er wanneer je ons <span className="it">nodig</span> hebt.</>}
        intro="Kies een thema om snel je antwoord te vinden. En als je het niet vindt, antwoordt een mens je, geen robot die in cirkels draait."
        breadcrumb={[{ name: "Helpcentrum", path: "/aide" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <InfoGrid
            items={[
              { n: "01", h: "Aan de slag", p: "Hoe je een behoefte formuleert, het oordeel leest en het beste aanbod activeert. Zie « Hoe het werkt »." },
              { n: "02", h: "Cashback", p: "Vergeleken platforms, combinatie met een promocode, validatie- en opnametermijnen." },
              { n: "03", h: "Refurbished", p: "Vermelde staat, garantie wanneer verstrekt en voorwaarden die je bij de verkoper controleert." },
              { n: "04", h: "Extensie", p: "Installatie, ondersteunde browsers, wat verschijnt op een productpagina." },
              { n: "05", h: "Account & meldingen", p: "Een account aanmaken, prijsdalings-meldingen en je voorkeuren beheren." },
              { n: "06", h: "Gegevens & privacy", p: "Wat FILON leest, wat het niet doet, en hoe je je GDPR-rechten uitoefent." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Vind je het niet ? <span className="it">Schrijf ons</span>.</>} alt>
        <p>
          De meeste antwoorden vind je in onze <a href="/faq">FAQ</a> en op de pagina{" "}
          <a href="/comment-ca-marche">Hoe het werkt</a>. Voor al de rest antwoordt ons team rechtstreeks.
        </p>
        <p>
          Contacteer ons op <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a> of via het{" "}
          <a href="/contact">contactformulier</a>. We komen snel bij je terug, in het Frans of het Nederlands.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Klaar om beter te <span className="it">vergelijken</span> ?</>} sub="Gebruik FILON voor geïndexeerde aanbiedingen en bevestig het totaal bij de winkel." />
    </>
  );
}

function AideEN() {
  return (
    <>
      <ContentHero
        eyebrow="Help"
        title={<>We&apos;re here when you <span className="it">need</span> us.</>}
        intro="Pick a topic to quickly find your answer. And if you can't find it, a human replies, not a robot going in circles."
        breadcrumb={[{ name: "Help centre", path: "/aide" }]}
      />

      <section className="ed-band" style={{ borderTop: 0, paddingTop: 0 }}>
        <div className="ed-wrap">
          <InfoGrid
            items={[
              { n: "01", h: "Getting started", p: "How to state a need, read the evidence and open an observed offer. See « How it works »." },
              { n: "02", h: "Cashback", p: "Platforms compared, combining with a promo code, validation and withdrawal times." },
              { n: "03", h: "Refurbished", p: "Stated condition, warranty when supplied and terms to verify with the seller." },
              { n: "04", h: "Extension", p: "Installation, supported browsers, what shows on a product page." },
              { n: "05", h: "Account & alerts", p: "Create an account, manage price-drop alerts and your preferences." },
              { n: "06", h: "Data & privacy", p: "What FILON reads, what it doesn't do, and how to exercise your GDPR rights." },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Can&apos;t find it ? <span className="it">Write to us</span>.</>} alt>
        <p>
          Most answers are in our <a href="/faq">FAQ</a> and on the{" "}
          <a href="/comment-ca-marche">How it works</a> page. For everything else, our team replies directly.
        </p>
        <p>
          Contact us at <a href={`mailto:contact@${site.domain}`}>contact@{site.domain}</a> or via the{" "}
          <a href="/contact">contact form</a>. We&apos;ll get back to you quickly, in French or Dutch.
        </p>
      </ProseBlock>

      <ClosingCta title={<>Ready to <span className="it">compare</span> more clearly ?</>} sub="Use FILON for indexed offers and confirm the total with the merchant." />
    </>
  );
}

export default function AidePage() {
  return <Localized fr={<AideFR />} nl={<AideNL />} en={<AideEN />} />;
}
