export const site = {
  name: "FILON",
  tagline: "Le réflexe malin avant chaque achat.",
  description:
    "FILON compare automatiquement le meilleur cashback, le meilleur prix en reconditionné et les codes promo qui marchent vraiment — avant chaque achat, en toute transparence.",
  // Update to the production domain before deploy.
  url: "https://filon.app",
  locale: "fr_BE",
  twitter: "@filon",
  founder: "Freddy Mvogo Eloundou",
  city: "Bruxelles",
} as const;

export type NavItem = { label: string; href: string };

export const primaryNav: NavItem[] = [
  { label: "Comment ça marche", href: "/comment-ca-marche" },
  { label: "Cashback", href: "/cashback" },
  { label: "Reconditionné", href: "/reconditionne" },
  { label: "Codes promo", href: "/codes-promo" },
  { label: "Blog", href: "/blog" },
];

export const footerNav: { title: string; items: NavItem[] }[] = [
  {
    title: "Produit",
    items: [
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
];
