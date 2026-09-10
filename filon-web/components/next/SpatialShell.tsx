"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { World } from "./World";
import { useLocale } from "@/lib/i18n";

export type WorldMode = "home" | "catalogue" | "assistant" | "product" | "editorial";
export function worldMode(path: string): WorldMode {
 if (path === "/") return "home";
 if (/^\/(produit|produits)\//.test(path)) return "product";
 if (/^\/(catalogue|categorie|marchands)(\/|$)/.test(path)) return "catalogue";
 if (/^\/(recherche|creer)(\/|$)/.test(path)) return "assistant";
 return "editorial";
}

/** One persistent WebGL world across routes; HTML remains the accessible control plane. */
export function SpatialShell({ children }: { children: ReactNode }) {
 const pathname = usePathname();
 const mode = worldMode(pathname);
 const shell = useRef<HTMLDivElement>(null);
 const { locale } = useLocale();
 const c = {
  fr:{world:"Votre espace d’exploration",home:"Accueil",catalogue:"Explorer",assistant:"Assistant",journal:"Journal",chapter:{home:"Découvrir",catalogue:"Explorer les possibilités",assistant:"Donner forme à vos envies",product:"Observer sous tous les angles",editorial:"Prendre du recul"}},
  nl:{world:"Uw ontdekkingsruimte",home:"Start",catalogue:"Ontdekken",assistant:"Assistent",journal:"Journal",chapter:{home:"Ontdekken",catalogue:"Mogelijkheden verkennen",assistant:"Geef uw wensen vorm",product:"Van alle kanten bekijken",editorial:"Een nieuw perspectief"}},
  en:{world:"Your exploration space",home:"Home",catalogue:"Explore",assistant:"Assistant",journal:"Journal",chapter:{home:"Discover",catalogue:"Explore the possibilities",assistant:"Give your wishes shape",product:"Look from every angle",editorial:"A fresh perspective"}},
 }[locale];
 useEffect(() => {
  const el=shell.current;
  if(!el)return;
  let frame=0;
  const update=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>el.style.setProperty("--fn-scroll",String(Math.min(1,window.scrollY/650))));};
  update();window.addEventListener("scroll",update,{passive:true});
  return()=>{cancelAnimationFrame(frame);window.removeEventListener("scroll",update);};
 },[]);
 useEffect(()=>{
  const root=shell.current;
  if(!root)return;
  const media=matchMedia("(prefers-reduced-motion: reduce)");
  let card:HTMLElement|null=null;
  let frame=0;
  const reset=()=>{if(card){card.style.removeProperty("--fn-rx");card.style.removeProperty("--fn-ry");card=null;}};
  const move=(event:PointerEvent)=>{
   if(event.pointerType!=="mouse"||media.matches)return;
   const next=(event.target as HTMLElement).closest<HTMLElement>(".fx-product,.fn-department,.fn-guide,.fn-spatial-card");
   if(next!==card){reset();card=next;}
   if(!card)return;
   const node=card,rect=node.getBoundingClientRect();
   cancelAnimationFrame(frame);
   frame=requestAnimationFrame(()=>{if(card!==node)return;node.style.setProperty("--fn-rx",`${-(event.clientY-rect.top-rect.height/2)/rect.height*6}deg`);node.style.setProperty("--fn-ry",`${(event.clientX-rect.left-rect.width/2)/rect.width*7}deg`);});
  };
  root.addEventListener("pointermove",move,{passive:true});root.addEventListener("pointerleave",reset);
  return()=>{cancelAnimationFrame(frame);reset();root.removeEventListener("pointermove",move);root.removeEventListener("pointerleave",reset);};
 },[]);
 return <div className="fn-spatial-shell" data-world={mode} ref={shell}>
  <div className="fn-global-world"><World mode={mode}/></div>
  <div className="fn-spatial-content">
   {mode!=="home"&&<div className="fn-world-chapter"><span>FILON / {mode.toUpperCase()}</span><p>{c.chapter[mode]}</p><span className="fn-chapter-orbit" aria-hidden="true">↗</span></div>}
   {children}
  </div>
  <nav className="fn-world-dock" aria-label={c.world}>
   <Link href="/" aria-current={mode==="home"?"page":undefined}><span aria-hidden="true">⌂</span>{c.home}</Link>
   <Link href="/catalogue/" aria-current={mode==="catalogue"?"page":undefined}><span aria-hidden="true">⊞</span>{c.catalogue}</Link>
   <Link href="/recherche/" aria-current={mode==="assistant"?"page":undefined}><span aria-hidden="true">✳</span>{c.assistant}</Link>
   <Link href="/blog/" aria-current={pathname.startsWith("/blog")?"page":undefined}><span aria-hidden="true">≡</span>{c.journal}</Link>
  </nav>
 </div>;
}
