"use client";

// Pile de coût — la scène 3D pilotée par le défilement.
//
// C'est le mécanisme observé chez w.wearebrand, pas son décor : sur les
// deux Reels les plus vus, le site montré tient sur un seul objet en 3D
// qui se transforme pendant qu'on descend. Le burger se sépare en ses
// couches (« THE STACK ») ; le site de fret enchaîne globe, conteneurs,
// grue, camion, porte-conteneurs. L'objet ne décore pas la page : il
// explique le produit.
//
// Transposé à FILON, l'objet évident est l'offre elle-même. Elle arrive
// comme un bloc plein — le prix affiché — puis se sépare en ce qui le
// compose réellement, couche par couche, et se referme sur le prix réel.
// C'est littéralement ce que fait le produit, rendu visible.
//
// Aucune donnée n'est inventée ici : les montants viennent du parent,
// qui les tient du catalogue. Sans données, la scène ne s'affiche pas.

import { Suspense, useRef, useMemo, useState, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

export type CostLayer = {
  /** Intitulé court affiché en regard de la couche. */
  label: string;
  /** Montant signé en euros : négatif pour ce qui se déduit. */
  amount: number;
};

const CONCRETE = "#2a2521";
const AMBER = "#c89544";

/** Une dalle de béton : une composante du prix. */
function Slab({
  index,
  count,
  progress,
  highlighted,
}: {
  index: number;
  count: number;
  progress: React.MutableRefObject<number>;
  highlighted: boolean;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const mat = useRef<THREE.MeshStandardMaterial>(null);

  // Chaque couche a sa fenêtre de séparation : elles ne s'écartent pas
  // toutes en même temps, sinon on lit un accordéon plutôt qu'une
  // décomposition.
  const start = index / (count + 1);

  useFrame(() => {
    if (!ref.current) return;
    const p = progress.current;
    // 0 → bloc plein ; 1 → couches séparées ; puis retour au bloc.
    const spread = THREE.MathUtils.clamp((p - start) * 2.2, 0, 1);
    const settle = THREE.MathUtils.clamp((p - 0.72) / 0.28, 0, 1);
    const open = spread * (1 - settle);

    const centered = index - (count - 1) / 2;
    const targetY = centered * (0.34 + open * 0.92);
    ref.current.position.y = THREE.MathUtils.lerp(ref.current.position.y, targetY, 0.12);
    ref.current.position.x = THREE.MathUtils.lerp(
      ref.current.position.x,
      open * (index % 2 === 0 ? -0.22 : 0.22),
      0.12
    );
    ref.current.rotation.y = THREE.MathUtils.lerp(
      ref.current.rotation.y,
      open * (index % 2 === 0 ? -0.16 : 0.16) + p * 0.5,
      0.1
    );

    // La couche courante prend la lumière : c'est le spot du hall,
    // pas un surlignage d'interface.
    if (mat.current) {
      const near = 1 - Math.min(Math.abs(p - (start + 0.12)) * 4.5, 1);
      const glow = highlighted ? Math.max(near, 0.25) : near;
      mat.current.emissiveIntensity = THREE.MathUtils.lerp(
        mat.current.emissiveIntensity,
        glow * 0.55,
        0.1
      );
    }
  });

  return (
    <mesh ref={ref} castShadow receiveShadow>
      <boxGeometry args={[2.6, 0.3, 1.7]} />
      <meshStandardMaterial
        ref={mat}
        color={CONCRETE}
        emissive={AMBER}
        emissiveIntensity={0}
        roughness={0.92}
        metalness={0.04}
      />
    </mesh>
  );
}

function Scene({
  layers,
  progress,
}: {
  layers: CostLayer[];
  progress: React.MutableRefObject<number>;
}) {
  const group = useRef<THREE.Group>(null);

  useFrame(() => {
    if (!group.current) return;
    // Le plan se redresse doucement : une caméra qui descend, pas un carrousel.
    const p = progress.current;
    group.current.rotation.x = THREE.MathUtils.lerp(
      group.current.rotation.x,
      0.32 - p * 0.24,
      0.08
    );
  });

  return (
    <>
      {/* Éclairage : un seul spot chaud rasant, une ambiance très basse.
          C'est l'étalonnage des plans observés — la lumière est rare. */}
      <ambientLight intensity={0.16} color="#b9ac97" />
      <spotLight
        position={[3.4, 6, 3.2]}
        angle={0.5}
        penumbra={1}
        intensity={38}
        color="#ffcf8a"
        castShadow
      />
      <pointLight position={[-3.5, -1.5, -2.5]} intensity={5} color="#4a5a3c" />
      <group ref={group}>
        {layers.map((l, i) => (
          <Slab
            key={l.label}
            index={i}
            count={layers.length}
            progress={progress}
            highlighted={i === layers.length - 1}
          />
        ))}
      </group>
    </>
  );
}

export function CostStack3D({
  layers,
  title,
}: {
  layers: CostLayer[];
  title: React.ReactNode;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const progress = useRef(0);
  const [active, setActive] = useState(0);
  const [enabled, setEnabled] = useState(false);

  // La scène ne se monte que si l'appareil et le réglage système
  // l'autorisent. Une carte graphique absente ou un « mouvement réduit »
  // renvoient au repli lisible, jamais à une page vide.
  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const coarse = window.matchMedia("(max-width: 720px)").matches;
    setEnabled(!reduced && !coarse);
  }, []);

  useEffect(() => {
    if (!enabled) return;
    let raf = 0;
    const onScroll = () => {
      const el = hostRef.current;
      if (!el) return;
      const r = el.getBoundingClientRect();
      const span = r.height - window.innerHeight;
      const p = span > 0 ? THREE.MathUtils.clamp(-r.top / span, 0, 1) : 0;
      progress.current = p;
      const i = Math.min(layers.length - 1, Math.floor(p * layers.length));
      setActive((prev) => (prev === i ? prev : i));
      raf = 0;
    };
    const queue = () => {
      if (!raf) raf = requestAnimationFrame(onScroll);
    };
    window.addEventListener("scroll", queue, { passive: true });
    onScroll();
    return () => {
      window.removeEventListener("scroll", queue);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [enabled, layers.length]);

  const fmt = useMemo(
    () => new Intl.NumberFormat("fr-BE", { style: "currency", currency: "EUR" }),
    []
  );

  return (
    <section ref={hostRef} className="fx-stack" aria-labelledby="fx-stack-title">
      <div className="fx-stack-sticky">
        <div className="fx-stack-canvas" aria-hidden="true">
          {enabled ? (
            <Canvas
              shadows
              dpr={[1, 1.75]}
              camera={{ position: [0, 0.6, 6.2], fov: 42 }}
              gl={{ antialias: true, alpha: true }}
            >
              <Suspense fallback={null}>
                <Scene layers={layers} progress={progress} />
              </Suspense>
            </Canvas>
          ) : null}
        </div>

        <div className="fx-stack-legend">
          <h2 id="fx-stack-title" className="fx-h2">
            {title}
          </h2>
          <ol className="fx-stack-list">
            {layers.map((l, i) => (
              <li
                key={l.label}
                className="fx-stack-item"
                aria-current={enabled && i === active ? "true" : undefined}
              >
                <span className="fx-stack-label">{l.label}</span>
                <span className="fx-stack-amount mono">
                  {l.amount > 0 && i > 0 ? "+" : ""}
                  {fmt.format(l.amount)}
                </span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
