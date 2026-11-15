import type { LngLat, YMap, YMapDefaultSchemeLayer } from "@yandex/ymaps3-types";
import { useEffect, useRef, useState } from "react";

import { useTheme } from "@/lib/theme";
import { loadYandexMaps, mapCustomization, YANDEX_MAPS_API_KEY, type YandexMapsApi } from "@/lib/yandexMaps";

export interface YandexMapHandle {
  api: YandexMapsApi;
  map: YMap;
}

export function useYandexMap(center: LngLat, zoom: number) {
  const element = useRef<HTMLDivElement>(null);
  const initial = useRef({ center, zoom });
  const scheme = useRef<YMapDefaultSchemeLayer | null>(null);
  const [handle, setHandle] = useState<YandexMapHandle | null>(null);
  const [failed, setFailed] = useState(!YANDEX_MAPS_API_KEY);
  const { resolved } = useTheme();
  const initialTheme = useRef(resolved);

  useEffect(() => {
    if (!YANDEX_MAPS_API_KEY || !element.current) return;
    let disposed = false;
    let created: YMap | null = null;
    loadYandexMaps()
      .then((api) => {
        if (disposed || !element.current) return;
        const schemeLayer = new api.YMapDefaultSchemeLayer({ customization: mapCustomization() });
        created = new api.YMap(
          element.current,
          { location: initial.current, theme: initialTheme.current, margin: [40, 40, 40, 40] },
          [schemeLayer, new api.YMapDefaultFeaturesLayer({})],
        );
        scheme.current = schemeLayer;
        setHandle({ api, map: created });
      })
      .catch((error: unknown) => {
        console.error("Yandex Maps failed to initialise", error);
        setFailed(true);
      });
    return () => {
      disposed = true;
      scheme.current = null;
      created?.destroy();
    };
  }, []);

  useEffect(() => {
    if (!handle) return;
    handle.map.update({ theme: resolved });
    scheme.current?.update({ customization: mapCustomization() });
  }, [handle, resolved]);

  return { element, handle, failed };
}
