import { useEffect, useRef, useState } from "react";
import i18n from "../i18n/config";

interface MapMarker {
  latitude: number;
  longitude: number;
  name?: string | null;
}

interface LocationMapProps {
  latitude?: number;
  longitude?: number;
  name?: string | null;
  interactive?: boolean;
  center?: { latitude: number; longitude: number };
  onChange?: (coordinates: { latitude: number; longitude: number }) => void;
  markers?: MapMarker[];
  polyline?: boolean;
}

interface YandexGeoObject {
  events: {
    add: (event: string, handler: (event: YandexEvent) => void) => void;
  };
  geometry: {
    getCoordinates: () => [number, number];
    setCoordinates: (coordinates: [number, number]) => void;
  };
  properties: {
    set: (key: string, value: string) => void;
  };
}

interface YandexPolyline {
  geometry: {
    set: (coordinates: [number, number][]) => void;
  };
}

interface YandexMap {
  geoObjects: {
    add: (object: YandexGeoObject | YandexPolyline) => void;
    removeAll: () => void;
  };
  events: {
    add: (event: string, handler: (event: YandexEvent) => void) => void;
    remove: (event: string, handler: (event: YandexEvent) => void) => void;
  };
  setCenter: (coordinates: [number, number], zoom: number) => void;
  setBounds: (bounds: [[number, number], [number, number]], options?: { checkZoomRange?: boolean }) => void;
  destroy: () => void;
}

interface YandexEvent {
  get: (key: string) => unknown;
}

interface YandexMapsApi {
  ready: (callback: () => void) => void;
  Map: new (
    element: HTMLDivElement,
    state: { center: [number, number]; zoom: number },
  ) => YandexMap;
  Placemark: new (
    coordinates: [number, number],
    properties?: { hintContent?: string; balloonContent?: string },
    options?: { draggable?: boolean; preset?: string },
  ) => YandexGeoObject;
  Polyline: new (
    coordinates: [number, number][],
    properties?: Record<string, unknown>,
    options?: { strokeColor?: string; strokeWidth?: number },
  ) => YandexPolyline;
}

declare global {
  interface Window {
    ymaps?: YandexMapsApi;
  }
}

const yandexMapsKey = import.meta.env.VITE_YANDEX_MAPS_API_KEY;

const YANDEX_LANG_MAP: Record<string, string> = {
  ru: "ru_RU",
  en: "en_US",
  zh: "zh_CN",
};

function loadYandexMaps(): Promise<YandexMapsApi> {
  if (window.ymaps) {
    return new Promise((resolve) => window.ymaps?.ready(() => resolve(window.ymaps as YandexMapsApi)));
  }

  const yandexLang = YANDEX_LANG_MAP[i18n.language?.slice(0, 2) ?? "ru"] ?? "ru_RU";

  return new Promise((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>(
      'script[data-yandex-maps="true"]',
    );
    const script = existingScript ?? document.createElement("script");

    const handleLoad = () => {
      if (window.ymaps) {
        window.ymaps.ready(() => resolve(window.ymaps as YandexMapsApi));
      }
      else reject(new Error("Yandex Maps API did not initialize"));
    };

    script.addEventListener("load", handleLoad, { once: true });
    script.addEventListener("error", () => reject(new Error("Yandex Maps API failed to load")), {
      once: true,
    });

    if (!existingScript) {
      script.dataset.yandexMaps = "true";
      script.src = `https://api-maps.yandex.ru/2.1/?apikey=${encodeURIComponent(yandexMapsKey)}&lang=${yandexLang}`;
      script.async = true;
      document.head.appendChild(script);
    }
  });
}

const DEFAULT_CENTER = { latitude: 56.8389, longitude: 60.6057 };

export default function LocationMap({
  latitude,
  longitude,
  name,
  interactive = false,
  center,
  onChange,
  markers,
  polyline = false,
}: LocationMapProps) {
  const mapElement = useRef<HTMLDivElement>(null);
  const map = useRef<YandexMap | null>(null);
  const placemark = useRef<YandexGeoObject | null>(null);
  const onChangeRef = useRef(onChange);
  const pointRef = useRef({ latitude: latitude ?? DEFAULT_CENTER.latitude, longitude: longitude ?? DEFAULT_CENTER.longitude });
  const centerRef = useRef(center);
  const markersRef = useRef(markers);
  const [mapError, setMapError] = useState(false);

  pointRef.current = { latitude: latitude ?? DEFAULT_CENTER.latitude, longitude: longitude ?? DEFAULT_CENTER.longitude };
  centerRef.current = center;
  markersRef.current = markers;

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  const isMultiMarker = markers != null && markers.length > 0;

  useEffect(() => {
    if (!mapElement.current || !yandexMapsKey) return;
    let disposed = false;
    const initialPoint = pointRef.current;
    const initialCenter = centerRef.current ?? initialPoint;
    const coordinates: [number, number] = [initialCenter.latitude, initialCenter.longitude];

    loadYandexMaps()
      .then((api) => {
        if (disposed || !mapElement.current) return;
        map.current = new api.Map(mapElement.current, {
          center: coordinates,
          zoom: interactive ? 14 : 16,
        });

        if (isMultiMarker) {
          const currentMarkers = markersRef.current ?? [];
          const markerCoords: [number, number][] = [];
          for (const m of currentMarkers) {
            const mc: [number, number] = [m.latitude, m.longitude];
            markerCoords.push(mc);
            const pm = new api.Placemark(mc, {
              hintContent: m.name ?? "",
              balloonContent: m.name ?? "",
            }, { preset: "islands#dotIcon" });
            map.current.geoObjects.add(pm);
          }
          if (polyline && markerCoords.length >= 2) {
            const line = new api.Polyline(markerCoords, {}, {
              strokeColor: "#b5502a",
              strokeWidth: 3,
            });
            map.current.geoObjects.add(line);
          }
          if (markerCoords.length === 1) {
            map.current.setCenter(markerCoords[0], 16);
          } else {
            const lats = markerCoords.map((c) => c[0]);
            const lngs = markerCoords.map((c) => c[1]);
            const bounds: [[number, number], [number, number]] = [
              [Math.min(...lats), Math.min(...lngs)],
              [Math.max(...lats), Math.max(...lngs)],
            ];
            map.current.setBounds(bounds, { checkZoomRange: true });
          }
        } else {
          placemark.current = new api.Placemark(coordinates, {
            hintContent: name ?? undefined,
            balloonContent: name ?? undefined,
          }, { draggable: interactive });
          map.current.geoObjects.add(placemark.current);

          if (interactive) {
            const handleMapClick = (event: YandexEvent) => {
              const clicked = event.get("coords");
              if (!Array.isArray(clicked) || clicked.length < 2) return;
              const nextCoordinates: [number, number] = [
                Number(clicked[0]),
                Number(clicked[1]),
              ];
              placemark.current?.geometry.setCoordinates(nextCoordinates);
              onChangeRef.current?.({
                latitude: nextCoordinates[0],
                longitude: nextCoordinates[1],
              });
            };
            const handleDragEnd = () => {
              const nextCoordinates = placemark.current?.geometry.getCoordinates();
              if (!nextCoordinates) return;
              onChangeRef.current?.({
                latitude: nextCoordinates[0],
                longitude: nextCoordinates[1],
              });
            };
            map.current.events.add("click", handleMapClick);
            placemark.current.events.add("dragend", handleDragEnd);
          }
        }
      })
      .catch(() => setMapError(true));

    return () => {
      disposed = true;
      map.current?.destroy();
      map.current = null;
      placemark.current = null;
    };
  }, [interactive, isMultiMarker, polyline]);

  useEffect(() => {
    if (!map.current || isMultiMarker) return;
    if (!placemark.current || latitude == null || longitude == null) return;
    const coordinates: [number, number] = [latitude, longitude];
    placemark.current.geometry.setCoordinates(coordinates);
    if (!interactive) map.current.setCenter(coordinates, 16);
    placemark.current.properties.set("hintContent", name ?? "");
    placemark.current.properties.set("balloonContent", name ?? "");
  }, [interactive, latitude, longitude, name, isMultiMarker]);

  useEffect(() => {
    if (!map.current || !interactive || !center || isMultiMarker) return;
    map.current.setCenter([center.latitude, center.longitude], 16);
  }, [center, interactive, isMultiMarker]);

  return (
    <div className="map-wrap">
      {yandexMapsKey && !mapError ? (
        <div ref={mapElement} className="map-canvas" aria-label="Карта расположения" />
      ) : (
        <div className="map-placeholder">
          {mapError ? "Не удалось загрузить карту" : "Карта будет доступна после настройки API-ключа"}
        </div>
      )}
      {name && !isMultiMarker ? <p className="meta">{name}</p> : null}
      {interactive ? <p className="map-help">Нажмите на карту или перетащите метку, чтобы выбрать точку</p> : null}
    </div>
  );
}
