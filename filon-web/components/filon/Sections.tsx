"use client";

// Sections de la home, refonte 2026.
//
// Elles remplacent les scènes WebGL défilantes de l'ancienne home. Mesure à
// l'appui : celle-ci faisait 11 202 px de haut sur un écran de 390 px, dont
// plusieurs milliers de pixels de dégradés sombres sans contenu. Un visiteur
// mobile devait traverser ça pour atteindre la moindre information — et un
// partenaire n'allait jamais jusqu'au bout.
//
// Rien ici n'affirme de chiffre : les preuves chiffrées vivent dans
// Proof, qui les lit dans le catalogue.

import { motion } from "framer-motion";
import type { Proof } from "@/lib/proof";

const STEPS: Array<{ n: string; title: string; body: string }> = [
  {
    n: "01",
    title: "On réunit les offres",
    body: "Le même produit est vendu par plusieurs marchands, sous des libellés différents. FILON les regroupe par code-barres pour qu'une comparaison porte bien sur un seul et même article.",
  },
  {
    n: "02",
    title: "On garde l'historique",
    body: "Chaque prix est relevé et conservé. C'est la seule façon de savoir si une promotion en est une, ou si le prix barré n'a jamais existé.",
  },
  {
    n: "03",
    title: "On tranche",
    body: "Le Verdict compare le prix du jour à ce que nous avons réellement observé, et le dit franchement : bon moment, moment ordinaire, ou attendez. Sans historique suffisant, il le dit aussi.",
  },
];

export function Method() {
  return (
    <section className="fx-section" id="methode">
      <div className="fx-container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <span className="fx-eyebrow brand">La méthode</span>
          <h2 className="fx-h2 fx-section-title">
            Un avis vaut ce que vaut
            <br />
            <span className="it">ce qu&apos;on a mesuré.</span>
          </h2>
        </motion.div>

        <motion.ol 
          className="fx-steps"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          variants={{
            hidden: { opacity: 0 },
            show: { opacity: 1, transition: { staggerChildren: 0.12 } }
          }}
        >
          {STEPS.map((s) => (
            <motion.li 
              className="fx-card padded fx-step" 
              key={s.n}
              variants={{
                hidden: { opacity: 0, y: 24 },
                show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 260, damping: 20 } }
              }}
            >
              <span className="fx-step-n">{s.n}</span>
              <h3 className="fx-h3">{s.title}</h3>
              <p className="fx-body">{s.body}</p>
            </motion.li>
          ))}
        </motion.ol>
      </div>
    </section>
  );
}

export function Closing({ proof }: { proof: Proof | null }) {
  const stats = proof?.stats ?? null;
  return (
    <section className="fx-section ink fx-closing">
      <motion.div 
        className="fx-container narrow"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="fx-eyebrow">Avant de payer</span>
        <h2 className="fx-h2 fx-closing-title">
          Posez la question à FILON.
          <br />
          <span className="it">C&apos;est gratuit, et c&apos;est rapide.</span>
        </h2>
        <p className="fx-lede fx-closing-lede">
          {stats
            ? `${stats.offers.toLocaleString("fr-BE")} offres suivies chez ${stats.merchants.toLocaleString("fr-BE")} marchands partenaires.`
            : "Les offres de nos marchands partenaires, réunies et suivies dans le temps."}
        </p>
        <motion.p 
          className="fx-closing-actions"
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <a className="fx-btn on-ink" href="/recherche/">
            Essayer le copilote
          </a>
          <a className="fx-btn secondary fx-btn-on-ink-ghost" href="/catalogue/">
            Explorer le catalogue
          </a>
        </motion.p>
      </motion.div>
    </section>
  );
}
