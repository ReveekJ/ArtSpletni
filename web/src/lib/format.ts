import { currentLanguage } from "@/i18n";

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat(currentLanguage(), { dateStyle: "medium" }).format(new Date(value));
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(currentLanguage(), { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}
