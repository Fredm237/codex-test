"use client";

// La traversée — l'environnement 3D plein écran de la page d'accueil.
//
// Correction d'après un second passage sur le compte, six Reels de plus.
// Ce que w.wearebrand appelle « site 3D » n'est pas un objet posé dans une
// page : c'est un LIEU plein cadre dans lequel on se déplace. Un chantier vu
// du ciel, un palais qu'on remonte, l'Everest, un intérieur qu'on traverse
// pièce par pièce. Le site est le monde ; le texte est rare et incrusté.
//
// Le premier jet faisait l'inverse — un bloc abstrait au centre d'un fond
// noir, avec du texte à côté. Il est remplacé.
//
// Le lieu est un atrium de béton banché : c'est l'architecture même du
// compte, et elle sert le propos de FILON — on descend dans un espace où les
// offres sont exposées, au lieu de les lire en liste.
//
// L'image d'environnement vient de Higgsfield, dirigée sur ce qui a été relevé
// sur les plans : béton chaud à trous de banche, spots ambrés à 2700 K,
// sous-exposition franche, végétation tropicale en contre-jour.
//
// Toujours pas de ScrollControls : il détourne le défilement et sort le
// contenu du DOM. Canvas fixe, DOM qui défile par-dessus, Lenis pour lisser.

import { Suspense, useRef, useState, useEffect } from "react";
import { Canvas, useFrame, useLoader } from "@react-three/fiber";
import * as THREE from "three";

const BETON_CLAIR = "#3a332c";
const BETON_SOMBRE = "#241f1a";

/** Progression 0→1 sur toute la hauteur défilable. */
function useProgressionPage() {
  const p = useRef(0);
  useEffect(() => {
    let raf = 0;
    const lire = () => {
      const course = document.documentElement.scrollHeight - window.innerHeight;
      p.current = course > 0 ? Math.min(Math.max(window.scrollY / course, 0), 1) : 0;
      raf = 0;
    };
    const file = () => {
      if (!raf) raf = requestAnimationFrame(lire);
    };
    window.addEventListener("scroll", file, { passive: true });
    window.addEventListener("resize", file, { passive: true });
    lire();
    return () => {
      window.removeEventListener("scroll", file);
      window.removeEventListener("resize", file);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);
  return p;
}

/** Le fond : l'atrium, projeté sur une sphère qui enveloppe la caméra. */
function Atrium() {
  const tex = useLoader(THREE.TextureLoader, "/3d/atrium.jpg");
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  return (
    <mesh scale={[-1, 1, 1]}>
      <sphereGeometry args={[60, 48, 32]} />
      <meshBasicMaterial map={tex} side={THREE.BackSide} toneMapped={false} />
    </mesh>
  );
}

/** Un portique de béton. Répétés en enfilade, ils font le couloir. */
function Portique({ z, teinte }: { z: number; teinte: string }) {
  return (
    <group position={[0, 0, z]}>
      {/* jambages */}
      <mesh position={[-3.1, 0, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.85, 7.2, 1.5]} />
        <meshStandardMaterial color={teinte} roughness={0.95} metalness={0.03} />
      </mesh>
      <mesh position={[3.1, 0, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.85, 7.2, 1.5]} />
        <meshStandardMaterial color={teinte} roughness={0.95} metalness={0.03} />
      </mesh>
      {/* linteau */}
      <mesh position={[0, 3.5, 0]} castShadow receiveShadow>
        <boxGeometry args={[7.05, 0.9, 1.5]} />
        <meshStandardMaterial color={teinte} roughness={0.95} metalness={0.03} />
      </mesh>
      {/* la flaque de spot sur le jambage droit — la lumière vient par
          points, jamais uniformément */}
      <pointLight position={[2.2, 1.6, 0.9]} intensity={5} distance={7} color="#ffcf8a" />
    </group>
  );
}

function Traversee({ prog }: { prog: React.MutableRefObject<number> }) {
  const PORTIQUES = 9;
  const PAS = 7;
  const sol = useRef<THREE.Mesh>(null);

  useFrame((state, dt) => {
    const p = prog.current;
    // La caméra avance dans le couloir : c'est le déplacement qui raconte,
    // pas la rotation d'un objet. Léger dévers pour éviter le rail de train.
    const z = 10 - p * (PORTIQUES - 1.5) * PAS;
    state.camera.position.z = THREE.MathUtils.lerp(state.camera.position.z, z, 1 - Math.pow(0.02, dt));
    state.camera.position.x = THREE.MathUtils.lerp(
      state.camera.position.x,
      Math.sin(p * Math.PI * 1.6) * 0.85,
      1 - Math.pow(0.05, dt)
    );
    state.camera.position.y = THREE.MathUtils.lerp(
      state.camera.position.y,
      -0.4 + Math.sin(p * Math.PI * 2.2) * 0.22,
      1 - Math.pow(0.05, dt)
    );
    state.camera.lookAt(0, -0.2, state.camera.position.z - 12);
    if (sol.current) sol.current.position.z = state.camera.position.z;
  });

  return (
    <>
      {/* Ambiance très basse : dans les plans observés, la lumière est rare.
          Le fond enveloppant fournit le reste. */}
      <ambientLight intensity={0.5} color="#c2b5a0" />
      <directionalLight position={[6, 9, 4]} intensity={1.1} color="#ffd7a0" castShadow />

      <Atrium />

      {/* Sol en dalles sombres, collé à la caméra pour rester infini */}
      <mesh ref={sol} rotation={[-Math.PI / 2, 0, 0]} position={[0, -3.6, 0]} receiveShadow>
        <planeGeometry args={[60, 160]} />
        <meshStandardMaterial color="#1d1916" roughness={0.8} metalness={0.12} />
      </mesh>

      {Array.from({ length: PORTIQUES }, (_, i) => (
        <Portique key={i} z={-i * PAS} teinte={i % 2 ? BETON_CLAIR : BETON_SOMBRE} />
      ))}
    </>
  );
}

export function Filon3D() {
  const prog = useProgressionPage();
  const [actif, setActif] = useState(false);

  // Ni sous « mouvement réduit », ni sur petit écran : la 3D pour la 3D
  // ralentit un site, et celui-ci reste entier sans elle.
  useEffect(() => {
    const reduit = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const petit = window.matchMedia("(max-width: 900px)").matches;
    setActif(!reduit && !petit);
  }, []);

  if (!actif) return null;

  return (
    <div className="fx-scene" aria-hidden="true">
      <Canvas
        shadows
        dpr={[1, 1.6]}
        camera={{ position: [0, -0.4, 10], fov: 58 }}
        gl={{ antialias: true, powerPreference: "high-performance" }}
      >
        <Suspense fallback={null}>
          <Traversee prog={prog} />
        </Suspense>
      </Canvas>
    </div>
  );
}
