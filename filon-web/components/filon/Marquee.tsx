"use client";

// Bandeau de marchands défilant en continu — inspiré de Phia.com.
//
// L'effet "infini" est obtenu en dupliquant la liste : quand la première copie
// sort à gauche, la seconde prend le relais, et le cycle recommence sans saut.
// Le défilement se met en pause au survol pour que l'utilisateur puisse lire.

export function Marquee({ merchants }: { merchants: string[] }) {
  if (!merchants || merchants.length === 0) return null;

  // On double la liste pour l'effet infini
  const items = [...merchants, ...merchants];

  return (
    <div className="fx-marquee" aria-label="Marchands partenaires">
      <div className="fx-marquee-track">
        {items.map((name, i) => (
          <span key={`${name}-${i}`} className="fx-marquee-item">
            {name}
          </span>
        ))}
      </div>
    </div>
  );
}
