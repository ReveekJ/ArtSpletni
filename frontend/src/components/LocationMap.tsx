import { useEffect, useRef, useState } from "react";

interface LocationMapProps {
  latitude: number;
  longitude: number;
  name?: string | null;
}

interface YandexMap {
  geoObjects: {
    add: (object: YandexPlacemark) => void;
  };
  setCenter: (coordinates: [number, number], zoom: number) => void;
  destroy: () => void;
}

interface YandexPlacemark {
  properties: {
    set: (key: string, value: string) => void;
  };
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

export default function LocationMap({ latitude, longitude, name }: LocationMapProps) {
  const mapElement = useRef<HTMLDivElement>(null);
  const map = useRef<YandexMap | null>(null);
  const [mapError, setMapError] = useState(false);

  useEffect(() => {
    if (!mapElement.current || !yandexMapsKey) return;
    let disposed = false;

    loadYandexMaps()
      .then((api) => {
        if (disposed || !mapElement.current) return;
        map.current = new api.Map(mapElement.current, {
          center: [latitude, longitude],
          zoom: 16,
        });
        const placemark = new api.Placemark([latitude, longitude], {
          hintContent: name ?? undefined,
          balloonContent: name ?? undefined,
        });
        map.current.geoObjects.add(placemark);
      })
      .catch(() => setMapError(true));

    return () => {
      disposed = true;
      map.current?.destroy();
      map.current = null;
    };
  }, [latitude, longitude, name]);

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
    </div>
  );
}
