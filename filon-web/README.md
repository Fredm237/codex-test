# FILON — Site web

> Le réflexe malin avant chaque achat.

Application web du produit FILON : assistant d'achat qui compare cashback,
reconditionné et codes promo. Construite avec **Next.js 15 (App Router)**,
**React 19**, **Tailwind CSS v4** et **TypeScript**.

> **Note sur les versions.** Le brief initial visait « Next.js 16 / React 20 ».
> Ces versions n'étaient pas publiées au moment de l'écriture — ce socle utilise
> le dernier stack stable réel (Next 15 / React 19 / Tailwind 4). Le passage aux
> versions majeures suivantes se fera en bumpant `package.json` puis en suivant
> le guide de migration officiel.

## Démarrer

```bash
cd filon-web
npm install
npm run dev      # http://localhost:3000
```

Autres scripts :

```bash
npm run build      # build de production
npm run start      # sert le build
npm run typecheck  # tsc --noEmit
```

## Architecture

```
filon-web/
├── app/
│   ├── layout.tsx          # <html>, SEO global, JSON-LD Organization + WebSite, Nav, Footer
│   ├── page.tsx            # Accueil (Hero + Stats + Steps + Transparence + CTA)
│   ├── globals.css         # Design tokens (light/dark) + @theme Tailwind v4 + responsive
│   ├── sitemap.ts          # /sitemap.xml
│   ├── robots.ts           # /robots.txt
│   ├── cashback/           # pages secondaires (une route par levier + entreprise)
│   ├── reconditionne/
│   ├── codes-promo/
│   ├── comment-ca-marche/
│   ├── a-propos/
│   ├── contact/
│   └── blog/
├── components/
│   ├── site/               # Nav, Footer, Hero (démo interactive), Sections, PageShell,
│   │                       #   ThemeToggle, ThemeScript, Atmosphere, Logo, ContactForm
│   └── ui/                 # Button, Container
└── lib/
    ├── site.ts             # config marque + navigation
    └── seo.tsx             # buildMetadata() + schémas JSON-LD (Org, WebSite, FAQ, Breadcrumb)
```

## Design system

Les tokens (`app/globals.css`) sont la source de vérité, identiques à la page de
référence du design system. Thème clair/sombre géré au niveau des tokens :
`prefers-color-scheme` par défaut, surchargé par `data-theme` (toggle + persistance
`localStorage`, appliqué avant le premier paint par `ThemeScript`).

## SEO

- Métadonnées par page via `buildMetadata()` (title, description, canonical, Open Graph, Twitter).
- JSON-LD : Organization + WebSite (global), Breadcrumb (pages secondaires). Helpers FAQ/Article prêts dans `lib/seo.tsx`.
- `sitemap.xml` et `robots.txt` générés.
- `metadataBase` et `site.url` à passer sur le domaine de production avant déploiement.

## Déploiement (Vercel)

```bash
# à la racine du repo, pointer le "Root Directory" du projet Vercel sur filon-web/
vercel
```

## Expérience immersive — `/experience`

Route « takeover » plein écran, niveau Awwwards, avec le vrai stack immersif :

- **three + @react-three/fiber** — fond WebGL vivant (shader GLSL maison : bruit
  fbm + rampe de couleurs de marque + veine électrique, réactif à la souris),
  code-splitté sur cette route uniquement (chargé via `next/dynamic`, `ssr:false`).
- **GSAP + ScrollTrigger** — révélation du titre ligne par ligne, reveals au scroll.
- **Lenis** — smooth-scroll (autoRaf), synchronisé avec ScrollTrigger.
- Curseur premium, boutons magnétiques, compteurs animés.
- Fallback `prefers-reduced-motion` complet (désactive shader, curseur, motion) ;
  fallback CSS si WebGL indisponible.

Composants réutilisables dans `components/immersive/` : `ShaderBackground`,
`SmoothScroll`, `Cursor`, `Reveal`, `MagneticButton`, `Counter`, `ScrollProgress`,
`ImmersiveHero`. La chrome marketing (nav/footer/aurora) vit dans le groupe de
routes `app/(site)/` et ne s'applique donc pas à `/experience`.

> three.js n'est chargé que sur `/experience` (First Load ~156 kB) ; le reste du
> site reste à ~103 kB.

## Prochaines étapes

- Porter les sections restantes de la maquette de référence (bento features,
  tableau comparatif complet, calculateur, témoignages, FAQ) en composants.
- Brancher le formulaire de contact et la newsletter à un backend (Supabase / Brevo).
- Blog : connecter MDX ou un CMS (contenu SEO — cœur de la Phase 1).
- Ajouter les images Open Graph (`opengraph-image.tsx`).
