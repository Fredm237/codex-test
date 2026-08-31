"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { API } from "@/lib/api";
import { useLocale, type Locale } from "@/lib/i18n";

type Subcategory = { name: string; count: number };
type Category = { name: string; slug: string; count: number; subcategories?: Subcategory[] };
type Department = { name: string; slug: string; count: number; categories: Category[] };

const L: Record<Locale, { label: string; all: string; products: (n: number) => string }> = {
  fr: {
    label: "Catalogue",
    all: "Tout le catalogue",
    products: (n) => `${n.toLocaleString("fr-FR")} produits`,
  },
  nl: {
    label: "Catalogus",
    all: "Hele catalogus",
    products: (n) => `${n.toLocaleString("nl-BE")} producten`,
  },
  en: {
    label: "Catalogue",
    all: "Whole catalogue",
    products: (n) => `${n.toLocaleString("en-GB")} products`,
  },
};

/** Nombre de sous-rayons montrés sous un rayon détaillé. */
const SUBS_SHOWN = 4;

/** Un méga-menu oriente : chaque département reste atteignable en entier par
 * son titre, mais il n’a pas à reproduire toute son arborescence. */
const CATEGORIES_SHOWN = 4;

/** Les trois rayons de tête peuvent exposer leurs sous-rayons dans le panneau.
 * Cela préserve la découverte sans produire un mur de liens concurrent avec la page. */
const DETAILED_PER_DEPT = 3;

/** Les plus gros sous-rayons, pas les premiers venus.
 *
 *  L'API renvoie les sous-rayons dans un ordre qui n'est pas celui de leur
 *  poids. Prendre les quatre premiers écartait « Montres » (18 662 produits) au
 *  profit de « Boucles d'oreilles » (2 883) : sur les douze rayons qui comptent
 *  plus de quatre sous-rayons, huit affichaient ainsi les mauvais. Le menu
 *  doit conduire là où il y a de la marchandise.
 *
 *  À nombre de produits égal, l'ordre alphabétique tranche : sans cela, deux
 *  chargements successifs peuvent inverser deux entrées et le menu paraît
 *  instable.
 */
export function pickSubcategories(subs: Subcategory[] | undefined, limit = SUBS_SHOWN): Subcategory[] {
  if (!subs || subs.length === 0) return [];
  return [...subs]
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, "fr"))
    .slice(0, limit);
}

/** Les rayons dont on déploie les sous-rayons.
 *
 *  Le poids en produits sert d'arbitre : dans « High-Tech », Téléphonie
 *  (72 634) mérite son détail, Photo (1 261) se contente de son lien.
 */
export function pickCategories(categories: Category[], limit = CATEGORIES_SHOWN): Category[] {
  return [...categories]
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, "fr"))
    .slice(0, limit);
}

export function detailedCategorySlugs(dep: Department, limit = DETAILED_PER_DEPT): Set<string> {
  return new Set(pickCategories(dep.categories, limit).map((c) => c.slug));
}

/** Répartit les départements en colonnes de hauteur comparable.
 *
 *  Une grille à trois colonnes égales plaçait 36 lignes (« Mode & Accessoires »)
 *  à côté de 6 (« Beauté & Santé ») : le panneau était haut et visiblement
 *  bancal. On mesure ici le coût en lignes de chaque département, puis on
 *  remplit la colonne la moins chargée — un ordonnancement glouton, suffisant
 *  pour six éléments et stable d'un rendu à l'autre.
 */
export function balanceColumns(departments: Department[], columns = 3): Department[][] {
  const cols: Department[][] = Array.from({ length: columns }, () => []);
  const load = new Array(columns).fill(0);
  const cost = (d: Department) => {
    const categories = pickCategories(d.categories);
    const detailed = detailedCategorySlugs(d);
    return (
      1 +
      categories.length +
      categories.reduce(
        (n, c) => n + (detailed.has(c.slug) ? pickSubcategories(c.subcategories).length : 0),
        0
      )
    );
  };

  for (const d of [...departments].sort((a, b) => cost(b) - cost(a))) {
    let target = 0;
    for (let i = 1; i < columns; i++) if (load[i] < load[target]) target = i;
    cols[target].push(d);
    load[target] += cost(d);
  }
  return cols.filter((c) => c.length > 0);
}

/** Méga-menu du catalogue : départements, rayons, sous-rayons.
 *
 *  Vingt-six rayons dans une liste plate ne se parcourent pas. Deux niveaux
 *  suffisent à rendre le catalogue lisible d'un coup d'œil.
 *
 *  Le menu s'ouvre au clic et non au survol. Sur un trackpad, un déplacement
 *  du pointeur pendant le défilement suffisait à déployer un panneau de 920 px
 *  sans que rien n'ait été demandé ; c'est aussi la seule façon d'offrir le même
 *  comportement au clavier, au toucher et à la souris.
 *
 *  `initialDepartments` vient du rendu serveur : le menu est complet dès la
 *  première image, sans attendre un aller-retour réseau depuis le navigateur.
 */
export function MegaMenu({ initialDepartments = [] }: { initialDepartments?: Department[] }) {
  const { locale } = useLocale();
  const t = L[locale];
  const [departments, setDepartments] = useState<Department[]>(initialDepartments);
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const panelId = useId();

  // Repli : si le serveur n'a rien fourni (rendu statique, API momentanément
  // muette), le navigateur retente. La donnée est mise en cache par le CDN :
  // cet appel reste l'exception, non la règle.
  useEffect(() => {
    if (initialDepartments.length > 0) return;
    const ctrl = new AbortController();
    (async () => {
      try {
        const res = await fetch(`${API}/api/catalog/categories`, { signal: ctrl.signal });
        if (!res.ok) return;
        const data = await res.json();
        setDepartments((data.departments || []) as Department[]);
      } catch {
        // Sans catalogue joignable, le lien simple reste utilisable.
      }
    })();
    return () => ctrl.abort();
  }, [initialDepartments.length]);

  const close = useCallback((focusTrigger = false) => {
    setOpen(false);
    if (focusTrigger) trigger.current?.focus();
  }, []);

  // Fermetures : Échap, clic extérieur, sortie du menu au clavier, défilement.
  useEffect(() => {
    if (!open) return;

    const onPointerDown = (e: PointerEvent) => {
      if (!wrap.current?.contains(e.target as Node)) close();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close(true);
      }
    };
    // Le focus qui sort du menu le referme : sans cela, tabuler au-delà du
    // dernier lien laisse un panneau ouvert derrière la page.
    const onFocusIn = (e: FocusEvent) => {
      if (!wrap.current?.contains(e.target as Node)) close();
    };
    // Un panneau ancré qui suit la page pendant le défilement donne une
    // impression de flottement ; on le referme.
    const onScroll = () => close();

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKey);
    document.addEventListener("focusin", onFocusIn);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("focusin", onFocusIn);
      window.removeEventListener("scroll", onScroll);
    };
  }, [open, close]);

  // Recadrage horizontal : le panneau était centré sur son déclencheur, donc
  // amputé à gauche dès que la fenêtre se resserrait. On le décale du strict
  // nécessaire pour qu'il tienne dans la fenêtre, marge comprise.
  useEffect(() => {
    if (!open) return;
    const el = panel.current;
    if (!el) return;

    const fit = () => {
      el.style.setProperty("--mm-shift", "0px");
      const box = el.getBoundingClientRect();
      const margin = 16;
      let shift = 0;
      if (box.left < margin) shift = margin - box.left;
      else if (box.right > window.innerWidth - margin) shift = window.innerWidth - margin - box.right;
      el.style.setProperty("--mm-shift", `${Math.round(shift)}px`);
    };

    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, [open, departments]);

  // Navigation clavier dans le panneau : flèches, Home/End.
  const onPanelKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const keys = ["ArrowDown", "ArrowUp", "Home", "End"];
    if (!keys.includes(e.key)) return;
    const links = Array.from(panel.current?.querySelectorAll<HTMLAnchorElement>("a[href]") || []);
    if (links.length === 0) return;
    e.preventDefault();
    const at = links.indexOf(document.activeElement as HTMLAnchorElement);
    const next =
      e.key === "Home" ? 0
      : e.key === "End" ? links.length - 1
      : e.key === "ArrowDown" ? (at + 1) % links.length
      : (at - 1 + links.length) % links.length;
    links[next]?.focus();
  };

  const columns = useMemo(() => balanceColumns(departments), [departments]);

  // Sans données, le lien simple fait le travail : mieux vaut une navigation
  // qui marche qu'un menu vide.
  if (departments.length === 0) {
    return <Link href="/catalogue/" prefetch>{t.label}</Link>;
  }

  return (
    <div className="mm" ref={wrap}>
      <Link className="mm-catalogue-link" href="/catalogue/" prefetch>
        {t.label}
      </Link>
      <button
        type="button"
        ref={trigger}
        className={`mm-trigger${open ? " open" : ""}`}
        aria-label={`${t.label} — menu`}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown" && !open) {
            e.preventDefault();
            setOpen(true);
            // Le panneau n'est pas encore peint : on attend la frame suivante.
            requestAnimationFrame(() =>
              panel.current?.querySelector<HTMLAnchorElement>("a[href]")?.focus()
            );
          }
        }}
      >
        <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
          <path d="M2 4l3 3 3-3" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      <div
        id={panelId}
        ref={panel}
        className={`mm-panel${open ? " show" : ""}`}
        hidden={!open}
        onKeyDown={onPanelKeyDown}
      >
        <div className="mm-grid">
          {columns.map((col, i) => (
            <div className="mm-col" key={i}>
              {col.map((d) => {
                const categories = pickCategories(d.categories);
                const detailed = detailedCategorySlugs(d);
                return (
                <section className="mm-dept" key={d.slug} aria-labelledby={`${panelId}-${d.slug}`}>
                  <a className="mm-dep" id={`${panelId}-${d.slug}`} href={`/catalogue/?dept=${d.slug}`} onClick={() => close()}>
                    {d.name}
                    <em>{t.products(d.count)}</em>
                  </a>
                  <ul>
                    {categories.map((c) => (
                      <li key={c.slug}>
                        <a href={`/categorie/${c.slug}/`} onClick={() => close()}>
                          {c.name}
                          <span>{c.count.toLocaleString(locale === "nl" ? "nl-BE" : locale === "en" ? "en-GB" : "fr-FR")}</span>
                        </a>
                        {detailed.has(c.slug) && pickSubcategories(c.subcategories).length > 0 && (
                          <ul className="mm-sub">
                            {pickSubcategories(c.subcategories).map((s) => (
                              <li key={s.name}>
                                <a
                                  href={`/categorie/${c.slug}/?sub=${encodeURIComponent(s.name)}`}
                                  onClick={() => close()}
                                >
                                  {s.name}
                                </a>
                              </li>
                            ))}
                          </ul>
                        )}
                      </li>
                    ))}
                  </ul>
                </section>
                );
              })}
            </div>
          ))}
        </div>
        <Link className="mm-all" href="/catalogue/" prefetch onClick={() => close()}>
          {t.all} →
        </Link>
      </div>
    </div>
  );
}
