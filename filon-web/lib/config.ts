/**
 * Configuration produit.
 *
 * CHROME_STORE_URL : l'adresse de la fiche FILON sur le Chrome Web Store, une
 * fois l'extension publiée. Tant qu'elle est vide, tous les boutons
 * « Ajouter à Chrome » mènent à la page /extension (hub d'installation).
 * Le jour de la publication : on colle l'URL ici (une seule ligne) et TOUT le
 * site pointe automatiquement vers l'installation en 1 clic.
 */
export const CHROME_STORE_URL = "";

/** Cible des boutons « Ajouter à Chrome ». */
export const chromeInstallHref = CHROME_STORE_URL || "/extension";
