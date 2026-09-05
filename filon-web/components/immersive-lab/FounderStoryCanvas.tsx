"use client";

import { RoundedBox, useTexture } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Suspense, useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import type { ImmersiveQuality } from "@/components/experience/signature/ImmersiveRuntime";
import { bindWebglContextLoss } from "@/components/experience/signature/WebglContextLoss.mjs";

type ProductProjection = { image: string; name: string };

type FounderStoryCanvasProps = {
  compact: boolean;
  offerCount: number;
  onFailure: () => void;
  onReady?: () => void;
  playing: boolean;
  product: ProductProjection;
  progress: number;
  quality: ImmersiveQuality;
};

const clamp = (value: number) => Math.min(1, Math.max(0, value));
const phase = (progress: number, start: number, end: number) => clamp((progress - start) / (end - start));
const ease = (value: number) => {
  const x = clamp(value);
  return x * x * (3 - 2 * x);
};

function CanvasLifecycle({ onFailure, onReady }: Pick<FounderStoryCanvasProps, "onFailure" | "onReady">) {
  const { gl } = useThree();
  const failureRef = useRef(onFailure);
  const readyRef = useRef(onReady);

  useEffect(() => {
    failureRef.current = onFailure;
    readyRef.current = onReady;
  }, [onFailure, onReady]);

  useEffect(() => {
    gl.outputColorSpace = THREE.SRGBColorSpace;
    gl.toneMapping = THREE.ACESFilmicToneMapping;
    gl.toneMappingExposure = 1.04;
    const unbind = bindWebglContextLoss(gl.domElement, () => failureRef.current());
    readyRef.current?.();
    return unbind;
  }, [gl]);

  return null;
}

function CameraJourney({ compact, playing, progress }: Pick<FounderStoryCanvasProps, "compact" | "playing" | "progress">) {
  const { camera, set, size } = useThree();
  const perspective = useRef(camera as THREE.PerspectiveCamera);
  const orthographic = useMemo(() => new THREE.OrthographicCamera(-5, 5, 5, -5, 0.1, 80), []);
  const target = useMemo(() => new THREE.Vector3(), []);
  const desired = useMemo(() => new THREE.Vector3(), []);
  const desiredTarget = useMemo(() => new THREE.Vector3(), []);
  const active = useRef<"perspective" | "orthographic">("perspective");

  useEffect(() => () => set({ camera: perspective.current }), [set]);

  useFrame((_, delta) => {
    const pass = ease(phase(progress, 0.08, 0.28));
    const explore = ease(phase(progress, 0.28, 0.58));
    const proof = ease(phase(progress, 0.58, 0.82));
    const settle = ease(phase(progress, 0.82, 1));
    const orbit = proof * Math.PI * 0.34;

    const wide = compact ? new THREE.Vector3(0, 1.35, 10.8) : new THREE.Vector3(0, 1.65, 11.8);
    const screen = new THREE.Vector3(0, 1.05, 4.35);
    const city = new THREE.Vector3(compact ? 0.2 : -1.2, 2.8, 9.2);
    const around = new THREE.Vector3(Math.sin(orbit) * 6.2, 3.2 - proof * 0.8, Math.cos(orbit) * 6.2);
    const final = new THREE.Vector3(0, 7.4, 0.15);

    desired.copy(wide).lerp(screen, pass).lerp(city, explore).lerp(around, proof).lerp(final, settle);
    desiredTarget.set(0, 0.8, 0).lerp(new THREE.Vector3(0, 0.15, 0), settle);
    const alpha = playing ? 1 - Math.exp(-delta * 6.5) : 1;
    const perspectiveCamera = perspective.current;
    perspectiveCamera.position.lerp(desired, alpha);
    target.lerp(desiredTarget, alpha);
    perspectiveCamera.lookAt(target);
    perspectiveCamera.aspect = size.width / Math.max(size.height, 1);
    perspectiveCamera.fov = THREE.MathUtils.lerp(perspectiveCamera.fov, compact ? 54 : 44, alpha);
    perspectiveCamera.updateProjectionMatrix();

    const aspect = size.width / Math.max(size.height, 1);
    const frustum = compact ? 4.7 : 4.05;
    orthographic.left = -frustum * aspect;
    orthographic.right = frustum * aspect;
    orthographic.top = frustum;
    orthographic.bottom = -frustum;
    orthographic.position.lerp(desired, alpha);
    orthographic.lookAt(target);
    orthographic.updateProjectionMatrix();

    const next = settle > 0.56 ? "orthographic" : "perspective";
    if (active.current !== next) {
      active.current = next;
      set({ camera: next === "orthographic" ? orthographic : perspectiveCamera });
    }
  });

  return null;
}

function ProductImage({ image, size = [1.65, 1.65] }: { image: string; size?: [number, number] }) {
  const texture = useTexture(image);
  useEffect(() => {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 4;
    texture.needsUpdate = true;
  }, [texture]);
  return (
    <mesh position={[0, 0, 0.025]}>
      <planeGeometry args={size} />
      <meshBasicMaterial map={texture} transparent toneMapped={false} />
    </mesh>
  );
}

function LaptopPortal({ image, progress }: { image: string; progress: number }) {
  const root = useRef<THREE.Group>(null);
  const material = useRef<THREE.MeshStandardMaterial>(null);
  useFrame(() => {
    const vanish = ease(phase(progress, 0.18, 0.34));
    if (root.current) {
      root.current.position.z = THREE.MathUtils.lerp(0, -2.5, vanish);
      root.current.scale.setScalar(1 - vanish * 0.55);
      root.current.visible = vanish < 0.99;
    }
    if (material.current) material.current.opacity = 1 - vanish;
  });

  return (
    <group ref={root} position={[0, 0.05, 0]}>
      <mesh position={[0, -2.05, 0]} receiveShadow>
        <boxGeometry args={[13, 0.18, 8]} />
        <meshStandardMaterial color="#d9cdbd" roughness={0.92} />
      </mesh>
      <group position={[0, 0.55, 0]} rotation={[-0.06, 0, 0]}>
        <RoundedBox args={[5.7, 3.55, 0.24]} radius={0.16} smoothness={4} castShadow>
          <meshStandardMaterial ref={material} color="#3c3b37" roughness={0.34} metalness={0.34} transparent />
        </RoundedBox>
        <mesh position={[0, 0, 0.132]}>
          <planeGeometry args={[5.28, 3.12]} />
          <meshBasicMaterial color="#f3eadc" />
        </mesh>
        <group position={[0, 0.1, 0.15]}>
          <Suspense fallback={null}><ProductImage image={image} size={[2.05, 2.05]} /></Suspense>
        </group>
      </group>
      <mesh position={[0, -1.32, 1.28]} rotation={[-0.9, 0, 0]} castShadow>
        <boxGeometry args={[6.2, 3.5, 0.12]} />
        <meshStandardMaterial color="#b9b5ac" roughness={0.45} metalness={0.48} />
      </mesh>
    </group>
  );
}

const BUILDINGS: Array<[number, number, number, number, string]> = [
  [-5.3, 0.2, -1.9, 3.6, "#b76346"], [-3.6, 0.55, -2.8, 4.3, "#d39b75"],
  [-1.8, 0.12, -3.5, 3.45, "#8f9b7c"], [1.8, 0.45, -3.6, 4.05, "#d5b692"],
  [3.75, 0.18, -2.6, 3.5, "#9f6b56"], [5.45, 0.62, -1.7, 4.4, "#c58a5e"],
];

function ShopBuilding({ data, image, index, progress }: { data: [number, number, number, number, string]; image: string; index: number; progress: number }) {
  const [x, y, z, height, color] = data;
  const root = useRef<THREE.Group>(null);
  const wall = useRef<THREE.MeshStandardMaterial>(null);
  const appear = ease(phase(progress, 0.2 + index * 0.018, 0.43 + index * 0.018));
  const settle = ease(phase(progress, 0.8, 1));
  useFrame(() => {
    if (!root.current || !wall.current) return;
    root.current.position.y = THREE.MathUtils.lerp(-5.2, y, appear);
    root.current.position.x = THREE.MathUtils.lerp(x, x * 0.52, settle);
    root.current.position.z = THREE.MathUtils.lerp(z, -0.65, settle);
    root.current.scale.y = THREE.MathUtils.lerp(0.08, 1, appear) * (1 - settle * 0.78);
    wall.current.opacity = appear * (1 - settle * 0.76);
  });
  return (
    <group ref={root} position={[x, -5.2, z]}>
      <mesh castShadow receiveShadow>
        <boxGeometry args={[1.55, height, 1.2]} />
        <meshStandardMaterial ref={wall} color={color} roughness={0.88} transparent />
      </mesh>
      <mesh position={[0, height / 2 + 0.31, 0]} rotation={[0, Math.PI / 4, 0]} castShadow>
        <coneGeometry args={[1.08, 0.68, 4]} />
        <meshStandardMaterial color={index % 2 ? "#6f594b" : "#7e4738"} roughness={0.92} />
      </mesh>
      {[-0.36, 0.36].map((windowX) => (
        <group key={windowX} position={[windowX, height * 0.2, 0.615]}>
          <mesh>
            <planeGeometry args={[0.42, 0.62]} />
            <meshStandardMaterial color="#8fa5a0" emissive="#e3d7bd" emissiveIntensity={0.18} roughness={0.34} />
          </mesh>
          <mesh position={[0, 0, 0.008]}>
            <planeGeometry args={[0.025, 0.62]} />
            <meshBasicMaterial color="#675b4f" />
          </mesh>
        </group>
      ))}
      <mesh position={[0, -height * 0.15, 0.62]}>
        <planeGeometry args={[1.12, 1.25]} />
        <meshBasicMaterial color="#ece1cf" />
      </mesh>
      <group position={[0, -height * 0.15, 0.65]}>
        <Suspense fallback={null}><ProductImage image={image} size={[0.88, 0.88]} /></Suspense>
      </group>
      <mesh position={[0, height * 0.24, 0.62]}>
        <planeGeometry args={[0.78, 0.1]} />
        <meshBasicMaterial color={index % 2 ? "#304c43" : "#8f3e2d"} />
      </mesh>
      <mesh position={[0, -height * 0.15 + 0.72, 0.77]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <boxGeometry args={[1.25, 0.42, 0.08]} />
        <meshStandardMaterial color={index % 2 ? "#315b51" : "#b14e36"} roughness={0.72} />
      </mesh>
    </group>
  );
}

const OFFER_POSITIONS: Array<[number, number, number]> = [
  [-4.4, 2.5, 1.8], [4.7, 2.1, 1.4], [-3.2, -0.6, 2.3], [3.5, -0.9, 2.1],
  [-1.5, 3.2, 0.5], [1.4, -2.1, 1.4], [-5.2, 0.4, 0.2], [5.1, 0.2, 0.4],
];

function OfferMatter({ admitted, index, progress }: { admitted: boolean; index: number; progress: number }) {
  const mesh = useRef<THREE.Mesh>(null);
  const material = useRef<THREE.MeshStandardMaterial>(null);
  const start = OFFER_POSITIONS[index % OFFER_POSITIONS.length];
  const angle = (index / 8) * Math.PI * 2;
  useFrame(() => {
    if (!mesh.current || !material.current) return;
    const chaos = ease(phase(progress, 0.34, 0.58));
    const resolve = ease(phase(progress, 0.58, 0.8));
    const settle = ease(phase(progress, 0.8, 1));
    const orbit: [number, number, number] = [Math.cos(angle) * 3.25, Math.sin(angle) * 1.95 + 0.7, 0.6];
    const end: [number, number, number] = [index % 2 ? 2.35 : -2.35, 1.7 - Math.floor(index / 2) * 0.62, 0.18];
    mesh.current.position.set(
      THREE.MathUtils.lerp(THREE.MathUtils.lerp(start[0], orbit[0], chaos), end[0], settle),
      THREE.MathUtils.lerp(THREE.MathUtils.lerp(start[1], orbit[1], chaos), end[1], settle),
      THREE.MathUtils.lerp(THREE.MathUtils.lerp(start[2], orbit[2], chaos), end[2], settle),
    );
    mesh.current.rotation.set(0, 0, THREE.MathUtils.lerp((index - 3) * 0.19, 0, settle));
    const survival = admitted ? 1 : 1 - resolve;
    mesh.current.scale.setScalar(THREE.MathUtils.lerp(0.82, admitted ? 0.62 : 0.22, settle) * Math.max(0.01, survival));
    material.current.opacity = admitted ? 0.92 : Math.max(0.03, 0.72 * (1 - resolve));
    material.current.roughness = admitted ? THREE.MathUtils.lerp(0.92, 0.28, resolve) : 1;
    material.current.metalness = admitted ? resolve * 0.2 : 0;
  });
  return (
    <mesh ref={mesh} position={start} castShadow={admitted}>
      <boxGeometry args={[1.08, 0.42, 0.08]} />
      <meshStandardMaterial ref={material} color={admitted ? "#f0c67a" : "#9c8775"} transparent wireframe={!admitted} />
    </mesh>
  );
}

function HeroProduct({ image, progress }: { image: string; progress: number }) {
  const root = useRef<THREE.Group>(null);
  const frame = useRef<THREE.MeshStandardMaterial>(null);
  useFrame(() => {
    if (!root.current || !frame.current) return;
    const reveal = ease(phase(progress, 0.27, 0.5));
    const resolve = ease(phase(progress, 0.58, 0.82));
    const settle = ease(phase(progress, 0.82, 1));
    root.current.position.set(0, THREE.MathUtils.lerp(-0.2, 0.4, settle), THREE.MathUtils.lerp(-0.6, 0.15, settle));
    root.current.rotation.y = Math.sin(progress * Math.PI * 2) * 0.12 * (1 - settle);
    root.current.scale.setScalar(THREE.MathUtils.lerp(0.72, 1.04, reveal) * (1 - settle * 0.22));
    frame.current.roughness = THREE.MathUtils.lerp(0.86, 0.22, resolve);
    frame.current.metalness = resolve * 0.26;
  });
  return (
    <group ref={root}>
      <RoundedBox args={[2.45, 2.85, 0.18]} radius={0.16} smoothness={4} castShadow>
        <meshStandardMaterial ref={frame} color="#efe6d6" roughness={0.86} />
      </RoundedBox>
      <group position={[0, 0, 0.105]}>
        <Suspense fallback={null}><ProductImage image={image} size={[1.9, 1.9]} /></Suspense>
      </group>
    </group>
  );
}

function WorldToInterface({ progress }: { progress: number }) {
  const plane = useRef<THREE.Mesh>(null);
  const material = useRef<THREE.MeshStandardMaterial>(null);
  useFrame(() => {
    const settle = ease(phase(progress, 0.82, 1));
    if (plane.current && material.current) {
      plane.current.position.y = THREE.MathUtils.lerp(-2.3, 0, settle);
      plane.current.scale.setScalar(THREE.MathUtils.lerp(0.82, 1, settle));
      material.current.opacity = settle * 0.98;
    }
  });
  return (
    <mesh ref={plane} position={[0, -2.3, -0.18]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[10.5, 7]} />
      <meshStandardMaterial ref={material} color="#f5efe5" roughness={0.92} transparent opacity={0} />
    </mesh>
  );
}

function Daylight({ progress }: { progress: number }) {
  const sun = useRef<THREE.DirectionalLight>(null);
  const proof = useRef<THREE.SpotLight>(null);
  useFrame(() => {
    const resolve = ease(phase(progress, 0.58, 0.82));
    if (sun.current) sun.current.intensity = 2.1 - resolve * 0.45;
    if (proof.current) proof.current.intensity = resolve * 4.8;
  });
  return (
    <>
      <hemisphereLight args={["#fff5df", "#69735e", 1.75]} />
      <directionalLight ref={sun} position={[-7, 10, 8]} color="#fff0d0" intensity={2.1} castShadow />
      <spotLight ref={proof} position={[5, 6, 4]} color="#ef8b54" intensity={0} angle={0.5} penumbra={0.88} distance={18} />
    </>
  );
}

function FounderWorld(props: FounderStoryCanvasProps) {
  const fragmentCount = props.compact ? 6 : props.quality === "degraded" ? 7 : 8;
  const admittedCount = Math.min(fragmentCount, props.offerCount);
  return (
    <>
      <color attach="background" args={["#d8d2be"]} />
      <fog attach="fog" args={["#d8d2be", 9, 24]} />
      <Daylight progress={props.progress} />
      <CameraJourney compact={props.compact} playing={props.playing} progress={props.progress} />
      <gridHelper args={[18, 22, "#8d7f6b", "#c6baa7"]} position={[0, -2.08, 0]} />
      <LaptopPortal image={props.product.image} progress={props.progress} />
      {BUILDINGS.slice(0, props.compact ? 4 : 6).map((building, index) => (
        <ShopBuilding key={index} data={building} image={props.product.image} index={index} progress={props.progress} />
      ))}
      {Array.from({ length: fragmentCount }, (_, index) => (
        <OfferMatter key={index} admitted={index < admittedCount} index={index} progress={props.progress} />
      ))}
      <HeroProduct image={props.product.image} progress={props.progress} />
      <WorldToInterface progress={props.progress} />
    </>
  );
}

export function FounderStoryCanvas(props: FounderStoryCanvasProps) {
  return (
    <Canvas
      camera={{ position: [0, 1.65, 11.8], fov: props.compact ? 54 : 44, near: 0.1, far: 80 }}
      dpr={props.quality === "degraded" ? 1 : [1, 1.35]}
      frameloop={props.playing ? "always" : "demand"}
      gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
      shadows={!props.compact && props.quality === "full"}
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
    >
      <CanvasLifecycle onFailure={props.onFailure} onReady={props.onReady} />
      <FounderWorld {...props} />
    </Canvas>
  );
}
