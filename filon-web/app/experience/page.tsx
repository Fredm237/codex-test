import type { Metadata } from "next";
import "./experience.css";
import { buildMetadata } from "@/lib/seo";
import { SmoothScroll } from "@/components/immersive/SmoothScroll";
import { ShaderBackground } from "@/components/immersive/ShaderBackground";
import { Cursor } from "@/components/immersive/Cursor";
import { ScrollProgress } from "@/components/immersive/ScrollProgress";
import { ImmersiveHero } from "@/components/immersive/ImmersiveHero";
import { Reveal } from "@/components/immersive/Reveal";
import { Counter } from "@/components/immersive/Counter";
import { Logo } from "@/components/site/Logo";

export const metadata: Metadata = buildMetadata({
  path: "/experience",
  title: "L'expérience",
  description:
    "L'expérience immersive FILON : fond WebGL vivant, smooth-scroll, storytelling. Ne payez plus jamais le prix fort.",
});

export default function ExperiencePage() {
  return (
    <div className="fx-root">
      <ShaderBackground />
      <div className="fx-vignette" aria-hidden="true" />
      <Cursor />
      <ScrollProgress />
      <SmoothScroll>
        <nav className="fx-nav">
          <a className="fx-brand" href="#top">
            <Logo size={28} />
            FILON
          </a>
          <div className="fx-nav-cta">
            <a className="fx-navlink" data-hover href="#story">Le principe</a>
            <a className="fx-navlink" data-hover href="#features">Ce que ça change</a>
            <a className="fx-btn fx-solid" data-hover href="#final">Installer</a>
          </div>
        </nav>

        <main id="top">
          <ImmersiveHero />

          <section className="fx-story wrap" id="story">
            <Reveal>
              <span className="fx-ey"><span className="fx-d" /> Le principe</span>
              <h2>Une veine d&apos;économies invisible. FILON la fait remonter.</h2>
              <p className="fx-lead">
                Un <em style={{ color: "#f3f6ff", fontStyle: "normal" }}>filon</em>, c&apos;est le bon plan que personne
                ne voit. Aujourd&apos;hui il est éclaté entre dix services. FILON le réunit en un seul geste — et le rend limpide.
              </p>
            </Reveal>
          </section>

          <section className="wrap" id="features" style={{ paddingBottom: 40 }}>
            <Reveal>
              <div style={{ maxWidth: 640, marginBottom: 52 }}>
                <span className="fx-ey"><span className="fx-d" /> Ce que ça change</span>
                <h2 style={{ fontSize: "clamp(30px,4.6vw,56px)", marginTop: 18, letterSpacing: "-0.035em" }}>
                  Dix onglets, remplacés par un réflexe.
                </h2>
              </div>
            </Reveal>
            <Reveal className="fx-panels" stagger>
              <div className="fx-panel fx-p7">
                <div>
                  <div className="fx-ico">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2ZM9 21h6" strokeLinecap="round" strokeLinejoin="round" /></svg>
                  </div>
                  <h3>Une IA qui cherche à votre place</h3>
                  <p>Cashback, reconditionné, promos et prix marchands croisés en temps réel — puis le meilleur cumul, calculé pour vous.</p>
                </div>
                <div className="fx-big-n gradient-text">
                  <Counter to={4} suffix=" sources" />
                </div>
              </div>
              <div className="fx-panel fx-p5">
                <div className="fx-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" strokeLinecap="round" /></svg></div>
                <h3>Toujours le meilleur taux</h3>
                <p>iGraal, Poulpeo, Widilo, Joko, eBuyClub — comparés, et le plus rémunérateur appliqué automatiquement.</p>
              </div>
              <div className="fx-panel fx-p5">
                <div className="fx-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5" strokeLinecap="round" strokeLinejoin="round" /></svg></div>
                <h3>Le même produit, moins cher</h3>
                <p>Le reconditionné équivalent, vérifié et garanti — souvent 40 % sous le neuf, cashback en plus.</p>
              </div>
              <div className="fx-panel fx-p7">
                <div>
                  <div className="fx-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 9h.01M15 15h.01M16 8l-8 8M4 7v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7" strokeLinecap="round" /></svg></div>
                  <h3>La transparence, par construction</h3>
                  <p>Chaque lien affilié est signalé, notre rémunération affichée, vos données jamais revendues. Après Honey et Phia, c&apos;est le seul modèle qui tient.</p>
                </div>
              </div>
            </Reveal>
          </section>

          <div className="fx-mq" aria-hidden="true">
            <div className="fx-mq-row">
              {Array.from({ length: 2 }).flatMap((_, k) =>
                ["iGraal", "Poulpeo", "Widilo", "Joko", "eBuyClub", "Back Market", "Rakuten"].map((s) => (
                  <span key={`${k}-${s}`}>{s} ·</span>
                ))
              )}
            </div>
          </div>

          <section className="fx-final wrap" id="final">
            <Reveal>
              <h2>Trouvez le filon.<br /><span className="gradient-text">Avant tout le monde.</span></h2>
              <p>Soyez parmi les premiers à ne plus jamais payer le prix fort.</p>
              <div style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}>
                <a className="fx-btn fx-solid fx-big" data-hover href="#top">Ajouter à mon navigateur</a>
                <a className="fx-btn fx-line-btn fx-big" data-hover href="#story">Comment ça marche</a>
              </div>
            </Reveal>
          </section>

          <footer className="fx-footer wrap">
            <div className="fx-foot-in">
              <span className="fx-brand" style={{ fontSize: 17 }}><Logo size={24} /> FILON</span>
              <span>© 2026 · Conçu à Bruxelles, pour la francophonie.</span>
            </div>
            <p className="fx-foot-discl">
              FILON est gratuit. Certains liens sont affiliés — lorsque vous activez une offre via FILON, la plateforme
              partenaire nous reverse une part de sa commission d&apos;apport. Cela n&apos;augmente jamais votre prix. Nous
              ne revendons aucune donnée de navigation.
            </p>
          </footer>
        </main>
      </SmoothScroll>
    </div>
  );
}
