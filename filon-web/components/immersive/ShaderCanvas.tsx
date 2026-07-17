"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

const vertexShader = /* glsl */ `
  void main() {
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

// Living aurora + electric "vein" — the FILON brand motif in a fragment shader.
const fragmentShader = /* glsl */ `
  precision highp float;
  uniform vec2 u_res;
  uniform float u_time;
  uniform vec2 u_mouse;

  float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float noise(vec2 p){
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1,0)), u.x),
               mix(hash(i + vec2(0,1)), hash(i + vec2(1,1)), u.x), u.y);
  }
  float fbm(vec2 p){
    float v = 0.0, a = 0.5;
    mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
    for (int i = 0; i < 6; i++){ v += a * noise(p); p = m * p; a *= 0.5; }
    return v;
  }

  void main(){
    vec2 p = (gl_FragCoord.xy - 0.5 * u_res.xy) / u_res.y;
    float t = u_time * 0.045;
    vec2 mo = (u_mouse - 0.5) * 0.35;
    vec2 q = vec2(fbm(p * 1.5 + t + mo), fbm(p * 1.5 - t + vec2(5.2, 1.3)));
    float f = fbm(p * 1.9 + q * 1.7 + t);

    vec3 c1 = vec3(0.016, 0.020, 0.039);
    vec3 c2 = vec3(0.235, 0.482, 1.0);
    vec3 c3 = vec3(0.545, 0.423, 1.0);
    vec3 c4 = vec3(0.141, 0.890, 0.776);

    vec3 col = mix(c1, c2, smoothstep(0.25, 0.85, f));
    col = mix(col, c3, smoothstep(0.45, 0.95, q.x));
    col = mix(col, c4, smoothstep(0.55, 1.05, q.y));

    float vein = smoothstep(0.015, 0.0, abs(f - 0.62));
    col += vein * vec3(0.5, 0.7, 1.0) * 0.5;

    float glow = smoothstep(1.1, 0.1, length(p - vec2(mo.x, -mo.y) * 1.5));
    col += glow * vec3(0.05, 0.09, 0.16);

    col *= 1.0 - 0.35 * length(p * vec2(0.55, 0.9));
    col = pow(col, vec3(0.86));
    gl_FragColor = vec4(col, 1.0);
  }
`;

function VeinPlane() {
  const mat = useRef<THREE.ShaderMaterial>(null);
  const { size, viewport } = useThree();
  const mouse = useRef(new THREE.Vector2(0.5, 0.5));
  const target = useRef(new THREE.Vector2(0.5, 0.5));

  const uniforms = useMemo(
    () => ({
      u_time: { value: 0 },
      u_res: { value: new THREE.Vector2(1, 1) },
      u_mouse: { value: new THREE.Vector2(0.5, 0.5) },
    }),
    []
  );

  useFrame((state) => {
    if (!mat.current) return;
    const dpr = Math.min(viewport.dpr || 1, 1.6);
    // Track pointer from R3F state (normalised -1..1) → 0..1
    target.current.set((state.pointer.x + 1) / 2, (state.pointer.y + 1) / 2);
    mouse.current.lerp(target.current, 0.05);
    mat.current.uniforms.u_time.value = state.clock.elapsedTime;
    mat.current.uniforms.u_res.value.set(size.width * dpr, size.height * dpr);
    mat.current.uniforms.u_mouse.value.copy(mouse.current);
  });

  return (
    <mesh frustumCulled={false}>
      <planeGeometry args={[2, 2]} />
      <shaderMaterial
        ref={mat}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        depthTest={false}
        depthWrite={false}
      />
    </mesh>
  );
}

export default function ShaderCanvas() {
  return (
    <Canvas
      gl={{ antialias: false, alpha: true, powerPreference: "high-performance" }}
      dpr={[1, 1.6]}
      style={{ position: "fixed", inset: 0, zIndex: -2, pointerEvents: "none" }}
      frameloop="always"
    >
      <VeinPlane />
    </Canvas>
  );
}
