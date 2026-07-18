# Déployer FILON sur Hostinger (hébergement mutualisé)

Hostinger mutualisé ne fait pas tourner Node.js — on déploie donc le site en
**statique** (fichiers HTML/CSS/JS), ce que Next.js génère avec `output: 'export'`.

## 1. Générer le site statique

```bash
cd filon-web
npm install
npm run build        # génère le dossier out/
```

Le dossier **`out/`** contient tout le site :
`index.html`, `cashback/`, `reconditionne/`, `comment-ca-marche/`, `a-propos/`,
`contact/`, `blog/`, `experience/`, plus `sitemap.xml`, `robots.txt`, `icon.png`.

Un zip prêt à l'emploi est aussi fourni : **`filon-site-static.zip`**.

## 2. Téléverser sur Hostinger

Via **hPanel → Gestionnaire de fichiers** (ou FTP) :

1. Ouvrez le dossier **`public_html`** de votre domaine.
2. Videz-le si besoin (sauvegardez d'abord tout fichier existant).
3. Téléversez **le contenu du dossier `out/`** (ou décompressez
   `filon-site-static.zip`) **à la racine de `public_html`**.
   - Important : mettez `index.html` directement dans `public_html/`, pas dans un
     sous-dossier `out/`.
4. Terminé — visitez votre domaine.

> Astuce : par FTP (FileZilla), glissez tout le contenu de `out/` dans
> `public_html`. Les URL propres (`/cashback`) fonctionnent car chaque page est
> un `dossier/index.html` (`trailingSlash` activé).

## 3. Avant la mise en ligne (recommandé)

- **Domaine** : dans `lib/site.ts`, remplacez `url: "https://filon.app"` par votre
  vrai domaine, puis rebuild — cela corrige les balises canoniques, Open Graph et
  le `sitemap.xml`.
- **Sous-dossier** : si le site n'est pas à la racine du domaine mais dans
  `https://mondomaine.com/filon/`, buildez avec
  `NEXT_PUBLIC_BASE_PATH=/filon npm run build`.
- **HTTPS** : activez le certificat SSL gratuit de Hostinger (hPanel → SSL).

## 4. Le formulaire de contact / la newsletter

En statique, il n'y a pas de backend. Le formulaire de contact affiche
actuellement une confirmation côté client. Pour recevoir les messages, branchez-le
sur un service (Formspree, Getform, Hostinger Forms, ou l'API Brevo). Je peux le
câbler quand vous voulez.

## Alternative ultra-simple (page unique)

Si vous ne voulez qu'**une seule page** : le fichier autonome
`filon-site/editorial.html` (à la racine du dépôt) suffit — renommez-le
`index.html` et déposez-le seul dans `public_html`. Police et 3D sont embarquées,
aucun build requis.
