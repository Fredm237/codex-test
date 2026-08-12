"use client";

// Page d'erreur du site.
//
// Elle existe pour une raison précise, et c'est du référencement. Quand le
// catalogue ne répond pas, les pages produit et rayon LÈVENT désormais au lieu
// de rendre `notFound()` : le serveur répond donc 500 et non 404.
//
// La différence n'est pas cosmétique. Un 404 dit à un moteur « cette page
// n'existe pas, retire-la de l'index ». Un 5xx dit « indisponible pour le
// moment, repasse plus tard ». Auparavant une base muette suffisait à faire
// désindexer tout le catalogue ; la Search Console a fini par le signaler.
//
// Ce que voit le visiteur doit donc dire la même chose que le code HTTP :
// c'est passager, revenez, et voici ce qui marche encore en attendant.

import { useEffect } from "react";
import Link from "next/link";

export default function Erreur({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Le digest est la seule clé qui relie cet écran à la trace serveur.
    console.error("Erreur de rendu", error.digest ?? "", error.message);
  }, [error]);

  const catalogue = error.name === "CatalogueIndisponible";

  return (
    <section className="fx-section page-top">
      <div className="fx-container narrow">
        <p className="fx-eyebrow brand">
          {catalogue ? "Catalogue momentanément injoignable" : "Erreur"}
        </p>
        <h1 className="fx-display" style={{ marginTop: "var(--fx-space-4)" }}>
          {catalogue ? (
            <>
              Le catalogue ne répond pas <em>pour l&apos;instant.</em>
            </>
          ) : (
            <>
              Quelque chose <em>a échoué.</em>
            </>
          )}
        </h1>
        <p className="fx-lede" style={{ marginTop: "var(--fx-space-5)" }}>
          {catalogue
            ? "Les prix ne sont pas consultables tant que la connexion n'est pas rétablie. Rien n'est perdu : la page reviendra telle quelle."
            : "L'incident a été enregistré. Vous pouvez réessayer, ou revenir à l'accueil."}
        </p>

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "var(--fx-space-3)",
            marginTop: "var(--fx-space-7)",
          }}
        >
          <button type="button" className="fx-btn primary" onClick={reset}>
            Réessayer
          </button>
          <Link href="/" className="fx-btn secondary">
            Retour à l&apos;accueil
          </Link>
          {/* Ces pages ne dépendent pas du catalogue : elles restent utiles
              pendant un incident. */}
          <Link href="/comment-ca-marche" className="fx-btn quiet">
            Comment ça marche
          </Link>
        </div>

        {error.digest ? (
          <p className="fx-fine" style={{ marginTop: "var(--fx-space-7)" }}>
            Référence de l&apos;incident : <span className="mono">{error.digest}</span>
          </p>
        ) : null}
      </div>
    </section>
  );
}
