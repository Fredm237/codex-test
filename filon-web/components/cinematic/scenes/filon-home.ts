import type { CinematicScene, Locale, Shot } from "../types";

const copy = (fr: string, nl: string, en: string, eyebrow?: [string, string, string]) => ({
  fr: { title: fr, eyebrow: eyebrow?.[0] },
  nl: { title: nl, eyebrow: eyebrow?.[1] },
  en: { title: en, eyebrow: eyebrow?.[2] },
}) satisfies Record<Locale, { title: string; eyebrow?: string }>;

const shots: Shot[] = [
  {
    id: "arrival",
    range: [0, 0.08], focus: "arrival", transition: "camera-pass", easing: "hold",
    camera: { from: { position: [0, 1.6, 8], target: [0, 1.2, 0], focalLength: 52 }, to: { position: [0.2, 1.45, 6.2], target: [0.2, 1.1, 0], focalLength: 54 } },
    copy: copy("Est-ce vraiment\nle bon prix ?", "Is dit echt\nde juiste prijs?", "Is this really\nthe right price?", ["FILON", "FILON", "FILON"]),
    overlayRange: [0.01, 0.07], visualRange: [0, 0.08],
  },
  {
    id: "threshold",
    range: [0.08, 0.17], focus: "world", transition: "deep-zoom", easing: "cinematic",
    camera: { from: { position: [0.2, 1.45, 6.2], target: [0.2, 1.1, 0], focalLength: 54 }, to: { position: [-1.9, 1.3, 4.4], target: [0, 1.0, 0], focalLength: 42 } },
    copy: copy("Derrière l’écran,\nun monde d’offres.", "Achter het scherm,\neen wereld van aanbiedingen.", "Behind the screen,\na world of offers."),
    overlayRange: [0.10, 0.16], visualRange: [0.08, 0.17],
  },
  {
    id: "streets",
    range: [0.17, 0.34], focus: "explore", transition: "spatial-travel", easing: "reveal",
    camera: { from: { position: [-1.9, 1.3, 4.4], target: [0, 1.0, 0], focalLength: 42 }, to: { position: [2.4, 1.55, 3.8], target: [0.1, 1.1, 0], focalLength: 38 } },
    copy: copy("Chaque vitrine\nmontre une possibilité.", "Elke vitrine\ntoont een mogelijkheid.", "Every window\nshows a possibility."),
    overlayRange: [0.22, 0.30], visualRange: [0.17, 0.34],
  },
  {
    id: "crossroads",
    range: [0.34, 0.48], focus: "compare", transition: "orbit-reveal", easing: "settle",
    camera: { from: { position: [2.4, 1.55, 3.8], target: [0.1, 1.1, 0], focalLength: 38 }, to: { position: [1.15, 1.25, 2.7], target: [0, 0.95, 0], focalLength: 48 } },
    copy: copy("Le même objet.\nDes chemins différents.", "Hetzelfde object.\nVerschillende paden.", "The same object.\nDifferent paths."),
    overlayRange: [0.37, 0.45], visualRange: [0.34, 0.48],
  },
  {
    id: "square",
    range: [0.48, 0.60], focus: "opportunity", transition: "camera-pass", easing: "cinematic",
    camera: { from: { position: [1.15, 1.25, 2.7], target: [0, 0.95, 0], focalLength: 48 }, to: { position: [-0.55, 1.12, 2.2], target: [0.15, 0.92, 0], focalLength: 58 } },
    copy: copy("Comparer ce qui est\nvraiment comparable.", "Vergelijk wat echt\nvergelijkbaar is.", "Compare what is\ngenuinely comparable."),
    overlayRange: [0.51, 0.58], visualRange: [0.48, 0.60],
  },
  {
    id: "rooftop",
    range: [0.60, 0.74], focus: "intelligence", transition: "object-bridge", easing: "hold",
    camera: { from: { position: [-0.55, 1.12, 2.2], target: [0.15, 0.92, 0], focalLength: 58 }, to: { position: [-0.3, 1.25, 2.85], target: [0, 1.0, 0], focalLength: 50 } },
    copy: copy("Prendre de la hauteur.\nGarder les détails.", "Neem afstand.\nBehoud de details.", "Take a step back.\nKeep the details."),
    overlayRange: [0.64, 0.72], visualRange: [0.60, 0.74],
  },
  {
    id: "return",
    range: [0.74, 0.90], focus: "score", transition: "spatial-travel", easing: "reveal",
    camera: { from: { position: [-0.3, 1.25, 2.85], target: [0, 1.0, 0], focalLength: 50 }, to: { position: [0.75, 1.35, 3.6], target: [0, 0.95, 0], focalLength: 52 } },
    copy: copy("La décision revient\nà l’essentiel.", "De beslissing keert terug\nnaar de essentie.", "The decision returns\nto what matters."),
    overlayRange: [0.78, 0.86], visualRange: [0.74, 0.90],
  },
  {
    id: "release",
    range: [0.90, 1], focus: "release", transition: "camera-pass", easing: "settle",
    camera: { from: { position: [0.75, 1.35, 3.6], target: [0, 0.95, 0], focalLength: 52 }, to: { position: [0, 1.6, 7.3], target: [0, 1.0, 0], focalLength: 46 } },
    copy: {
      fr: { title: "Prêt à trouver\nvotre bon prix ?", cta: { label: "Explorer les offres", href: "/recherche" } },
      nl: { title: "Klaar om jouw\njuiste prijs te vinden?", cta: { label: "Aanbiedingen ontdekken", href: "/recherche" } },
      en: { title: "Ready to find\nyour right price?", cta: { label: "Explore offers", href: "/recherche" } },
    },
    overlayRange: [0.93, 1], visualRange: [0.90, 1],
  },
];

export const filonHomeScene: CinematicScene = {
  id: "filon-interior-city",
  desktop: {
    frameBase: "/cinematic/interior-city/desktop",
    frames: 1200,
    poster: "/cinematic/interior-city/poster.png",
    scrollHeightVh: 460,
    frameStride: 1,
  },
  mobile: {
    frameBase: "/cinematic/interior-city/desktop",
    frames: 1200,
    poster: "/cinematic/interior-city/poster.png",
    scrollHeightVh: 460,
    frameStride: 1,
  },
  shots,
  reducedMotion: { posterDesktop: "/cinematic/interior-city/poster.png", posterMobile: "/cinematic/interior-city/poster.png" },
};
