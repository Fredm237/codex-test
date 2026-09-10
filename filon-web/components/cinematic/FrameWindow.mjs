export function frameWindow(frame, frames, stride = 1) {
  const safeStride = Math.max(1, stride);
  return {
    from: Math.max(0, frame - safeStride * 8),
    to: Math.min(frames - 1, frame + safeStride * 24),
  };
}

export function shouldRetainFrame(index, window) {
  return index === 0 || (index >= window.from && index <= window.to);
}
