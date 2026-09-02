# FILON — Reçu de préparation confidentialité Phases 15 à 18

Date : 2026-09-02

Branche locale : `codex/filon-phase-15-18-privacy-readiness`

## Décision

**GO local** pour la confidentialité du trajet d'authentification mobile et la
portabilité/effacement du dressing local. **P18F READY local** pour le journal
serveur privé, sa rétention, son export et son effacement.

Ce reçu ne change pas les décisions de production : **P15G, P18F et P18G
restent NO-GO production** tant que leurs preuves appareil, shadow réel et
canary atomique ne sont pas produites.

## Confidentialité OAuth

- le callback mobile n'accepte plus de jeton de session ou de profil sérialisé
  dans ses paramètres ou dans une URL ;
- le callback ne traite que `code`, `state` et la présence neutre d'une erreur
  fournisseur ;
- l'échange mobile du code à usage unique utilise désormais `POST` et place
  `code + state` dans le corps, jamais dans l'URL de requête ;
- jetons, préfixes de jetons, en-têtes, cookies, profils, URL et corps d'erreur
  ne sont plus écrits dans les journaux du trajet mobile ;
- les erreurs montrées à la personne et remontées au client sont neutralisées ;
- le jeton natif demeure stocké dans `SecureStore` et le web conserve son
  modèle de cookie serveur.

## Portabilité, conservation et effacement local

Le dressing expose maintenant un export local versionné :

- `schemaVersion = 1` ;
- `kind = filon_wardrobe_export` ;
- `storageScope = local_device` ;
- `retentionPolicy = until_user_deletion` ;
- contenu resanitisé avant export ;
- aucune transmission réseau implicite.

L'effacement sérialisé supprime les clés v2 et legacy v1, relit les deux clés,
échoue fermé si l'une subsiste et n'émet un reçu
`filon_wardrobe_erasure_receipt` qu'après vérification effective à `null`.

## Preuves exécutées

| Contrôle | Résultat |
|---|---|
| Tests ciblés auth + dressing | **PASS — 12/12** |
| Garde anti-régression URL/logs | **PASS** |
| Échange OAuth POST comportemental | **PASS** |
| Corps d'erreur privé non divulgué | **PASS** |
| Export et reçu d'effacement | **PASS** |
| TypeScript `--noEmit` | **PASS** |
| Bundle serveur mobile | **PASS** |
| ESLint des fichiers modifiés | **PASS — 0 erreur, 0 avertissement de code** |
| Suite mobile complète | **PASS — 362 réussis, 4 ignorés** |

L'avertissement Node relatif au type de module de `eslint.config.js` préexiste
et n'affecte aucun contrôle fonctionnel. Les quatre tests ignorés exigent des
services ou identifiants externes et ne sont pas déclarés réussis.

## Journal serveur Personal Commerce

La migration additive `b5d3f7a9c1e4` et le commit local `c196c71` ajoutent un
journal sans contexte brut, un identifiant sujet HMAC uniquement sous
consentement, une échéance obligatoire, un export isolé et des reçus
d'effacement vérifiés. Le writer reste OFF et la clé HMAC n'a aucune valeur
versionnée. La qualification locale compte 91 tests d'intégration réussis ; la
suite backend couvre 2 640 tests exécutables. Les trois preuves PostgreSQL sont
explicitement réservées à la CI avec `TEST_POSTGRES_URL`.

## Frontière restante avant fermeture réelle de Phase 18

1. publier et qualifier ce durcissement sur CI distante ;
2. qualifier l'authentification et l'effacement sur appareils iOS et Android ;
3. appliquer en production le journal Personal Commerce additif déjà préparé,
   après CI distante PostgreSQL verte ;
4. exécuter un replay production borné `dry-run → apply → replay` et prouver
   l'idempotence ainsi que l'effacement ;
5. qualifier une cohorte explicitement consentante avec export et rollback ;
6. promouvoir atomiquement les maillons V2 nécessaires, sans lecteur shadow
   isolé.

Tant que ces points ne sont pas fermés, le mandat créatif post-Phase 18 reste
conditionnel et ne doit pas être présenté comme commencé.
