import type { CustomizationConfig, LngLat, LngLatBounds } from "@yandex/ymaps3-types";

import { currentLanguage, type Language } from "@/i18n";

export type YandexMapsApi = typeof ymaps3;

export const YANDEX_MAPS_API_KEY: string = import.meta.env.VITE_YANDEX_MAPS_API_KEY ?? "";
export const EKATERINBURG_CENTER: LngLat = [60.6057, 56.8389];

const LOCALES: Record<Language, string> = { ru: "ru_RU", en: "en_US", zh: "en_US" };

let loader: Promise<YandexMapsApi> | null = null;

function injectScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://api-maps.yandex.ru/v3/?apikey=${encodeURIComponent(YANDEX_MAPS_API_KEY)}&lang=${LOCALES[currentLanguage()]}`;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Yandex Maps JS API v3 failed to load"));
    document.head.appendChild(script);
  });
}

export function loadYandexMaps(): Promise<YandexMapsApi> {
  loader ??= injectScript()
    .then(() => ymaps3.ready)
    .then(() => ymaps3)
    .catch((error: unknown) => {
      loader = null;
      throw error;
    });
  return loader;
}

function token(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim();
}

export function mapCustomization(): CustomizationConfig {
  const land = token("map-land");
  const road = token("map-road");
  return [
    {
      tags: { any: ["land", "landscape", "urban_area", "admin"] },
      elements: "geometry",
      stylers: [{ color: land }],
    },
    { tags: { any: ["water"] }, elements: "geometry", stylers: [{ color: token("map-water") }] },
    {
      tags: { any: ["park", "vegetation", "national_park", "cemetery", "sports_ground"] },
      elements: "geometry",
      stylers: [{ color: token("map-park") }],
    },
    { tags: { any: ["road", "path"] }, elements: "geometry", stylers: [{ color: road }] },
    {
      tags: { any: ["building", "structure"] },
      elements: "geometry",
      stylers: [{ color: road, opacity: 0.55 }],
    },
    { tags: { any: ["poi", "transit", "traffic_light", "entrance"] }, stylers: [{ visibility: "off" }] },
    { elements: "label.text.fill", stylers: [{ color: token("ink-muted") }] },
    { elements: "label.text.outline", stylers: [{ color: land }] },
    { elements: "label.icon", stylers: [{ visibility: "off" }] },
  ];
}

export function boundsOf(points: LngLat[]): LngLatBounds {
  const lngs = points.map((point) => point[0]);
  const lats = points.map((point) => point[1]);
  return [
    [Math.min(...lngs), Math.max(...lats)],
    [Math.max(...lngs), Math.min(...lats)],
  ];
}
