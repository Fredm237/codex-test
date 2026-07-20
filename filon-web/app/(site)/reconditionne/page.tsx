import type { Metadata } from "next";
import { buildMetadata } from "@/lib/seo";
import { ContentHero, ProseBlock, InfoGrid, ClosingCta } from "@/components/editorial/ContentPage";
import { FaqBlock } from "@/components/editorial/Faq";

export const metadata: Metadata = buildMetadata({
  path: "/reconditionne",
  title: "Reconditionné : le même produit, jusqu'à 50 % moins cher",
  description:
    "Neuf ou reconditionné ? FILON compare le prix neuf au reconditionné équivalent (grade vérifié, garanti) et calcule l'économie réelle, meilleur pour votre budget et pour la planète.",
});

const FAQ = [
  { q: "Un produit reconditionné, est-ce fiable ?", a: "Oui, quand il est bien sourcé. FILON ne compare que du reconditionné de grade vérifié, issu de vendeurs certifiés (type Back Market) et garanti 12 à 24 mois. Vous voyez le grade, la garantie et l'économie avant de décider." },
  { q: "Quelle économie peut-on vraiment espérer ?", a: "Un smartphone haut de gamme reconditionné se négocie souvent 40 % sous le neuf. En ajoutant un cashback partenaire (3 à 8 %), l'économie totale atteint 45 à 50 %. FILON calcule ce cumul pour vous." },
  { q: "Que veulent dire les grades A, A+, etc. ?", a: "Le grade décrit l'état esthétique : un grade A+ est quasi neuf, un grade B présente de légères marques d'usage sans impact sur le fonctionnement. FILON affiche le grade pour chaque offre afin que vous choisissiez en connaissance de cause." },
  { q: "Le reconditionné, est-ce vraiment plus écologique ?", a: "Oui : prolonger la vie d'un appareil évite la fabrication d'un neuf, gros consommateur de ressources et d'énergie. C'est l'un des gestes les plus efficaces pour réduire l'empreinte de vos achats tech." },
  { q: "Puis-je cumuler reconditionné et cashback ?", a: "Absolument, et c'est là que FILON brille : il additionne le prix reconditionné le plus bas, le cashback le plus élevé et un éventuel code promo pour afficher votre prix réel final." },
];

export default function ReconditionnePage() {
  return (
    <>
      <ContentHero
        eyebrow="Reconditionné"
        title={<>Le même produit. Jusqu&apos;à <span className="it">50 %</span> moins cher.</>}
        intro="Pourquoi payer le neuf plein tarif quand l'équivalent reconditionné, vérifié et garanti, coûte souvent 40 % de moins ? FILON compare les deux et ajoute le cashback pour révéler votre prix réel, meilleur pour votre budget, et pour la planète."
        breadcrumb={[{ name: "Reconditionné", path: "/reconditionne" }]}
      />

      <ProseBlock heading={<>Neuf ou reconditionné ? FILON <span className="it">tranche</span> pour vous.</>}>
        <p>
          Comparer soi-même le neuf et le reconditionné, c'est fastidieux : trouver l'équivalent exact, vérifier le grade,
          la garantie, le vendeur, puis calculer l'économie réelle une fois le cashback ajouté.
        </p>
        <p>
          FILON fait ce croisement en une seconde. Il vous montre le <b>prix neuf</b>, le <b>reconditionné équivalent garanti</b>,
          et le <b>prix réel final</b> cashback inclus. Vous décidez en un coup d'œil, sans y passer votre soirée.
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

      <FaqBlock items={FAQ} eyebrow="Reconditionné · FAQ" title="Le reconditionné, en toute confiance." />
      <ClosingCta title={<>Payez le <span className="it">juste</span> prix. Pas le prix neuf.</>} sub="FILON compare neuf et reconditionné à chaque achat, gratuitement." />
    </>
  );
}
