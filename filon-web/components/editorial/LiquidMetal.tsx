"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Liquid-metal 3D object (SmartWave chrome). WebGL runs only on capable
 * desktops, pauses when off-screen, and falls back to a CSS gradient orb on
 * mobile / low-power / reduced-motion — keeping the page fast everywhere.
 */
export function LiquidMetal({ className }: { className?: string }) {
  const [useGL, setUseGL] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Decide whether to run WebGL at all
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const nav = navigator as Navigator & { connection?: { saveData?: boolean }; deviceMemory?: number };
    const weak =
      window.innerWidth < 768 ||
      (typeof nav.hardwareConcurrency === "number" && nav.hardwareConcurrency <= 4) ||
      (typeof nav.deviceMemory === "number" && nav.deviceMemory <= 4) ||
      nav.connection?.saveData === true;
    let webglOk = false;
    try {
      const c = document.createElement("canvas");
      webglOk = !!(c.getContext("webgl") || c.getContext("experimental-webgl"));
    } catch {
      webglOk = false;
    }
    setUseGL(!reduce && !weak && webglOk);
  }, []);

  useEffect(() => {
    if (!useGL) return;
    const cv = canvasRef.current;
    if (!cv) return;
    const gl = cv.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: false });
    if (!gl) return;

    const vs = "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";
    const fs = [
      "precision highp float;uniform vec2 R;uniform float T;uniform vec2 M;",
      "mat2 rot(float a){float c=cos(a),s=sin(a);return mat2(c,-s,s,c);}",
      "float smin(float a,float b,float k){float h=clamp(0.5+0.5*(b-a)/k,0.,1.);return mix(b,a,h)-k*h*(1.-h);}",
      "float map(vec3 p){",
      " vec3 a=vec3(sin(T*0.7)*0.34,cos(T*0.5)*0.30,sin(T*0.3)*0.15);",
      " vec3 b=vec3(cos(T*0.6)*0.40,sin(T*0.8)*0.24,cos(T*0.45)*0.18);",
      " vec3 c=vec3(sin(T*0.9+1.0)*0.30,cos(T*0.7+2.0)*0.34,cos(T*0.5)*0.16);",
      " float d=smin(length(p-a)-0.50,length(p-b)-0.46,0.36);",
      " return smin(d,length(p-c)-0.42,0.36);}",
      "vec3 nrm(vec3 p){vec2 e=vec2(0.0015,0.);return normalize(vec3(map(p+e.xyy)-map(p-e.xyy),map(p+e.yxy)-map(p-e.yxy),map(p+e.yyx)-map(p-e.yyx)));}",
      "vec3 env(vec3 r){float y=r.y*0.5+0.5;",
      " vec3 teal=vec3(0.078,0.776,0.752),silver=vec3(0.97,0.98,1.0),blue=vec3(0.118,0.459,0.788);",
      " vec3 c=mix(teal,silver,smoothstep(0.0,0.48,y));c=mix(c,blue,smoothstep(0.52,1.0,y));",
      " c+=vec3(1.0)*pow(max(dot(r,normalize(vec3(0.4,0.85,0.5))),0.),90.);return c;}",
      "void main(){vec2 uv=(gl_FragCoord.xy-0.5*R)/R.y;",
      " vec3 ro=vec3(0.,0.,2.6);vec3 rd=normalize(vec3(uv,-1.7));",
      " float ry=T*0.12+M.x*0.5, rx=-0.08+M.y*0.32;",
      " mat2 RY=rot(ry),RX=rot(rx);",
      " ro.xz=RY*ro.xz;rd.xz=RY*rd.xz;ro.yz=RX*ro.yz;rd.yz=RX*rd.yz;",
      " float t=0.;float d;vec3 pos;bool hit=false;",
      " for(int i=0;i<90;i++){pos=ro+rd*t;d=map(pos);if(d<0.001){hit=true;break;}t+=d;if(t>7.)break;}",
      " if(!hit){gl_FragColor=vec4(0.);return;}",
      " vec3 n=nrm(pos);vec3 V=-rd;",
      " float fres=pow(1.-clamp(dot(n,V),0.,1.),3.0);",
      " vec3 refl=reflect(rd,n);",
      " vec3 col=env(refl);",
      " col=mix(col,vec3(1.0),fres*0.5);",
      " col*=vec3(0.90,0.97,1.0);",
      " col+=vec3(1.0)*pow(max(dot(refl,normalize(vec3(0.4,0.85,0.5))),0.),130.)*0.55;",
      " col=col/(1.0+col*0.14);col=pow(col,vec3(0.92));",
      " gl_FragColor=vec4(col,0.97);}",
    ].join("\n");

    const sh = (type: number, src: string) => {
      const o = gl.createShader(type)!;
      gl.shaderSource(o, src);
      gl.compileShader(o);
      if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) return null;
      return o;
    };
    const v = sh(gl.VERTEX_SHADER, vs);
    const f = sh(gl.FRAGMENT_SHADER, fs);
    if (!v || !f) return;
    const pr = gl.createProgram()!;
    gl.attachShader(pr, v);
    gl.attachShader(pr, f);
    gl.linkProgram(pr);
    gl.useProgram(pr);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const lp = gl.getAttribLocation(pr, "p");
    gl.enableVertexAttribArray(lp);
    gl.vertexAttribPointer(lp, 2, gl.FLOAT, false, 0, 0);
    const uR = gl.getUniformLocation(pr, "R");
    const uT = gl.getUniformLocation(pr, "T");
    const uM = gl.getUniformLocation(pr, "M");
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

    let mt = [0, 0];
    const m = [0, 0];
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const onMove = (e: MouseEvent) => {
      mt = [(e.clientX / window.innerWidth - 0.5) * 2, (e.clientY / window.innerHeight - 0.5) * 2];
    };
    window.addEventListener("mousemove", onMove, { passive: true });
    const size = () => {
      cv.width = cv.clientWidth * dpr;
      cv.height = cv.clientHeight * dpr;
      gl.viewport(0, 0, cv.width, cv.height);
    };
    size();
    window.addEventListener("resize", size);

    // Pause when off-screen or tab hidden (perf/battery)
    let onScreen = true;
    const io = new IntersectionObserver((es) => es.forEach((e) => (onScreen = e.isIntersecting)), { threshold: 0.01 });
    io.observe(cv);
    let tabVisible = true;
    const onVis = () => (tabVisible = !document.hidden);
    document.addEventListener("visibilitychange", onVis);

    const t0 = performance.now();
    let raf = 0;
    const frame = (now: number) => {
      if (onScreen && tabVisible) {
        m[0] += (mt[0] - m[0]) * 0.05;
        m[1] += (mt[1] - m[1]) * 0.05;
        gl.uniform2f(uR, cv.width, cv.height);
        gl.uniform1f(uT, (now - t0) / 1000);
        gl.uniform2f(uM, m[0], m[1]);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
      }
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("resize", size);
      document.removeEventListener("visibilitychange", onVis);
      io.disconnect();
    };
  }, [useGL]);

  return (
    <div className={className} aria-hidden="true">
      {useGL ? <canvas ref={canvasRef} /> : <div className="ed-coin-fallback" />}
    </div>
  );
}
