// Ambient aurora / mesh background. Purely decorative, pointer-events: none.
export function Atmosphere() {
  const blob = (s: React.CSSProperties): React.CSSProperties => ({
    position: "fixed",
    zIndex: -1,
    filter: "blur(90px)",
    borderRadius: "50%",
    pointerEvents: "none",
    ...s,
  });
  return (
    <>
      <div style={{ position: "fixed", inset: 0, zIndex: -2, background: "var(--ground)" }} />
      <div style={blob({ width: 620, height: 620, top: -180, left: -120, opacity: 0.42, background: "radial-gradient(circle, var(--blue), transparent 70%)" })} />
      <div style={blob({ width: 540, height: 540, top: "6%", right: -160, opacity: 0.3, background: "radial-gradient(circle, var(--aqua), transparent 70%)" })} />
      <div style={blob({ width: 700, height: 700, top: "44%", left: "30%", opacity: 0.2, background: "radial-gradient(circle, var(--violet), transparent 70%)" })} />
    </>
  );
}
