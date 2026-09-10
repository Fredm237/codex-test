"use client";
import { useEffect } from "react";

/** A real product photograph is projected into the shared scene, never a fabricated 3D model. */
export function ProductStage({ image, texture, name, ean }: { image: string | null; texture: string | null; name: string; ean?: string }) {
 useEffect(()=>{
  window.dispatchEvent(new CustomEvent("filon:spatial-product",{detail:{texture}}));
  return()=>{window.dispatchEvent(new CustomEvent("filon:spatial-product",{detail:{texture:null}}));};
 },[texture]);
 return <div className="fn-product-stage fn-spatial-card" data-product-transition-target>
   <div className="fn-product-stage-label"><span>FILON / PRODUCT</span>{ean&&<span>EAN {ean}</span>}</div>
   {image ? <img src={image} alt={name} /> : <span className="fn-product-stage-missing">—</span>}
   <div className="fn-product-stage-caption">{name}</div>
 </div>;
}
