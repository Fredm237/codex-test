import localFont from "next/font/local";

// Fraunces — conservée pour les rares usages éditoriaux en italique.
// Elle n'habille plus les titres : la refonte tient sur une seule grotesque.
export const fraunces = localFont({
  src: [
    { path: "./fonts/Fraunces-opsz-normal.woff2", style: "normal" },
    { path: "./fonts/Fraunces-opsz-italic.woff2", style: "italic" },
  ],
  variable: "--font-serif",
  display: "swap",
  weight: "100 900",
});

// Les fontes sont embarquées avec l'application : next/font/google téléchargeait
// Outfit et Inter pendant chaque build Vercel. Une indisponibilité temporaire de
// Google Fonts faisait alors échouer une prévisualisation pourtant saine.
export const outfit = localFont({
  src: [{ path: "./fonts/Outfit-200-500-latin.woff2", weight: "200 500", style: "normal" }],
  variable: "--font-display",
  display: "swap",
  // Une seule variable WOFF2 remplace les quatre graisses TTF historiques.
  // Elle reste chargée à la demande : Fraunces porte le premier titre public.
  preload: false,
});

export const inter = localFont({
  src: [{ path: "./fonts/Inter-400-700-latin.woff2", weight: "400 700", style: "normal" }],
  variable: "--font-sans",
  display: "swap",
  // Le navigateur charge le fichier variable uniquement lorsqu'une route
  // rencontre du corps de texte, sans huit requêtes globales anticipées.
  preload: false,
});
