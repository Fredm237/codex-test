# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** FILON
**Category:** SaaS Premium / Assistant d'Achat
**Design Dials:** Variance 3/10 (Minimaliste / Premium) | Motion 8/10 (Fluide / Vivant) | Density 3/10 (Aéré)
**Inspiration:** Phia.com, Apple, Stripe, Linear

---

## Règles Globales (Refonte 2026)

### L'ADN Design

1.  **La Respiration** : Ne surchargez jamais l'interface. Utilisez des espaces blancs généreux pour laisser le contenu respirer.
2.  **La Profondeur Naturelle** : Évitez les designs plats. Utilisez des ombres multi-couches et diffuses pour créer un relief réaliste.
3.  **Le Mouvement Subtil** : Toute interface doit paraître "vivante". Utilisez Framer Motion pour des animations *spring*, des transitions d'opacité douces et des micro-interactions au survol.
4.  **La Typographie Sophistiquée** : Privilégiez des polices sans-serif modernes. N'utilisez jamais de noir pur (`#000`), préférez une encre foncée (`#14171c`).
5.  **L'Effet "Humain"** : Évitez l'aspect "généré par IA". Utilisez des visuels de haute qualité et un langage clair.

### Palette de Couleurs (Couche Sémantique)

| Rôle | Description | CSS Variable |
|------|-------------|--------------|
| **Background** | Papier tiède, jamais blanc pur. | `--fx-bg` (`#faf9f7`) |
| **Surface** | Cartes et éléments surélevés. | `--fx-surface` (`#ffffff`) |
| **Text (Ink)** | Encre foncée, pas de noir pur. | `--fx-text` (`#14171c`) |
| **Text Muted** | Texte secondaire, gris doux. | `--fx-text-muted` (`#6a7280`) |
| **Action** | Boutons principaux (noir encre). | `--fx-action` (`#14171c`) |
| **Brand (Or)** | Accents, badges, focus. | `--fx-brand` (`#8a6a24`) |
| **Gain (Turquoise)** | Réservé uniquement aux économies. | `--fx-gain` (`#0a7d74`) |

### Typographie

- **Police principale :** Sans-serif moderne (Inter, SF Pro).
- **Police secondaire (Titres spécifiques) :** Serif élégante (Playfair Display) utilisée avec parcimonie pour l'effet éditorial.
- **Mood :** Premium, vivant, clair, digne de confiance.

### Spacing Variables

*Density: 5/10 — Standard*

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `16px` / `1rem` | Standard padding |
| `--space-lg` | `24px` / `1.5rem` | Section padding |
| `--space-xl` | `32px` / `2rem` | Large gaps |
| `--space-2xl` | `48px` / `3rem` | Section margins |
| `--space-3xl` | `64px` / `4rem` | Hero padding |

### Élévation et Ombres (Multi-couches)

Les ombres doivent être subtiles et naturelles, jamais dures.

| Niveau | Usage | CSS Variable |
|--------|-------|--------------|
| **Level 1** | Cartes de base, boutons au repos. | `--fx-elevation-1` |
| **Level 2** | Cartes au survol, dropdowns. | `--fx-elevation-2` |
| **Level 3** | Modales, CTA flottants (Sticky). | `--fx-elevation-3` |

---

## Composants et Micro-interactions

### Boutons (`.fx-btn`)
- **Primary (`.on-ink`) :** Fond papier, texte encre, ombre Level 1. Au survol : élévation Level 2 et translation Y (-2px).
- **Secondary (`.secondary`) :** Transparent, bordure forte. Au survol : fond papier légèrement assombri.
- **Interaction :** Tous les boutons doivent avoir un effet de pression au clic (`transform: scale(0.97)`).

### Cartes (`.fx-card`, `.fx-product`)
- **Base :** Bordure subtile, rayon moyen (`--fx-radius-md`), ombre Level 1.
- **Survol :** Bordure plus forte, ombre Level 2, translation Y (-2px) avec une animation *spring* (Framer Motion).

### Skeletons de Chargement (`.fx-skeleton`)
- Utiliser une animation *shimmer* douce et continue.
- Respecter les proportions finales des éléments pour éviter le *layout shift*.

### Transitions de Page (`PageTransition`)
- Envelopper le contenu de `main` avec `AnimatePresence` et un composant `motion.div`.
- Animation : Fondu enchaîné (opacity 0 -> 1) combiné à un léger glissement vertical (y: 8px -> 0).

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## Style Guidelines

**Style:** Trust & Authority

**Keywords:** Certificates/badges displayed, expert credentials, case studies with metrics, before/after comparisons, industry recognition, security badges

**Best For:** Healthcare/medical landing pages, financial services, enterprise software, premium/luxury products, legal services

**Key Effects:** Badge hover effects, metric pulse animations, certificate carousel, smooth stat reveal

### Page Pattern

**Pattern Name:** Pricing Page + CTA

- **Conversion Strategy:** Recommend starter plan (pre-select/highlight). Show annual discount (20-30%). Use FAQs to address concerns.
- **CTA Placement:** Each card: CTA button. Sticky CTA in nav
- **Section Order:** 1. Hero (pricing headline), 2. Price comparison cards, 3. Feature comparison table, 4. FAQ section, 5. Final CTA

---

## Mouvement et Animations (Framer Motion)

L'animation est au cœur de l'expérience Filon. Elle doit être fluide, basée sur la physique (spring) et jamais agressive.

### Courbes de base (CSS)
- `--fx-duration-fast`: `150ms` (Micro-interactions)
- `--fx-duration`: `220ms` (Transitions standard)
- `--fx-duration-slow`: `320ms` (Menus, éléments complexes)
- `--fx-ease-out`: `cubic-bezier(0.16, 1, 0.3, 1)` (Signature Filon)

### Framer Motion (React)
Privilégier les animations de type `spring` pour un rendu naturel :
```javascript
transition={{ type: "spring", stiffness: 300, damping: 20 }}
```

**Stagger (Apparition en cascade) :**
Idéal pour les listes, les grilles de produits et les étapes.
```javascript
variants={{
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } }
}}
```

---

## Anti-Patterns (Do NOT Use)

- ❌ Confusing pricing
- ❌ No trust signals
- ❌ AI purple/pink gradients

### Additional Forbidden Patterns

- ❌ **Emojis as icons** — Use SVG icons (Heroicons, Lucide, Simple Icons)
- ❌ **Missing cursor:pointer** — All clickable elements must have cursor:pointer
- ❌ **Layout-shifting hovers** — Avoid scale transforms that shift layout
- ❌ **Low contrast text** — Maintain 4.5:1 minimum contrast ratio
- ❌ **Instant state changes** — Always use transitions (150-300ms)
- ❌ **Invisible focus states** — Focus states must be visible for a11y

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] **Cohérence visuelle :** Plus aucun dégradé bleu/turquoise "SmartWave". Uniquement l'encre, le papier, l'or (marque) et le turquoise (économies).
- [ ] **Icônes :** Utiliser exclusivement des SVG au trait fin (currentColor), jamais d'emojis.
- [ ] **Micro-interactions :** Tous les éléments cliquables ont un effet au survol (hover) ET au clic (active/tap).
- [ ] **Ombres :** Utiliser les variables `--fx-elevation-*` multi-couches, jamais de box-shadow en dur.
- [ ] **Animations :** Les éléments importants apparaissent avec un effet *scroll-reveal* (Framer Motion).
- [ ] **Accessibilité :** Focus visible (anneau doré), contraste > 4.5:1, respect de `prefers-reduced-motion`.
- [ ] **Mobile :** Navigation fluide, pas de défilement horizontal, zones tactiles d'au moins 44px.
