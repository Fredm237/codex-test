"use client";

import { useTexture } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Suspense, useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import type { ImmersiveQuality } from "./ImmersiveRuntime";
import {
  cinematicEase,
  dampAlpha,
  MATERIAL_SEQUENCE,
  phase,
  sampleCausalCamera,
  sampleCausalLights,
} from "./SignatureMotion";
import { bindWebglContextLoss } from "./WebglContextLoss.mjs";
import styles from "./signature-commerce.module.css";

type ProductProjection = { image: string | null; name: string } | null;
type SignatureWorld = "evidence" | "grand-receipt" | "cabinet";

type SignatureCanvasProps = {
  compact: boolean;
  offerCount: number;
  onFailure: () => void;
  playing: boolean;
  product: ProductProjection;
  progress: number;
  quality: ImmersiveQuality;
  onReady?: () => void;
  world?: SignatureWorld;
};

function CanvasLifecycle({ onFailure, onReady }: Pick<SignatureCanvasProps, "onFailure" | "onReady">) {
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
    gl.toneMappingExposure = 1.08;
    gl.setClearAlpha(0);

    const unbindContextLoss = bindWebglContextLoss(gl.domElement, () => failureRef.current());
    readyRef.current?.();
    return unbindContextLoss;
  }, [gl]);

  return null;
}

const RAW_POSITIONS: Array<[number, number, number]> = [
  [-4.6, 2.2, -2.4], [4.2, 2.5, -1.8], [-4.1, -2.1, 0.8], [4.8, -1.7, -0.6],
  [-2.9, 3.1, 1.5], [2.7, -3.2, 1.2], [-5.2, 0.2, 2.1], [5.1, 0.5, 1.8],
  [-1.5, 3.8, -2.8], [1.4, -3.8, -2.2], [-3.2, 0.3, -3.5], [3.4, -0.4, -3.2],
];

function sampleCabinetCamera(progress: number, compact: boolean) {
  const p = Math.max(0, Math.min(1, progress));
  const wide: [number, number, number] = [compact ? -1.8 : -3.8, 1.2, compact ? 11.8 : 10.2];
  const detail: [number, number, number] = [compact ? 1.4 : 2.3, .2, compact ? 5.6 : 4.5];
  const reveal: [number, number, number] = [compact ? -.8 : -1.7, 1.05, compact ? 8.8 : 7.5];
  const final: [number, number, number] = [0, compact ? .35 : .1, compact ? 10.6 : 9.2];
  const lerp = (from: [number, number, number], to: [number, number, number], amount: number): [number, number, number] => [
    THREE.MathUtils.lerp(from[0], to[0], amount),
    THREE.MathUtils.lerp(from[1], to[1], amount),
    THREE.MathUtils.lerp(from[2], to[2], amount),
  ];

  if (p < .34) {
    const t = cinematicEase(phase(p, 0, .34));
    return { position: lerp(wide, detail, t), target: [0, 0, 0] as [number, number, number], fov: THREE.MathUtils.lerp(48, 35, t), projection: "perspective" as const };
  }
  if (p < .76) {
    const t = cinematicEase(phase(p, .34, .76));
    return { position: lerp(detail, reveal, t), target: [0, 0, 0] as [number, number, number], fov: THREE.MathUtils.lerp(35, 42, t), projection: "perspective" as const };
  }
  const t = cinematicEase(phase(p, .76, 1));
  return {
    position: lerp(reveal, final, t),
    target: [0, -.08, 0] as [number, number, number],
    fov: THREE.MathUtils.lerp(42, 34, t),
    projection: p >= .92 ? "orthographic" as const : "perspective" as const,
  };
}

function CameraRig({ compact, playing, progress, world }: { compact: boolean; playing: boolean; progress: number; world?: SignatureWorld }) {
  const { camera, set, size } = useThree();
  const perspective = useRef(camera as THREE.PerspectiveCamera);
  const orthographic = useMemo(() => new THREE.OrthographicCamera(-4, 4, 4, -4, 0.1, 60), []);
  const activeCamera = useRef<"perspective" | "orthographic">("perspective");
  const target = useMemo(() => new THREE.Vector3(), []);
  const desired = useMemo(() => new THREE.Vector3(), []);
  const desiredTarget = useMemo(() => new THREE.Vector3(), []);

  useEffect(() => () => {
    set({ camera: perspective.current });
  }, [set]);

  useFrame((_, delta) => {
    const pose = world === "cabinet" ? sampleCabinetCamera(progress, compact) : sampleCausalCamera(progress, compact);
    desired.fromArray(pose.position);
    desiredTarget.fromArray(pose.target);
    const alpha = playing ? dampAlpha(delta) : 1;
    const perspectiveCamera = perspective.current;
    perspectiveCamera.position.lerp(desired, alpha);
    target.lerp(desiredTarget, alpha);
    perspectiveCamera.lookAt(target);
    perspectiveCamera.aspect = size.width / Math.max(size.height, 1);
    perspectiveCamera.fov = THREE.MathUtils.lerp(
      perspectiveCamera.fov,
      pose.fov,
      alpha,
    );
    perspectiveCamera.updateProjectionMatrix();

    const aspect = size.width / Math.max(size.height, 1);
    const frustum = compact ? 4.2 : 3.55;
    orthographic.left = -frustum * aspect;
    orthographic.right = frustum * aspect;
    orthographic.top = frustum;
    orthographic.bottom = -frustum;
    orthographic.position.lerp(desired, alpha);
    orthographic.lookAt(target);
    orthographic.updateProjectionMatrix();

    const nextCamera = pose.projection;
    if (activeCamera.current !== nextCamera) {
      activeCamera.current = nextCamera;
      set({ camera: nextCamera === "orthographic" ? orthographic : perspectiveCamera });
    }
  });
  return null;
}

function MarketFragment({ active, index, progress, total }: { active: boolean; index: number; progress: number; total: number }) {
  const mesh = useRef<THREE.Mesh>(null);
  const material = useRef<THREE.MeshStandardMaterial>(null);
  const raw = RAW_POSITIONS[index % RAW_POSITIONS.length];
  const ringAngle = (index / Math.max(total, 1)) * Math.PI * 2 - Math.PI / 2;
  const ring = useMemo<[number, number, number]>(() => [Math.cos(ringAngle) * 3.15, Math.sin(ringAngle) * 2.15, (index % 3 - 1) * 0.28], [index, ringAngle]);
  const final = useMemo<[number, number, number]>(() => {
    const column = index % 2 === 0 ? -1 : 1;
    const row = Math.floor(index / 2);
    return [column * 2.35, 1.48 - row * 0.58, active ? 0 : -0.35];
  }, [active, index]);

  useFrame(() => {
    if (!mesh.current || !material.current) return;
    const gather = cinematicEase(phase(progress, ...MATERIAL_SEQUENCE.gather));
    const seal = cinematicEase(phase(progress, ...MATERIAL_SEQUENCE.seal));
    const orbit = phase(progress, 0.34, 0.72) * (index % 2 ? -0.35 : 0.35);
    const orbitX = Math.cos(ringAngle + orbit) * 3.15;
    const orbitY = Math.sin(ringAngle + orbit) * 2.15;
    mesh.current.position.set(
      THREE.MathUtils.lerp(THREE.MathUtils.lerp(raw[0], orbitX, gather), final[0], seal),
      THREE.MathUtils.lerp(THREE.MathUtils.lerp(raw[1], orbitY, gather), final[1], seal),
      THREE.MathUtils.lerp(THREE.MathUtils.lerp(raw[2], ring[2], gather), final[2], seal),
    );
    mesh.current.rotation.set(
      THREE.MathUtils.lerp(index * 0.31, 0, seal),
      THREE.MathUtils.lerp(index * -0.23, 0, seal),
      THREE.MathUtils.lerp((index % 4) * 0.22, 0, seal),
    );
    const scale = active ? 1 : 0.72;
    mesh.current.scale.setScalar(THREE.MathUtils.lerp(scale, active ? 0.58 : 0.24, seal));
    const anneal = active ? cinematicEase(phase(progress, ...MATERIAL_SEQUENCE.anneal)) : 0;
    material.current.color.lerpColors(new THREE.Color(active ? "#2f769f" : "#9fb7c7"), new THREE.Color("#f05f43"), anneal);
    material.current.roughness = THREE.MathUtils.lerp(active ? 0.96 : 1, active ? 0.24 : 1, anneal);
    material.current.metalness = active ? anneal * 0.58 : 0;
    material.current.opacity = active ? THREE.MathUtils.lerp(0.76, 1, anneal) : THREE.MathUtils.lerp(0.17, 0.035, seal);
  });

  return (
    <mesh ref={mesh} castShadow={active} receiveShadow>
      <boxGeometry args={[1.36, 0.64, 0.16]} />
      <meshStandardMaterial ref={material} transparent wireframe={!active} depthWrite={active} />
    </mesh>
  );
}

function CausalLightRig({ progress }: { progress: number }) {
  const key = useRef<THREE.DirectionalLight>(null);
  const proof = useRef<THREE.SpotLight>(null);
  const decision = useRef<THREE.PointLight>(null);

  useFrame(() => {
    const lights = sampleCausalLights(progress);
    if (key.current) {
      key.current.position.fromArray(lights.key.position);
      key.current.intensity = lights.key.intensity;
    }
    if (proof.current) {
      proof.current.position.fromArray(lights.proof.position);
      proof.current.intensity = lights.proof.intensity;
    }
    if (decision.current) {
      decision.current.position.fromArray(lights.decision.position);
      decision.current.intensity = lights.decision.intensity;
    }
  });

  return (
    <>
      <ambientLight intensity={0.78} />
      <directionalLight ref={key} position={[-5.5, 3.5, 8]} color="#fffdf7" intensity={1.5} castShadow />
      <spotLight ref={proof} position={[6.5, 2, 2.2]} color="#f05f43" intensity={6} angle={0.38} penumbra={0.92} distance={20} />
      <pointLight ref={decision} position={[0, -2, 4]} color="#f4c84c" intensity={1.7} distance={10} />
    </>
  );
}

function ProductCore({ product, progress }: { product: ProductProjection; progress: number }) {
  const group = useRef<THREE.Group>(null);
  const proven = Boolean(product);

  useFrame(() => {
    if (!group.current) return;
    const focus = cinematicEase(phase(progress, ...MATERIAL_SEQUENCE.focus));
    const seal = cinematicEase(phase(progress, ...MATERIAL_SEQUENCE.seal));
    group.current.rotation.y = THREE.MathUtils.lerp(-0.34, Math.PI * 0.24, focus) * (1 - seal);
    group.current.rotation.x = THREE.MathUtils.lerp(0.22, -0.08, focus) * (1 - seal);
    group.current.scale.setScalar(THREE.MathUtils.lerp(0.82, 1.08, focus) - seal * 0.12);
  });

  return (
    <group ref={group}>
      {product?.image ? (
        <Suspense fallback={<ProductImageFallback />}>
          <ProductImagePlane image={product.image} />
        </Suspense>
      ) : <ProductImageFallback unknown />}
      {proven ? (
        <mesh position={[0, -1.72, -0.04]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <circleGeometry args={[1.45, 64]} />
          <meshStandardMaterial color="#fffdf7" transparent opacity={0.42} roughness={.92} />
        </mesh>
      ) : null}
    </group>
  );
}

function ProductImageFallback({ unknown = false }: { unknown?: boolean }) {
  return (
    <mesh position={[0, 0, 0.115]}>
      <ringGeometry args={[.72, .76, 64]} />
      <meshBasicMaterial color={unknown ? "#143451" : "#fffdf7"} transparent opacity={unknown ? 0.28 : 0.72} />
    </mesh>
  );
}

function ProductImagePlane({ image }: { image: string }) {
  const texture = useTexture(image);
  const size = useMemo<[number, number]>(() => {
    const source = texture.image as { naturalWidth?: number; naturalHeight?: number; width?: number; height?: number } | undefined;
    const width = source?.naturalWidth || source?.width || 1;
    const height = source?.naturalHeight || source?.height || 1;
    const ratio = width / Math.max(height, 1);
    const maxWidth = 2.72;
    const maxHeight = 3.18;
    return ratio >= maxWidth / maxHeight
      ? [maxWidth, maxWidth / ratio]
      : [maxHeight * ratio, maxHeight];
  }, [texture]);

  useEffect(() => {
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 4;
    texture.needsUpdate = true;
  }, [texture]);

  return (
    <group position={[0, 0, 0.116]}>
      <mesh>
        <planeGeometry args={size} />
        <meshBasicMaterial map={texture} toneMapped={false} />
      </mesh>
    </group>
  );
}

function EvidenceSeal({ progress, proven }: { progress: number; proven: boolean }) {
  const plane = useRef<THREE.Mesh>(null);
  const material = useRef<THREE.MeshStandardMaterial>(null);
  const beam = useRef<THREE.Mesh>(null);

  useFrame(() => {
    const settle = cinematicEase(phase(progress, ...MATERIAL_SEQUENCE.seal));
    if (plane.current && material.current) {
      plane.current.position.y = THREE.MathUtils.lerp(-3.4, -1.62, settle);
      material.current.opacity = settle * 0.72;
    }
    if (beam.current) {
      const scan = phase(progress, 0.48, 0.74);
      beam.current.position.x = THREE.MathUtils.lerp(-4.8, 4.8, scan);
      beam.current.visible = scan > 0 && scan < 1 && proven;
    }
  });

  return (
    <>
      <mesh ref={plane} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[11, 7]} />
        <meshStandardMaterial ref={material} color="#ddecf3" transparent opacity={0} roughness={0.82} metalness={0.04} />
      </mesh>
      <mesh ref={beam} position={[-4.8, 0, 0.9]}>
        <boxGeometry args={[0.045, 5.8, 0.025]} />
        <meshBasicMaterial color="#f05f43" transparent opacity={0.72} blending={THREE.NormalBlending} />
      </mesh>
    </>
  );
}

function CommerceWorld({ compact, offerCount, playing, product, progress, quality }: SignatureCanvasProps) {
  const fragmentCount = compact ? 7 : quality === "degraded" ? 9 : 12;
  const activeCount = Math.min(fragmentCount, offerCount);
  const proven = Boolean(product && offerCount >= 2);

  return (
    <>
      <color attach="background" args={["#ddecf3"]} />
      <fog attach="fog" args={["#ddecf3", compact ? 7 : 8, compact ? 18 : 20]} />
      <CausalLightRig progress={progress} />
      <CameraRig compact={compact} playing={playing} progress={progress} world="evidence" />
      <gridHelper args={[18, 18, "#6795b5", "#b8d1df"]} position={[0, -1.64, 0]} />
      {Array.from({ length: fragmentCount }, (_, index) => (
        <MarketFragment key={index} active={index < activeCount} index={index} progress={progress} total={fragmentCount} />
      ))}
      <ProductCore product={product} progress={progress} />
      <EvidenceSeal progress={progress} proven={proven} />
    </>
  );
}

const RECEIPT_PATH: Array<[number, number, number]> = [
  [-4.8, 2.8, -2.4], [4.5, 2.3, -2.1], [-4.2, -2.4, -1.3], [4.6, -2.2, -.8],
  [-2.8, 3.4, .6], [2.5, -3.4, .8], [-5.1, .2, 1.4], [5.2, .4, 1.6],
  [-1.4, 3.8, -2.8], [1.2, -3.8, -2.6],
];

function ReceiptPanel({ index, progress, total }: { index: number; progress: number; total: number }) {
  const group = useRef<THREE.Group>(null);
  const paper = useRef<THREE.MeshStandardMaterial>(null);
  const raw = RECEIPT_PATH[index % RECEIPT_PATH.length];
  const centred = index - (total - 1) / 2;

  useFrame(() => {
    if (!group.current || !paper.current) return;
    const gather = cinematicEase(phase(progress, .05, .48));
    const seal = cinematicEase(phase(progress, .72, 1));
    const wave = Math.sin(index * 1.37 + progress * Math.PI * 1.8) * .16 * (1 - seal);
    const ribbonX = centred * .88;
    const ribbonY = -1.5 + wave;
    const ribbonZ = centred * -.08;
    const finalX = (index % 2 === 0 ? -1 : 1) * 1.72;
    const finalY = 1.52 - Math.floor(index / 2) * .64;
    group.current.position.set(
      THREE.MathUtils.lerp(THREE.MathUtils.lerp(raw[0], ribbonX, gather), finalX, seal),
      THREE.MathUtils.lerp(THREE.MathUtils.lerp(raw[1], ribbonY, gather), finalY, seal),
      THREE.MathUtils.lerp(THREE.MathUtils.lerp(raw[2], ribbonZ, gather), -.32, seal),
    );
    const gatheredRotationX = THREE.MathUtils.lerp((index % 3 - 1) * .24, -Math.PI / 2, gather);
    group.current.rotation.set(
      THREE.MathUtils.lerp(gatheredRotationX, 0, seal),
      THREE.MathUtils.lerp(index * -.13, 0, seal),
      THREE.MathUtils.lerp(index % 2 ? -.08 : .08, 0, seal),
    );
    paper.current.roughness = THREE.MathUtils.lerp(.88, .68, seal);
    paper.current.color.lerpColors(new THREE.Color("#f5efe2"), new THREE.Color("#fffdf7"), seal);
  });

  const accent = index % 3 === 0 ? "#d95d3d" : index % 3 === 1 ? "#2f718c" : "#d1a446";
  return (
    <group ref={group}>
      <mesh castShadow receiveShadow>
        <boxGeometry args={[.78, .52, .035]} />
        <meshStandardMaterial ref={paper} color="#f5efe2" roughness={.88} metalness={0} />
      </mesh>
      <mesh position={[0, .11, .021]}>
        <boxGeometry args={[.54, .035, .008]} />
        <meshBasicMaterial color={accent} />
      </mesh>
      <mesh position={[0, -.05, .021]}>
        <boxGeometry args={[.46, .018, .008]} />
        <meshBasicMaterial color="#887d6e" transparent opacity={.52} />
      </mesh>
      <mesh position={[-.08, -.13, .021]}>
        <boxGeometry args={[.3, .014, .008]} />
        <meshBasicMaterial color="#887d6e" transparent opacity={.32} />
      </mesh>
    </group>
  );
}

function MerchantSeal({ index, progress, total }: { index: number; progress: number; total: number }) {
  const group = useRef<THREE.Group>(null);
  const angle = (index / Math.max(total, 1)) * Math.PI * 2 - Math.PI / 2;

  useFrame(() => {
    if (!group.current) return;
    const prove = cinematicEase(phase(progress, .42, .74));
    const settle = cinematicEase(phase(progress, .74, 1));
    const radius = THREE.MathUtils.lerp(2.9, 2.28, prove);
    group.current.position.set(
      THREE.MathUtils.lerp(Math.cos(angle) * radius, index % 2 ? 2.72 : -2.72, settle),
      THREE.MathUtils.lerp(Math.sin(angle) * 1.86, -1.58 + Math.floor(index / 2) * .36, settle),
      THREE.MathUtils.lerp(.45, -.14, settle),
    );
    group.current.rotation.z = THREE.MathUtils.lerp(angle + Math.PI / 2, 0, settle);
    group.current.scale.setScalar(THREE.MathUtils.lerp(.42, .7, prove));
  });

  return (
    <group ref={group}>
      <mesh castShadow>
        <cylinderGeometry args={[.3, .3, .055, 48]} />
        <meshStandardMaterial color="#c85638" roughness={.5} metalness={.08} />
      </mesh>
      <mesh position={[0, .035, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[.17, .018, 12, 40]} />
        <meshBasicMaterial color="#f8e8d1" />
      </mesh>
    </group>
  );
}

function ReceiptPedestal({ progress }: { progress: number }) {
  const table = useRef<THREE.Group>(null);

  useFrame(() => {
    if (!table.current) return;
    const focus = cinematicEase(phase(progress, .12, .48));
    table.current.position.y = THREE.MathUtils.lerp(-2.05, -1.82, focus);
    table.current.rotation.y = THREE.MathUtils.lerp(-.08, .025, focus);
  });

  return (
    <group ref={table}>
      <mesh receiveShadow castShadow>
        <boxGeometry args={[8.4, .48, 5.8]} />
        <meshStandardMaterial color="#c9bda9" roughness={.78} metalness={.02} />
      </mesh>
      <mesh position={[0, .251, 0]} receiveShadow>
        <boxGeometry args={[8.25, .012, 5.65]} />
        <meshStandardMaterial color="#dfd5c4" roughness={.6} metalness={.03} />
      </mesh>
      <mesh position={[0, -.78, .1]} receiveShadow>
        <boxGeometry args={[5.8, 1.1, 3.9]} />
        <meshStandardMaterial color="#b3a58f" roughness={.84} />
      </mesh>
    </group>
  );
}

function DaylightRig({ progress }: { progress: number }) {
  const sun = useRef<THREE.DirectionalLight>(null);
  const proof = useRef<THREE.SpotLight>(null);

  useFrame(() => {
    const focus = cinematicEase(phase(progress, .16, .52));
    const settle = cinematicEase(phase(progress, .72, 1));
    if (sun.current) {
      sun.current.position.set(THREE.MathUtils.lerp(-6, 3.5, focus), 8, 6);
      sun.current.intensity = THREE.MathUtils.lerp(2.4, 3.4, focus) * (1 - settle * .14);
    }
    if (proof.current) proof.current.intensity = THREE.MathUtils.lerp(0, 18, focus) * (1 - settle * .6);
  });

  return (
    <>
      <hemisphereLight color="#fff7e8" groundColor="#9db5bd" intensity={1.35} />
      <directionalLight ref={sun} position={[-6, 8, 6]} color="#fff0d2" intensity={2.4} castShadow />
      <spotLight ref={proof} position={[4, 5, 4]} color="#f6c66f" intensity={0} angle={.46} penumbra={.9} distance={22} />
    </>
  );
}

function GrandReceiptWorld({ compact, offerCount, playing, product, progress, quality }: SignatureCanvasProps) {
  const panelCount = compact || quality === "degraded" ? 6 : 10;
  const merchantCount = Math.min(compact ? 4 : 8, Math.max(0, offerCount));

  return (
    <>
      <color attach="background" args={["#e9e4d8"]} />
      <fog attach="fog" args={["#e9e4d8", compact ? 8 : 10, compact ? 19 : 24]} />
      <DaylightRig progress={progress} />
      <CameraRig compact={compact} playing={playing} progress={progress} world="grand-receipt" />
      <ReceiptPedestal progress={progress} />
      {Array.from({ length: panelCount }, (_, index) => (
        <ReceiptPanel key={index} index={index} progress={progress} total={panelCount} />
      ))}
      {Array.from({ length: merchantCount }, (_, index) => (
        <MerchantSeal key={index} index={index} progress={progress} total={merchantCount} />
      ))}
      <ProductCore product={product} progress={progress} />
    </>
  );
}

function CabinetGlassFrame({ progress }: { progress: number }) {
  const group = useRef<THREE.Group>(null);
  const glass = useRef<THREE.MeshPhysicalMaterial>(null);

  useFrame(() => {
    if (!group.current || !glass.current) return;
    const focus = cinematicEase(phase(progress, .08, .42));
    const settle = cinematicEase(phase(progress, .7, 1));
    group.current.rotation.y = THREE.MathUtils.lerp(-.18, .04, focus) * (1 - settle);
    group.current.position.x = THREE.MathUtils.lerp(.34, 0, settle);
    glass.current.opacity = THREE.MathUtils.lerp(.12, .24, focus) * (1 - settle * .38);
  });

  const bars: Array<{ position: [number, number, number]; size: [number, number, number] }> = [
    { position: [-2.18, 0, 0], size: [.06, 4.1, .08] },
    { position: [2.18, 0, 0], size: [.06, 4.1, .08] },
    { position: [0, 2.02, 0], size: [4.42, .06, .08] },
    { position: [0, -2.02, 0], size: [4.42, .06, .08] },
  ];

  return (
    <group ref={group}>
      <mesh position={[0, 0, -.08]} receiveShadow>
        <planeGeometry args={[4.36, 4]} />
        <meshPhysicalMaterial
          ref={glass}
          color="#dbe8e6"
          metalness={0}
          opacity={.12}
          roughness={.08}
          thickness={.12}
          transmission={.9}
          transparent
        />
      </mesh>
      {bars.map((bar, index) => (
        <mesh key={index} position={bar.position} castShadow>
          <boxGeometry args={bar.size} />
          <meshStandardMaterial color="#9da5a1" metalness={.82} roughness={.24} />
        </mesh>
      ))}
      <mesh position={[0, -1.66, .04]} receiveShadow>
        <boxGeometry args={[4.28, .12, 1.18]} />
        <meshStandardMaterial color="#d5cab8" roughness={.72} metalness={.02} />
      </mesh>
    </group>
  );
}

function CabinetWorld({ compact, playing, product, progress }: SignatureCanvasProps) {
  return (
    <>
      <fog attach="fog" args={["#eee9df", compact ? 9 : 11, compact ? 20 : 26]} />
      <DaylightRig progress={progress} />
      <CameraRig compact={compact} playing={playing} progress={progress} world="cabinet" />
      <CabinetGlassFrame progress={progress} />
      <ProductCore product={product} progress={progress} />
    </>
  );
}

export function SignatureCommerceCanvas(props: SignatureCanvasProps) {
  const signature = props.world === "cabinet"
    ? "cabinet"
    : props.world === "grand-receipt"
      ? "grand-receipt"
      : "commerce-evidence";
  return (
    <div className={styles.canvas} aria-hidden="true" data-webgl-signature={signature}>
      <Canvas
        camera={{ position: [0, 1.8, 10.5], fov: props.compact ? 52 : 46, near: 0.1, far: 60 }}
        dpr={props.quality === "degraded" ? 1 : [1, 1.35]}
        frameloop={props.playing ? "always" : "demand"}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        shadows={!props.compact && props.quality === "full"}
      >
        <CanvasLifecycle onFailure={props.onFailure} onReady={props.onReady} />
        {props.world === "cabinet"
          ? <CabinetWorld {...props} />
          : props.world === "grand-receipt"
            ? <GrandReceiptWorld {...props} />
            : <CommerceWorld {...props} />}
      </Canvas>
    </div>
  );
}
