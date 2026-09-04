import * as THREE from "three";

export type SignatureProjection = "perspective" | "orthographic";
export type SignatureShotId = "market" | "identity" | "proof" | "decision";

export type CameraPose = {
  fov: number;
  position: [number, number, number];
  projection: SignatureProjection;
  target: [number, number, number];
};

export const FILON_MOTION = {
  duration: {
    micro: 180,
    camera: 1_100,
    material: 760,
    scene: 10_000,
  },
  easing: {
    cinematic: [0.22, 1, 0.36, 1],
    mechanical: [0.4, 0, 0.2, 1],
    soft: [0.16, 1, 0.3, 1],
  },
  response: {
    camera: 8.4,
    focus: 10.5,
  },
} as const;

export const CAMERA_SEQUENCE = [
  { id: "market", start: 0, end: 0.2, projection: "perspective" },
  { id: "identity", start: 0.2, end: 0.34, projection: "perspective" },
  { id: "proof", start: 0.34, end: 0.72, projection: "perspective" },
  { id: "decision", start: 0.72, end: 1, projection: "orthographic", projectionAt: 0.9 },
] as const satisfies ReadonlyArray<{
  end: number;
  id: SignatureShotId;
  projection: SignatureProjection;
  projectionAt?: number;
  start: number;
}>;

export const MATERIAL_SEQUENCE = {
  gather: [0.08, 0.45],
  focus: [0.2, 0.52],
  anneal: [0.46, 0.76],
  seal: [0.72, 1],
} as const;

export function clamp(value: number, low = 0, high = 1) {
  return Math.max(low, Math.min(high, value));
}

export function phase(progress: number, start: number, end: number) {
  return clamp((progress - start) / (end - start));
}

export function cinematicEase(value: number) {
  const x = clamp(value);
  return x * x * (3 - 2 * x);
}

export function dampAlpha(delta: number, response = FILON_MOTION.response.camera) {
  return 1 - Math.exp(-response * Math.max(0, delta));
}

function lerpTuple(
  from: [number, number, number],
  to: [number, number, number],
  amount: number,
): [number, number, number] {
  return [
    THREE.MathUtils.lerp(from[0], to[0], amount),
    THREE.MathUtils.lerp(from[1], to[1], amount),
    THREE.MathUtils.lerp(from[2], to[2], amount),
  ];
}

export function sampleCausalCamera(progress: number, compact: boolean): CameraPose {
  const p = clamp(progress);
  const wide: [number, number, number] = [0, 1.8, compact ? 12.7 : 10.5];
  const macro: [number, number, number] = [compact ? 1.85 : 2.65, 0.35, compact ? 5.3 : 4.3];
  const macroRadius = Math.hypot(macro[0], macro[2]);
  const macroAngle = Math.atan2(macro[0], macro[2]);
  const orbitEndAngle = Math.PI * 0.82;
  const orbitEnd: [number, number, number] = [
    Math.sin(orbitEndAngle) * macroRadius,
    1.35,
    Math.cos(orbitEndAngle) * macroRadius,
  ];
  const decision: [number, number, number] = [0, compact ? 5.7 : 6.4, compact ? 9.6 : 8.8];

  if (p < 0.34) {
    const t = cinematicEase(phase(p, 0, 0.34));
    return {
      position: lerpTuple(wide, macro, t),
      target: [0, 0, 0],
      fov: THREE.MathUtils.lerp(compact ? 52 : 46, compact ? 41 : 36, t),
      projection: "perspective",
    };
  }

  if (p < 0.72) {
    const t = cinematicEase(phase(p, 0.34, 0.72));
    const angle = THREE.MathUtils.lerp(macroAngle, orbitEndAngle, t);
    return {
      position: [Math.sin(angle) * macroRadius, THREE.MathUtils.lerp(0.35, 1.35, t), Math.cos(angle) * macroRadius],
      target: [0, THREE.MathUtils.lerp(0, -0.08, t), 0],
      fov: THREE.MathUtils.lerp(compact ? 41 : 36, 33, t),
      projection: "perspective",
    };
  }

  const t = cinematicEase(phase(p, 0.72, 1));
  return {
    position: lerpTuple(orbitEnd, decision, t),
    target: [0, THREE.MathUtils.lerp(-0.08, -0.2, t), 0],
    fov: THREE.MathUtils.lerp(33, 31, t),
    projection: p >= 0.9 ? "orthographic" : "perspective",
  };
}

export function sampleCausalLights(progress: number) {
  const identity = cinematicEase(phase(progress, 0.2, 0.48));
  const anneal = cinematicEase(phase(progress, 0.46, 0.76));
  const settle = cinematicEase(phase(progress, 0.76, 1));
  return {
    key: {
      position: [
        THREE.MathUtils.lerp(-5.5, 0.8, identity),
        THREE.MathUtils.lerp(3.5, 7.4, identity),
        THREE.MathUtils.lerp(8, 4.2, anneal),
      ] as [number, number, number],
      intensity: THREE.MathUtils.lerp(1.25, 3.1, identity) * (1 - settle * 0.22),
    },
    proof: {
      position: [THREE.MathUtils.lerp(6.5, -2.4, anneal), 2, THREE.MathUtils.lerp(2.2, 6.8, anneal)] as [number, number, number],
      intensity: THREE.MathUtils.lerp(8, 48, anneal) * (1 - settle * 0.5),
    },
    decision: {
      position: [0, THREE.MathUtils.lerp(-2, 3.4, settle), 4] as [number, number, number],
      intensity: THREE.MathUtils.lerp(2, 15, settle),
    },
  };
}
