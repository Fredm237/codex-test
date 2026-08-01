export type VerdictData = {
  level: string;
  headline: string;
  reasons: string[];
  tracked_days: number;
  samples: number;
  confidence: string;
};

const CONFIDENCE_LABEL: Record<string, string> = {
  faible: "confiance faible",
  moyenne: "confiance moyenne",
  bonne: "bonne confiance",
};

/** Le verdict FILON : la conclusion, avant le détail des offres.
 *
 *  L'ampleur du suivi est affichée avec le verdict, pas cachée : une conclusion
 *  tirée de trois jours de relevés ne vaut pas celle tirée de six mois, et
 *  l'utilisateur doit pouvoir en juger.
 */
export function Verdict({ v }: { v: VerdictData }) {
  if (!v) return null;
  const level = ["excellent", "bon", "neutre", "attendre", "insuffisant"].includes(v.level)
    ? v.level
    : "neutre";

  return (
    <section className={`vd vd-${level}`} aria-label="Verdict FILON">
      <span className="vd-eyebrow">Verdict FILON</span>
      <div className="vd-head">
        <span className="vd-dot" aria-hidden="true" />
        <b className="vd-title">{v.headline}</b>
      </div>
      {v.reasons?.length > 0 && (
        <ul className="vd-reasons">
          {v.reasons.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ul>
      )}
      {v.samples > 0 && (
        <p className="vd-meta">
          {v.samples} relevé{v.samples > 1 ? "s" : ""} sur {v.tracked_days} jour
          {v.tracked_days > 1 ? "s" : ""} · {CONFIDENCE_LABEL[v.confidence] ?? v.confidence}
        </p>
      )}
    </section>
  );
}
