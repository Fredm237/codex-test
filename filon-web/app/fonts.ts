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
  src: [
    { path: "./fonts/Outfit-200.ttf", weight: "200", style: "normal" },
    { path: "./fonts/Outfit-300.ttf", weight: "300", style: "normal" },
    { path: "./fonts/Outfit-400.ttf", weight: "400", style: "normal" },
    { path: "./fonts/Outfit-500.ttf", weight: "500", style: "normal" },
  ],
  variable: "--font-display",
  display: "swap",
});

export const inter = localFont({
  src: [
    { path: "./fonts/Inter-400.ttf", weight: "400", style: "normal" },
    { path: "./fonts/Inter-500.ttf", weight: "500", style: "normal" },
    { path: "./fonts/Inter-600.ttf", weight: "600", style: "normal" },
    { path: "./fonts/Inter-700.ttf", weight: "700", style: "normal" },
  ],
  variable: "--font-sans",
  display: "swap",
});
