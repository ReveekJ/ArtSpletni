import type { Schemas } from "@/api/client";

export type LocalizedValue = Record<string, string>;
export type LocalizedOut = Record<string, Schemas["LocalizedField"]>;

export function fromLocalized(value: LocalizedOut | undefined): LocalizedValue {
  return Object.fromEntries(Object.entries(value ?? {}).map(([lang, field]) => [lang, field.text]));
}

export function cleanLocalized(value: LocalizedValue): LocalizedValue | null {
  const entries = Object.entries(value).filter(([, text]) => text.trim() !== "");
  return entries.length ? Object.fromEntries(entries) : null;
}
