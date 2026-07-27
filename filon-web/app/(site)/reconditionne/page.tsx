import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";
import { Localized } from "@/components/editorial/Localized";

export const metadata: Metadata = buildMetadata({
  path: "/reconditionne",
  title: "Reconditionné : le même produit, jusqu'à 50 % moins cher",
  description:
    "Neuf ou reconditionné ? FILON compare le prix neuf au reconditionné équivalent (grade vérifié, garanti) et calcule l'économie réelle, meilleur pour votre budget et pour la planète.",
});

const FAQ_FR = [
  { q: "Un produit reconditionné, est-ce fiable ?", a: "Oui, quand il est bien choisi. FILON ne retient que du reconditionné vérifié, chez des vendeurs certifiés et sous garantie. Vous voyez la garantie et l'économie avant de décider." },
  { q: "Quelle économie peut-on vraiment espérer ?", a: "Un smartphone haut de gamme reconditionné se négocie souvent 40 % sous le neuf. En ajoutant un cashback partenaire (3 à 8 %), l'économie totale atteint 45 à 50 %. FILON calcule ce cumul pour vous." },
  { q: "Que veulent dire les grades A, A+, etc. ?", a: "Le grade décrit l'état esthétique : un grade A+ est quasi neuf, un grade B présente de légères marques d'usage sans impact sur le fonctionnement. FILON affiche le grade pour chaque offre afin que vous choisissiez en connaissance de cause." },
  { q: "Le reconditionné, est-ce vraiment plus écologique ?", a: "Oui : prolonger la vie d'un appareil évite la fabrication d'un neuf, gros consommateur de ressources et d'énergie. C'est l'un des gestes les plus efficaces pour réduire l'empreinte de vos achats tech." },
  { q: "Puis-je cumuler reconditionné et cashback ?", a: "Absolument, et c'est là que FILON brille : il additionne le prix reconditionné le plus bas, le cashback le plus élevé et un éventuel code promo pour afficher votre prix réel final." },
];

const FAQ_NL = [
  { q: "Is een refurbished product betrouwbaar ?", a: "Ja, als het goed gekozen is. FILON weerhoudt alleen geverifieerd refurbished, bij gecertificeerde verkopers en met garantie. Je ziet de garantie en de besparing voordat je beslist." },
  { q: "Hoeveel kun je echt besparen ?", a: "Een high-end smartphone gaat refurbished vaak 40 % onder nieuw. Met een partner-cashback (3 tot 8 %) loopt de totale besparing op tot 45 à 50 %. FILON telt dat samen voor jou." },
  { q: "Wat betekenen de grades A, A+, enz. ?", a: "De grade beschrijft de esthetische staat: A+ is zo goed als nieuw, grade B vertoont lichte gebruikssporen zonder invloed op de werking. FILON toont de grade bij elke aanbieding zodat je met kennis van zaken kiest." },
  { q: "Is refurbished echt milieuvriendelijker ?", a: "Ja: het leven van een toestel verlengen vermijdt de productie van een nieuw toestel, dat veel grondstoffen en energie verbruikt. Het is een van de doeltreffendste gebaren om de voetafdruk van je tech-aankopen te verkleinen." },
  { q: "Kan ik refurbished en cashback combineren ?", a: "Absoluut, en daar blinkt FILON in uit: het telt de laagste refurbished-prijs, de hoogste cashback en een eventuele kortingscode op om je echte eindprijs te tonen." },
];

const FAQ_EN = [
  { q: "Is a refurbished product reliable ?", a: "Yes, when well chosen. FILON only keeps verified refurbished, from certified sellers and under warranty. You see the warranty and the saving before you decide." },
  { q: "How much can you really save ?", a: "A high-end refurbished smartphone often sells 40% below new. Adding a partner cashback (3 to 8%), the total saving reaches 45 to 50%. FILON adds this up for you." },
  { q: "What do grades A, A+, etc. mean ?", a: "The grade describes the cosmetic condition: an A+ grade is almost new, a B grade shows slight signs of use with no impact on functioning. FILON displays the grade for each offer so you choose with full knowledge." },
  { q: "Is refurbished really more eco-friendly ?", a: "Yes: extending a device's life avoids manufacturing a new one, a heavy consumer of resources and energy. It's one of the most effective moves to reduce the footprint of your tech purchases." },
  { q: "Can I combine refurbished and cashback ?", a: "Absolutely, and that's where FILON shines: it adds up the lowest refurbished price, the highest cashback and any promo code to show your real final price." },
];

function ReconditionneFR() {
  return (
    <>
      <ContentHero
        eyebrow="Reconditionné"
        title={<>Le même produit. Jusqu&apos;à <span className="it">50 %</span> moins cher.</>}
        intro="Pourquoi payer le neuf plein tarif quand l'équivalent reconditionné, vérifié et garanti, coûte souvent 40 % de moins ? FILON compare les deux et ajoute le cashback pour révéler votre prix réel, meilleur pour votre budget, et pour la planète."
        breadcrumb={[{ name: "Reconditionné", path: "/reconditionne" }]}
        photo="/img/page-reconditionne.webp"
      />
      <ProseBlock heading={<>Neuf ou reconditionné ? FILON <span className="it">tranche</span> pour vous.</>}>
        <p>
          Comparer soi-même le neuf et le reconditionné, c&apos;est fastidieux : trouver l&apos;équivalent exact, vérifier
          la garantie, le vendeur, puis calculer l&apos;économie réelle.
        </p>
        <p>
          FILON le fait pour vous, en une seconde. Il vous montre le <b>neuf</b>, le <b>reconditionné équivalent
          garanti</b>, et <b>votre vrai prix</b>. Vous décidez en un coup d&apos;œil, sans y passer votre soirée.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Ce que FILON vérifie avant de vous le proposer.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "✓", h: "Grade vérifié", p: "L'état esthétique et fonctionnel est affiché clairement (A+, A, B…)." },
              { n: "✓", h: "Garantie réelle", p: "12 à 24 mois selon le vendeur, jamais un reconditionné sans filet." },
              { n: "✓", h: "Économie chiffrée", p: "Le gain vs neuf, cashback compris, calculé et affiché avant l'achat." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_FR} eyebrow="Reconditionné · FAQ" title="Le reconditionné, en toute confiance." />
      <ClosingCta title={<>Payez le <span className="it">juste</span> prix. Pas le prix neuf.</>} sub="FILON compare neuf et reconditionné à chaque achat, gratuitement." />
    </>
  );
}

function ReconditionneNL() {
  return (
    <>
      <ContentHero
        eyebrow="Refurbished"
        title={<>Hetzelfde product. Tot <span className="it">50 %</span> goedkoper.</>}
        intro="Waarom de volle nieuwprijs betalen als het gelijkwaardige refurbished toestel, geverifieerd en met garantie, vaak 40 % minder kost ? FILON vergelijkt beide en telt de cashback erbij om je echte prijs te tonen — beter voor je budget, en voor de planeet."
        breadcrumb={[{ name: "Refurbished", path: "/reconditionne" }]}
        photo="/img/page-reconditionne.webp"
      />
      <ProseBlock heading={<>Nieuw of refurbished ? FILON <span className="it">beslist</span> voor jou.</>}>
        <p>
          Zelf nieuw en refurbished vergelijken is bewerkelijk : het exacte equivalent vinden, de garantie en de
          verkoper checken, en dan de echte besparing berekenen.
        </p>
        <p>
          FILON doet het voor jou, in één seconde. Het toont je het <b>nieuwe toestel</b>, het <b>gelijkwaardige
          refurbished met garantie</b>, en <b>je echte prijs</b>. Jij beslist in één oogopslag, zonder er je avond aan
          te besteden.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>Wat FILON controleert voordat het je iets aanbeveelt.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "✓", h: "Geverifieerde grade", p: "De esthetische en functionele staat wordt duidelijk getoond (A+, A, B…)." },
              { n: "✓", h: "Echte garantie", p: "12 tot 24 maanden volgens de verkoper, nooit refurbished zonder vangnet." },
              { n: "✓", h: "Becijferde besparing", p: "De winst t.o.v. nieuw, cashback inbegrepen, berekend en getoond vóór aankoop." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_NL} eyebrow="Refurbished · FAQ" title="Refurbished, met een gerust hart." />
      <ClosingCta title={<>Betaal de <span className="it">juiste</span> prijs. Niet de nieuwprijs.</>} sub="FILON vergelijkt nieuw en refurbished bij elke aankoop, gratis." />
    </>
  );
}

function ReconditionneEN() {
  return (
    <>
      <ContentHero
        eyebrow="Refurbished"
        title={<>The same product. Up to <span className="it">50%</span> cheaper.</>}
        intro="Why pay full price for new when the refurbished equivalent — verified and guaranteed — often costs 40% less ? FILON compares the two and adds the cashback to reveal your real price, better for your budget, and for the planet."
        breadcrumb={[{ name: "Refurbished", path: "/reconditionne" }]}
        photo="/img/page-reconditionne.webp"
      />
      <ProseBlock heading={<>New or refurbished ? FILON <span className="it">decides</span> for you.</>}>
        <p>
          Comparing new and refurbished yourself is tedious: finding the exact equivalent, checking the warranty,
          the seller, then calculating the real saving.
        </p>
        <p>
          FILON does it for you, in one second. It shows you the <b>new</b>, the <b>guaranteed refurbished
          equivalent</b>, and <b>your real price</b>. You decide at a glance, without spending your evening on it.
        </p>
      </ProseBlock>
      <section className="ed-band alt">
        <div className="ed-wrap">
          <div className="ed-prose" style={{ marginBottom: 28 }}>
            <h2 style={{ maxWidth: "20ch" }}>What FILON checks before recommending it to you.</h2>
          </div>
          <InfoGrid
            items={[
              { n: "✓", h: "Verified grade", p: "The cosmetic and functional condition is displayed clearly (A+, A, B…)." },
              { n: "✓", h: "Real warranty", p: "12 to 24 months depending on the seller, never refurbished without a safety net." },
              { n: "✓", h: "Quantified saving", p: "The gain vs new, cashback included, calculated and shown before purchase." },
            ]}
          />
        </div>
      </section>
      <FaqBlock items={FAQ_EN} eyebrow="Refurbished · FAQ" title="Refurbished, with peace of mind." />
      <ClosingCta title={<>Pay the <span className="it">right</span> price. Not the new price.</>} sub="FILON compares new and refurbished on every purchase, free." />
    </>
  );
}

export default function ReconditionnePage() {
  return <Localized fr={<ReconditionneFR />} nl={<ReconditionneNL />} en={<ReconditionneEN />} />;
}
