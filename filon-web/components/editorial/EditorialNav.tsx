"use client";
import { useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandLogo } from "./Brand";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { ThemeToggle } from "./ThemeToggle";
import { MegaMenu } from "./MegaMenu";
import { useLocale } from "@/lib/i18n";
import type { Department } from "@/lib/catalogue";
import { catalogueLabel } from "@/lib/catalogue-labels";

export function EditorialNav({ departments = [] }: { departments?: Department[] }) {
 const { locale } = useLocale();
 const path = usePathname();
 const dialog = useRef<HTMLDialogElement>(null);
 const trigger = useRef<HTMLButtonElement>(null);
 const text = {
  fr:{links:["Explorer","L’assistant","La méthode","Journal"], open:"Ouvrir le menu",close:"Fermer le menu",go:"Trouver mon prochain achat",menu:"Navigation",categories:"Les univers"},
  nl:{links:["Ontdekken","De assistent","Onze methode","Journal"],open:"Menu openen",close:"Menu sluiten",go:"Vind mijn volgende aankoop",menu:"Navigatie",categories:"Categorieën"},
  en:{links:["Explore","The assistant","Our method","Journal"],open:"Open menu",close:"Close menu",go:"Find my next purchase",menu:"Navigation",categories:"Departments"},
 }[locale];
 const links=["/catalogue/","/recherche/","/comment-ca-marche/","/blog/"];
 const close=()=>{dialog.current?.close(); trigger.current?.focus();};
 useEffect(()=>{dialog.current?.close();},[path]);
 useEffect(()=>()=>{document.body.style.overflow="";},[]);
 return <>
  <header className="fn-header"><nav className="fn-nav" aria-label={text.menu}>
   <BrandLogo />
   <div className="fn-nav-links"><MegaMenu initialDepartments={departments} />{links.slice(1).map((href,i)=><Link href={href} key={href} aria-current={path.replace(/\/$/,"")===href.replace(/\/$/,"")?"page":undefined}>{text.links[i+1]}</Link>)}</div>
   <div className="fn-nav-tools"><ThemeToggle /><LanguageSwitcher /><Link className="fn-nav-action" href="/recherche/" aria-label={text.go}>↗</Link><button ref={trigger} className="fn-menu-button" type="button" aria-label={text.open} aria-haspopup="dialog" aria-controls="filon-navigation" onClick={()=>{dialog.current?.showModal();document.body.style.overflow="hidden";}}><span /><span /></button></div>
  </nav></header>
  <dialog ref={dialog} id="filon-navigation" className="fn-menu" aria-label={text.menu} onClose={()=>{document.body.style.overflow="";}} onClick={e=>{if(e.target===e.currentTarget)close();}}>
   <div className="fn-menu-top"><BrandLogo onClick={close}/><button autoFocus onClick={close} aria-label={text.close}>×</button></div>
   <nav>{links.map((href,i)=><Link key={href} href={href} onClick={close}><small>0{i+1}</small>{text.links[i]}<span>↗</span></Link>)}</nav>
   <div className="fn-menu-categories"><p className="fn-kicker">{text.categories}</p>{departments.map(d=><Link key={d.slug} href={`/catalogue/?dept=${encodeURIComponent(d.slug)}`} onClick={close}>{catalogueLabel(d.name,locale)} ↗</Link>)}</div>
   <div className="fn-menu-preferences"><ThemeToggle compact/><LanguageSwitcher /></div>
  </dialog>
 </>;
}
