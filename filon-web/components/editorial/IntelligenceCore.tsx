"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * The FILON Intelligence Core — a GPU particle sphere that breathes and reacts
 * to the pointer. Thousands of points coloured across the SmartWave gradient,
 * with real depth. Gated for mobile / low-power, paused off-screen and when the
 * tab is hidden, and reduced to a single static frame under prefers-reduced-motion.
 */
const VERT = /* glsl */ `
  uniform float uTime;
  uniform float uSize;
  uniform float uPixelRatio;
  uniform vec2 uMouse;
  uniform float uBurst;
  attribute float aScale;
  attribute float aPhase;
  varying float vDepth;
  varying float vGrad;
  varying float vTwinkle;

  void main() {
    vec3 p = position;
    float ph = aPhase * 6.2831853;
    // organic breathing along the radius
    float n = sin(uTime * 0.6 + ph + p.y * 2.6) * 0.5 + 0.5;
    float disp = (0.05 + 0.05 * uBurst) * n;
    vec3 pos = p * (1.0 + disp);
    // swirl around Y
    float a = uTime * 0.085;
    float ca = cos(a), sa = sin(a);
    pos.xz = mat2(ca, -sa, sa, ca) * pos.xz;
    // pointer parallax — front particles react more
    float front = pos.z * 0.5 + 0.5;
    pos.xy += uMouse * 0.62 * front;

    vec4 mv = modelViewMatrix * vec4(pos, 1.0);
    vDepth = -mv.z;
    vGrad = clamp(pos.y * 0.42 + 0.5, 0.0, 1.0);
    vTwinkle = 0.6 + 0.4 * sin(uTime * 1.6 + ph * 3.0);
    gl_Position = projectionMatrix * mv;
    gl_PointSize = uSize * aScale * uPixelRatio * (1.0 / max(-mv.z, 0.1));
  }
`;

const FRAG = /* glsl */ `
  precision highp float;
  uniform vec3 uColorA;
  uniform vec3 uColorB;
  uniform vec3 uColorC;
  varying float vDepth;
  varying float vGrad;
  varying float vTwinkle;

  void main() {
    vec2 uv = gl_PointCoord - 0.5;
    float d = length(uv);
    if (d > 0.5) discard;
    float alpha = smoothstep(0.5, 0.0, d);
    // soft luminous core
    alpha *= alpha;
    vec3 col = mix(uColorA, uColorB, smoothstep(0.15, 0.85, vGrad));
    col = mix(col, uColorC, smoothstep(0.72, 1.0, vGrad) * 0.6);
    // depth fade — far points recede
    float depthFade = clamp(1.0 - (vDepth - 4.0) / 7.0, 0.22, 1.0);
    gl_FragColor = vec4(col, alpha * depthFade * vTwinkle * 1.15);
  }
`;

export function IntelligenceCore({ className }: { className?: string }) {
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const small = window.matchMedia("(max-width: 720px)").matches;
    const lowPower =
      (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) || false;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
    } catch {
      host.classList.add("core-fallback");
      return;
    }
    const dpr = Math.min(window.devicePixelRatio || 1, small ? 1.5 : 2);
    renderer.setPixelRatio(dpr);
    renderer.setClearColor(0x000000, 0);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    camera.position.set(0, 0, 7.2);

    // ── particle geometry: two fibonacci shells for volume ──
    const COUNT = small ? 3600 : lowPower ? 6000 : 11000;
    const positions = new Float32Array(COUNT * 3);
    const scales = new Float32Array(COUNT);
    const phases = new Float32Array(COUNT);
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < COUNT; i++) {
      const shell = i % 5 === 0 ? 0.62 : 1.0; // sparse inner shell
      const radius = 2.05 * shell + (Math.random() - 0.5) * 0.12;
      const y = 1 - (i / (COUNT - 1)) * 2;
      const r = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = golden * i;
      positions[i * 3] = Math.cos(theta) * r * radius;
      positions[i * 3 + 1] = y * radius;
      positions[i * 3 + 2] = Math.sin(theta) * r * radius;
      scales[i] = 0.5 + Math.random() * 1.7;
      phases[i] = Math.random();
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geo.setAttribute("aScale", new THREE.BufferAttribute(scales, 1));
    geo.setAttribute("aPhase", new THREE.BufferAttribute(phases, 1));

    const uniforms = {
      uTime: { value: 0 },
      uSize: { value: small ? 30 : 44 },
      uPixelRatio: { value: dpr },
      uMouse: { value: new THREE.Vector2(0, 0) },
      uBurst: { value: 0 },
      uColorA: { value: new THREE.Color(0x1e75c9) }, // SmartWave blue
      uColorB: { value: new THREE.Color(0x14c6c0) }, // turquoise
      uColorC: { value: new THREE.Color(0xdfe9f2) }, // chrome light
    };
    const material = new THREE.ShaderMaterial({
      uniforms,
      vertexShader: VERT,
      fragmentShader: FRAG,
      transparent: true,
      depthWrite: false,
      blending: THREE.NormalBlending,
    });
    const points = new THREE.Points(geo, material);
    scene.add(points);

    host.appendChild(renderer.domElement);
    Object.assign(renderer.domElement.style, { width: "100%", height: "100%", display: "block" });

    const resize = () => {
      const w = host.clientWidth || 1;
      const h = host.clientHeight || 1;
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(host);

    // pointer parallax (smoothed)
    const target = new THREE.Vector2(0, 0);
    const onMove = (e: PointerEvent) => {
      const r = host.getBoundingClientRect();
      target.set(((e.clientX - r.left) / r.width) * 2 - 1, -(((e.clientY - r.top) / r.height) * 2 - 1));
    };
    window.addEventListener("pointermove", onMove, { passive: true });

    let visible = true;
    const io = new IntersectionObserver((ents) => ents.forEach((en) => (visible = en.isIntersecting)), { threshold: 0.01 });
    io.observe(host);

    const clock = new THREE.Clock();
    let raf = 0;
    let burst = 0;

    const renderFrame = () => {
      uniforms.uTime.value = clock.getElapsedTime();
      uniforms.uMouse.value.lerp(target, 0.09);
      burst += (0 - burst) * 0.02;
      uniforms.uBurst.value = burst;
      // continuous spin + pointer-driven tilt for a livelier object
      points.rotation.y += 0.0016;
      points.rotation.x += (uniforms.uMouse.value.y * 0.22 - points.rotation.x) * 0.06;
      points.rotation.z += (uniforms.uMouse.value.x * 0.12 - points.rotation.z) * 0.06;
      renderer.render(scene, camera);
    };

    if (reduce) {
      renderFrame();
    } else {
      const loop = () => {
        raf = requestAnimationFrame(loop);
        if (!visible || document.hidden) return;
        renderFrame();
      };
      loop();
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
      ro.disconnect();
      io.disconnect();
      geo.dispose();
      material.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === host) host.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={hostRef} className={className} aria-hidden="true" />;
}
