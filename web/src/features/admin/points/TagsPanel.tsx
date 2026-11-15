import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { Panel } from "@/features/admin/ui/Panel";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

interface NdefWriter {
  write: (message: { records: { recordType: "url"; data: string }[] }) => Promise<void>;
}

declare global {
  interface Window {
    NDEFReader?: new () => NdefWriter;
  }
}

export function TagsPanel({ pointId }: { pointId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const path = { params: { path: { point_id: pointId } } };
  const [label, setLabel] = useState("");
  const [nfcState, setNfcState] = useState<"idle" | "written" | "unsupported">("idle");
  const [copied, setCopied] = useState(false);
  const tags = useQuery({
    queryKey: ["admin", "tags", pointId],
    queryFn: () => unwrap(api.GET("/api/admin/points/{point_id}/tags", path)),
  });
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ["admin", "tags", pointId] });
  const issue = useMutation({
    mutationFn: () =>
      unwrap(api.POST("/api/admin/points/{point_id}/tags", { ...path, body: { label: label || null } })),
    onSuccess: refresh,
  });
  const revoke = useMutation({
    mutationFn: (tagId: string) =>
      unwrap(api.POST("/api/admin/tags/{tag_id}/revoke", { params: { path: { tag_id: tagId } } })),
    onSuccess: refresh,
  });

  const writeNfc = async (url: string) => {
    if (!window.NDEFReader) {
      setNfcState("unsupported");
      return;
    }
    await new window.NDEFReader().write({ records: [{ recordType: "url", data: url }] });
    setNfcState("written");
  };

  const copy = async (url: string) => {
    await navigator.clipboard.writeText(url);
    setCopied(true);
  };

  return (
    <Panel title={t("app.admin.tags")} className="2xl:sticky 2xl:top-7">
      <div className="flex flex-wrap gap-2">
        <Input
          className="h-11 min-w-[160px] flex-1"
          aria-label={t("app.admin.tagLabel")}
          placeholder={t("app.admin.tagLabel")}
          value={label}
          onChange={(event) => setLabel(event.target.value)}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            setNfcState("idle");
            setCopied(false);
            issue.mutate();
          }}
        >
          <Icon name="nfc" size={18} />
          {t("app.admin.issueTag")}
        </Button>
      </div>
      <ErrorText error={issue.error ?? revoke.error} />
      {issue.data ? (
        <Alert>
          <Icon name="info" />
          <AlertDescription className="min-w-0 gap-2.5">
            <span>{t("app.admin.tagUrlOnce")}</span>
            <code className="block truncate rounded-[10px] border-sketch bg-paper-raised px-3 py-2 font-sans text-[13px]">
              {issue.data.url}
            </code>
            <span className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" size="xs" onClick={() => void copy(issue.data.url)}>
                <Icon name={copied ? "check" : "copy"} size={16} />
                {copied ? t("app.admin.copied") : t("app.admin.copy")}
              </Button>
              <Button type="button" variant="outline" size="xs" onClick={() => void writeNfc(issue.data.url)}>
                <Icon name="nfc" size={16} />
                {t("app.admin.writeNfc")}
              </Button>
            </span>
            {nfcState === "written" ? (
              <Badge variant="success">
                <Icon name="check" />
                {t("app.admin.nfcWritten")}
              </Badge>
            ) : null}
            {nfcState === "unsupported" ? (
              <span className="text-caption text-ink-muted">{t("app.admin.nfcUnsupported")}</span>
            ) : null}
          </AlertDescription>
        </Alert>
      ) : null}
      <ul className="m-0 flex list-none flex-col p-0">
        {(tags.data ?? []).map((tag) => (
          <li
            key={tag.id}
            className={cn(
              "flex items-center gap-3 border-b border-solid border-rule py-3 last:border-b-0",
              tag.revokedAt && "text-ink-muted",
            )}
          >
            <span
              aria-hidden="true"
              className={cn(
                "grid size-9 shrink-0 place-items-center rounded-wobble",
                tag.revokedAt ? "border-todo" : "border-sketch bg-paper-sunk",
              )}
            >
              <Icon name="nfc" size={18} />
            </span>
            <span className="flex min-w-0 flex-1 flex-col gap-0.5">
              <span className="truncate text-[15px] font-semibold">{tag.label ?? "—"}</span>
              <span className="text-caption text-ink-muted">
                {formatDateTime(tag.createdAt)} · {t("app.admin.lastScan")}:{" "}
                {tag.lastScannedAt ? formatDateTime(tag.lastScannedAt) : "—"}
              </span>
            </span>
            {tag.revokedAt ? (
              <Badge variant="todo">{t("app.admin.revoked")}</Badge>
            ) : (
              <Button type="button" variant="destructive" size="xs" onClick={() => revoke.mutate(tag.id)}>
                {t("app.admin.revoke")}
              </Button>
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
