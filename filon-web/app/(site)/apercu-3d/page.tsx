// Aperçu de la scène 3D — page de validation visuelle, pas de production.
"use client";

import { Filon3D } from "@/components/filon/Filon3D";

const CHAPITRES = [
  ["Le prix affiché", "n’est pas le prix payé."],
  ["799 435 offres", "chez 154 marchands partenaires."],
  ["Le bloc s’ouvre", "sur ce qu’il cachait."],
  ["Le filon", "c’est l’écart que personne ne montre."],
];

export default function Apercu3D() {
  return (
    <>
      <Filon3D />
      {CHAPITRES.map(([titre, suite]) => (
        <section key={titre} className="fx-chapter sur-scene">
          <div className="fx-container">
            <h2 className="fx-chapter-title">
              {titre} <em>{suite}</em>
            </h2>
          </div>
        </section>
      ))}
    </>
  );
}
