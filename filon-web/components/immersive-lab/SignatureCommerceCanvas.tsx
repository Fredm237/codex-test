"use client";

import { Edges, RoundedBox, useTexture } from "@react-three/drei";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Suspense, useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import styles from "./signature-commerce.module.css";

type ProductProjection = { image: string | null; name: string } | null;

type SignatureCanvasProps = {
  compact: boolean;
  offerCount: number;
  playing: boolean;
  product: ProductProjection;
  progress: number;
};

const RAW_POSITIONS: Array<[number, number, number]> = [
  [-4.6, 2.2, -2.4], [4.2, 2.5, -1.8], [-4.1, -2.1, 0.8], [4.8, -1.7, -0.6],
  [-2.9, 3.1, 1.5], [2.7, -3.2, 1.2], [-5.2, 0.2, 2.1], [5.1, 0.5, 1.8],
  [-1.5, 3.8, -2.8], [1.4, -3.8, -2.2], [-3.2, 0.3, -3.5], [3.4, -0.4, -3.2],
];

function clamp(value: number, low = 0, high = 1) {
  return Math.max(low, Math.min(high, value));
}

function phase(progress: number, start: number, end: number) {
  return clamp((progress - start) / (end - start));
}

function smooth(value: number) {
  const x = clamp(value);
  return x * x * (3 - 2 * x);
}

function CameraRig({ compact, playing, progress }: { compact: boolean; playing: boolean; progress: number }) {
  const { camera, set, size } = useThree();
  const perspective = useRef(camera as THREE.PerspectiveCamera);
  const orthographic = useMemo(() => new THREE.OrthographicCamera(-4, 4, 4, -4, 0.1, 60), []);
  const activeCamera = useRef<"perspective" | "orthographic">("perspective");
  const target = useMemo(() => new THREE.Vector3(), []);
  const desired = useMemo(() => new THREE.Vector3(), []);

  useEffect(() => () => {
    set({ camera: perspective.current });
  }, [set]);

  useFrame(() => {
    const wideToMacro = smooth(phase(progress, 0, 0.34));
    const orbit = smooth(phase(progress, 0.34, 0.72));
    const settle = smooth(phase(progress, 0.72, 1));
    const portrait = compact ? 1 : 0;

    if (progress < 0.34) {
      desired.set(
        THREE.MathUtils.lerp(0, 2.65 - portrait * 0.8, wideToMacro),
        THREE.MathUtils.lerp(1.8, 0.35, wideToMacro),
        THREE.MathUtils.lerp(10.5 + portrait * 2.2, 4.3 + portrait, wideToMacro),
      );
    } else if (progress < 0.72) {
      const angle = THREE.MathUtils.lerp(-0.2, Math.PI * 0.82, orbit);
      const radius = compact ? 5.3 : 4.9;
      desired.set(Math.sin(angle) * radius, THREE.MathUtils.lerp(0.35, 1.35, orbit), Math.cos(angle) * radius);
    } else {
      desired.set(
        THREE.MathUtils.lerp(3.9, 0, settle),
        THREE.MathUtils.lerp(1.25, compact ? 4.8 : 5.8, settle),
        THREE.MathUtils.lerp(4.5, compact ? 9.8 : 8.2, settle),
      );
    }

    const alpha = playing ? 0.13 : 1;
    const perspectiveCamera = perspective.current;
    perspectiveCamera.position.lerp(desired, alpha);
    target.set(0, settle * -0.2, 0);
    perspectiveCamera.lookAt(target);
    perspectiveCamera.aspect = size.width / Math.max(size.height, 1);
    perspectiveCamera.fov = THREE.MathUtils.lerp(
      perspectiveCamera.fov,
      THREE.MathUtils.lerp(compact ? 52 : 46, 31, settle),
      alpha,
    );
    perspectiveCamera.updateProjectionMatrix();

    const aspect = size.width / Math.max(size.height, 1);
    const frustum = compact ? 4.2 : 3.55;
    orthographic.left = -frustum * aspect;
    orthographic.right = frustum * aspect;
    orthographic.top = frustum;
    orthographic.bottom = -frustum;
    orthographic.position.set(0, compact ? 5.7 : 6.4, compact ? 9.6 : 8.8);
    orthographic.lookAt(0, -0.2, 0);
    orthographic.updateProjectionMatrix();

    const nextCamera = progress >= 0.9 ? "orthographic" : "perspective";
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
    const gather = smooth(phase(progress, 0.08, 0.45));
    const seal = smooth(phase(progress, 0.7, 0.96));
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
    const anneal = active ? smooth(phase(progress, 0.46, 0.74)) : 0;
    material.current.color.lerpColors(new THREE.Color(active ? "#71503f" : "#3b342e"), new THREE.Color("#c89544"), anneal);
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
    const identity = smooth(phase(progress, 0.2, 0.48));
    const anneal = smooth(phase(progress, 0.46, 0.76));
    const settle = smooth(phase(progress, 0.76, 1));
    if (key.current) {
      key.current.position.set(
        THREE.MathUtils.lerp(-5.5, 0.8, identity),
        THREE.MathUtils.lerp(3.5, 7.4, identity),
        THREE.MathUtils.lerp(8, 4.2, anneal),
      );
      key.current.intensity = THREE.MathUtils.lerp(1.25, 3.1, identity) * (1 - settle * 0.22);
    }
    if (proof.current) {
      proof.current.position.x = THREE.MathUtils.lerp(6.5, -2.4, anneal);
      proof.current.position.z = THREE.MathUtils.lerp(2.2, 6.8, anneal);
      proof.current.intensity = THREE.MathUtils.lerp(8, 48, anneal) * (1 - settle * 0.5);
    }
    if (decision.current) {
      decision.current.position.y = THREE.MathUtils.lerp(-2, 3.4, settle);
      decision.current.intensity = THREE.MathUtils.lerp(2, 15, settle);
    }
  });

  return (
    <>
      <ambientLight intensity={0.18} />
      <directionalLight ref={key} position={[-5.5, 3.5, 8]} color="#fff0da" intensity={1.25} castShadow />
      <spotLight ref={proof} position={[6.5, 2, 2.2]} color="#f05a31" intensity={8} angle={0.38} penumbra={0.92} distance={20} />
      <pointLight ref={decision} position={[0, -2, 4]} color="#e8a34b" intensity={2} distance={10} />
    </>
  );
}

function ProductCore({ product, progress }: { product: ProductProjection; progress: number }) {
  const group = useRef<THREE.Group>(null);
  const shell = useRef<THREE.MeshStandardMaterial>(null);
  const proven = Boolean(product);

  useFrame(() => {
    if (!group.current || !shell.current) return;
    const focus = smooth(phase(progress, 0.2, 0.52));
    const seal = smooth(phase(progress, 0.72, 1));
    group.current.rotation.y = THREE.MathUtils.lerp(-0.34, Math.PI * 0.24, focus) * (1 - seal);
    group.current.rotation.x = THREE.MathUtils.lerp(0.22, -0.08, focus) * (1 - seal);
    group.current.scale.setScalar(THREE.MathUtils.lerp(0.82, 1.08, focus) - seal * 0.12);
    shell.current.roughness = proven ? THREE.MathUtils.lerp(0.82, 0.2, smooth(phase(progress, 0.46, 0.76))) : 1;
    shell.current.metalness = proven ? smooth(phase(progress, 0.46, 0.76)) * 0.68 : 0;
    shell.current.emissiveIntensity = proven ? 0.08 + focus * 0.18 : 0.02;
  });

  return (
    <group ref={group}>
      <RoundedBox args={[2.36, 2.92, 0.2]} radius={0.13} smoothness={5} castShadow receiveShadow>
        <meshStandardMaterial
          ref={shell}
          color={proven ? "#7f4a34" : "#302925"}
          emissive={proven ? "#7d2e1c" : "#181512"}
          transparent
          opacity={proven ? 0.9 : 0.62}
          wireframe={!proven}
        />
        <Edges color={proven ? "#e4aa66" : "#6c625b"} threshold={12} />
      </RoundedBox>
      {product?.image ? (
        <Suspense fallback={<ProductImageFallback />}>
          <ProductImagePlane image={product.image} />
        </Suspense>
      ) : <ProductImageFallback unknown />}
      <mesh position={[0, -1.64, 0.06]} castShadow>
        <boxGeometry args={[3.04, 0.08, 0.54]} />
        <meshStandardMaterial color={proven ? "#d89750" : "#4b433e"} metalness={0.46} roughness={0.34} />
      </mesh>
      <mesh position={[-1.44, 0, 0.02]}>
        <boxGeometry args={[0.025, 3.58, 0.025]} />
        <meshBasicMaterial color={proven ? "#f05a31" : "#665c55"} transparent opacity={0.82} />
      </mesh>
      <mesh position={[1.44, 0, 0.02]}>
        <boxGeometry args={[0.025, 3.58, 0.025]} />
        <meshBasicMaterial color={proven ? "#d69a48" : "#665c55"} transparent opacity={0.58} />
      </mesh>
    </group>
  );
}

function ProductImageFallback({ unknown = false }: { unknown?: boolean }) {
  return (
    <mesh position={[0, 0, 0.115]}>
      <planeGeometry args={[1.86, 2.38]} />
      <meshBasicMaterial color={unknown ? "#2d2622" : "#eadfce"} transparent opacity={unknown ? 0.38 : 0.92} />
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
    const maxWidth = 1.86;
    const maxHeight = 2.38;
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
        <planeGeometry args={[1.86, 2.38]} />
        <meshBasicMaterial color="#eadfce" transparent opacity={0.92} />
      </mesh>
      <mesh position={[0, 0, 0.008]}>
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
    const settle = smooth(phase(progress, 0.72, 1));
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
        <meshStandardMaterial ref={material} color="#211914" transparent opacity={0} roughness={0.72} metalness={0.12} />
      </mesh>
      <mesh ref={beam} position={[-4.8, 0, 0.9]}>
        <boxGeometry args={[0.045, 5.8, 0.025]} />
        <meshBasicMaterial color="#ffb36a" transparent opacity={0.78} blending={THREE.AdditiveBlending} />
      </mesh>
    </>
  );
}

function CommerceWorld({ compact, offerCount, playing, product, progress }: SignatureCanvasProps) {
  const fragmentCount = compact ? 7 : 12;
  const activeCount = Math.min(fragmentCount, offerCount);
  const proven = Boolean(product && offerCount >= 2);

  return (
    <>
      <color attach="background" args={["#0b0908"]} />
      <fog attach="fog" args={["#0b0908", compact ? 7 : 8, compact ? 18 : 20]} />
      <CausalLightRig progress={progress} />
      <CameraRig compact={compact} playing={playing} progress={progress} />
      <gridHelper args={[18, 18, "#6e4737", "#241b17"]} position={[0, -1.64, 0]} />
      {Array.from({ length: fragmentCount }, (_, index) => (
        <MarketFragment key={index} active={index < activeCount} index={index} progress={progress} total={fragmentCount} />
      ))}
      <ProductCore product={product} progress={progress} />
      <EvidenceSeal progress={progress} proven={proven} />
    </>
  );
}

export function SignatureCommerceCanvas(props: SignatureCanvasProps) {
  return (
    <div className={styles.canvas} aria-hidden="true" data-webgl-signature="commerce-evidence">
      <Canvas
        camera={{ position: [0, 1.8, 10.5], fov: props.compact ? 52 : 46, near: 0.1, far: 60 }}
        dpr={[1, 1.35]}
        frameloop={props.playing ? "always" : "demand"}
        gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
        shadows={!props.compact}
        onCreated={({ gl }) => {
          gl.outputColorSpace = THREE.SRGBColorSpace;
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.08;
        }}
      >
        <CommerceWorld {...props} />
      </Canvas>
    </div>
  );
}
