import localFont from "next/font/local";
import { Playfair_Display, Inter } from "next/font/google";

// Fraunces — fallback serif self-hosted
export const fraunces = localFont({
  src: [
    { path: "./fonts/Fraunces-opsz-normal.woff2", style: "normal" },
    { path: "./fonts/Fraunces-opsz-italic.woff2", style: "italic" },
  ],
  variable: "--font-serif",
  display: "swap",
  weight: "100 900",
});

// Playfair Display — serif display pour les titres (comme GT Super Display chez Phia)
export const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
});

// Inter — sans-serif pour le corps de texte
export const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});
