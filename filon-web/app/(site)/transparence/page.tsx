import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/transparence",
  title: "Transparence & affiliation",
  description:
    "Comment FILON utilise les liens d'affiliation, quels champs entrent dans le score actuel et quelles conditions restent à confirmer chez le marchand.",
});

function TransparenceFR() {
  return (
    <>
      <ContentHero
        eyebrow="Transparence"
        title={
          <>
            Comment FILON utilise l&apos;affiliation, <span className="it">avec un périmètre explicite</span>.
          </>
        }
        intro={
          <>
            Un service gratuit doit s&apos;expliquer. Voici, sans détour, notre modèle : d&apos;où vient
            l&apos;argent et les données qui entrent — ou non — dans le score actuel.
          </>
        }
        breadcrumb={[{ name: "Transparence", path: "/transparence" }]}
      />

      <ProseBlock heading={<>Nous sommes rémunérés par <span className="it">l&apos;affiliation</span>.</>}>
        <p>
          Quand vous cliquez sur «&nbsp;Voir l&apos;offre&nbsp;» et que vous achetez chez un marchand, celui-ci peut
          nous verser une <b>commission d&apos;affiliation</b>. C&apos;est notre source de revenus.
        </p>
        <p>
          La commission éventuelle n&apos;entre pas dans les dimensions du score actuel. Le prix, les frais, les
          conditions d&apos;éligibilité et le total final restent toutefois à confirmer sur le site du marchand.
        </p>
        <p style={{ color: "var(--ink-3)", fontSize: 14 }}>
          En clair&nbsp;: certains liens de ce site sont affiliés. Cliquer puis acheter peut rapporter une commission
          à FILON. La fiche affiche le marchand ; le panier du marchand fait foi pour le montant payé.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-lead">
            <span className="idx">Nos règles</span>
            <h2>
              Ce que l&apos;implémentation actuelle <span className="it">sépare</span>.
            </h2>
          </div>
          <InfoGrid
            items={[
              {
                n: "01",
                h: "Commission hors score",
                p: "Le score actuel utilise les preuves de comparaison, d'historique, de disponibilité, de fraîcheur et de largeur de comparaison ; aucun taux de commission n'est un champ d'entrée.",
              },
              {
                n: "02",
                h: "Périmètre comparé visible",
                p: "Une position ou un prix n'est décrit que dans le périmètre des offres éligibles et indexées ; FILON ne prétend pas à une couverture exhaustive.",
              },
              {
                n: "03",
                h: "Lien affilié identifiable",
                p: "Le lien peut générer une commission. L'offre conserve son marchand source et les inconnues restent visibles.",
              },
              {
                n: "04",
                h: "Accès actuel gratuit",
                p: "L'accès public actuel ne demande ni paiement ni carte bancaire. Les conditions publiées font foi si l'offre évolue.",
              },
              {
                n: "05",
                h: "Confidentialité documentée",
                p: "La politique de confidentialité décrit les données traitées et la mesure d'audience. Consultez-la pour le périmètre à jour.",
              },
              {
                n: "06",
                h: "Le raisonnement est ouvert",
                p: "Le Score expose ses dimensions documentées, ses dimensions manquantes et son périmètre de recommandation.",
              },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Quand l&apos;information manque, on le <span className="it">dit</span>.</>} alt>
        <p>
          Les offres et l&apos;historique ne sont pas disponibles avec la même profondeur pour chaque produit. Une
          garantie, une alternative comparable ou un historique suffisant peuvent manquer.
        </p>
        <p>
          Dans ce cas, FILON ne transforme pas une hypothèse en recommandation&nbsp;: l&apos;information est absente,
          ou le verdict indique que le suivi est trop récent.
        </p>
        <p>
          Notre seul actif, c&apos;est votre confiance&nbsp;: nous préférons afficher «&nbsp;on ne sait pas encore&nbsp;»
          plutôt qu&apos;un beau chiffre faux.
        </p>
      </ProseBlock>

      <ClosingCta
        title={<>Des preuves visibles, <span className="it">des inconnues nommées.</span></>}
        sub="Demandez à FILON avant d'acheter, puis confirmez le total et les conditions chez le marchand."
      />
    </>
  );
}

function TransparenceNL() {
  return (
    <>
      <ContentHero
        eyebrow="Transparantie"
        title={
          <>
            Hoe FILON affiliatie gebruikt, <span className="it">met een expliciete reikwijdte</span>.
          </>
        }
        intro={
          <>
            Een gratis dienst moet zich verantwoorden. Hier, zonder omwegen, ons model : waar het geld vandaan komt,
            en welke gegevens wel of niet in de huidige score worden gebruikt.
          </>
        }
        breadcrumb={[{ name: "Transparantie", path: "/transparence" }]}
      />

      <ProseBlock heading={<>We worden vergoed via <span className="it">affiliatie</span>.</>}>
        <p>
          Wanneer je op «&nbsp;Bekijk het aanbod&nbsp;» klikt en bij een winkel koopt, kan die ons een{" "}
          <b>affiliatiecommissie</b> betalen. Dat is onze inkomstenbron.
        </p>
        <p>
          Een eventuele commissie is geen invoerveld van de huidige score. Bevestig prijs, kosten,
          geschiktheidsvoorwaarden en eindtotaal op de website van de winkel.
        </p>
        <p style={{ color: "var(--ink-3)", fontSize: 14 }}>
          In klare taal&nbsp;: sommige links op deze site zijn affiliatielinks. Klikken en kopen kan FILON een
          commissie opleveren. De winkelmand van de verkoper bepaalt het betaalde bedrag.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-lead">
            <span className="idx">Onze regels</span>
            <h2>
              Wat de huidige implementatie <span className="it">scheidt</span>.
            </h2>
          </div>
          <InfoGrid
            items={[
              {
                n: "01",
                h: "Commissie buiten de score",
                p: "De huidige score gebruikt bewijs voor vergelijking, historiek, beschikbaarheid, actualiteit en vergelijkingsbreedte; een commissietarief is geen invoerveld.",
              },
              {
                n: "02",
                h: "Zichtbare vergelijkingsomvang",
                p: "Een positie of prijs geldt alleen binnen de in aanmerking komende, geïndexeerde aanbiedingen; FILON claimt geen volledige marktdekking.",
              },
              {
                n: "03",
                h: "Herkenbare affiliatielink",
                p: "De link kan een commissie opleveren. De aanbieding behoudt haar bron en onbekenden blijven zichtbaar.",
              },
              {
                n: "04",
                h: "Huidige toegang gratis",
                p: "De huidige publieke toegang vraagt geen betaling of bankkaart. De gepubliceerde voorwaarden gelden als het aanbod verandert.",
              },
              {
                n: "05",
                h: "Gedocumenteerde privacy",
                p: "Het privacybeleid beschrijft de verwerkte gegevens en bezoekersmeting. Raadpleeg het voor de actuele reikwijdte.",
              },
              {
                n: "06",
                h: "De redenering ligt open",
                p: "De Score toont gedocumenteerde dimensies, ontbrekende dimensies en de aanbevelingsomvang.",
              },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>Wanneer informatie ontbreekt, <span className="it">zeggen we dat</span>.</>} alt>
        <p>
          Aanbiedingen en prijsgeschiedenis zijn niet voor elk product even volledig beschikbaar. Een garantie,
          vergelijkbaar alternatief of voldoende geschiedenis kan ontbreken.
        </p>
        <p>
          In dat geval maakt FILON van een aanname geen aanbeveling: de informatie ontbreekt, of het oordeel geeft
          aan dat de opvolging te recent is.
        </p>
        <p>
          Onze enige troef is je vertrouwen: we tonen liever «&nbsp;dat weten we nog niet&nbsp;» dan een mooi vals cijfer.
        </p>
      </ProseBlock>

      <ClosingCta
        title={<>Zichtbaar bewijs, <span className="it">benoemde onbekenden.</span></>}
        sub="Vraag FILON vóór je koopt en bevestig daarna totaal en voorwaarden bij de winkel."
      />
    </>
  );
}

function TransparenceEN() {
  return (
    <>
      <ContentHero
        eyebrow="Transparency"
        title={
          <>
            How FILON uses affiliation, <span className="it">with explicit scope</span>.
          </>
        }
        intro={
          <>
            A free service owes an explanation. Here, plainly, is our model: where the money comes from, what it
            and which data does or does not enter the current score.
          </>
        }
        breadcrumb={[{ name: "Transparency", path: "/transparence" }]}
      />

      <ProseBlock heading={<>We&apos;re paid through <span className="it">affiliation</span>.</>}>
        <p>
          When you click « See the offer » and buy from a merchant, that merchant may pay us an{" "}
          <b>affiliation commission</b>. That&apos;s our source of income.
        </p>
        <p>
          A possible commission is not an input field in the current score. Confirm the price, fees, eligibility
          terms and final total on the merchant&apos;s website.
        </p>
        <p style={{ color: "var(--ink-3)", fontSize: 14 }}>
          In plain terms&nbsp;: some links on this site are affiliate links. Clicking and buying may earn FILON a
          commission. The merchant&apos;s basket determines the amount paid.
        </p>
      </ProseBlock>

      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-lead">
            <span className="idx">Our rules</span>
            <h2>
              What the current implementation <span className="it">separates</span>.
            </h2>
          </div>
          <InfoGrid
            items={[
              {
                n: "01",
                h: "Commission outside the score",
                p: "The current score uses evidence for comparison, history, availability, freshness and comparison breadth; a commission rate is not an input field.",
              },
              {
                n: "02",
                h: "Visible comparison scope",
                p: "A position or price applies only within eligible indexed offers; FILON does not claim whole-market coverage.",
              },
              {
                n: "03",
                h: "Identifiable affiliate link",
                p: "The link may generate a commission. The offer retains its source merchant and unknowns remain visible.",
              },
              {
                n: "04",
                h: "Current access is free",
                p: "Current public access requires no payment or card. Published terms apply if the offering changes.",
              },
              {
                n: "05",
                h: "Documented privacy",
                p: "The privacy policy describes processed data and audience measurement. Consult it for the current scope.",
              },
              {
                n: "06",
                h: "The reasoning is open",
                p: "The Score exposes documented dimensions, missing dimensions and its recommendation scope.",
              },
            ]}
          />
        </div>
      </section>

      <ProseBlock heading={<>When information is missing, we <span className="it">say so</span>.</>} alt>
        <p>
          Offers and price history are not available with the same depth for every product. A warranty, comparable
          alternative or sufficient history may be missing.
        </p>
        <p>
          In that case, FILON does not turn an assumption into a recommendation: the information is unavailable, or
          the verdict states that tracking is still too recent.
        </p>
        <p>
          Trust is our only asset: we&apos;d rather show « we don&apos;t know yet » than a nice but false figure.
        </p>
      </ProseBlock>

      <ClosingCta
        title={<>Visible evidence, <span className="it">named unknowns.</span></>}
        sub="Ask FILON before buying, then confirm the total and terms with the merchant."
      />
    </>
  );
}

export default function TransparencePage() {
  return <Localized fr={<TransparenceFR />} nl={<TransparenceNL />} en={<TransparenceEN />} />;
}
