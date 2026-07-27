import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/codes-promo",
  title: "Codes promo testés en direct",
  description:
    "Fini les « code expiré ». FILON teste chaque code promo en direct au moment du paiement et applique automatiquement celui qui offre la plus grosse réduction.",
});

const FAQ_FR = [
  { q: "Pourquoi tant de codes promo ne fonctionnent-ils pas ?", a: "La plupart des codes trouvés en ligne sont périmés, réservés à certains produits, ou déjà utilisés. Les tester un par un est chronophage et décourageant. FILON les teste pour vous, en direct, et ne garde que celui qui marche." },
  { q: "Comment FILON trouve-t-il les bons codes ?", a: "Il rassemble les codes disponibles pour le marchand, les essaie automatiquement au moment du paiement, et applique celui qui offre la plus grosse réduction sur votre panier réel." },
  { q: "Un code promo se cumule-t-il avec le cashback ?", a: "Souvent oui. FILON calcule la combinaison la plus rentable entre code promo, cashback et prix reconditionné, puis affiche votre prix réel final." },
  { q: "Les codes sont-ils fiables et à jour ?", a: "Comme ils sont testés en direct sur votre panier, vous n'appliquez jamais un code mort : soit un code fonctionne et la réduction s'affiche, soit FILON passe au suivant." },
  { q: "Dois-je copier-coller les codes moi-même ?", a: "Non. Une fois l'extension active, FILON s'en charge automatiquement à l'étape du paiement. Vous voyez simplement le prix baisser." },
];

const FAQ_NL = [
  { q: "Waarom werken zoveel kortingscodes niet ?", a: "De meeste codes die je online vindt zijn verlopen, voorbehouden aan bepaalde producten, of al gebruikt. Ze één voor één testen kost tijd en ontmoedigt. FILON test ze voor jou, live, en houdt alleen de code die werkt." },
  { q: "Hoe vindt FILON de juiste codes ?", a: "Het verzamelt de beschikbare codes voor de winkel, probeert ze automatisch bij het betalen, en past de code toe die de grootste korting geeft op je echte mandje." },
  { q: "Kan een kortingscode gecombineerd worden met cashback ?", a: "Vaak wel. FILON berekent de voordeligste combinatie tussen kortingscode, cashback en refurbished-prijs, en toont dan je echte eindprijs." },
  { q: "Zijn de codes betrouwbaar en up-to-date ?", a: "Omdat ze live op je mandje worden getest, pas je nooit een dode code toe : ofwel werkt een code en verschijnt de korting, ofwel gaat FILON naar de volgende." },
  { q: "Moet ik de codes zelf kopiëren-plakken ?", a: "Nee. Zodra de extensie actief is, doet FILON dat automatisch bij het betalen. Jij ziet gewoon de prijs dalen." },
];

const FAQ_EN = [
  { q: "Why do so many promo codes not work ?", a: "Most codes found online are expired, reserved for certain products, or already used. Testing them one by one is time-consuming and discouraging. FILON tests them for you, live, and keeps only the one that works." },
  { q: "How does FILON find the right codes ?", a: "It gathers the codes available for the merchant, tries them automatically at checkout, and applies the one that gives the biggest discount on your real basket." },
  { q: "Can a promo code be combined with cashback ?", a: "Often yes. FILON calculates the most profitable combination of promo code, cashback and refurbished price, then shows your real final price." },
  { q: "Are the codes reliable and up to date ?", a: "Since they're tested live on your basket, you never apply a dead code: either a code works and the discount appears, or FILON moves to the next one." },
  { q: "Do I have to copy-paste the codes myself ?", a: "No. Once the extension is active, FILON handles it automatically at the checkout step. You simply watch the price drop." },
];

function CodesFR() {
  return (
    <>
      <ContentHero
        eyebrow="Codes promo"
        title={<>Des codes promo qui fonctionnent <span className="it">vraiment</span>.</>}
        intro="« Code expiré », « non applicable à cet article »… tout le monde connaît la frustration. FILON teste chaque code en direct au moment du paiement et applique automatiquement celui qui offre la plus grosse réduction, sans que vous essayiez dix combinaisons."
        breadcrumb={[{ name: "Codes promo", path: "/codes-promo" }]}
      />
      <ProseBlock heading={<>Le code promo, sans la <span className="it">chasse</span> au code.</>}>
        <p>
          Chercher un code, ouvrir cinq sites de bons plans, coller, essuyer un « invalide », recommencer… Ce petit rituel
          coûte du temps et, souvent, on abandonne en payant plein tarif.
        </p>
        <p>
          FILON inverse la logique : il <b>teste tous les codes disponibles en direct</b> sur votre panier réel et applique
          le plus avantageux. Vous ne voyez qu'une chose : le prix qui baisse, tout seul.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Trois secondes, zéro copier-coller.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Collecte", p: "FILON réunit les codes disponibles pour le marchand où vous êtes." },
              { n: "02", h: "Test en direct", p: "Chaque code est essayé sur votre panier réel, au moment du paiement." },
              { n: "03", h: "Meilleure réduction", p: "Le code le plus avantageux est appliqué, et cumulé au cashback si possible." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_FR} eyebrow="Codes promo · FAQ" title="Les codes promo, enfin sans frustration." />
      <ClosingCta title={<>Ne payez plus jamais <span className="it">avant</span> d&apos;avoir testé les codes.</>} sub="FILON le fait automatiquement, gratuitement, à chaque paiement." />
    </>
  );
}

function CodesNL() {
  return (
    <>
      <ContentHero
        eyebrow="Kortingscodes"
        title={<>Kortingscodes die <span className="it">echt</span> werken.</>}
        intro="« Code verlopen », « niet geldig voor dit artikel »… iedereen kent de frustratie. FILON test elke code live bij het betalen en past automatisch de code toe die de grootste korting geeft, zonder dat jij tien combinaties probeert."
        breadcrumb={[{ name: "Kortingscodes", path: "/codes-promo" }]}
      />
      <ProseBlock heading={<>De kortingscode, zonder de <span className="it">jacht</span> op codes.</>}>
        <p>
          Een code zoeken, vijf dealsites openen, plakken, een « ongeldig » incasseren, opnieuw beginnen… Dat ritueel kost
          tijd en vaak geef je op en betaal je de volle prijs.
        </p>
        <p>
          FILON draait de logica om : het <b>test alle beschikbare codes live</b> op je echte winkelmandje en past de
          voordeligste toe. Jij ziet maar één ding : de prijs die vanzelf daalt.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Drie seconden, nul kopiëren-plakken.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Verzamelen", p: "FILON verzamelt de beschikbare codes voor de winkel waar je bent." },
              { n: "02", h: "Live testen", p: "Elke code wordt geprobeerd op je echte winkelmandje, bij het betalen." },
              { n: "03", h: "Beste korting", p: "De voordeligste code wordt toegepast, en gecombineerd met cashback indien mogelijk." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_NL} eyebrow="Kortingscodes · FAQ" title="Kortingscodes, eindelijk zonder frustratie." />
      <ClosingCta title={<>Betaal nooit meer <span className="it">voordat</span> de codes getest zijn.</>} sub="FILON doet het automatisch, gratis, bij elke betaling." />
    </>
  );
}

function CodesEN() {
  return (
    <>
      <ContentHero
        eyebrow="Promo codes"
        title={<>Promo codes that <span className="it">actually</span> work.</>}
        intro="« Code expired », « not valid for this item »… everyone knows the frustration. FILON tests every code live at checkout and automatically applies the one that gives the biggest discount, without you trying ten combinations."
        breadcrumb={[{ name: "Promo codes", path: "/codes-promo" }]}
      />
      <ProseBlock heading={<>The promo code, without the code <span className="it">hunt</span>.</>}>
        <p>
          Searching for a code, opening five deal sites, pasting, taking an « invalid », starting over… That little
          ritual costs time and, often, you give up and pay full price.
        </p>
        <p>
          FILON flips the logic: it <b>tests all available codes live</b> on your real basket and applies the most
          advantageous one. You see only one thing: the price dropping, all by itself.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "18ch" }}>Three seconds, zero copy-paste.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "01", h: "Collect", p: "FILON gathers the codes available for the merchant you're on." },
              { n: "02", h: "Live test", p: "Each code is tried on your real basket, at the checkout moment." },
              { n: "03", h: "Best discount", p: "The most advantageous code is applied, and combined with cashback where possible." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_EN} eyebrow="Promo codes · FAQ" title="Promo codes, finally without frustration." />
      <ClosingCta title={<>Never pay again <span className="it">before</span> testing the codes.</>} sub="FILON does it automatically, free, at every checkout." />
    </>
  );
}

export default function CodesPromoPage() {
  return <Localized fr={<CodesFR />} nl={<CodesNL />} en={<CodesEN />} />;
}
