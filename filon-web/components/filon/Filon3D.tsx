"use client";

// Le filon — la scène 3D unique qui traverse toute la page d'accueil.
//
// Repris du mécanisme observé chez w.wearebrand : un seul objet, tenu d'un
// bout à l'autre, dont la transformation raconte le produit. Le burger se
// sépare en ses couches, le transporteur enchaîne globe, conteneurs, camion.
// Jamais une galerie d'effets : une seule chose qui se transforme.
//
// L'objet est donné par le nom de la marque. Un filon est une veine de
// minerai dans la roche : ce que l'on cherche est enfermé dans un bloc qui ne
// le montre pas. La séquence suit exactement cette idée.
//
//   0.00 → 0.22   le bloc est fermé, massif, il tourne lentement
//   0.22 → 0.48   il se fend, la veine ambrée apparaît à l'intérieur
//   0.48 → 0.74   il éclate en dalles — les composantes du prix
//   0.74 → 1.00   les dalles se referment autour de la veine
//
// Le parti technique : PAS de ScrollControls. Il détourne le défilement,
// casse l'ancrage clavier et sort le contenu du DOM — inacceptable pour un
// site qui doit être lu et indexé. Le canvas est donc fixe et transparent
// derrière un DOM qui défile normalement, et Lenis (déjà en place) lisse le
// mouvement. C'est le montage de r3f-scroll-rig, sans la dépendance.
//
// Les couleurs viennent du système existant : béton chaud, ambre du spot.
// Elles ne sont pas redéfinies ici, elles sont lues.

import { Suspense, useRef, useState, useEffect, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

const BETON = "#2a2521";
const BETON_SOMBRE = "#1a1613";
const AMBRE = "#c89544";

/** Progression 0→1 sur toute la hauteur défilable de la page. */
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

/** Interpolation bornée, avec adoucissement aux extrémités. */
function phase(p: number, debut: number, fin: number) {
  const t = THREE.MathUtils.clamp((p - debut) / (fin - debut), 0, 1);
  return t * t * (3 - 2 * t);
}

/** Une dalle du bloc. Six dalles forment la gangue autour de la veine. */
function Dalle({
  index,
  total,
  prog,
}: {
  index: number;
  total: number;
  prog: React.MutableRefObject<number>;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const centre = index - (total - 1) / 2;
  // Chaque dalle part dans sa direction propre : l'éclatement doit se lire
  // comme une ouverture, pas comme un accordéon.
  const ecart = useMemo(() => {
    const a = (index / total) * Math.PI * 2;
    return new THREE.Vector3(Math.cos(a) * 1.5, centre * 0.5, Math.sin(a) * 1.1);
  }, [index, total, centre]);

  useFrame((_, dt) => {
    if (!ref.current) return;
    const p = prog.current;
    const fente = phase(p, 0.22, 0.48);
    const eclat = phase(p, 0.48, 0.74);
    const refermeture = phase(p, 0.74, 1);
    // ouverture puis retour : la gangue se referme sur la veine
    const ouvert = Math.max(fente * 0.28 + eclat, 0) * (1 - refermeture * 0.82);

    const cible = new THREE.Vector3(
      ecart.x * ouvert,
      centre * 0.42 + ecart.y * ouvert,
      ecart.z * ouvert
    );
    ref.current.position.lerp(cible, 1 - Math.pow(0.001, dt));
    ref.current.rotation.y = THREE.MathUtils.lerp(
      ref.current.rotation.y,
      ouvert * (index % 2 ? 0.5 : -0.5),
      1 - Math.pow(0.004, dt)
    );
  });

  return (
    <mesh ref={ref} castShadow receiveShadow>
      <boxGeometry args={[2.5, 0.42, 1.7]} />
      <meshStandardMaterial
        color={index % 2 ? BETON : BETON_SOMBRE}
        roughness={0.95}
        metalness={0.05}
      />
    </mesh>
  );
}

/** La veine — ce que le bloc cache, et que le produit sert à trouver. */
function Veine({ prog }: { prog: React.MutableRefObject<number> }) {
  const ref = useRef<THREE.Mesh>(null);
  const mat = useRef<THREE.MeshStandardMaterial>(null);

  useFrame((_, dt) => {
    const p = prog.current;
    // Elle ne s'allume que lorsque la gangue s'ouvre : avant, rien ne prouve
    // qu'elle est là. C'est tout le propos.
    const revelee = phase(p, 0.24, 0.55);
    if (mat.current) {
      mat.current.emissiveIntensity = THREE.MathUtils.lerp(
        mat.current.emissiveIntensity,
        revelee * 2.4,
        1 - Math.pow(0.005, dt)
      );
      mat.current.opacity = 0.25 + revelee * 0.75;
    }
    if (ref.current) {
      const s = 0.55 + revelee * 0.45;
      ref.current.scale.setScalar(THREE.MathUtils.lerp(ref.current.scale.x, s, 0.08));
    }
  });

  return (
    <mesh ref={ref}>
      <icosahedronGeometry args={[0.82, 1]} />
      <meshStandardMaterial
        ref={mat}
        color={AMBRE}
        emissive={AMBRE}
        emissiveIntensity={0}
        roughness={0.35}
        metalness={0.7}
        transparent
        opacity={0.25}
      />
    </mesh>
  );
}

function Scene({ prog }: { prog: React.MutableRefObject<number> }) {
  const groupe = useRef<THREE.Group>(null);
  const DALLES = 6;

  useFrame((state, dt) => {
    if (!groupe.current) return;
    const p = prog.current;
    // Rotation continue lente — le plan respire, il ne tourne pas en vitrine.
    groupe.current.rotation.y += dt * 0.12;
    groupe.current.rotation.x = THREE.MathUtils.lerp(
      groupe.current.rotation.x,
      0.34 - p * 0.3,
      1 - Math.pow(0.01, dt)
    );
    // La caméra recule pendant l'éclatement, puis revient : le mouvement
    // accompagne l'ouverture au lieu de la subir.
    const recul = 6.4 + phase(p, 0.4, 0.74) * 2.2 - phase(p, 0.78, 1) * 1.4;
    state.camera.position.z = THREE.MathUtils.lerp(state.camera.position.z, recul, 0.05);
    state.camera.lookAt(0, 0, 0);
  });

  return (
    <>
      {/* Un seul spot chaud rasant, une ambiance très basse : l'étalonnage
          des plans observés, où la lumière est rare et vient par flaques. */}
      <ambientLight intensity={0.18} color="#b9ac97" />
      <spotLight
        position={[4, 6.5, 3.5]}
        angle={0.55}
        penumbra={1}
        intensity={46}
        color="#ffcf8a"
        castShadow
        shadow-mapSize={[1024, 1024]}
      />
      <pointLight position={[-4, -2, -3]} intensity={6} color="#4a5a3c" />
      <group ref={groupe}>
        <Veine prog={prog} />
        {Array.from({ length: DALLES }, (_, i) => (
          <Dalle key={i} index={i} total={DALLES} prog={prog} />
        ))}
      </group>
    </>
  );
}

export function Filon3D() {
  const prog = useProgressionPage();
  const [actif, setActif] = useState(false);

  // La scène ne se monte que si l'appareil et le réglage système l'autorisent.
  // « Éviter la 3D pour la 3D » : sur mobile elle rame, et sous « mouvement
  // réduit » elle n'a rien à faire là. Le site reste entier sans elle.
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
        camera={{ position: [0, 0.5, 6.4], fov: 42 }}
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      >
        <Suspense fallback={null}>
          <Scene prog={prog} />
        </Suspense>
      </Canvas>
    </div>
  );
}
