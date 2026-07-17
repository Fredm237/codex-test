import type { ReactNode } from "react";
import { Container } from "@/components/ui/Container";
import { Button } from "@/components/ui/Button";

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 12.5, fontWeight: 600, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--text-dim)" }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--aqua)", boxShadow: "0 0 12px var(--aqua)" }} />
      {children}
    </span>
  );
}

const STATS = [
  { n: "12 M+", l: "consommateurs utilisent déjà le cashback en francophonie" },
  { n: "200–450 €", l: "économisés par foyer actif, chaque année" },
  { n: "50 %", l: "d'économie possible en cumulant reconditionné + cashback" },
  { n: "0 €", l: "pour vous — FILON est gratuit, aujourd'hui et demain" },
];

export function Stats() {
  return (
    <section style={{ padding: "70px 0 10px" }}>
      <Container>
        <div className="filon-stats" style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 24 }}>
          {STATS.map((s) => (
            <div key={s.l} style={{ paddingLeft: 18, borderLeft: "2px solid", borderImage: "var(--vein) 1" }}>
              <div className="mono" style={{ fontSize: "clamp(28px,4vw,40px)", fontWeight: 700, letterSpacing: "-0.03em", lineHeight: 1, marginBottom: 10 }}>{s.n}</div>
              <div style={{ fontSize: 14, color: "var(--text-dim)", lineHeight: 1.4 }}>{s.l}</div>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}

const STEPS = [
  { num: "01 — Détection", h: "Vous arrivez sur un produit", p: "FILON reconnaît l'article et lance une analyse silencieuse de toutes les sources d'économies." },
  { num: "02 — Comparaison", h: "FILON scanne tout, en direct", p: "Cashback, reconditionné équivalent, codes promo testés un par un, et prix chez 37+ marchands." },
  { num: "03 — Le filon", h: "Vous voyez le vrai prix", p: "Un seul chiffre : votre prix réel le plus bas, cumul d'économies inclus. Un clic pour l'appliquer." },
];

export function Steps() {
  return (
    <section id="comment" style={{ padding: "90px 0" }}>
      <Container>
        <div style={{ maxWidth: 680, marginBottom: 52 }}>
          <Eyebrow>Comment ça marche</Eyebrow>
          <h2 style={{ fontSize: "clamp(30px,4.4vw,50px)", margin: "16px 0" }}>Trois secondes. Zéro effort. Le meilleur prix, toujours.</h2>
          <p style={{ color: "var(--text-dim)", fontSize: 18 }}>
            FILON travaille en arrière-plan pendant que vous faites vos courses en ligne. Vous ne changez rien à vos habitudes — vous payez simplement moins cher.
          </p>
        </div>
        <div className="filon-steps" style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 20 }}>
          {STEPS.map((s) => (
            <div key={s.num} style={{ padding: 26, borderRadius: "var(--r-lg)", background: "var(--surface)", border: "1px solid var(--border)", position: "relative", overflow: "hidden" }}>
              <span style={{ position: "absolute", left: 0, top: 0, height: "100%", width: 3, background: "var(--vein)", opacity: 0.7 }} />
              <span className="mono" style={{ fontSize: 13, color: "var(--text-mute)", fontWeight: 600 }}>{s.num}</span>
              <h3 style={{ fontSize: 20, margin: "14px 0 9px" }}>{s.h}</h3>
              <p style={{ color: "var(--text-dim)", fontSize: 15 }}>{s.p}</p>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}

export function Transparency() {
  const items = [
    ["Rémunération affichée.", "Nous vous disons exactement comment FILON gagne de l'argent sur chaque recommandation."],
    ["Liens affiliés signalés.", "Chaque lien rémunéré est identifié — une exigence légale que nous traitons comme une promesse."],
    ["Zéro captation déloyale.", "FILON n'écrase jamais l'attribution d'un créateur ou d'un site. De la valeur seulement quand il y en a."],
    ["Vos données restent les vôtres.", "Pas de profil publicitaire, pas de revente. Conforme RGPD, par défaut."],
  ];
  return (
    <section id="transparence" style={{ padding: "90px 0" }}>
      <Container>
        <div style={{ maxWidth: 720 }}>
          <Eyebrow>Notre engagement</Eyebrow>
          <h2 style={{ fontSize: "clamp(28px,4.2vw,46px)", margin: "16px 0" }}>La transparence n&apos;est pas un argument. C&apos;est notre modèle.</h2>
          <p style={{ color: "var(--text-dim)", fontSize: 17 }}>
            Les affaires Honey et Phia ont montré comment certaines extensions détournaient les commissions au détriment des
            créateurs — et des utilisateurs. FILON prend le contre-pied, par principe et par construction.
          </p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 28 }} className="filon-grid2">
          {items.map(([b, s]) => (
            <div key={b} style={{ padding: 20, borderRadius: "var(--r-md)", background: "var(--surface)", border: "1px solid var(--border)", fontSize: 15, color: "var(--text-dim)" }}>
              <b style={{ color: "var(--text)" }}>{b}</b> {s}
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}

export function FinalCta() {
  return (
    <section id="installer" style={{ padding: "90px 0" }}>
      <Container>
        <div style={{ borderRadius: "var(--r-xl)", padding: "64px 40px", textAlign: "center", position: "relative", overflow: "hidden", border: "1px solid var(--border-2)", background: "linear-gradient(180deg, var(--surface-2), var(--surface))", boxShadow: "var(--shadow-soft)" }}>
          <div style={{ position: "absolute", inset: 0, background: "radial-gradient(80% 120% at 50% -20%, rgba(60,123,255,.22), transparent 60%)" }} />
          <div style={{ position: "relative" }}>
            <h2 style={{ fontSize: "clamp(30px,5vw,52px)", fontWeight: 620, marginBottom: 16 }}>
              N&apos;achetez plus jamais<br />sans avoir trouvé <span className="gradient-text">le filon.</span>
            </h2>
            <p style={{ color: "var(--text-dim)", fontSize: 18, maxWidth: 520, margin: "0 auto 30px" }}>
              Soyez prévenu·e du lancement de l&apos;extension et rejoignez les premiers à économiser sur chaque achat.
            </p>
            <Button href="/contact" style={{ padding: "15px 32px", fontSize: 16 }}>Rejoindre la liste d&apos;attente</Button>
          </div>
        </div>
      </Container>
    </section>
  );
}
