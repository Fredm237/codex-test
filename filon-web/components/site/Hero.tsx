"use client";

import { useState, useCallback, type CSSProperties } from "react";
import { Container } from "@/components/ui/Container";
import { Button } from "@/components/ui/Button";

type SourceKey = "cashback" | "recond" | "promo" | "price";

const SOURCES: { key: SourceKey; title: string; sub: string; val: string }[] = [
  { key: "cashback", title: "Cashback", sub: "42 programmes analysés", val: "+6,5 %" },
  { key: "recond", title: "Reconditionné", sub: "Grade A+ · garanti 24 mois", val: "−94 €" },
  { key: "promo", title: "Codes promo", sub: "Testés en direct, 3 valides", val: "−15 €" },
  { key: "price", title: "Comparateur prix", sub: "37 marchands en temps réel", val: "379 €" },
];

const CHIPS = ["iPhone 15 Pro", "Dyson V15", "Nike Air Max", "MacBook Air M3"];

export function Hero() {
  const [query, setQuery] = useState("Sony WH-1000XM5");
  const [revealed, setRevealed] = useState<number>(0);
  const [done, setDone] = useState(false);

  const runScan = useCallback((value: string) => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setDone(false);
    setRevealed(0);
    if (reduce) {
      setRevealed(SOURCES.length);
      setDone(true);
      return;
    }
    let i = 0;
    const tick = () => {
      i += 1;
      setRevealed(i);
      if (i < SOURCES.length) {
        window.setTimeout(tick, 420);
      } else {
        window.setTimeout(() => setDone(true), 300);
      }
    };
    window.setTimeout(tick, 300);
  }, []);

  const total = 90 + ((query.length || 8) * 7) % 120;

  const card: CSSProperties = {
    position: "relative",
    borderRadius: "var(--r-xl)",
    padding: 20,
    background: "linear-gradient(180deg, var(--surface-2), var(--surface))",
    border: "1px solid var(--border-2)",
    boxShadow: "var(--shadow-soft)",
    backdropFilter: "blur(18px)",
  };

  return (
    <section style={{ padding: "78px 0 40px" }}>
      <Container>
        <div className="filon-hero-grid" style={{ display: "grid", gridTemplateColumns: "1.05fr .95fr", gap: 48, alignItems: "center" }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 10, padding: "7px 8px 7px 14px", borderRadius: "var(--r-full)", background: "var(--surface)", border: "1px solid var(--border)", fontSize: 13, color: "var(--text-dim)", marginBottom: 26 }}>
              <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 9px", borderRadius: "var(--r-full)", color: "#05121f", background: "var(--vein)" }}>Nouveau</span>
              L&apos;assistant qui trouve <b style={{ color: "var(--text)" }}>&nbsp;le filon&nbsp;</b> avant chaque achat
            </div>
            <h1 style={{ fontSize: "clamp(44px, 7vw, 88px)", fontWeight: 620, marginBottom: 22 }}>
              Le réflexe malin
              <br />
              <span className="gradient-text">avant chaque achat.</span>
            </h1>
            <p style={{ fontSize: "clamp(17px, 2vw, 21px)", color: "var(--text-dim)", maxWidth: 620, marginBottom: 34, lineHeight: 1.5 }}>
              FILON compare automatiquement le meilleur cashback, le meilleur prix en reconditionné et les codes promo qui marchent
              vraiment — en une seconde, sans quitter votre panier. Vous n&apos;achetez plus jamais au prix fort.
            </p>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <Button href="/#installer" style={{ padding: "15px 28px", fontSize: 16 }}>Ajouter à mon navigateur</Button>
              <Button href="/comment-ca-marche" variant="ghost" style={{ padding: "15px 28px", fontSize: 16 }}>Voir comment ça marche</Button>
            </div>
          </div>

          <div style={card} role="region" aria-label="Démonstration : FILON compare les sources d'économies">
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <span style={{ display: "flex", gap: 6 }}>
                {[0, 1, 2].map((n) => (
                  <i key={n} style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--border-2)" }} />
                ))}
              </span>
              <span className="mono" style={{ marginLeft: 6, fontSize: 12, color: "var(--text-mute)" }}>filon.app/scan</span>
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                runScan(query);
              }}
              style={{ display: "flex", gap: 8, alignItems: "center", padding: "6px 6px 6px 16px", borderRadius: "var(--r-full)", background: "var(--bg-2)", border: "1px solid var(--border-2)" }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-mute)" strokeWidth="2">
                <circle cx="11" cy="11" r="7" />
                <path d="m21 21-4.3-4.3" strokeLinecap="round" />
              </svg>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Produit à comparer"
                style={{ flex: 1, background: "transparent", border: 0, color: "var(--text)", fontFamily: "inherit", fontSize: 15, outline: "none", padding: "9px 0" }}
              />
              <button type="submit" className="filon-btn" style={{ padding: "9px 16px", fontSize: 13.5, fontWeight: 600, borderRadius: "var(--r-full)", border: 0, color: "#05121f", background: "var(--vein)", boxShadow: "var(--shadow-glow)", cursor: "pointer" }}>
                Trouver le filon
              </button>
            </form>

            <div style={{ display: "flex", gap: 7, flexWrap: "wrap", marginTop: 12 }}>
              {CHIPS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => {
                    setQuery(c);
                    runScan(c);
                  }}
                  style={{ fontSize: 12.5, padding: "6px 12px", borderRadius: "var(--r-full)", background: "var(--surface)", border: "1px solid var(--border)", color: "var(--text-dim)", cursor: "pointer" }}
                >
                  {c}
                </button>
              ))}
            </div>

            <div style={{ marginTop: 14, display: "grid", gap: 8 }}>
              {SOURCES.map((s, i) => {
                const active = i < revealed;
                return (
                  <div
                    key={s.key}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      padding: "12px 14px",
                      borderRadius: "var(--r-md)",
                      background: "var(--surface)",
                      border: `1px solid ${active ? "var(--border-2)" : "var(--border)"}`,
                      opacity: active ? 1 : 0.4,
                      transform: active ? "none" : "translateY(4px)",
                      transition: "opacity .4s var(--ease-out), transform .4s var(--ease-out), border-color .4s",
                    }}
                  >
                    <span style={{ width: 34, height: 34, borderRadius: 10, display: "grid", placeItems: "center", background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--aqua-2)", fontFamily: "var(--font-mono)", fontSize: 13 }}>
                      {s.title.charAt(0)}
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13.5, fontWeight: 600 }}>{s.title}</div>
                      <div style={{ fontSize: 12, color: "var(--text-mute)" }}>{s.sub}</div>
                    </div>
                    <div className="mono" style={{ fontSize: 14, fontWeight: 600, color: active ? "var(--pos)" : "var(--text-mute)" }}>
                      {active ? s.val : "…"}
                    </div>
                  </div>
                );
              })}
            </div>

            {done && (
              <div style={{ marginTop: 12, padding: "16px 18px", borderRadius: "var(--r-lg)", background: "var(--pos-dim)", border: "1px solid color-mix(in srgb, var(--pos) 40%, transparent)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
                  <span style={{ fontSize: 12.5, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 600 }}>Économie totale trouvée</span>
                  <span className="mono" style={{ fontSize: 30, fontWeight: 700, color: "var(--pos)", letterSpacing: "-0.03em" }}>{total} €</span>
                </div>
                <div style={{ fontSize: 13, color: "var(--text-dim)", marginTop: 4 }}>
                  Le meilleur cumul cashback + reconditionné + promo, calculé en 0,8 s.
                </div>
              </div>
            )}
          </div>
        </div>
      </Container>
    </section>
  );
}
