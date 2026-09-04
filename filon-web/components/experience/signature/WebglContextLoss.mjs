/**
 * Bascule l'enrichissement immersif vers son récit DOM quand le navigateur
 * perd le contexte GPU. `preventDefault` conserve la possibilité de restauration
 * native, tandis que le cleanup garantit qu'aucun listener ne survit au canvas.
 *
 * @param {Pick<HTMLCanvasElement, "addEventListener" | "removeEventListener">} target
 * @param {() => void} onFailure
 */
export function bindWebglContextLoss(target, onFailure) {
  /** @type {EventListener} */
  const handleContextLoss = (event) => {
    event.preventDefault();
    onFailure();
  };

  target.addEventListener("webglcontextlost", handleContextLoss);
  return () => target.removeEventListener("webglcontextlost", handleContextLoss);
}
