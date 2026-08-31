# FILON — registre des claims non supportés

Date d'audit : 29 août 2026
Périmètre : web, mobile, extension et sorties backend suivies dans le dépôt.

## Règle

Un claim public doit nommer son périmètre, sa source et sa limite. Les mots
`meilleur`, `vérifié`, `garanti`, `tout` et `maximum` ne sont acceptables que si
la preuve correspondante existe dans la réponse et si le périmètre est visible.

## Claims bloquants observés

| ID | Claim observé | Emplacements principaux | Preuve réelle actuelle | Décision Phase 0 |
|---|---|---|---|---|
| C-001 | « tout le marché » / « tous les marchands » | homepage, méthode, listing extension | catalogue de marchands Awin indexés, couverture non exhaustive | Remplacer par « offres/marchands indexés » |
| C-002 | « meilleur prix » absolu | hero, cashback, extension | depuis `f5ae21b`, `/advise` ne retient que les offres EUR explicitement en stock, fraîches et à prix valide ; un total livré connu prime sur une livraison inconnue et aucune économie n'est calculée si la comparaison est incomplète | Nommer prix article ou total livré, offres éligibles observées, devise, fraîcheur et limite de livraison |
| C-003 | codes promo « testés au paiement » | extension et page Score | aucune exécution checkout documentée | Retirer ; dire « promotion fournie » |
| C-004 | reconditionné/vendeur « certifié » ou « garanti » | FAQ, aide, extension | feed pouvant fournir état/garantie ; aucune certification FILON | Retirer ; renvoyer aux conditions marchand |
| C-005 | « cashback maximal » ou automatique | extension et page Cashback | aucune optimisation multi-plateforme prouvée | Afficher seulement l'avantage indexé et ses conditions |
| C-006 | Score basé sur avis, livraison, garantie, cashback | page Score | moteur v3 : comparaison, historique, stock, fraîcheur, largeur ; une livraison inconnue n'est pas une dimension positive et ne permet aucune économie comparative | Réécrire la méthode selon le code réel et exposer les inconnus |
| C-007 | réparabilité, durée de vie et avis « analysés » | graphe visuel | aucune evidence canonique exigée pour ces dimensions | Remplacer par les dimensions v3 observées |
| C-008 | « acheter ou attendre » sans possibilité d'abstention | méthode et extension | le moteur peut rendre `insuffisant`/`a_verifier` | Nommer explicitement l'abstention |
| C-009 | « prix jamais augmenté » / affiliation neutre absolue | transparence, CGU, preuves, extension | dans la clé Core et le reranker Assistant testés, des taux synthétiques inversés ne changent ni les offres, ni leur ordre, ni le contexte du reranker ; la projection affiliée simulée ne modifie que les liens après classement ; aucun taux réel n'est ingéré et le panier marchand n'est pas mesuré | Autoriser seulement ce résultat borné aux deux composants testés ; conserver l'absolu et le prix final interdits, et faire confirmer le total marchand |
| C-010 | marchands « partenaires » | catalogue, FAQ, preuves, assistant | une source indexée ou un domaine autorisé ne prouve pas un partenariat public actif | Dire « marchands/sources indexés » sans registre de partenariat sourcé |
| C-011 | recommandations synthétiques avec prix, garantie, cashback ou score estimés | ancien repli backend inutilisé | aucune observation source | Supprimer le moteur mort ; abstention vide sans offre indexée |
| C-012 | gratuité perpétuelle / « jamais facturé » | tarifs, CGU, footer, presse, extension | offre publique affichée à 0 € au moment de l'audit ; aucun engagement perpétuel documenté | Nommer l'offre actuelle et renvoyer vers la page Tarifs |
| C-013 | extension : « aucune lecture automatique » / « aucune donnée collectée » | fiche store et README | le content script lit localement le produit ; une action ouvre FILON avec le nom dans l'URL | Décrire lecture locale, absence de transmission automatique et transfert après action |
| C-014 | « chaque incident produit de production reçoit un code » | objectif du mandat de gouvernance | registre E001–E018 canonique ; seule la projection Awin émet actuellement E008, E010 et E016–E018 | Ne pas revendiquer la couverture exhaustive avant instrumentation et audit de tous les producteurs |
| C-015 | « sous votre budget » comme prix final livré | décision générale / Assistant | `f5ae21b` applique le budget EUR comme contrainte dure au total article actuellement calculable, mais la livraison reste `unknown` et le total est explicitement `items_only` | Dire « sous-total articles dans le budget connu » ; ne pas promettre le total livré |
| C-016 | confiance « haute » ou pourcentage de confiance | décision générale | aucune calibration indépendante ; `f5ae21b` renvoie `confidence_score=null`, `confidence_band=not_calibrated` pour les recommandations ; l'abstention conserve encore le marqueur historique `0`/`low`, qui n'est pas une probabilité calibrée | Ne pas afficher de niveau chiffré ou qualitatif avant calibration sur holdout indépendant ; normaliser aussi l'abstention |
| C-017 | score, compatibilité ou qualité Outfit chiffrée | Outfit Studio, Lookbook et journal mobile | aucun score Fashion calibré sur cas humains indépendants ; les anciennes valeurs étaient heuristiques | Afficher « Non mesuré » et conserver l'abstention tant que P0.2 n'a pas de holdout humain |
| C-018 | prix, stock ou bouton marchand « actuel » sans preuve explicite | Assistant, cartes produit web/mobile, favoris, alertes et comparateur | depuis `1a167dc`, l'Assistant exige `evidence_current=true`, revalide les cartes et utilise le cache v4 ; les clients exigent aussi un `observed_at` strict, non futur et âgé d'au plus 72 h. Le backend catalogue protégé n'émet pas encore tous ces champs | Masquer l'action et le claim ; ne jamais inférer la fraîcheur de la simple présence d'un prix ou d'un stock |
| C-019 | baisse, plus bas ou meilleur prix calculé entre devises différentes ou à partir d'un prix indisponible | détail produit, rails, Pulse et comparaisons mobiles | aucun FX qualifié ; les clients imposent une comparaison mono-devise, une devise explicite, une date non future et `in_stock=true` sur chaque point d'historique | Ne comparer que des observations achetables de même devise ; sinon afficher une information non comparable ou s'abstenir |
| C-020 | lien marchand « sûr » parce qu'il est seulement présent | CTA web/mobile et partage | les clients refusent les URL non HTTPS, avec identifiants, hôte non qualifié, suffixe local/réservé ou littéral IP, y compris les formes IPv4/IPv6 contournées | Rendre actionnable uniquement une URL HTTPS dotée d'un nom DNS public admissible ; ce contrôle ne certifie pas le marchand |
| C-021 | tri ou filtre prix comparable sur un catalogue sans scope devise | catalogue web/mobile | l'API actuelle ne garantit pas une devise commune pour la liste ; ordonner des nombres bruts produirait un classement multidevise trompeur | Retirer les tris/filtres prix tant que le contrat ne fournit pas un scope mono-devise ou une conversion qualifiée |
| C-022 | paramètres de deep-link présentés comme preuve d'achat ou d'alerte | détail produit et création d'alerte mobile | `55aaf41` traite la route comme display-only, recharge le détail Core avant achat/partage/sauvegarde/alerte et revalide encore l'alerte au submit | Ne jamais agir depuis le seul prix, la seule URL ou le seul identifiant transporté par la route ; s'abstenir en cas d'absence ou de contradiction Core |

## Faits actuellement publiables sans extrapolation

- pour l'offre retenue par `/advise` : marchand, prix article, devise,
  disponibilité et `observed_at`, uniquement lorsque la sélection Core a
  validé l'observation ;
- coût de livraison observé ou absent, avec `shipping_cost_known` explicite ;
- comparaison complète ou incomplète via `price_comparison_complete` et absence
  d'économie via `savings_vs_market=null` lorsque la comparaison est
  incomplète ;
- « historique insuffisant » avec nombre de relevés et jours suivis ;
- disponibilité tri-state `in_stock`, `out_of_stock`, `unknown` ;
- prix, devise, marchands et fraîcheur issus d'un feed identifié ; le TTL actuel
  de **72 h** doit être nommé comme provisoire, pas comme garantie de fraîcheur ;
- dans les clients, prix/stock/action uniquement avec
  `evidence_current=true` explicite et `observed_at` valide, non futur et âgé
  d'au plus 72 h ;
- dans l'Assistant, carte publiable uniquement avec le même marqueur explicite
  et après revalidation ; le cache moteur v4 invalide le format précédent ;
- « comparaison parmi les offres observées de même devise » lorsque toutes
  les observations comparées et tous les points d'historique portent cette
  devise, une date non future et un stock positif explicite ; aucune conversion
  FX implicite ;
- action marchande seulement tant que la preuve reste courante ; web et mobile
  recalculent l'expiration dynamiquement, y compris après reprise de l'application ;
- lien externe HTTPS avec nom DNS public qualifié ; les suffixes locaux ou
  réservés sont refusés. Cela prouve un garde-fou de navigation, pas une
  certification du marchand ;
- sur mobile, paramètres de route utilisables pour l'affichage seulement ; toute
  action exige le détail Core concordant et l'alerte une seconde validation au
  moment de l'enregistrement ;
- le proxy Pulse web peut mutualiser sa lecture pendant **120 s** ; ce cache
  technique n'est ni une observation marchande ni le TTL de preuve de 72 h ;
- « sous-total articles dans le budget EUR connu » lorsque la livraison reste
  explicitement inconnue ;
- absence visible de livraison, retour, garantie ou contexte requis.

Les claims « total livré le plus bas parmi N offres/marchands » et « prix
article uniquement » ne sont pas encore publiables comme tels : le contrat
`ProductAnalysis` n'expose ni le nombre de candidats, ni
`price_comparison_basis`. Ces informations restent internes au comparateur et
devront être ajoutées explicitement au contrat avant affichage.

## Limites de comparabilité au 29 août 2026

Le contrat public `/advise` conserve désormais la devise observée, mais son
budget est exprimé en EUR et aucun moteur FX n'est disponible. Les offres sans
devise ou hors EUR ne participent donc pas à cette comparaison. Le parcours de
décision générale s'abstient sur des devises incompatibles et, lorsqu'un budget
EUR existe, écarte les offres non EUR au lieu de fabriquer une conversion. Les
clients web/mobile appliquent la même règle fail-closed : une comparaison est
mono-devise et chaque point historique doit porter une devise identique. Les
tris et filtres prix ont été retirés des listes dont le contrat ne fournit pas
de scope devise.

La livraison est fail-closed : `None` reste unknown, jamais `0`. Si au moins un
total livré est connu, les offres au shipping inconnu ne peuvent pas le battre.
Si tous les shippings sont inconnus, seul le prix article ordonne les offres et
aucun `savings_vs_market` ni écart en euros n'est supporté. Cette correction
locale au commit `f5ae21b` ne prouve ni le total affiché au checkout marchand,
ni une couverture exhaustive du marché.

La confiance des recommandations générales est également fail-closed : elle
reste `not_calibrated` tant que les datasets humains indépendants sont vides.
L'abstention porte encore `0`/`low`, valeur sentinelle héritée à normaliser et
non mesure de confiance. Le rapport Quality actuel est intègre
(`integrity_valid=true`) mais non prêt (`ready=false`, `status=not_ready`, 0 cas
humain) ; il ne soutient donc aucun pourcentage de qualité ou de confiance
produit.

La simple présence d'un prix, d'un stock ou d'une date ne suffit plus à rendre
une offre actionnable. Le marqueur `evidence_current=true` doit être explicite
dans l'Assistant comme dans les clients, et `observed_at` doit rester dans la
fenêtre provisoire de 72 h. L'éligibilité expire dynamiquement sur web et mobile.
Le mobile rejette aussi tout historique futur, multidevise ou sans
`in_stock=true`, et ne transforme jamais les faits d'un deep-link en preuve Core.

Les intégrations protégées `catalog.py` et `SearchAssistant.tsx` ne sont pas
incluses. Les surfaces dépendantes doivent rester masquées ou s'abstenir ; leur
silence n'est pas une preuve de couverture. L'intégration de `catalog.py` devra
conserver le contrat UTC naïf de `PriceSnapshot.captured_at` ou le migrer
explicitement. La divergence d'URL marchande canonique entre les cartes
Assistant et le détail catalogue doit aussi être résolue afin que la
réconciliation stricte ne retire pas une preuve valide.

## Hors gate

Le test `AFFILIATE_INVARIANCE_TEST` est livré pour le parcours Assistant backend,
au niveau du reranking et de la construction des cartes : sous une perturbation
contrôlée, il prouve que la projection affiliée simulée ne modifie que les liens
après ce classement et qu'elle ne change ni les identifiants retenus, ni leur
ordre, ni le contexte envoyé au reranker. Il ne valide ni des taux Awin réels —
aucun n'est actuellement ingéré —, ni la couverture et l'inclusion des marchands
en amont, ni le prix du panier chez le marchand, ni les autres parcours et
clients. Seul le résultat « dans la clé Core et le reranker Assistant testés,
des taux synthétiques ne modifient pas le classement » est couvert localement
par ce test borné ; une neutralité absolue reste non supportée. Le contrôle
automatique web/extension interdit désormais les principales formulations
absolues. Le fichier local `SearchAssistant.tsx` comporte encore des modifications
utilisateur non incluses dans ce lot ; elles ne sont ni écrasées ni présentées
comme auditées. Les textes légaux et de confidentialité doivent être revus par
leur owner ; cet audit technique ne constitue pas un avis juridique.

Les preuves versionnées courantes restent techniques : l'archive backend de
`1a167dc` passe **1 795 tests**, avec 7 warnings, en 120,91 s ; l'archive web de
`0c6f674` passe le typecheck, les gates contrat/claims/vérité produit et le build
de production ; le mobile `55aaf41` passe **166 tests**, avec **4 smoke tests
ignorés**, le typecheck et ESLint à **0 erreur / 15 avertissements**. L'audit
indépendant mobile ne relève aucun P0, P1 ou P2. Le `npm test` web complet vert
reste une preuve de la copie de travail, car il inclut MegaMenu et
`SearchAssistant.tsx` protégés ; il ne doit pas être attribué à l'archive propre.
Ces contrôles ne fournissent ni cas humain P0.2, ni calibration Outfit, ni
qualification de production. Le statut reste **NO-GO** avec **0 cas humain**.
