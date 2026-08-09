import localFont from "next/font/local";
import { Outfit, Inter } from "next/font/google";

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

// Outfit — grotesque géométrique pour les titres.
// C'est la lettre du mot-signe « wearebrand. » : bas de casse, tracé
// régulier, aucune fioriture. Tenue en graisses légères, l'échelle fait
// tout le travail — comme dans les plans du compte, où c'est le cadrage
// qui impose, pas l'ornement.
export const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  weight: ["200", "300", "400", "500"],
});

// Inter — sans-serif pour le corps de texte.
export const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});
