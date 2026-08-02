"use client";

// Orbe 3D interactif — Three.js + React Three Fiber
// L'orbe flotte, tourne lentement, et réagit au mouvement de la souris.
// Utilise le modèle GLB généré par Higgsfield.

import { Suspense, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { useGLTF, Environment, Float } from "@react-three/drei";
import * as THREE from "three";

function Orb() {
  const { scene } = useGLTF("/3d/orb.glb");
  const ref = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!ref.current) return;
    // Rotation lente continue
    ref.current.rotation.y += 0.003;
    // Réaction subtile à la souris
    const { pointer } = state;
    ref.current.rotation.x = THREE.MathUtils.lerp(
      ref.current.rotation.x,
      pointer.y * 0.2,
      0.05
    );
    ref.current.rotation.z = THREE.MathUtils.lerp(
      ref.current.rotation.z,
      -pointer.x * 0.1,
      0.05
    );
  });

  return (
    <Float speed={2} rotationIntensity={0.3} floatIntensity={0.5}>
      <group ref={ref} scale={2.5}>
        <primitive object={scene} />
      </group>
    </Float>
  );
}

export function OrbViewer3D() {
  return (
    <div className="fx-orb-viewer" aria-hidden="true">
      <Canvas
        camera={{ position: [0, 0, 4], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.4} />
          <pointLight position={[5, 5, 5]} intensity={1.2} color="#f5c542" />
          <pointLight position={[-5, -3, 2]} intensity={0.6} color="#4a90d9" />
          <Orb />
          <Environment preset="city" />
        </Suspense>
      </Canvas>
    </div>
  );
}
