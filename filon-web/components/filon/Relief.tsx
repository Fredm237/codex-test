"use client";

// Relief — le paysage des prix.
//
// Chaque offre est une colonne dont la hauteur est son prix et les strates
// ses paliers successifs. Le premier plan est occupé par ce qui vient de
// décrocher — la seule information qui réponde à « est-ce le bon moment ? ».
//
// Rendu en CSS Grid + divs : pas de WebGL pour une visualisation passive.
// La direction dit : « WebGL temps réel n'est autorisé que pour l'interaction. »
// Ici le visiteur regarde, il ne manipule pas.

import { useEffect, useState } from "react";

type Column = {
  id: number;
  name: string;
  brand: string;
  merchant: string;
  price: number;
  high: number;
  low: number;
  drop_pct: number;
  steps: [number, number][];
  confidence: string;
  image?: string;
};

type ReliefData = {
  live: boolean;
  count: number;
  columns: Column[];
};

export function Relief() {
  const [data, setData] = useState<ReliefData | null>(null);

  useEffect(() => {
    fetch("/api/catalog/relief?limit=60")
      .then((r) => (r.ok ? r.json() : null))
      .then(setData)
      .catch(() => null);
  }, []);

  if (!data || !data.live || data.columns.length === 0) return null;

  const maxPrice = Math.max(...data.columns.map((c) => c.high));

  return (
    <section className="fx-relief" aria-label="Paysage des prix">
      <div className="fx-container">
        <h2 className="fx-relief-title">
          Le relief des prix<em>.</em>
        </h2>
        <p className="fx-relief-lede">
          {data.count} offres en mouvement. La hauteur est le prix, la couleur
          est la baisse.
        </p>
      </div>
      <div className="fx-relief-landscape">
        {data.columns.map((col) => {
          const heightPct = maxPrice > 0 ? (col.high / maxPrice) * 100 : 0;
          const dropAbs = Math.abs(col.drop_pct);
          // Plus la baisse est forte, plus la colonne est ambre
          const intensity = Math.min(dropAbs / 50, 1);

          return (
            <a
              key={col.id}
              className="fx-relief-col"
              href={`/produit/${col.id}/`}
              title={`${col.name} — ${col.drop_pct}%`}
              style={{
                "--h": `${heightPct}%`,
                "--intensity": intensity,
              } as React.CSSProperties}
              data-confidence={col.confidence}
            >
              <span className="fx-relief-bar" />
              <span className="fx-relief-drop">{col.drop_pct}%</span>
            </a>
          );
        })}
      </div>
    </section>
  );
}
