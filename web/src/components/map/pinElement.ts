import { cn } from "@/lib/utils";

export type MarkerState = "done" | "current" | "open" | "locked";

export function pinElement(state: MarkerState, label?: string, title?: string | null): HTMLElement {
  const element = document.createElement("span");
  element.className = cn(
    "sk-pin absolute -translate-x-1/2 -translate-y-1/2 select-none",
    state === "done" && "sk-pin--done",
    state === "current" && "sk-pin--now",
    state === "locked" && "sk-pin--locked",
  );
  if (label && state !== "locked") element.textContent = label;
  if (title) {
    element.title = title;
    element.setAttribute("aria-label", title);
    element.setAttribute("role", "img");
  }
  return element;
}
