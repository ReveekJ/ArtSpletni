import { currentLanguage } from "@/i18n";

export function formatDistance(distanceM: number, t: (key: string, options: { value: string }) => string) {
  const locale = currentLanguage();
  if (distanceM >= 1000) {
    const km = new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(distanceM / 1000);
    return t("app.gossip.distanceKm", { value: km });
  }
  const meters = new Intl.NumberFormat(locale).format(Math.max(10, Math.round(distanceM / 10) * 10));
  return t("app.gossip.distanceM", { value: meters });
}
