export const site = {
  name: "FILON",
  tagline: "Le réflexe malin avant chaque achat.",
  description:
    "Avant chaque achat, FILON compare le meilleur cashback, le meilleur prix en reconditionné et les codes promo qui marchent vraiment. En toute transparence.",
  url: "https://filon.be",
  domain: "filon.be",
  locale: "fr_BE",
  twitter: "@filon",
  founder: "Freddy Mvogo Eloundou",
  city: "Bruxelles",
  // Legal / registered editor entity (shown on legal pages, distinct from the
  // marketing founder above). Belgian sole proprietorship.
  legalName: "Ricardo Aimon",
  legalForm: "Entreprise individuelle (personne physique)",
  bce: "BE 0797.756.902",
  vat: "BE 0797.756.902",
  // TODO confirm: registered seat address of Ricardo Aimon (from the KBO/BCE
  // extract). Update here in one place if different.
  legalAddress: "Chaussée de Stockel 406, 1150 Woluwe-Saint-Pierre, Belgique",
  // Formspree endpoint for contact + newsletter (create at formspree.io, then
  // paste the form URL here or set NEXT_PUBLIC_FORM_ENDPOINT). Empty = demo mode.
  formEndpoint: process.env.NEXT_PUBLIC_FORM_ENDPOINT || "",
  // Plausible analytics (privacy-first, cookieless). Empty disables the script.
  plausibleDomain: process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN || "filon.be",
} as const;

export type NavItem = { label: string; href: string };

export const primaryNav: NavItem[] = [
  { label: "Assistant IA", href: "/recherche" },
  { label: "Comment ça marche", href: "/comment-ca-marche" },
  { label: "Tarifs", href: "/tarifs" },
  { label: "Cashback", href: "/cashback" },
  { label: "Reconditionné", href: "/reconditionne" },
  { label: "Codes promo", href: "/codes-promo" },
];

export const footerNav: { title: string; items: NavItem[] }[] = [
  {
    title: "Produit",
    items: [
      { label: "Assistant IA", href: "/recherche" },
      { label: "Comment ça marche", href: "/comment-ca-marche" },
      { label: "Cashback", href: "/cashback" },
      { label: "Reconditionné", href: "/reconditionne" },
      { label: "Codes promo", href: "/codes-promo" },
    ],
  },
  {
    title: "Entreprise",
    items: [
      { label: "À propos", href: "/a-propos" },
      { label: "Blog", href: "/blog" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    title: "Légal",
    items: [
      { label: "Mentions légales", href: "/mentions-legales" },
      { label: "Confidentialité", href: "/confidentialite" },
    ],
  },
];
