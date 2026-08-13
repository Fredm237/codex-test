"use client";

// ImmersiveExperience v3 — Vrais screenshots FILON, pas de vidéo IA.
//
// Approche : au lieu de vidéos générées par IA (qui inventent des interfaces
// comme "Velora" ou "PriceLens"), on utilise les VRAIS screenshots du site
// FILON, animés au scroll avec des transitions CSS.
//
// Chaque section montre un vrai screenshot dans un mockup laptop, avec un
// texte qui apparaît. Le scroll fait défiler les sections.

import { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { HeroSearch } from "./HeroSearch";

type Section = {
  image: string;
  titre: string;
  sousTitre?: string;
  cta?: { label: string; href: string };
};

const SECTIONS: Section[] = [
  {
    image: "/img/real_catalogue_full.webp",
    titre: "Est-ce vraiment le bon prix ?",
    sousTitre: "FILON compare les prix chez tous les marchands pour vous.",
  },
  {
    image: "/img/real_catalogue_full.webp",
    titre: "1,3 million d'offres.\n207 marchands.",
  },
  {
    image: "/img/real_assistant.webp",
    titre: "Le prix que personne d'autre ne vous montre.",
  },
  {
    image: "/img/real_assistant.webp",
    titre: "Vous venez d'économiser 47€.",
  },
  {
    image: "/img/real_catalogue_full.webp",
    titre: "FILON.",
    cta: { label: "Essayer le copilote", href: "/recherche" },
  },
];

function LaptopMockup({ image, progress }: { image: string; progress: number }) {
  return (
    <div className="fx-laptop">
      <div className="fx-laptop-screen">
        <img
          src={image}
          alt=""
          className="fx-laptop-screenshot"
          style={{ transform: `scale(${1 + progress * 0.05})` }}
        />
      </div>
      <div className="fx-laptop-base" />
    </div>
  );
}

function ImmersiveSection({ section, index }: { section: Section; index: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });
  const opacity = useTransform(scrollYProgress, [0, 0.3, 0.7, 1], [0, 1, 1, 0]);
  const y = useTransform(scrollYProgress, [0, 0.3, 0.7, 1], [60, 0, 0, -60]);
  const scale = useTransform(scrollYProgress, [0, 0.3, 0.7, 1], [0.95, 1, 1, 0.95]);

  return (
    <section ref={ref} className="fx-imm-section">
      <motion.div className="fx-imm-laptop-wrap" style={{ scale }}>
        <LaptopMockup image={section.image} progress={0} />
      </motion.div>
      <motion.div className="fx-imm-text" style={{ opacity, y }}>
        <h2 className="fx-imm-titre">{section.titre}</h2>
        {section.sousTitre && <p className="fx-imm-sous">{section.sousTitre}</p>}
        {section.cta && (
          <a href={section.cta.href} className="fx-imm-cta">{section.cta.label}</a>
        )}
      </motion.div>
    </section>
  );
}

export function ImmersiveExperience() {
  return (
    <div className="fx-imm-container">
      {/* Barre de recherche fixe en bas */}
      <div className="fx-imm-search-fixed">
        <HeroSearch />
      </div>

      {/* Sections */}
      {SECTIONS.map((section, i) => (
        <ImmersiveSection key={i} section={section} index={i} />
      ))}
    </div>
  );
}
