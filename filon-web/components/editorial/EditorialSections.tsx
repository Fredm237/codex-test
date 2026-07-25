import { Reveal } from "./Reveal";

const STEP_ICONS = [
  // Reconnaît le produit — cadre de scan
  <svg key="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8" />
    <path d="M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8" />
    <path d="M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16" />
    <path d="M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16" />
    <rect x="9" y="9" width="6" height="6" rx="1.4" />
  </svg>,
  // Regarde partout — globe
  <svg key="ii" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="8.2" />
    <path d="M12 3.8v16.4M3.8 12h16.4" />
    <ellipse cx="12" cy="12" rx="4" ry="8.2" />
  </svg>,
  // Tranche — verdict validé
  <svg key="iii" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="8.2" />
    <path d="M8.5 12.2 11 14.7 15.7 9.6" />
  </svg>,
];

const STEPS = [
  ["Il reconnaît le produit", "Sur n'importe quelle page, il comprend ce que vous regardez."],
  ["Il regarde partout", "En une seconde, tout le marché passé au crible."],
  ["Il tranche", "Un chiffre : votre vrai prix. Une réponse : acheter, ou attendre."],
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
          {STEPS.map(([h, p], i) => (
            <Reveal className="ed-step" key={h} style={{ transitionDelay: `${i * 90}ms` }}>
              <span className="ed-step-ico">{STEP_ICONS[i]}</span>
              <h3>{h}</h3>
              <p>{p}</p>
            </Reveal>
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
          <a className="ed-btn dark" href="/recherche" style={{ marginTop: "clamp(34px,5vw,50px)" }}>
            Essayer le copilote
          </a>
        </Reveal>
      </div>
    </section>
  );
}
