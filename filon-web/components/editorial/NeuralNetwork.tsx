"use client";

import { useEffect, useRef } from "react";

/**
 * Live network canvas (2D, GPU-friendly): labelled nodes connected to a glowing
 * FILON core, with analysis pulses travelling inward. Two variants:
 *  - "merchants": shops/platforms being compared in real time
 *  - "graph": the Intelligence Graph data dimensions
 * Paused off-screen and when hidden; a single static frame under reduced-motion.
 */
type Variant = "merchants" | "graph";

const LABELS: Record<Variant, string[]> = {
  merchants: ["Amazon", "Fnac", "Cdiscount", "Back Market", "Boulanger", "Darty", "Rakuten", "Decathlon", "Zalando", "Leroy Merlin", "Micromania", "Nike"],
  graph: ["Prix historique", "Fiabilité marque", "Réparabilité", "Durée de vie", "Coût total", "Avis analysés", "Garantie", "Disponibilité"],
};

export function NeuralNetwork({ variant = "merchants", className }: { variant?: Variant; className?: string }) {
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    host.appendChild(canvas);
    Object.assign(canvas.style, { width: "100%", height: "100%", display: "block" });

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const small = window.matchMedia("(max-width: 720px)").matches;
    const labels = LABELS[variant];
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    let W = 0, H = 0, cx = 0, cy = 0, radius = 0;
    type Node = { a: number; r: number; x: number; y: number; label: string; drift: number; ph: number };
    let nodes: Node[] = [];

    const layout = () => {
      W = host.clientWidth; H = host.clientHeight;
      canvas.width = Math.floor(W * dpr); canvas.height = Math.floor(H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = W / 2; cy = H / 2;
      radius = Math.min(W, H) * (small ? 0.4 : 0.36);
      nodes = labels.map((label, i) => {
        const a = (i / labels.length) * Math.PI * 2 - Math.PI / 2;
        const rr = radius * (0.72 + ((i * 37) % 100) / 100 * 0.5);
        return { a, r: rr, x: 0, y: 0, label, drift: 0.4 + ((i * 53) % 100) / 100 * 0.8, ph: (i * 1.7) % 6.28 };
      });
    };
    layout();
    const ro = new ResizeObserver(layout);
    ro.observe(host);

    const teal = "20,198,192";
    const blue = "30,117,201";
    type Pulse = { i: number; t: number; speed: number };
    let pulses: Pulse[] = [];
    const spawn = () => pulses.push({ i: (Math.random() * nodes.length) | 0, t: 0, speed: 0.006 + Math.random() * 0.01 });

    let coreGlow = 0;
    let t0 = performance.now();

    const draw = (now: number) => {
      const time = (now - t0) / 1000;
      ctx.clearRect(0, 0, W, H);

      // node positions with gentle drift
      nodes.forEach((n) => {
        const wobble = reduce ? 0 : Math.sin(time * n.drift + n.ph) * 6;
        n.x = cx + Math.cos(n.a + (reduce ? 0 : time * 0.02)) * (n.r + wobble);
        n.y = cy + Math.sin(n.a + (reduce ? 0 : time * 0.02)) * (n.r + wobble);
      });

      // connections node → core
      nodes.forEach((n) => {
        const g = ctx.createLinearGradient(n.x, n.y, cx, cy);
        g.addColorStop(0, `rgba(${blue},0.05)`);
        g.addColorStop(1, `rgba(${teal},0.16)`);
        ctx.strokeStyle = g; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(cx, cy); ctx.stroke();
      });
      // a few node-node links
      for (let i = 0; i < nodes.length; i += 2) {
        const a = nodes[i], b = nodes[(i + 3) % nodes.length];
        ctx.strokeStyle = `rgba(${teal},0.05)`; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      }

      // pulses travelling inward
      pulses = pulses.filter((p) => p.t < 1);
      pulses.forEach((p) => {
        p.t += reduce ? 0 : p.speed;
        const n = nodes[p.i];
        const x = n.x + (cx - n.x) * p.t;
        const y = n.y + (cy - n.y) * p.t;
        const rr = 2.5 + p.t * 2;
        ctx.fillStyle = `rgba(${teal},${0.9 * (1 - p.t) + 0.1})`;
        ctx.shadowColor = `rgba(${teal},0.9)`; ctx.shadowBlur = 12;
        ctx.beginPath(); ctx.arc(x, y, rr, 0, 6.2832); ctx.fill();
        ctx.shadowBlur = 0;
        if (p.t > 0.97) coreGlow = 1;
      });

      // nodes + labels
      ctx.font = `${small ? 11 : 12.5}px ui-sans-serif, system-ui, sans-serif`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      nodes.forEach((n) => {
        ctx.fillStyle = `rgba(${teal},0.85)`;
        ctx.shadowColor = `rgba(${teal},0.7)`; ctx.shadowBlur = 8;
        ctx.beginPath(); ctx.arc(n.x, n.y, 3, 0, 6.2832); ctx.fill();
        ctx.shadowBlur = 0;
        ctx.fillStyle = "rgba(234,242,251,0.66)";
        const ty = n.y > cy ? n.y + 16 : n.y - 15;
        ctx.fillText(n.label, n.x, ty);
      });

      // core
      coreGlow += (0.35 - coreGlow) * 0.04;
      const cr = small ? 30 : 40;
      const cg = ctx.createRadialGradient(cx, cy, 0, cx, cy, cr * 2.4);
      cg.addColorStop(0, `rgba(255,255,255,${0.85})`);
      cg.addColorStop(0.3, `rgba(${teal},${0.6 + coreGlow * 0.4})`);
      cg.addColorStop(0.7, `rgba(${blue},0.25)`);
      cg.addColorStop(1, "rgba(10,21,36,0)");
      ctx.fillStyle = cg;
      ctx.beginPath(); ctx.arc(cx, cy, cr * 2.4, 0, 6.2832); ctx.fill();
      ctx.fillStyle = "#eaf2fb"; ctx.font = `600 ${small ? 12 : 13}px ui-sans-serif, system-ui`;
      ctx.fillText("FILON", cx, cy);
    };

    let raf = 0, visible = true, pulseTimer = 0;
    const io = new IntersectionObserver((e) => e.forEach((en) => (visible = en.isIntersecting)), { threshold: 0.02 });
    io.observe(host);

    if (reduce) {
      spawn();
      draw(performance.now());
    } else {
      const loop = (now: number) => {
        raf = requestAnimationFrame(loop);
        if (!visible || document.hidden) return;
        if (now - pulseTimer > 620) { spawn(); pulseTimer = now; }
        draw(now);
      };
      raf = requestAnimationFrame(loop);
    }

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
      if (canvas.parentNode === host) host.removeChild(canvas);
    };
  }, [variant]);

  return <div ref={hostRef} className={className} aria-hidden="true" />;
}
