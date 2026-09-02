import type { ReactNode } from "react";

export type EvidenceState = "verified" | "warning" | "unknown";

export function EvidenceBadge({
  state,
  children,
}: {
  state: EvidenceState;
  children: ReactNode;
}) {
  return (
    <span className={`p11EvidenceBadge is-${state}`} data-evidence-state={state}>
      <span aria-hidden="true" />
      {children}
    </span>
  );
}

export function ConfidenceIndicator({
  calibrated,
  label,
  statusLabel,
}: {
  calibrated: boolean;
  label: string;
  statusLabel: string;
}) {
  return (
    <span
      className={`p11Confidence is-${calibrated ? "verified" : "unknown"}`}
      aria-label={`${label}. ${statusLabel}`}
    >
      {label}
    </span>
  );
}

export function UnknownField({ label, detail }: { label: string; detail: string }) {
  return (
    <div className="p11Unknown" role="status">
      <EvidenceBadge state="unknown">{label}</EvidenceBadge>
      <p>{detail}</p>
    </div>
  );
}

export function DecisionCard({
  eyebrow,
  titleId,
  title,
  state,
  stateLabel,
  children,
}: {
  eyebrow: string;
  titleId: string;
  title: string;
  state: EvidenceState;
  stateLabel: string;
  children: ReactNode;
}) {
  return (
    <section className="p11DecisionCard" aria-labelledby={titleId}>
      <header>
        <span>{eyebrow}</span>
        <EvidenceBadge state={state}>{stateLabel}</EvidenceBadge>
      </header>
      <h2 id={titleId}>{title}</h2>
      {children}
    </section>
  );
}

export function OfferComparison({
  title,
  titleId,
  rows,
}: {
  title: string;
  titleId: string;
  rows: Array<{ label: string; value: string; emphasis?: boolean }>;
}) {
  return (
    <section className="p11Comparison" aria-labelledby={titleId}>
      <h3 id={titleId}>{title}</h3>
      <dl>
        {rows.map((row) => (
          <div key={row.label}>
            <dt>{row.label}</dt>
            <dd className={row.emphasis ? "is-emphasis" : undefined}>{row.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export function TradeoffCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <article className="p11Tradeoff">
      <h3>{title}</h3>
      <p>{children}</p>
    </article>
  );
}

export function ConstraintSummary({
  title,
  titleId,
  items,
}: {
  title: string;
  titleId: string;
  items: Array<{ label: string; state: EvidenceState }>;
}) {
  return (
    <section className="p11Constraints" aria-labelledby={titleId}>
      <h3 id={titleId}>{title}</h3>
      <ul>
        {items.map((item) => (
          <li key={item.label}><EvidenceBadge state={item.state}>{item.label}</EvidenceBadge></li>
        ))}
      </ul>
    </section>
  );
}

export function WhyThisResult({ title, titleId, reasons }: { title: string; titleId: string; reasons: string[] }) {
  return (
    <section className="p11Why" aria-labelledby={titleId}>
      <h3 id={titleId}>{title}</h3>
      <ul>{reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
    </section>
  );
}
