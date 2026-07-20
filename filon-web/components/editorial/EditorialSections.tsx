import { Reveal } from "./Reveal";

const STEPS = [
  ["i.", "Il reconnaît le produit", "Sur n'importe quelle page, il comprend ce que vous regardez. Vous ne changez rien à vos habitudes."],
  ["ii.", "Il regarde partout", "En une seconde, il a fait le tour du marché. Là où vous auriez passé une heure."],
  ["iii.", "Il tranche", "Un seul chiffre : votre vrai prix. Et une réponse : acheter, ou attendre."],
];

const PLEDGE = [
  ["01", "Rémunération affichée.", "Vous savez exactement ce que FILON perçoit sur chaque recommandation."],
  ["02", "Liens affiliés signalés.", "Toujours. Une exigence légale que nous traitons comme une promesse."],
  ["03", "Zéro captation déloyale.", "Nous n'écrasons jamais l'attribution d'un créateur ou d'un site."],
  ["04", "Vos données restent les vôtres.", "Pas de profil publicitaire, pas de revente. RGPD par défaut."],
];

const PARTNERS = ["iGraal", "Poulpeo", "Widilo", "Joko", "eBuyClub", "Back Market", "Rakuten"];

export function Method() {
  return (
    <section className="ed-band" id="comment">
      <div className="ed-wrap">
        <Reveal>
          <div className="ed-lead">
            <span className="idx">01 — 03</span>
            <h2>
              Trois secondes entre vous et <span className="it">le meilleur prix</span>.
            </h2>
          </div>
        </Reveal>
        <div className="ed-steps">
          {STEPS.map(([no, h, p]) => (
            <div className="ed-step" key={h}>
              <div className="no">{no}</div>
              <h3>{h}</h3>
              <p>{p}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function Transparency() {
  return (
    <section className="ed-band alt" id="transparence">
      <div className="ed-wrap">
        <div className="ed-mgrid">
          <Reveal className="ed-manifesto">
            <span className="eyebrow" style={{ display: "block", marginBottom: 24 }}>Notre serment</span>
            <h2>
              La transparence n&apos;est pas une promesse. C&apos;est le <span className="it">modèle</span>.
            </h2>
          </Reveal>
          <Reveal className="ed-mbody">
            <p>
              D&apos;autres ont promis de « ne jamais payer trop cher » — puis se sont fait prendre à détourner discrètement
              les commissions. La confiance ne se déclare pas : elle se prouve, ligne après ligne.
            </p>
            <p>
              Chez FILON, la manière dont nous gagnons de l&apos;argent est <b>écrite, visible, et alignée avec la vôtre</b>.
              Rien à cacher, par construction.
            </p>
            <div className="ed-pledge">
              {PLEDGE.map(([n, b, t]) => (
                <div key={n}>
                  <span>{n}</span>
                  <p><b>{b}</b> {t}</p>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

export function Partners() {
  return (
    <div className="ed-partners" aria-hidden="true">
      <div className="track">
        {[0, 1].flatMap((k) => PARTNERS.map((p) => <span key={`${k}-${p}`}>{p}</span>))}
      </div>
    </div>
  );
}

export function Closing() {
  return (
    <section className="ed-closing" id="installer">
      <div className="ed-wrap">
        <Reveal>
          <span className="eyebrow" style={{ display: "block", marginBottom: 26 }}>Ne payez plus jamais trop cher</span>
          <h2>
            Demandez à FILON <span className="it">avant d&apos;acheter.</span>
          </h2>
          <a className="ed-btn dark" href="/#top" style={{ marginTop: "clamp(34px,5vw,50px)" }}>
            Ajouter FILON — gratuit
          </a>
        </Reveal>
      </div>
    </section>
  );
}
