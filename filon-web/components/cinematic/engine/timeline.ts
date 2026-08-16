import type { CinematicScene, EasingKind, Shot, TimelineState } from "../types";

const clamp = (value: number) => Math.max(0, Math.min(1, value));

export function ease(value: number, kind: EasingKind) {
  const t = clamp(value);
  if (kind === "hold") return t < 0.18 ? 0 : t > 0.82 ? 1 : (t - 0.18) / 0.64;
  if (kind === "reveal") return 1 - Math.pow(1 - t, 3);
  if (kind === "settle") return t * t * (3 - 2 * t);
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function localProgress(progress: number, range: [number, number]) {
  const [start, end] = range;
  return clamp((progress - start) / Math.max(0.0001, end - start));
}

export function resolveShot(shots: Shot[], progress: number) {
  return shots.find((shot) => progress >= shot.range[0] && progress <= shot.range[1]) ?? shots[shots.length - 1];
}

export function resolveTimeline(scene: CinematicScene, progress: number): TimelineState {
  const safeProgress = clamp(progress);
  const shot = resolveShot(scene.shots, safeProgress);
  const rawShotProgress = localProgress(safeProgress, shot.range);
  const shotProgress = ease(rawShotProgress, shot.easing);
  const overlayProgress = localProgress(safeProgress, shot.overlayRange);
  const overlayOpacity = Math.sin(Math.PI * clamp(overlayProgress));
  const frameProgress = clamp(
    shot.visualRange[0] + (shot.visualRange[1] - shot.visualRange[0]) * shotProgress,
  );

  return { progress: safeProgress, shot, shotProgress, overlayOpacity, frameProgress };
}

export function lerp(from: number, to: number, progress: number) {
  return from + (to - from) * progress;
}
