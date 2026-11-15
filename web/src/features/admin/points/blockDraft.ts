import type { Schemas } from "@/api/client";
import type { LocalizedValue } from "@/features/admin/localized";

export type BlockKind = Schemas["BlockInput"]["kind"];

export interface BlockDraft {
  key: string;
  kind: BlockKind;
  text: LocalizedValue;
  caption: LocalizedValue;
  assetId: string | null;
  mediaVariants: Record<string, string>;
  original?: Schemas["AdminBlockOut"];
}

export function newBlock(kind: BlockKind): BlockDraft {
  return { key: crypto.randomUUID(), kind, text: {}, caption: {}, assetId: null, mediaVariants: {} };
}
