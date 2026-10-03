import { useEffect, useRef, useState } from "react";

interface LocationMapProps {
  latitude: number;
  longitude: number;
  name?: string | null;
  interactive?: boolean;
  center?: { latitude: number; longitude: number };
  onChange?: (coordinates: { latitude: number; longitude: number }) => void;
}

interface YandexMap {
  geoObjects: {
    add: (object: YandexPlacemark) => void;
  };
  events: {
    add: (event: string, handler: (event: YandexEvent) => void) => void;
    remove: (event: string, handler: (event: YandexEvent) => void) => void;
  };
  setCenter: (coordinates: [number, number], zoom: number) => void;
  destroy: () => void;
}

interface YandexPlacemark {
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
    options?: { draggable?: boolean },
  ) => YandexPlacemark;
}

declare global {
  interface Window {
    ymaps?: YandexMapsApi;
  }
}

const yandexMapsKey = import.meta.env.VITE_YANDEX_MAPS_API_KEY;

function loadYandexMaps(): Promise<YandexMapsApi> {
  if (window.ymaps) {
    return new Promise((resolve) => window.ymaps?.ready(() => resolve(window.ymaps as YandexMapsApi)));
  }

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
      script.src = `https://api-maps.yandex.ru/2.1/?apikey=${encodeURIComponent(yandexMapsKey)}&lang=ru_RU`;
      script.async = true;
      document.head.appendChild(script);
    }
  });
}

export default function LocationMap({
  latitude,
  longitude,
  name,
  interactive = false,
  center,
  onChange,
}: LocationMapProps) {
  const mapElement = useRef<HTMLDivElement>(null);
  const map = useRef<YandexMap | null>(null);
  const placemark = useRef<YandexPlacemark | null>(null);
  const onChangeRef = useRef(onChange);
  const pointRef = useRef({ latitude, longitude });
  const centerRef = useRef(center);
  const [mapError, setMapError] = useState(false);

  pointRef.current = { latitude, longitude };
  centerRef.current = center;

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

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
      })
      .catch(() => setMapError(true));

    return () => {
      disposed = true;
      map.current?.destroy();
      map.current = null;
      placemark.current = null;
    };
  }, [interactive]);

  useEffect(() => {
    if (!map.current || !placemark.current) return;
    const coordinates: [number, number] = [latitude, longitude];
    placemark.current.geometry.setCoordinates(coordinates);
    if (!interactive) map.current.setCenter(coordinates, 16);
    placemark.current.properties.set("hintContent", name ?? "");
    placemark.current.properties.set("balloonContent", name ?? "");
  }, [interactive, latitude, longitude, name]);

  useEffect(() => {
    if (!map.current || !interactive || !center) return;
    map.current.setCenter([center.latitude, center.longitude], 16);
  }, [center, interactive]);

  return (
    <div className="map-wrap">
      {yandexMapsKey && !mapError ? (
        <div ref={mapElement} className="map-canvas" aria-label="Карта расположения" />
      ) : (
        <div className="map-placeholder">
          {mapError ? "Не удалось загрузить карту" : "Карта будет доступна после настройки API-ключа"}
        </div>
      )}
      {name ? <p className="meta">{name}</p> : null}
      {interactive ? <p className="map-help">Нажмите на карту или перетащите метку, чтобы выбрать точку</p> : null}
    </div>
  );
}
