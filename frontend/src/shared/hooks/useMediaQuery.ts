import { useEffect, useState } from "react";

/**
 * Returns true while the given media query matches.
 * SSR-safe: defaults to false on the server.
 *
 * Example: const isMobile = useMediaQuery("(max-width: 640px)");
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia(query);
    setMatches(mql.matches);

    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [query]);

  return matches;
}
