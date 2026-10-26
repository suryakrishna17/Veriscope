import { useEffect, useState } from "react";

export type Route =
  | { name: "landing" }
  | { name: "login" }
  | { name: "queue" }
  | { name: "new" }
  | { name: "analytics" }
  | { name: "coverage" }
  | { name: "case"; id: string }
  | { name: "report"; id: string }
  | { name: "notfound" };

export function parse(hash: string): Route {
  const path = hash.replace(/^#/, "");
  // Empty hash → landing; explicit /landing → landing
  if (!path || path === "/" || path === "/landing") return { name: "landing" };
  const parts = path.split("/").filter(Boolean);
  if (parts[0] === "landing") return { name: "landing" };
  if (parts[0] === "login") return { name: "login" };
  if (parts[0] === "analytics") return { name: "analytics" };
  if (parts[0] === "coverage") return { name: "coverage" };
  if (parts[0] === "cases" && parts.length === 1) return { name: "queue" };
  if (parts[0] === "cases" && parts[1] === "new") return { name: "new" };
  if (parts[0] === "cases" && parts[1] && parts[2] === "report") return { name: "report", id: decodeURIComponent(parts[1]) };
  if (parts[0] === "cases" && parts[1]) return { name: "case", id: decodeURIComponent(parts[1]) };
  return { name: "notfound" };
}

export function navigate(path: string) {
  window.location.hash = path;
}

export function useRoute(): Route {
  const [route, setRoute] = useState(() => parse(window.location.hash));
  useEffect(() => {
    const on = () => setRoute(parse(window.location.hash));
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return route;
}
