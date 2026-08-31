import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/codes-promo",
  title: "Codes promo : conditions à vérifier",
  description:
    "FILON peut afficher un code présent dans une source indexée. Son éligibilité, son cumul et sa validité restent à confirmer chez le marchand.",
});

const FAQ_FR = [
  { q: "Pourquoi un code peut-il ne pas fonctionner ?", a: "Un code peut être expiré, réservé à un produit, un pays, un compte ou un panier minimum. Seul le marchand confirme son application au panier." },
  { q: "Que peut afficher FILON ?", a: "Un code ou une promotion lorsqu'une source indexée les fournit, avec les conditions connues. FILON ne simule pas le checkout." },
  { q: "Un code se cumule-t-il avec le cashback ?", a: "Cela dépend des conditions du code et du cashback. Sans preuve explicite, le cumul reste inconnu." },
  { q: "Les codes sont-ils à jour ?", a: "La date et la source disponibles doivent être affichées. Vérifiez toujours l'application réelle dans le panier du marchand." },
  { q: "L'extension applique-t-elle le code automatiquement ?", a: "Non. La version actuelle repère le produit et ouvre l'analyse FILON ; elle ne lit ni ne modifie le panier." },
];

const FAQ_NL = [
  { q: "Waarom kan een kortingscode niet werken ?", a: "Een code kan verlopen zijn of beperkt zijn tot een product, land, account of minimumbedrag. Alleen de winkel bevestigt toepassing in het mandje." },
  { q: "Wat kan FILON tonen ?", a: "Een code of promotie wanneer een geïndexeerde bron die levert, met bekende voorwaarden. FILON simuleert de checkout niet." },
  { q: "Kan een kortingscode gecombineerd worden met cashback ?", a: "Dat hangt af van de voorwaarden. Zonder expliciet bewijs blijft de combinatie onbekend." },
  { q: "Zijn de codes up-to-date ?", a: "Beschikbare datum en bron moeten zichtbaar zijn. Controleer de echte toepassing altijd in het winkelmandje." },
  { q: "Past de extensie de code automatisch toe ?", a: "Nee. De huidige versie herkent het product en opent de FILON-analyse; ze leest of wijzigt het mandje niet." },
];

const FAQ_EN = [
  { q: "Why might a promo code not work ?", a: "A code may be expired or limited to a product, country, account or minimum basket. Only the merchant confirms its application in the basket." },
  { q: "What can FILON show ?", a: "A code or promotion when an indexed source supplies it, together with known conditions. FILON does not simulate checkout." },
  { q: "Can a promo code be combined with cashback ?", a: "That depends on both sets of terms. Without explicit evidence, the combination remains unknown." },
  { q: "Are the codes up to date ?", a: "The available date and source must be visible. Always verify actual application in the merchant's basket." },
  { q: "Does the extension apply a code automatically ?", a: "No. The current version identifies the product and opens the FILON analysis; it does not read or modify the basket." },
];

function CodesFR() {
  return (
    <>
      <ContentHero
        eyebrow="Codes promo"
        title={<>Des codes promo, avec leurs <span className="it">conditions</span>.</>}
        intro="FILON peut relayer une promotion issue d'une source indexée. La validité, l'éligibilité et le cumul sont confirmés uniquement dans le panier du marchand."
        breadcrumb={[{ name: "Codes promo", path: "/codes-promo" }]}
      />
      <ProseBlock heading={<>Le code promo, sans la <span className="it">chasse</span> au code.</>}>
        <p>
          Chercher un code, ouvrir cinq sites de bons plans, coller, essuyer un « invalide », recommencer… Ce petit rituel
          coûte du temps et, souvent, on abandonne en payant plein tarif.
        </p>
        <p>
          La version actuelle de FILON ne lit pas votre panier et ne teste aucun
          code au checkout. Elle peut montrer une promotion documentée et vous
          renvoie vers le marchand pour la vérification finale.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Trois informations à contrôler.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Source", p: "D'où vient le code et quand a-t-il été observé ?" },
              { n: "02", h: "Éligibilité", p: "Produit, pays, compte, minimum de panier et date d'expiration." },
              { n: "03", h: "Vérification finale", p: "Le marchand confirme l'application et le montant réel dans le panier." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_FR} eyebrow="Codes promo · FAQ" title="Les codes promo, enfin sans frustration." />
      <ClosingCta title={<>Vérifiez le code dans le <span className="it">panier</span>.</>} sub="FILON ne présente jamais une réduction inconnue comme acquise." />
    </>
  );
}

function CodesNL() {
  return (
    <>
      <ContentHero
        eyebrow="Kortingscodes"
        title={<>Kortingscodes, met hun <span className="it">voorwaarden</span>.</>}
        intro="FILON kan een promotie uit een geïndexeerde bron tonen. Geldigheid, geschiktheid en combinatie worden alleen in het winkelmandje bevestigd."
        breadcrumb={[{ name: "Kortingscodes", path: "/codes-promo" }]}
      />
      <ProseBlock heading={<>De kortingscode, zonder de <span className="it">jacht</span> op codes.</>}>
        <p>
          Een code zoeken, vijf dealsites openen, plakken, een « ongeldig » incasseren, opnieuw beginnen… Dat ritueel kost
          tijd en vaak geef je op en betaal je de volle prijs.
        </p>
        <p>
          De huidige FILON-versie leest je winkelmandje niet en test geen code
          bij de checkout. Ze kan een gedocumenteerde promotie tonen en verwijst
          naar de winkel voor de uiteindelijke controle.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Drie gegevens om te controleren.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Bron", p: "Waar komt de code vandaan en wanneer werd hij waargenomen?" },
              { n: "02", h: "Geschiktheid", p: "Product, land, account, minimumbedrag en vervaldatum." },
              { n: "03", h: "Eindcontrole", p: "De winkel bevestigt toepassing en werkelijk bedrag in het mandje." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_NL} eyebrow="Kortingscodes · FAQ" title="Kortingscodes, eindelijk zonder frustratie." />
      <ClosingCta title={<>Controleer de code in het <span className="it">mandje</span>.</>} sub="FILON stelt een onbekende korting nooit als verworven voor." />
    </>
  );
}

function CodesEN() {
  return (
    <>
      <ContentHero
        eyebrow="Promo codes"
        title={<>Promo codes, with their <span className="it">terms</span>.</>}
        intro="FILON can relay a promotion from an indexed source. Validity, eligibility and combination are confirmed only in the merchant's basket."
        breadcrumb={[{ name: "Promo codes", path: "/codes-promo" }]}
      />
      <ProseBlock heading={<>The promo code, without the code <span className="it">hunt</span>.</>}>
        <p>
          Searching for a code, opening five deal sites, pasting, taking an « invalid », starting over… That little
          ritual costs time and, often, you give up and pay full price.
        </p>
        <p>
          The current FILON version does not read your basket or test any code
          at checkout. It can show a documented promotion and directs you to the
          merchant for final verification.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Three details to check.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Source", p: "Where did the code come from and when was it observed?" },
              { n: "02", h: "Eligibility", p: "Product, country, account, minimum basket and expiry date." },
              { n: "03", h: "Final verification", p: "The merchant confirms application and actual amount in the basket." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_EN} eyebrow="Promo codes · FAQ" title="Promo codes, finally without frustration." />
      <ClosingCta title={<>Check the code in the <span className="it">basket</span>.</>} sub="FILON never presents an unknown discount as secured." />
    </>
  );
}

export default function CodesPromoPage() {
  return <Localized fr={<CodesFR />} nl={<CodesNL />} en={<CodesEN />} />;
}
