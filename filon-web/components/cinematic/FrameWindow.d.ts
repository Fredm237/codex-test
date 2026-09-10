export type FrameWindow = { from: number; to: number };

export function frameWindow(frame: number, frames: number, stride?: number): FrameWindow;
export function shouldRetainFrame(index: number, window: FrameWindow): boolean;
