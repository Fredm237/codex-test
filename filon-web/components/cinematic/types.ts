export type Locale = "fr" | "nl" | "en";

export type TransitionKind =
  | "camera-pass"
  | "deep-zoom"
  | "orbit-reveal"
  | "spatial-travel"
  | "object-bridge"
  | "cut";

export type EasingKind = "hold" | "cinematic" | "reveal" | "settle";

export type FocusTarget = "arrival" | "world" | "explore" | "compare" | "opportunity" | "intelligence" | "score" | "decision" | "release";

export type CameraPose = {
  position: [number, number, number];
  target: [number, number, number];
  focalLength: number;
};

export type CopyFragment = {
  eyebrow?: string;
  title: string;
  detail?: string;
  cta?: { label: string; href: string };
};

export type Shot = {
  id: string;
  range: [number, number];
  focus: FocusTarget;
  transition: TransitionKind;
  easing: EasingKind;
  camera: { from: CameraPose; to: CameraPose };
  copy: Record<Locale, CopyFragment>;
  overlayRange: [number, number];
  visualRange: [number, number];
};

export type SequenceDefinition = {
  frameBase: string;
  frames: number;
  poster: string;
  scrollHeightVh: number;
  frameStride: number;
};

export type CinematicScene = {
  id: string;
  desktop: SequenceDefinition;
  mobile: SequenceDefinition;
  shots: Shot[];
  reducedMotion: {
    posterDesktop: string;
    posterMobile: string;
  };
};

export type TimelineState = {
  progress: number;
  shot: Shot;
  shotProgress: number;
  overlayOpacity: number;
  frameProgress: number;
};
