import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const seq = useRef(0);
  // Store the latest fn in a ref so useCallback can read it without listing fn
  // as a dependency (which would cause a new callback on every render).
  const fnRef = useRef(fn);
  fnRef.current = fn;  // always up-to-date; safe to call inside the callback
  const run = useCallback(async (quiet = false) => {
    const id = ++seq.current;
    if (!quiet) setLoading(true);
    try {
      const v = await fnRef.current();
      if (id === seq.current) { setData(v); setError(null); }
    } catch (e) {
      if (id === seq.current) setError(e instanceof ApiError ? e : new ApiError(0, "UNKNOWN", String(e)));
    } finally {
      if (id === seq.current) setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { void run(); }, [run]);
  return { data, error, loading, reload: run, setData };
}

export function errorText(e: unknown): string {
  if (e instanceof ApiError) return e.correlationId && e.status >= 500 ? `${e.message} (ref ${e.correlationId.slice(0, 8)})` : e.message;
  return "Something unexpected happened. Try again.";
}
