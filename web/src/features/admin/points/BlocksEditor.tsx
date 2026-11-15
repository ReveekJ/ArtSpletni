import { useTranslation } from "react-i18next";

import { UploadButton } from "@/components/UploadButton";
import { Button } from "@/components/ui/button";
import { Icon, type IconName } from "@/components/ui/icon";
import { LocalizedInput } from "@/features/admin/LocalizedInput";
import { type BlockDraft, type BlockKind, newBlock } from "@/features/admin/points/blockDraft";
import { AssetDrop } from "@/features/admin/ui/AssetDrop";
import { LANGUAGES } from "@/i18n";
import { cn } from "@/lib/utils";

const ACCEPT: Record<BlockKind, string> = { text: "", image: "image/*", audio: "audio/*", video: "video/*" };
const ICONS: Record<BlockKind, IconName> = {
  text: "text",
  image: "image",
  audio: "headphones",
  video: "play",
};
const KINDS: BlockKind[] = ["text", "image", "audio", "video"];

interface BlocksEditorProps {
  blocks: BlockDraft[];
  onChange: (blocks: BlockDraft[]) => void;
}

export function BlocksEditor({ blocks, onChange }: BlocksEditorProps) {
  const { t } = useTranslation();
  const update = (index: number, patch: Partial<BlockDraft>) =>
    onChange(blocks.map((block, position) => (position === index ? { ...block, ...patch } : block)));
  const move = (index: number, delta: number) => {
    const target = index + delta;
    if (target < 0 || target >= blocks.length) return;
    const next = [...blocks];
    const [item] = next.splice(index, 1);
    if (item) next.splice(target, 0, item);
    onChange(next);
  };

  return (
    <fieldset className="m-0 flex flex-col gap-3 border-0 p-0">
      <legend className="mb-3 p-0 text-h3">{t("app.admin.blocks")}</legend>
      {blocks.map((block, index) => (
        <div key={block.key} className="flex flex-col gap-4 rounded-md border-sketch bg-paper p-4">
          <div className="flex items-center gap-2">
            <Icon name={ICONS[block.kind]} size={18} />
            <strong className="flex-1 text-[15px]">{t(`app.admin.blockKinds.${block.kind}`)}</strong>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label={t("app.admin.moveUp")}
              onClick={() => move(index, -1)}
            >
              <Icon name="chevron-down" size={18} className="rotate-180" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label={t("app.admin.moveDown")}
              onClick={() => move(index, 1)}
            >
              <Icon name="chevron-down" size={18} />
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="icon-sm"
              aria-label={t("app.common.delete")}
              onClick={() => onChange(blocks.filter((_, position) => position !== index))}
            >
              <Icon name="trash" size={18} />
            </Button>
          </div>
          {block.kind === "text" ? (
            <LocalizedInput
              label={t("app.admin.blockKinds.text")}
              value={block.text}
              original={block.original?.text}
              multiline
              required
              onChange={(text) => update(index, { text })}
            />
          ) : (
            <>
              <AssetDrop
                assetId={block.assetId}
                accept={ACCEPT[block.kind]}
                scope="admin"
                icon={ICONS[block.kind]}
                onUploaded={(asset) => update(index, { assetId: asset.id })}
              />
              <details className="group rounded-md border-todo px-3.5 py-2.5">
                <summary className="flex cursor-pointer list-none items-center gap-2 text-label">
                  <Icon
                    name="chevron-right"
                    size={16}
                    className="transition-transform group-open:rotate-90"
                  />
                  {t("app.admin.variants")}
                </summary>
                <div className="mt-3 flex flex-col gap-2.5">
                  {LANGUAGES.slice(1).map((lang) => {
                    const variant = block.mediaVariants[lang];
                    return (
                      <div key={lang} className="flex flex-wrap items-center gap-3">
                        <span className={cn("sk-lang", variant ? "sk-lang--ready" : "sk-lang--missing")}>
                          {lang.toUpperCase()}
                        </span>
                        <span className="min-w-0 flex-1 truncate text-caption text-ink-muted">
                          {variant ?? t("app.admin.noFile")}
                        </span>
                        <UploadButton
                          accept={ACCEPT[block.kind]}
                          scope="admin"
                          onUploaded={(asset) =>
                            update(index, { mediaVariants: { ...block.mediaVariants, [lang]: asset.id } })
                          }
                        />
                      </div>
                    );
                  })}
                </div>
              </details>
              <LocalizedInput
                label={t("app.admin.caption")}
                value={block.caption}
                original={block.original?.caption}
                onChange={(caption) => update(index, { caption })}
              />
            </>
          )}
        </div>
      ))}
      <div className="flex flex-wrap gap-2.5 pt-1">
        {KINDS.map((kind) => (
          <Button
            key={kind}
            type="button"
            variant="outline"
            size="xs"
            onClick={() => onChange([...blocks, newBlock(kind)])}
          >
            <Icon name="plus" size={16} />
            {t(`app.admin.blockKinds.${kind}`)}
          </Button>
        ))}
      </div>
    </fieldset>
  );
}
