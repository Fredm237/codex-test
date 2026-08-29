export type SingleFlightRef<T> = { current: Promise<T> | null };

export function runSingleFlight<T>(
  ref: SingleFlightRef<T>,
  operation: () => Promise<T>,
  onPendingChange?: (pending: boolean) => void,
): Promise<T> {
  if (ref.current) return ref.current;
  onPendingChange?.(true);
  const inFlight = Promise.resolve().then(operation);
  ref.current = inFlight;
  const clear = () => {
    if (ref.current !== inFlight) return;
    ref.current = null;
    onPendingChange?.(false);
  };
  void inFlight.then(clear, clear);
  return inFlight;
}
