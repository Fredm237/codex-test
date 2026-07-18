"use client";

import { useState } from "react";
import { site } from "@/lib/site";

type State = "idle" | "sending" | "ok" | "error";

async function postForm(data: Record<string, string>): Promise<boolean> {
  // Demo mode when no endpoint is configured yet.
  if (!site.formEndpoint) {
    await new Promise((r) => setTimeout(r, 600));
    return true;
  }
  try {
    const res = await fetch(site.formEndpoint, {
      method: "POST",
      headers: { Accept: "application/json" },
      body: new URLSearchParams(data),
    });
    return res.ok;
  } catch {
    return false;
  }
}

const input: React.CSSProperties = {
  width: "100%",
  background: "var(--card)",
  border: "1px solid var(--line-2)",
  borderRadius: 12,
  padding: "14px 16px",
  color: "var(--ink)",
  fontFamily: "var(--sans)",
  fontSize: 15,
  outline: "none",
};

export function ContactForm() {
  const [state, setState] = useState<State>("idle");

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    if (fd.get("_gotcha")) return; // honeypot
    setState("sending");
    const ok = await postForm({
      nom: String(fd.get("nom") || ""),
      email: String(fd.get("email") || ""),
      message: String(fd.get("message") || ""),
      _subject: "Nouveau message — FILON",
    });
    setState(ok ? "ok" : "error");
    if (ok) e.currentTarget.reset();
  };

  if (state === "ok") {
    return (
      <p className="ed-form-ok" role="status">
        ✓ Merci ! Votre message est bien parti. Nous revenons vers vous rapidement.
      </p>
    );
  }

  return (
    <form onSubmit={onSubmit} style={{ maxWidth: 560, display: "grid", gap: 12 }}>
      <input name="nom" aria-label="Votre nom" placeholder="Votre nom" style={input} required />
      <input name="email" type="email" aria-label="Votre email" placeholder="votre@email.com" style={input} required />
      <textarea name="message" aria-label="Votre message" placeholder="Votre message" rows={5} style={{ ...input, resize: "vertical" }} required />
      <input type="text" name="_gotcha" tabIndex={-1} autoComplete="off" style={{ position: "absolute", left: "-9999px" }} aria-hidden="true" />
      <button type="submit" className="ed-btn wave" style={{ justifySelf: "start" }} disabled={state === "sending"}>
        {state === "sending" ? "Envoi…" : "Envoyer"}
      </button>
      {state === "error" && (
        <p className="ed-form-err" role="alert">
          Une erreur est survenue. Réessayez, ou écrivez-nous directement à contact@{site.domain}.
        </p>
      )}
    </form>
  );
}

export function Newsletter() {
  const [state, setState] = useState<State>("idle");

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    if (fd.get("_gotcha")) return;
    setState("sending");
    const ok = await postForm({ email: String(fd.get("email") || ""), _subject: "Le Filon — inscription newsletter", liste: "le-filon" });
    setState(ok ? "ok" : "error");
    if (ok) e.currentTarget.reset();
  };

  return (
    <form className="ed-news" onSubmit={onSubmit}>
      <input name="email" type="email" aria-label="Votre email" placeholder="votre@email.com" required disabled={state === "ok"} />
      <input type="text" name="_gotcha" tabIndex={-1} autoComplete="off" aria-hidden="true" style={{ display: "none" }} />
      <button type="submit" className="ed-btn wave" disabled={state === "sending" || state === "ok"}>
        {state === "ok" ? "✓ Inscrit·e" : state === "sending" ? "…" : "M'inscrire"}
      </button>
      {state === "error" && <span className="ed-news-msg err">Réessayez.</span>}
      {state === "ok" && <span className="ed-news-msg ok">Vous serez prévenu·e du lancement.</span>}
    </form>
  );
}
