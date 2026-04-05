"use client";

import * as React from "react";

function easeOutCubic(t: number): number {
  return 1 - (1 - t) ** 3;
}

/**
 * Animates from 0 to `end` over `durationMs` (client-only).
 */
export function useCountUp(end: number, durationMs: number) {
  const [value, setValue] = React.useState(0);

  React.useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(1, elapsed / durationMs);
      setValue(from + (end - from) * easeOutCubic(t));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [end, durationMs]);

  return value;
}
