"use client";

import { useState } from "react";
import { Container } from "@/components/ui/Container";

export function ContactForm() {
  const [sent, setSent] = useState(false);
  const [email, setEmail] = useState("");

  const inputStyle: React.CSSProperties = {
    width: "100%",
    background: "var(--bg-2)",
    border: "1px solid var(--border-2)",
    borderRadius: "var(--r-md)",
    padding: "13px 16px",
    color: "var(--text)",
    fontFamily: "inherit",
    fontSize: 15,
    outline: "none",
  };

  return (
    <section style={{ padding: "20px 0 70px" }}>
      <Container>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (email.includes("@")) setSent(true);
          }}
          style={{ maxWidth: 560, display: "grid", gap: 12 }}
        >
          <input aria-label="Votre nom" placeholder="Votre nom" style={inputStyle} required />
          <input
            aria-label="Votre email"
            type="email"
            placeholder="votre@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={inputStyle}
            required
          />
          <textarea aria-label="Votre message" placeholder="Votre message" rows={5} style={{ ...inputStyle, resize: "vertical" }} required />
          <button
            type="submit"
            className="filon-btn"
            style={{ justifySelf: "start", padding: "13px 26px", fontSize: 15, fontWeight: 600, borderRadius: "var(--r-full)", border: 0, color: "#05121f", background: "var(--vein)", boxShadow: "var(--shadow-glow)", cursor: "pointer" }}
          >
            Envoyer
          </button>
          {sent && (
            <p style={{ color: "var(--pos)", fontSize: 14, fontWeight: 500 }}>
              ✓ Merci ! Votre message est bien parti. Nous revenons vers vous rapidement.
            </p>
          )}
        </form>
      </Container>
    </section>
  );
}
