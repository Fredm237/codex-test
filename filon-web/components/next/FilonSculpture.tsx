"use client";

import { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer, Float, useTexture } from "@react-three/drei";
import type { WorldMode } from "./SpatialShell";
import * as THREE from "three";

/** An original extruded FILON glyph; no model download or frame sequence. */
function Sculpture({ active, mode, texture, angle }: { active: boolean; mode: WorldMode; texture: string|null; angle:boolean }) {
  const group = useRef<THREE.Group>(null);
  const satellites = useRef<THREE.Group>(null);
  const pointer=useRef({x:0,y:0});
  useEffect(()=>{
    const move=(e:PointerEvent)=>{if(e.pointerType==="mouse"){pointer.current={x:e.clientX/window.innerWidth*2-1,y:-(e.clientY/window.innerHeight*2-1)};}};
    window.addEventListener("pointermove",move,{passive:true});
    return()=>window.removeEventListener("pointermove",move);
  },[]);
  const glyph = useMemo(() => {
    const shape = new THREE.Shape();
    shape.moveTo(-1.12, -1.6);
    shape.lineTo(-1.12, 1.6);
    shape.lineTo(1.2, 1.6);
    shape.lineTo(1.2, .78);
    shape.lineTo(-.24, .78);
    shape.lineTo(-.24, .12);
    shape.lineTo(.86, .12);
    shape.lineTo(.86, -.66);
    shape.lineTo(-.24, -.66);
    shape.lineTo(-.24, -1.6);
    shape.closePath();
    return new THREE.ExtrudeGeometry(shape, { depth: .64, bevelEnabled: true, bevelSegments: 5, steps: 1, bevelSize: .1, bevelThickness: .12 });
  }, []);
  useEffect(() => () => glyph.dispose(), [glyph]);
  useFrame((state, delta) => {
    if (!group.current || !active) return;
    const d = Math.min(delta, .04);
    const target = { home: -.42, catalogue: .3, assistant: -.8, product: .6, editorial: -.25 }[mode];
    const scroll = Math.min(1, window.scrollY / Math.max(1, window.innerHeight));
    group.current.rotation.y = THREE.MathUtils.damp(group.current.rotation.y, target + (angle ? .9 : 0) + pointer.current.x * .3 + scroll * .45, 3, d);
    const scale = mode === "home" ? 1 : mode === "assistant" ? .85 : .66;
    group.current.scale.setScalar(THREE.MathUtils.damp(group.current.scale.x,scale,3,d));
    if(satellites.current) satellites.current.rotation.y += d * .045;
    group.current.rotation.x = THREE.MathUtils.damp(group.current.rotation.x, .1 - pointer.current.y * .18, 3, d);
  });
  return (
    <group ref={group} rotation={[.1, -.42 + (angle ? .9 : 0), -.1]} scale={mode === "home" ? 1 : .75}>
      <group ref={satellites} visible={mode !== "home"}>
        {Array.from({length:6},(_,i)=>{
          const a=i*Math.PI/3;
          return <mesh key={i} position={[Math.cos(a)*3.4,Math.sin(a)*2.3,-.8]} rotation={[.25,a,.2]}>
            <boxGeometry args={mode === "editorial" ? [1.05,1.5,.06] : [.65,.65,.65]} />
            <meshPhysicalMaterial color={i===1?"#ceff80":"#aab8dc"} metalness={.85} roughness={.2} clearcoat={1}/>
          </mesh>;
        })}
      </group>
      <Float speed={active ? 1.3 : 0} rotationIntensity={.12} floatIntensity={.35}>
        {texture ? <ProductProjection texture={texture} /> : <mesh geometry={glyph} position={[0, 0, -.3]}>
          <meshPhysicalMaterial color="#dce1ff" metalness={.95} roughness={.16} clearcoat={1} clearcoatRoughness={.12} />
        </mesh>}
        <mesh position={[.1, 0, -.72]} rotation={[0, 0, .35]}>
          <torusGeometry args={[2.2, .065, 12, 100]} />
          <meshStandardMaterial color="#cbff75" emissive="#b8ff53" emissiveIntensity={1.1} metalness={.4} roughness={.2} />
        </mesh>
        <mesh position={[.15, 0, -.75]} rotation={[.95, .65, -.3]}>
          <torusGeometry args={[2.52, .017, 8, 100]} />
          <meshStandardMaterial color="#a6b4e4" metalness={.9} roughness={.22} />
        </mesh>
        <mesh position={[1.78, 1.4, .5]}>
          <octahedronGeometry args={[.23, 0]} />
          <meshPhysicalMaterial color="#ceff80" metalness={.4} roughness={.1} clearcoat={1} />
        </mesh>
        <mesh position={[-1.65, -1.15, .75]}>
          <sphereGeometry args={[.11, 20, 16]} />
          <meshStandardMaterial color="#e6eaff" metalness={1} roughness={.1} />
        </mesh>
      </Float>
    </group>
  );
}

function ProductProjection({texture}:{texture:string}) {
  const map=useTexture(texture);
  useEffect(()=>{map.colorSpace=THREE.SRGBColorSpace;},[map]);
  const ratio=(map.image as HTMLImageElement).width/(map.image as HTMLImageElement).height;
  const width=Math.min(3,3.4*ratio), height=width/ratio;
  return <group>
    <mesh position={[0,0,-.08]}><boxGeometry args={[3.2,3.6,.14]}/><meshStandardMaterial color="#e7edf8" metalness={.8} roughness={.2}/></mesh>
    <mesh position={[0,0,.001]}><planeGeometry args={[width,height]}/><meshBasicMaterial map={map} toneMapped={false}/></mesh>
  </group>;
}

function Lifecycle({ onFailure }: { onFailure: () => void }) {
  const { gl } = useThree();
  useEffect(() => {
    const canvas = gl.domElement;
    const lost = (event: Event) => { event.preventDefault(); onFailure(); };
    canvas.addEventListener("webglcontextlost", lost);
    return () => canvas.removeEventListener("webglcontextlost", lost);
  }, [gl, onFailure]);
  return null;
}

export default function FilonSculpture({ active, onFailure, mode, texture, angle }: { active: boolean; onFailure: () => void; mode: WorldMode; texture:string|null; angle:boolean }) {
  return (
    <Canvas dpr={[1, 1.5]} camera={{ position: [0, 0, 7.7], fov: 42 }} frameloop={active ? "always" : "demand"} gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}>
      <Lifecycle onFailure={onFailure} />
      <ambientLight intensity={.6} />
      <directionalLight position={[3, 4, 5]} intensity={2.4} color="#eef3ff" />
      <pointLight position={[-3, -2, 3]} intensity={18} color="#647bff" />
      <Suspense fallback={null}>
        <Environment resolution={128}>
          <Lightformer intensity={4} position={[0, 4, 2]} scale={[10, 2, 1]} />
          <Lightformer intensity={3} position={[-4, 0, 2]} rotation={[0, Math.PI / 2, 0]} scale={[4, 8, 1]} color="#abbaff" />
          <Lightformer intensity={4} position={[4, 1, 0]} rotation={[0, -Math.PI / 2, 0]} scale={[2, 6, 1]} />
          <Lightformer intensity={2} position={[0, -4, 2]} rotation={[Math.PI / 2, 0, 0]} scale={[8, 4, 1]} color="#ceff80" />
        </Environment>
        <Sculpture active={active} mode={mode} texture={texture} angle={angle} />
      </Suspense>
    </Canvas>
  );
}
