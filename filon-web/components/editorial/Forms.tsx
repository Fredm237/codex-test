"use client";

import { useState } from "react";
import { site } from "@/lib/site";
import { useLocale } from "@/lib/i18n";

type State = "idle" | "sending" | "ok" | "error";

const FL = {
  fr: {
    ok: "✓ Merci ! Votre message est bien parti. Nous revenons vers vous rapidement.",
    name: "Votre nom", email: "votre@email.com", message: "Votre message",
    sending: "Envoi…", send: "Envoyer",
    err: "Une erreur est survenue. Réessayez, ou écrivez-nous directement à ",
    subscribed: "✓ Inscrit·e", subscribe: "M'inscrire",
    retry: "Réessayez.", newsOk: "Vous serez prévenu·e du lancement.",
  },
  nl: {
    ok: "✓ Bedankt ! Je bericht is verzonden. We komen snel bij je terug.",
    name: "Je naam", email: "jouw@email.com", message: "Je bericht",
    sending: "Verzenden…", send: "Verzenden",
    err: "Er is iets misgegaan. Probeer opnieuw, of schrijf ons direct op ",
    subscribed: "✓ Ingeschreven", subscribe: "Inschrijven",
    retry: "Probeer opnieuw.", newsOk: "Je wordt verwittigd bij de lancering.",
  },
};

async function postForm(data: Record<string, string>): Promise<boolean> {
  // No form backend configured: route the request to the real mailbox through
  // the visitor's mail client, so contact still works without Formspree.
  if (!site.formEndpoint) {
    const subject = data._subject || "Message FILON";
    const body = Object.entries(data)
      .filter(([k]) => !k.startsWith("_"))
      .map(([k, v]) => `${k}: ${v}`)
      .join("\n");
    if (typeof window !== "undefined") {
      window.location.href = `mailto:contact@${site.domain}?subject=${encodeURIComponent(
        subject
      )}&body=${encodeURIComponent(body)}`;
    }
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
  borderRadius: "var(--r-md)",
  padding: "14px 16px",
  color: "var(--ink)",
  fontFamily: "var(--sans)",
  fontSize: 15,
  outline: "none",
};

export function ContactForm() {
  const [state, setState] = useState<State>("idle");
  const { locale } = useLocale();
  const T = FL[locale];

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    if (fd.get("_gotcha")) return; // honeypot
    setState("sending");
    const ok = await postForm({
      nom: String(fd.get("nom") || ""),
      email: String(fd.get("email") || ""),
      message: String(fd.get("message") || ""),
      _subject: "Nouveau message FILON",
    });
    setState(ok ? "ok" : "error");
    if (ok) e.currentTarget.reset();
  };

  if (state === "ok") {
    return (
      <p className="ed-form-ok" role="status">
        {T.ok}
      </p>
    );
  }

  return (
    <form onSubmit={onSubmit} style={{ maxWidth: 560, display: "grid", gap: 12 }}>
      <input name="nom" aria-label={T.name} placeholder={T.name} style={input} required />
      <input name="email" type="email" aria-label={T.email} placeholder={T.email} style={input} required />
      <textarea name="message" aria-label={T.message} placeholder={T.message} rows={5} style={{ ...input, resize: "vertical" }} required />
      <input type="text" name="_gotcha" tabIndex={-1} autoComplete="off" style={{ position: "absolute", left: "-9999px" }} aria-hidden="true" />
      <button type="submit" className="ed-btn wave" style={{ justifySelf: "start" }} disabled={state === "sending"}>
        {state === "sending" ? T.sending : T.send}
      </button>
      {state === "error" && (
        <p className="ed-form-err" role="alert">
          {T.err}contact@{site.domain}.
        </p>
      )}
    </form>
  );
}

export function Newsletter() {
  const [state, setState] = useState<State>("idle");
  const { locale } = useLocale();
  const T = FL[locale];

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    if (fd.get("_gotcha")) return;
    setState("sending");
    const ok = await postForm({ email: String(fd.get("email") || ""), _subject: "Inscription à la newsletter Le Filon", liste: "le-filon" });
    setState(ok ? "ok" : "error");
    if (ok) e.currentTarget.reset();
  };

  return (
    <form className="ed-news" onSubmit={onSubmit}>
      <input name="email" type="email" aria-label={T.email} placeholder={T.email} required disabled={state === "ok"} />
      <input type="text" name="_gotcha" tabIndex={-1} autoComplete="off" aria-hidden="true" style={{ display: "none" }} />
      <button type="submit" className="ed-btn wave" disabled={state === "sending" || state === "ok"}>
        {state === "ok" ? T.subscribed : state === "sending" ? "…" : T.subscribe}
      </button>
      {state === "error" && <span className="ed-news-msg err">{T.retry}</span>}
      {state === "ok" && <span className="ed-news-msg ok">{T.newsOk}</span>}
    </form>
  );
}
