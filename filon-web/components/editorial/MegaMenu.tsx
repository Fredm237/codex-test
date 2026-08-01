"use client";

import { useEffect, useRef, useState } from "react";
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

/** Méga-menu du catalogue : départements puis rayons.
 *
 *  Vingt-six rayons dans une liste plate ne se parcourent pas. Deux niveaux
 *  suffisent à rendre le catalogue lisible d'un coup d'œil — c'est ce que font
 *  les marchands sérieux, et ce qui manquait ici.
 */
export function MegaMenu() {
  const { locale } = useLocale();
  const t = L[locale];
  const [departments, setDepartments] = useState<Department[]>([]);
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/api/catalog/categories`);
        if (!res.ok) return;
        const data = await res.json();
        setDepartments((data.departments || []) as Department[]);
      } catch {
        // Sans catalogue joignable, le lien simple reste utilisable.
      }
    })();
  }, []);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (!wrap.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  // Petite latence à la sortie : traverser le vide entre le lien et le panneau
  // ne doit pas refermer le menu.
  const scheduleClose = () => {
    closeTimer.current = setTimeout(() => setOpen(false), 180);
  };
  const cancelClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
  };

  if (departments.length === 0) {
    return <a href="/catalogue/">{t.label}</a>;
  }

  return (
    <div
      className="mm"
      ref={wrap}
      onMouseEnter={() => {
        cancelClose();
        setOpen(true);
      }}
      onMouseLeave={scheduleClose}
    >
      <button
        type="button"
        className={`mm-trigger${open ? " open" : ""}`}
        aria-expanded={open}
        aria-haspopup="true"
        onClick={() => setOpen((v) => !v)}
      >
        {t.label}
        <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
          <path d="M2 4l3 3 3-3" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      <div className={`mm-panel${open ? " show" : ""}`} role="menu" aria-hidden={!open}>
        <div className="mm-grid">
          {departments.map((d) => (
            <div className="mm-col" key={d.slug}>
              <span className="mm-dep">
                {d.name}
                <em>{t.products(d.count)}</em>
              </span>
              <ul>
                {d.categories.map((c) => (
                  <li key={c.slug}>
                    <a href={`/categorie/${c.slug}/`} onClick={() => setOpen(false)}>
                      {c.name}
                      <span>{c.count.toLocaleString("fr-FR")}</span>
                    </a>
                    {/* Troisième niveau : les quatre premiers sous-rayons
                        suffisent à donner la profondeur sans noyer la colonne. */}
                    {c.subcategories && c.subcategories.length > 0 && (
                      <ul className="mm-sub">
                        {c.subcategories.slice(0, 4).map((s) => (
                          <li key={s.name}>
                            <a
                              href={`/categorie/${c.slug}/?sub=${encodeURIComponent(s.name)}`}
                              onClick={() => setOpen(false)}
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
            </div>
          ))}
        </div>
        <a className="mm-all" href="/catalogue/" onClick={() => setOpen(false)}>
          {t.all} →
        </a>
      </div>
    </div>
  );
}
