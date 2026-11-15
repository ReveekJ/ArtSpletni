import type { Schemas } from "@/api/client";
import { cleanLocalized, fromLocalized, type LocalizedValue } from "@/features/admin/localized";
import type { BlockDraft } from "@/features/admin/points/blockDraft";

export type Point = Schemas["AdminPointOut"];
export type PointKind = Schemas["PointInput"]["kind"];

export interface Draft {
  kind: PointKind;
  title: LocalizedValue;
  address: LocalizedValue;
  note: LocalizedValue;
  latitude: number | null;
  longitude: number | null;
  coverAssetId: string | null;
  partnerId: string | null;
  isPublished: boolean;
  blocks: BlockDraft[];
}

export function toDraft(point: Point | undefined): Draft {
  return {
    kind: point?.kind ?? "gossip",
    title: fromLocalized(point?.title),
    address: fromLocalized(point?.address),
    note: fromLocalized(point?.note),
    latitude: point?.latitude ?? null,
    longitude: point?.longitude ?? null,
    coverAssetId: point?.coverAssetId ?? null,
    partnerId: point?.partnerId ?? null,
    isPublished: point?.isPublished ?? false,
    blocks: (point?.blocks ?? []).map((block) => ({
      key: block.id,
      kind: block.kind,
      text: fromLocalized(block.text),
      caption: fromLocalized(block.caption),
      assetId: block.assetId,
      mediaVariants: block.mediaVariants,
      original: block,
    })),
  };
}

export function toInput(draft: Draft): Schemas["PointInput"] {
  return {
    kind: draft.kind,
    title: draft.title,
    latitude: draft.latitude ?? 0,
    longitude: draft.longitude ?? 0,
    address: cleanLocalized(draft.address),
    note: cleanLocalized(draft.note),
    coverAssetId: draft.coverAssetId,
    partnerId: draft.kind === "partner" ? draft.partnerId : null,
    isPublished: draft.isPublished,
    blocks: draft.blocks.map((block) => ({
      kind: block.kind,
      text: block.kind === "text" ? block.text : null,
      caption: block.kind === "text" ? null : cleanLocalized(block.caption),
      assetId: block.assetId,
      mediaVariants: block.mediaVariants,
    })),
  };
}
