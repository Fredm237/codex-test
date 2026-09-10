"use client";

import Link from "next/link";
import type { Proof } from "@/lib/proof";
import type { Department, Offer } from "@/lib/catalogue";
import { useLocale } from "@/lib/i18n";
import { catalogueLabel } from "@/lib/catalogue-labels";
import { ProductCard } from "@/components/filon/ProductCard";

const COPY = {
 fr: { tag:"L’instinct d’achat. Augmenté.", title:"Le bon choix", end:"commence ici.", intro:"Des envies aux bonnes références. Explorez, comparez et trouvez ce qui vous correspond.", label:"Que cherchez-vous ?", placeholder:"Un produit, une envie, un besoin…", go:"Explorer", quick:["Un casque pour voyager", "Un ordinateur pour créer", "Aménager mon bureau"], universes:"À chaque envie, son univers.", all:"Tout le catalogue", offers:"À découvrir dans le catalogue", offersSub:"Les offres disponibles, avec leurs sources et leurs dates de relevé.", empty:"Votre prochaine trouvaille vous attend.", emptySub:"Parcourez les rayons ou décrivez ce que vous cherchez à l’assistant.", step:"Votre prochain achat, sous un autre angle.", steps:[["Exprimez votre envie.","Une référence précise ou une idée encore floue : commencez là où vous en êtes."],["Explorez les possibilités.","Parcourez les offres et consultez les informations disponibles sur chaque produit."],["Choisissez en connaissance de cause.","Comparez les références, les prix observés et leurs sources avant de rejoindre le marchand."]], assistant:"Moins d’hésitation. Plus de possibilités.", assistantSub:"Expliquez votre usage, votre budget, vos priorités. L’assistant vous aide à explorer les offres du catalogue.", ask:"Parler à FILON", method:"Comprendre la méthode", merchants:"marchands indexés", count:"offres indexées", editorial:"L’envie est à vous. Le recul aussi.", editorialSub:"Nos guides pour regarder au-delà du prix affiché.", read:"Lire le guide", guides:["Choisir l’ordinateur qui vous correspond", "Neuf ou reconditionné : que comparer ?"], explore:"Explorer un univers" },
 nl: { tag:"Koopinstinct. Versterkt.", title:"De juiste keuze", end:"begint hier.", intro:"Van wens naar het juiste product. Ontdek, vergelijk en vind wat bij u past.", label:"Wat zoekt u?", placeholder:"Een product, een wens, een behoefte…", go:"Ontdekken", quick:["Koptelefoon voor onderweg", "Laptop om te creëren", "Mijn bureau inrichten"], universes:"Voor elke wens een wereld.", all:"De volledige catalogus", offers:"Ontdek de catalogus", offersSub:"Beschikbare aanbiedingen, met bronnen en waarnemingsdata.", empty:"Uw volgende ontdekking wacht.", emptySub:"Bekijk de categorieën of vertel de assistent wat u zoekt.", step:"Een andere kijk op uw volgende aankoop.", steps:[["Vertel wat u zoekt.","Een precies product of een eerste idee: begin waar u bent."],["Ontdek de mogelijkheden.","Bekijk aanbiedingen en de beschikbare productinformatie."],["Kies met inzicht.","Vergelijk referenties, waargenomen prijzen en bronnen voordat u naar de winkel gaat."]], assistant:"Minder twijfel. Meer mogelijkheden.", assistantSub:"Beschrijf uw gebruik, budget en prioriteiten. De assistent helpt u de catalogus te verkennen.", ask:"Praat met FILON", method:"Onze methode", merchants:"geïndexeerde winkels", count:"geïndexeerde aanbiedingen", editorial:"Uw wens. Uw perspectief.", editorialSub:"Onze gidsen kijken verder dan de getoonde prijs.", read:"Lees de gids", guides:["De juiste laptop kiezen", "Nieuw of refurbished: wat vergelijken?"], explore:"Ontdek een categorie" },
 en: { tag:"Shopping instinct. Amplified.", title:"The right choice", end:"starts here.", intro:"From a spark of interest to the right product. Explore, compare and find what fits you.", label:"What are you looking for?", placeholder:"A product, a wish, a need…", go:"Explore", quick:["Headphones for travelling", "A laptop for creating", "Set up my desk"], universes:"A world for every wish.", all:"The full catalogue", offers:"Discover the catalogue", offersSub:"Available offers, with their sources and observation dates.", empty:"Your next find is out there.", emptySub:"Explore the departments or tell the assistant what you need.", step:"A fresh angle on your next purchase.", steps:[["Tell us what you want.","An exact reference or a first idea: start wherever you are."],["Explore the possibilities.","Browse offers and the available information for each product."],["Choose with clarity.","Compare references, observed prices and their sources before visiting the merchant."]], assistant:"Less hesitation. More possibilities.", assistantSub:"Share your needs, budget and priorities. The assistant helps you explore the catalogue.", ask:"Talk to FILON", method:"Our method", merchants:"indexed merchants", count:"indexed offers", editorial:"Your curiosity. Your perspective.", editorialSub:"Our guides look beyond the price tag.", read:"Read the guide", guides:["Choose the laptop that fits you", "New or refurbished: what to compare?"], explore:"Explore a department" },
} as const;

export function CommerceJourney({ proof, departments = [], offers = [] }: { proof: Proof | null; departments?: Department[]; offers?: Offer[] }) {
 const { locale } = useLocale();
 const c = COPY[locale];
 const number = new Intl.NumberFormat(locale === "fr" ? "fr-BE" : locale === "nl" ? "nl-BE" : "en-GB");
 return <div className="fn-home">
   <section className="fn-hero" aria-labelledby="filon-home-title">
     <div className="fn-hero-copy">
       <p className="fn-kicker"><span className="fn-live-dot" />{c.tag}</p>
       <h1 id="filon-home-title">{c.title}<br /><em>{c.end}</em></h1>
       <p className="fn-hero-intro">{c.intro}</p>
       <form className="fn-search" action="/recherche/" method="get" role="search">
         <label className="fx-sr" htmlFor="home-commerce-query">{c.label}</label>
         <svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></svg>
         <input id="home-commerce-query" name="q" type="search" required minLength={2} placeholder={c.placeholder} />
         <button type="submit">{c.go}<span aria-hidden="true">↗</span></button>
       </form>
       <div className="fn-suggestions">{c.quick.map(q=><Link href={`/recherche/?q=${encodeURIComponent(q)}`} key={q}>{q}<span aria-hidden="true">↗</span></Link>)}</div>
     </div>
     <div className="fn-home-world-slot" aria-hidden="true" />
     <div className="fn-hero-bottom"><span>01 — DISCOVER YOUR NEXT</span><Link href="#universes">{c.explore}<span aria-hidden="true">↓</span></Link></div>
   </section>
   <section className="fn-section fn-universes" id="universes">
     <div className="fn-section-head"><div><span className="fn-kicker">02 / EXPLORE</span><h2>{c.universes}</h2></div><Link className="fn-text-link" href="/catalogue/">{c.all} ↗</Link></div>
     {departments.length > 0 ? <div className="fn-departments">{departments.slice(0,8).map((d,i)=><Link className="fn-department" href={`/catalogue/?dept=${encodeURIComponent(d.slug)}`} key={d.slug}><span className="fn-department-index">0{i+1}</span><h3>{catalogueLabel(d.name,locale)}</h3><span className="fn-department-arrow" aria-hidden="true">↗</span></Link>)}</div> : <Link className="fn-empty" href="/catalogue/"><h3>{c.empty}</h3><p>{c.emptySub}</p><span>{c.all} ↗</span></Link>}
   </section>
   <section className="fn-section fn-discovery">
     <div className="fn-section-head"><div><span className="fn-kicker">03 / THE FINDS</span><h2>{c.offers}</h2><p>{c.offersSub}</p></div><Link className="fn-text-link" href="/catalogue/">{c.all} ↗</Link></div>
     {offers.length > 0 ? <div className="fn-offers">{offers.map(offer=><ProductCard key={offer.id} offer={offer} showEvidence />)}</div> : <div className="fn-empty"><p>{c.emptySub}</p><Link className="fn-button" href="/recherche/">{c.ask} ↗</Link></div>}
   </section>
   <section className="fn-assistant-banner fn-section"><span className="fn-kicker">FILON / INTELLIGENCE</span><div><h2>{c.assistant}</h2><div><p>{c.assistantSub}</p><Link className="fn-button" href="/recherche/">{c.ask}<span aria-hidden="true">↗</span></Link></div></div></section>
   <section className="fn-section fn-method"><div className="fn-section-head"><div><span className="fn-kicker">04 / THE PERSPECTIVE</span><h2>{c.step}</h2></div><Link className="fn-text-link" href="/comment-ca-marche/">{c.method} ↗</Link></div><div className="fn-method-grid">{c.steps.map(([title,description],i)=><article key={title}><span>0{i+1}</span><h3>{title}</h3><p>{description}</p></article>)}</div></section>
   <section className="fn-section fn-reading"><div className="fn-section-head"><div><span className="fn-kicker">05 / FIELD NOTES</span><h2>{c.editorial}</h2><p>{c.editorialSub}</p></div><Link className="fn-text-link" href="/blog/">Journal ↗</Link></div><div className="fn-guides">{["choisir-ordinateur-portable","neuf-vs-reconditionne-economie-reelle"].map((slug,i)=><Link key={slug} href={`/blog/${slug}/`} className="fn-guide"><span className="fn-guide-number">0{i+1}</span><div><h3>{c.guides[i]}</h3><span>{c.read} ↗</span></div></Link>)}</div></section>
   {proof && <aside className="fn-stats"><div><strong>{number.format(proof.stats.offers)}</strong><span>{c.count}</span></div><div><strong>{number.format(proof.stats.merchants)}</strong><span>{c.merchants}</span></div><div className="fn-stats-signature">FILON<span>MAKE ROOM FOR BETTER.</span></div></aside>}
 </div>;
}
