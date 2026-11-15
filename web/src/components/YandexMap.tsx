import type { LngLat, YMapEntity, YMapMarker } from "@yandex/ymaps3-types";
import { type RefObject, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

import { type MarkerState, pinElement } from "@/components/map/pinElement";
import { useYandexMap } from "@/components/map/useYandexMap";
import { Icon } from "@/components/ui/icon";
import { useTheme } from "@/lib/theme";
import { boundsOf, EKATERINBURG_CENTER } from "@/lib/yandexMaps";

export type { MarkerState };

export interface MapMarker {
  id: string;
  latitude: number;
  longitude: number;
  title?: string | null;
  muted?: boolean;
  label?: string;
  state?: MarkerState;
}

const FRAME =
  "relative h-[300px] w-full overflow-hidden rounded-lg border-sketch bg-map-land shadow-sketch-lg";
const ROUTE_STROKE_WIDTH = 3;
const AHEAD_DASH = [7, 7];

function MapFrame({ failed, element }: { failed: boolean; element: RefObject<HTMLDivElement> }) {
  const { t } = useTranslation();
  if (failed)
    return (
      <div className={`${FRAME} grid place-items-center gap-2 p-6 text-center text-body-sm text-ink-muted`}>
        <span className="flex flex-col items-center gap-2">
          <Icon name="map" size={28} />
          {t("app.point.mapUnavailable")}
        </span>
      </div>
    );
  return <div ref={element} className={FRAME} />;
}

function toLngLat(marker: MapMarker): LngLat {
  return [marker.longitude, marker.latitude];
}

function markerState(marker: MapMarker): MarkerState {
  return marker.state ?? (marker.muted ? "open" : "current");
}

function inkColor(): string {
  return getComputedStyle(document.documentElement).getPropertyValue("--map-route").trim();
}

function reachedIndex(markers: MapMarker[]): number {
  return markers.reduce(
    (last, marker, index) => (marker.state === "done" || marker.state === "current" ? index : last),
    -1,
  );
}

export function MapView({ markers, polyline = false }: { markers: MapMarker[]; polyline?: boolean }) {
  const { resolved } = useTheme();
  const first = markers[0];
  const { element, handle, failed } = useYandexMap(first ? toLngLat(first) : EKATERINBURG_CENTER, 15);

  useEffect(() => {
    if (!handle) return;
    const { api, map } = handle;
    const coordinates = markers.map(toLngLat);
    const entities: YMapEntity<unknown>[] = [];

    if (polyline && coordinates.length > 1) {
      const color = inkColor();
      const split = reachedIndex(markers);
      const walked = split > 0 ? coordinates.slice(0, split + 1) : [];
      const ahead = coordinates.slice(Math.max(split, 0));
      if (walked.length > 1)
        entities.push(
          new api.YMapFeature({
            geometry: { type: "LineString", coordinates: walked },
            style: { stroke: [{ color, width: ROUTE_STROKE_WIDTH }] },
          }),
        );
      if (ahead.length > 1)
        entities.push(
          new api.YMapFeature({
            geometry: { type: "LineString", coordinates: ahead },
            style: { stroke: [{ color, width: ROUTE_STROKE_WIDTH, dash: AHEAD_DASH }] },
          }),
        );
    }

    markers.forEach((marker, index) => {
      entities.push(
        new api.YMapMarker(
          { coordinates: coordinates[index] as LngLat, zIndex: markerState(marker) === "current" ? 2 : 1 },
          pinElement(markerState(marker), marker.label, marker.title),
        ),
      );
    });
    entities.forEach((entity) => map.addChild(entity));

    const [single] = coordinates;
    if (coordinates.length === 1 && single) map.update({ location: { center: single, zoom: 16 } });
    if (coordinates.length > 1) map.update({ location: { bounds: boundsOf(coordinates) } });

    return () => entities.forEach((entity) => map.removeChild(entity));
  }, [handle, markers, polyline, resolved]);

  return <MapFrame failed={failed} element={element} />;
}

interface MapPickerProps {
  latitude: number | null;
  longitude: number | null;
  onChange: (latitude: number, longitude: number) => void;
}

export function MapPicker({ latitude, longitude, onChange }: MapPickerProps) {
  const start: LngLat = latitude != null && longitude != null ? [longitude, latitude] : EKATERINBURG_CENTER;
  const { element, handle, failed } = useYandexMap(start, 15);
  const marker = useRef<YMapMarker | null>(null);
  const startRef = useRef(start);
  const onChangeRef = useRef(onChange);
  useEffect(() => {
    onChangeRef.current = onChange;
  });

  useEffect(() => {
    if (!handle) return;
    const { api, map } = handle;
    const pick = (coordinates: LngLat) => {
      marker.current?.update({ coordinates });
      onChangeRef.current(coordinates[1], coordinates[0]);
    };
    const placed = new api.YMapMarker(
      {
        coordinates: startRef.current,
        draggable: true,
        mapFollowsOnDrag: true,
        onDragEnd: (coordinates) => onChangeRef.current(coordinates[1], coordinates[0]),
      },
      pinElement("current"),
    );
    const listener = new api.YMapListener({
      layer: "any",
      onClick: (_object, event) => pick(event.coordinates),
    });
    marker.current = placed;
    map.addChild(placed);
    map.addChild(listener);
    return () => {
      map.removeChild(placed);
      map.removeChild(listener);
      marker.current = null;
    };
  }, [handle]);

  useEffect(() => {
    if (latitude != null && longitude != null) marker.current?.update({ coordinates: [longitude, latitude] });
  }, [latitude, longitude]);

  return <MapFrame failed={failed} element={element} />;
}
