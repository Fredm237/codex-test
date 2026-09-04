export function bindWebglContextLoss(
  target: Pick<HTMLCanvasElement, "addEventListener" | "removeEventListener">,
  onFailure: () => void,
): () => void;
