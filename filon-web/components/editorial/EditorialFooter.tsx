"use client";

import { site } from "@/lib/site";
import { Newsletter } from "./Forms";
import { BrandLogo } from "./Brand";
import { useLocale } from "@/lib/i18n";

// Libellés NL par href (FR reste la valeur d'origine des tableaux LINKS/LEGAL).
const NL_LABELS: Record<string, string> = {
  "/recherche": "Assistent",
  "/catalogue": "Catalogus",
  "/marchands": "Winkels",
  "/tarifs": "Tarieven",
  "/extension": "Extensie",
  "/intelligence": "Intelligentie",
  "/comment-ca-marche": "Hoe het werkt",
  "/cashback": "Cashback",
  "/reconditionne": "Refurbished",
  "/codes-promo": "Kortingscodes",
  "/blog": "Blog",
  "/faq": "FAQ",
  "/aide": "Hulp",
  "/partenaires": "Partners",
  "/presse": "Pers",
  "/carrieres": "Jobs",
  "/a-propos": "Over ons",
  "/contact": "Contact",
  "/transparence": "Transparantie & affiliatie",
  "/mentions-legales": "Wettelijke vermeldingen",
  "/confidentialite": "Privacy",
  "/cookies": "Cookiebeleid",
  "/cgu": "Gebruiksvoorwaarden",
  "/securite": "Veiligheid",
};

// Libellés EN par href.
const EN_LABELS: Record<string, string> = {
  "/recherche": "AI assistant",
  "/catalogue": "Catalogue",
  "/marchands": "Merchants",
  "/tarifs": "Pricing",
  "/extension": "Extension",
  "/intelligence": "Intelligence",
  "/comment-ca-marche": "The method",
  "/cashback": "Cashback",
  "/reconditionne": "Refurbished",
  "/codes-promo": "Promo codes",
  "/blog": "Blog",
  "/faq": "FAQ",
  "/aide": "Help",
  "/partenaires": "Partners",
  "/presse": "Press",
  "/carrieres": "Careers",
  "/a-propos": "About",
  "/contact": "Contact",
  "/transparence": "Transparency & affiliation",
  "/mentions-legales": "Legal notice",
  "/confidentialite": "Privacy",
  "/cookies": "Cookie policy",
  "/cgu": "Terms of use",
  "/securite": "Security",
};

const FOOT = {
  fr: {
    coordinate: "FILON / CONTINUER",
    newsH: <>Le brief <span className="it">FILON</span>.</>,
    newsP: "Les observations et conseils publiés par FILON, lorsqu'un nouvel envoi est disponible.",
    designed: "Conçu à",
    disc1: "L'accès public actuel est gratuit. Consultez les pages Tarifs et Confidentialité pour le périmètre à jour.",
    disc2: "Certains liens sont affiliés : acheter via FILON peut générer une commission. Le taux de commission n'entre pas dans le score actuel ; confirmez le total chez le marchand",
    more: "en savoir plus",
  },
  nl: {
    coordinate: "FILON / VERDER",
    newsH: <>De <span className="it">FILON</span>-brief.</>,
    newsP: "Waarnemingen en advies van FILON wanneer een nieuwe verzending beschikbaar is.",
    designed: "Ontworpen in",
    disc1: "De huidige publieke toegang is gratis. Raadpleeg Tarieven en Privacy voor de actuele reikwijdte.",
    disc2: "Sommige links zijn affiliatielinks : kopen via FILON kan een commissie opleveren. Het commissietarief telt niet mee in de huidige score; bevestig het totaal bij de winkel",
    more: "meer weten",
  },
  en: {
    coordinate: "FILON / CONTINUE",
    newsH: <><span className="it">FILON</span> brief.</>,
    newsP: "Observations and guidance published by FILON when a new mailing is available.",
    designed: "Designed in",
    disc1: "Current public access is free. See Pricing and Privacy for the current scope.",
    disc2: "Some links are affiliate links: buying through FILON may generate a commission. The commission rate is not part of the current score; confirm the total with the merchant",
    more: "learn more",
  },
};

const LINKS = [
  { label: "Assistant IA", href: "/recherche" },
  { label: "Catalogue", href: "/catalogue" },
  { label: "Marchands", href: "/marchands" },
  { label: "Tarifs", href: "/tarifs" },
  { label: "Extension", href: "/extension" },
  { label: "Intelligence", href: "/intelligence" },
  { label: "La méthode", href: "/comment-ca-marche" },
  { label: "Blog", href: "/blog" },
  { label: "FAQ", href: "/faq" },
  { label: "Aide", href: "/aide" },
  { label: "Partenaires", href: "/partenaires" },
  { label: "Presse", href: "/presse" },
  { label: "Carrières", href: "/carrieres" },
  { label: "À propos", href: "/a-propos" },
  { label: "Contact", href: "/contact" },
];

const LEGAL = [
  { label: "Transparence & affiliation", href: "/transparence" },
  { label: "Mentions légales", href: "/mentions-legales" },
  { label: "Confidentialité", href: "/confidentialite" },
  { label: "Politique cookies", href: "/cookies" },
  { label: "CGU", href: "/cgu" },
  { label: "Sécurité", href: "/securite" },
];

export function EditorialFooter() {
  const { locale } = useLocale();
  const x = FOOT[locale];
  const lbl = (href: string, fr: string) =>
    locale === "nl" ? NL_LABELS[href] ?? fr : locale === "en" ? EN_LABELS[href] ?? fr : fr;
  return (
    <footer className="ed-footer p19-global-footer" data-experience-exit="continuation">
      <div className="ed-wrap">
        <span className="p19-footer-coordinate" aria-hidden="true">{x.coordinate}</span>
        <div className="ed-newsblock">
          <div>
            <h3 style={{ fontFamily: "var(--serif)", fontVariationSettings: '"opsz" 40', fontSize: 24, letterSpacing: "-0.01em", color: "var(--fx-text)" }}>
              {x.newsH}
            </h3>
            <p style={{ color: "var(--fx-text-secondary)", fontSize: 14.5, marginTop: 6 }}>
              {x.newsP}
            </p>
          </div>
          <Newsletter />
        </div>
        <div className="ed-foot">
          <BrandLogo as="span" markSize={26} />
          <div className="ed-foot-links">
            {LINKS.map((l) => (
              <a key={l.href} href={l.href}>{lbl(l.href, l.label)}</a>
            ))}
          </div>
          <span className="cr">© {new Date().getFullYear()} · {x.designed} {site.city}</span>
        </div>
        <div className="ed-foot-links" style={{ marginTop: 18 }}>
          {LEGAL.map((l) => (
            <a key={l.href} href={l.href} style={{ fontSize: 12.5, color: "var(--ink-3)" }}>
              {lbl(l.href, l.label)}
            </a>
          ))}
        </div>
        <p className="ed-disc">
          {x.disc1}{" "}
          {x.disc2} (<a href="/transparence" style={{ color: "inherit", textDecoration: "underline" }}>{x.more}</a>).
        </p>
      </div>
    </footer>
  );
}
