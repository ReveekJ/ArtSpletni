import Lenis from "lenis";
import { useEffect } from "react";

const REDUCED_MOTION = "(prefers-reduced-motion: reduce)";

export function useSmoothScroll(): void {
  useEffect(() => {
    if (window.matchMedia(REDUCED_MOTION).matches) return;
    const lenis = new Lenis({
      autoRaf: true,
      lerp: 0.09,
      anchors: { offset: -8 },
      prevent: (node) => node.closest("[role='dialog'], [data-lenis-prevent]") !== null,
    });
    return () => lenis.destroy();
  }, []);
}
