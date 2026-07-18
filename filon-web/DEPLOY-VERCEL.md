# Déployer FILON sur Vercel

Vercel est l'hébergeur natif de Next.js : déploiement automatique à chaque `git push`,
URL gratuite en HTTPS immédiate, et domaine personnalisé (`filon.be`) en quelques clics.

L'application Next.js se trouve dans le sous-dossier **`filon-web/`** du dépôt
`fredm237/codex-test`. Le point le plus important de toute la procédure est donc de
régler le **Root Directory** sur `filon-web`.

---

## 1. Importer le projet (2 min)

1. Va sur **https://vercel.com** et connecte-toi avec ton compte **GitHub**.
2. **Add New… → Project**.
3. Choisis le dépôt **`fredm237/codex-test`** → **Import**.
4. Dans l'écran de configuration :
   - **Root Directory** → clique **Edit** → sélectionne **`filon-web`**. ⚠️ *Étape critique.*
   - **Framework Preset** → `Next.js` (détecté automatiquement).
   - **Build Command** / **Output** → laisse les valeurs par défaut, ne touche à rien.
5. Déplie **Environment Variables** et ajoute (voir §2), puis **Deploy**.

Au bout d'une minute, Vercel te donne une URL du type
`https://codex-test-xxxx.vercel.app` — le site des 24 pages est en ligne.

---

## 2. Variables d'environnement

À coller dans **Settings → Environment Variables** (ou à l'import). Toutes préfixées
`NEXT_PUBLIC_` (elles sont lues au moment du build) :

| Variable | Valeur | Rôle |
|---|---|---|
| `NEXT_PUBLIC_PLAUSIBLE_DOMAIN` | `filon.be` | Analytics Plausible (déjà la valeur par défaut) |
| `NEXT_PUBLIC_FORM_ENDPOINT` | *(ton URL Formspree)* | Active l'envoi réel des formulaires contact + newsletter |

- Sans `NEXT_PUBLIC_FORM_ENDPOINT`, les formulaires restent en **mode démo** (ils
  affichent le succès sans rien envoyer). Crée un formulaire gratuit sur
  **formspree.io**, copie l'URL `https://formspree.io/f/xxxx` ici.
- Après avoir ajouté/modifié une variable, **redéploie** (onglet Deployments → ⋯ →
  Redeploy) pour qu'elle soit prise en compte.

---

## 3. Quelle branche déployer

À l'import, Vercel considère la **branche par défaut du dépôt comme production**, et
crée automatiquement une **preview** pour chaque autre branche/PR.

Le travail est actuellement sur la branche
`claude/ui-ux-pro-max-skill-install-8x985i`. Deux options :

- **A — Preview immédiate** : dès l'import, Vercel construit une URL de *preview* pour
  cette branche. Pratique pour tester tout de suite.
- **B — Production propre** : fusionne la branche dans `main` (via une Pull Request),
  et Vercel déploiera `main` en production. *(Recommandé pour associer le domaine.)*
  Alternative : **Settings → Git → Production Branch** et choisis la branche de travail.

---

## 4. Brancher le domaine `filon.be`

1. **Settings → Domains → Add** → saisis `filon.be` (et `www.filon.be`).
2. Vercel affiche les enregistrements DNS à créer chez ton registrar :
   - soit un **A record** `76.76.21.21` sur `@`,
   - soit un **CNAME** `cname.vercel-dns.com` sur `www`.
   (Vercel te donne les valeurs exactes — suis-les.)
3. Une fois le DNS propagé (quelques minutes à quelques heures), le **HTTPS/SSL est
   automatique** — rien à activer.

---

## 5. Déploiements automatiques

Une fois le projet lié, **chaque `git push`** sur la branche de production redéploie le
site tout seul. Les autres branches et PR obtiennent une URL de preview. Plus rien à
uploader à la main.

---

## Notes techniques

- La config `output: "export"` (dans `next.config.mjs`) produit un site 100 % statique ;
  Vercel le sert parfaitement. Si tu veux plus tard des fonctions serveur (API routes,
  recherche IA réelle, formulaires côté serveur), il suffira de retirer cette ligne —
  Vercel gère alors le rendu Next.js natif, sans autre changement.
- `trailingSlash: true` et `images.unoptimized: true` sont compatibles Vercel, aucune
  action requise.
- Rien à installer en local : Vercel fait le `npm install` + `next build` côté serveur.
