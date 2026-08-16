import type { CinematicScene, Locale, Shot } from "../types";

const copy = (fr: string, nl: string, en: string, eyebrow?: [string, string, string]) => ({
  fr: { title: fr, eyebrow: eyebrow?.[0] },
  nl: { title: nl, eyebrow: eyebrow?.[1] },
  en: { title: en, eyebrow: eyebrow?.[2] },
}) satisfies Record<Locale, { title: string; eyebrow?: string }>;

const shots: Shot[] = [
  {
    id: "arrival",
    range: [0, 0.09], focus: "arrival", transition: "camera-pass", easing: "hold",
    camera: { from: { position: [0, 1.6, 8], target: [0, 1.2, 0], focalLength: 52 }, to: { position: [0.2, 1.45, 6.2], target: [0.2, 1.1, 0], focalLength: 54 } },
    copy: copy("Est-ce vraiment\nle bon prix ?", "Is dit echt\nde juiste prijs?", "Is this really\nthe right price?", ["FILON", "FILON", "FILON"]),
    overlayRange: [0.01, 0.08], visualRange: [0, 0.08],
  },
  {
    id: "world",
    range: [0.09, 0.20], focus: "world", transition: "deep-zoom", easing: "cinematic",
    camera: { from: { position: [0.2, 1.45, 6.2], target: [0.2, 1.1, 0], focalLength: 54 }, to: { position: [-1.9, 1.3, 4.4], target: [0, 1.0, 0], focalLength: 42 } },
    copy: copy("Bien plus qu’un\nprix affiché.", "Veel meer dan\neen getoonde prijs.", "More than a\ndisplayed price."),
    overlayRange: [0.11, 0.18], visualRange: [0.08, 0.20],
  },
  {
    id: "explore",
    range: [0.20, 0.34], focus: "explore", transition: "spatial-travel", easing: "reveal",
    camera: { from: { position: [-1.9, 1.3, 4.4], target: [0, 1.0, 0], focalLength: 42 }, to: { position: [2.4, 1.55, 3.8], target: [0.1, 1.1, 0], focalLength: 38 } },
    copy: copy("Un monde d’offres.\nUne seule décision.", "Een wereld van aanbiedingen.\nEén beslissing.", "A world of offers.\nOne decision."),
    overlayRange: [0.23, 0.32], visualRange: [0.20, 0.34],
  },
  {
    id: "converge",
    range: [0.34, 0.47], focus: "compare", transition: "orbit-reveal", easing: "settle",
    camera: { from: { position: [2.4, 1.55, 3.8], target: [0.1, 1.1, 0], focalLength: 38 }, to: { position: [1.15, 1.25, 2.7], target: [0, 0.95, 0], focalLength: 48 } },
    copy: copy("Comparer ce qui est\nvraiment comparable.", "Vergelijk wat echt\nvergelijkbaar is.", "Compare what is\ngenuinely comparable."),
    overlayRange: [0.37, 0.45], visualRange: [0.34, 0.47],
  },
  {
    id: "opportunity",
    range: [0.47, 0.60], focus: "opportunity", transition: "camera-pass", easing: "cinematic",
    camera: { from: { position: [1.15, 1.25, 2.7], target: [0, 0.95, 0], focalLength: 48 }, to: { position: [-0.55, 1.12, 2.2], target: [0.15, 0.92, 0], focalLength: 58 } },
    copy: copy("Une offre mérite\nvotre attention.", "Eén aanbod verdient\nje aandacht.", "One offer deserves\nyour attention."),
    overlayRange: [0.50, 0.58], visualRange: [0.47, 0.60],
  },
  {
    id: "intelligence",
    range: [0.60, 0.72], focus: "intelligence", transition: "object-bridge", easing: "hold",
    camera: { from: { position: [-0.55, 1.12, 2.2], target: [0.15, 0.92, 0], focalLength: 58 }, to: { position: [-0.3, 1.25, 2.85], target: [0, 1.0, 0], focalLength: 50 } },
    copy: copy("Ce que nous savons.\nCe que nous ignorons.", "Wat we weten.\nWat we niet weten.", "What we know.\nWhat we do not know."),
    overlayRange: [0.63, 0.70], visualRange: [0.60, 0.72],
  },
  {
    id: "score",
    range: [0.72, 0.84], focus: "score", transition: "orbit-reveal", easing: "settle",
    camera: { from: { position: [-0.3, 1.25, 2.85], target: [0, 1.0, 0], focalLength: 50 }, to: { position: [0, 1.05, 2.0], target: [0, 0.88, 0], focalLength: 65 } },
    copy: copy("Le Score FILON\nmet les preuves en contexte.", "De FILON-score\nplaatst bewijs in context.", "The FILON Score\nputs evidence in context."),
    overlayRange: [0.75, 0.82], visualRange: [0.72, 0.84],
  },
  {
    id: "decision",
    range: [0.84, 0.94], focus: "decision", transition: "spatial-travel", easing: "reveal",
    camera: { from: { position: [0, 1.05, 2.0], target: [0, 0.88, 0], focalLength: 65 }, to: { position: [0.75, 1.35, 3.6], target: [0, 0.95, 0], focalLength: 52 } },
    copy: copy("Décidez avec\nle contexte.", "Beslis met\nde juiste context.", "Decide with\ncontext."),
    overlayRange: [0.87, 0.92], visualRange: [0.84, 0.94],
  },
  {
    id: "release",
    range: [0.94, 1], focus: "release", transition: "camera-pass", easing: "settle",
    camera: { from: { position: [0.75, 1.35, 3.6], target: [0, 0.95, 0], focalLength: 52 }, to: { position: [0, 1.6, 7.3], target: [0, 1.0, 0], focalLength: 46 } },
    copy: {
      fr: { title: "Prêt à trouver\nvotre bon prix ?", cta: { label: "Explorer les offres", href: "/recherche" } },
      nl: { title: "Klaar om jouw\njuiste prijs te vinden?", cta: { label: "Aanbiedingen ontdekken", href: "/recherche" } },
      en: { title: "Ready to find\nyour right price?", cta: { label: "Explore offers", href: "/recherche" } },
    },
    overlayRange: [0.95, 1], visualRange: [0.94, 1],
  },
];

export const filonHomeScene: CinematicScene = {
  id: "filon-home-world",
  desktop: { frameBase: "/cinematic/filon-world/desktop", frames: 1, poster: "/cinematic/filon-world/desktop/001.jpg", scrollHeightVh: 2800, frameStride: 1 },
  mobile: { frameBase: "/cinematic/filon-world/mobile", frames: 1, poster: "/cinematic/filon-world/mobile/001.jpg", scrollHeightVh: 1850, frameStride: 1 },
  shots,
  reducedMotion: { posterDesktop: "/cinematic/filon-world/desktop/001.jpg", posterMobile: "/cinematic/filon-world/mobile/001.jpg" },
};
