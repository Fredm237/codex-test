import { Reveal } from "./Reveal";

const STEPS = [
  ["i.", "Il reconnaît le produit", "Sur n'importe quelle page, il comprend ce que vous regardez. Vous ne changez rien à vos habitudes."],
  ["ii.", "Il regarde partout", "En une seconde, il a fait le tour du marché. Là où vous auriez passé une heure."],
  ["iii.", "Il tranche", "Un seul chiffre : votre vrai prix. Et une réponse : acheter, ou attendre."],
];

const PLEDGE = [
  ["01", "De votre côté.", "Aucune marque ne peut acheter sa place dans un conseil FILON."],
  ["02", "Sans publicité.", "Rien ne vient troubler la réponse que vous recevez."],
  ["03", "Vos données restent les vôtres.", "Pas de profil publicitaire, pas de revente. RGPD par défaut."],
  ["04", "Gratuit, pour de vrai.", "Aucune carte, aucun abonnement. Vous ne payez jamais."],
];

export function Method() {
  return (
    <section className="ed-band" id="comment">
      <div className="ed-wrap">
        <Reveal>
          <div className="ed-lead">
            <span className="idx">3 étapes</span>
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
            <span className="eyebrow" style={{ display: "block", marginBottom: 24 }}>Notre principe</span>
            <h2>
              De votre côté. <span className="it">Uniquement.</span>
            </h2>
          </Reveal>
          <Reveal className="ed-mbody">
            <p>
              FILON travaille pour vous, pas pour une marque. Ce qu&apos;il vous montre, c&apos;est ce qui est vraiment le
              mieux pour vous. Rien d&apos;autre n&apos;entre en jeu.
            </p>
            <p>
              La confiance ne se déclare pas. Elle se prouve, à chaque conseil.
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
            Ajouter gratuitement
          </a>
        </Reveal>
      </div>
    </section>
  );
}
