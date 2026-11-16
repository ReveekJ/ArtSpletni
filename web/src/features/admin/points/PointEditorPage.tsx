import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";

import { api, type Schemas, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { MapPicker } from "@/components/YandexMap";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { titleOf, useAdminPartners } from "@/features/admin/api";
import { LocalizedInput } from "@/features/admin/LocalizedInput";
import { BlocksEditor } from "@/features/admin/points/BlocksEditor";
import { type Draft, type Point, type PointKind, toDraft, toInput } from "@/features/admin/points/pointDraft";
import { GossipPanel } from "@/features/admin/points/GossipPanel";
import { TagsPanel } from "@/features/admin/points/TagsPanel";
import { AssetDrop } from "@/features/admin/ui/AssetDrop";
import { FormField, SwitchField } from "@/features/admin/ui/FormField";
import { NativeSelect } from "@/features/admin/ui/NativeSelect";
import { StatusChip } from "@/features/admin/ui/StatusChip";
import { useGoBack } from "@/lib/useGoBack";

export default function PointEditorPage() {
  const { pointId } = useParams();
  const isNew = !pointId || pointId === "new";
  const point = useQuery({
    queryKey: ["admin", "point", pointId],
    queryFn: () =>
      unwrap(api.GET("/api/admin/points/{point_id}", { params: { path: { point_id: pointId ?? "" } } })),
    enabled: !isNew,
  });
  if (!isNew && point.isPending) return <Loader />;
  if (point.error) return <ErrorText error={point.error} />;
  return <PointForm key={point.data?.updatedAt ?? "new"} point={point.data} />;
}

function PointForm({ point }: { point: Point | undefined }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const goBack = useGoBack("/admin/points");
  const queryClient = useQueryClient();
  const partners = useAdminPartners();
  const [draft, setDraft] = useState<Draft>(() => toDraft(point));
  const patch = (value: Partial<Draft>) => setDraft((current) => ({ ...current, ...value }));

  const save = useMutation({
    mutationFn: (body: Schemas["PointInput"]) =>
      point
        ? unwrap(api.PUT("/api/admin/points/{point_id}", { params: { path: { point_id: point.id } }, body }))
        : unwrap(api.POST("/api/admin/points", { body })),
    onSuccess: (saved) => {
      void queryClient.invalidateQueries({ queryKey: ["admin"] });
      if (!point) navigate(`/admin/points/${saved.id}`, { replace: true });
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) =>
      unwrap(api.DELETE("/api/admin/points/{point_id}", { params: { path: { point_id: id } } })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin"] });
      goBack();
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    save.mutate(toInput(draft));
  };

  return (
    <div className="grid items-start gap-6 2xl:grid-cols-[minmax(0,1fr)_380px]">
      <Card asChild className="overflow-hidden rounded-[24px] shadow-dialog">
        <form onSubmit={submit}>
          <header className="flex items-start justify-between gap-4 border-b border-solid border-rule px-6 pt-5 pb-4">
            <div className="flex min-w-0 flex-col gap-1">
              <span className="text-caption text-ink-muted">
                {t(`app.admin.kinds.${draft.kind}`)} ·{" "}
                {point ? <StatusChip published={point.isPublished} /> : t("app.admin.draft")}
              </span>
              <h1 className="m-0 text-h2">{point ? titleOf(point.title) : t("app.admin.newPoint")}</h1>
            </div>
            <Button
              type="button"
              variant="outline"
              size="icon-sm"
              aria-label={t("app.common.close")}
              onClick={goBack}
            >
              <Icon name="x" size={18} />
            </Button>
          </header>

          <div className="grid gap-x-6 gap-y-5 px-6 py-5 md:grid-cols-2">
            <FormField label={t("app.admin.kind")}>
              {(id) => (
                <NativeSelect
                  id={id}
                  value={draft.kind}
                  onChange={(event) => patch({ kind: event.target.value as PointKind })}
                >
                  <option value="gossip">{t("app.admin.kinds.gossip")}</option>
                  <option value="partner">{t("app.admin.kinds.partner")}</option>
                </NativeSelect>
              )}
            </FormField>
            {draft.kind === "partner" ? (
              <FormField label={t("app.admin.partner")}>
                {(id) => (
                  <NativeSelect
                    id={id}
                    required
                    value={draft.partnerId ?? ""}
                    onChange={(event) => patch({ partnerId: event.target.value || null })}
                  >
                    <option value="" />
                    {(partners.data ?? []).map((partner) => (
                      <option key={partner.id} value={partner.id}>
                        {partner.name}
                      </option>
                    ))}
                  </NativeSelect>
                )}
              </FormField>
            ) : (
              <div className="hidden md:block" />
            )}
            <LocalizedInput
              label={t("app.admin.titleField")}
              value={draft.title}
              original={point?.title}
              required
              onChange={(title) => patch({ title })}
            />
            <LocalizedInput
              label={t("app.admin.address")}
              value={draft.address}
              original={point?.address}
              onChange={(address) => patch({ address })}
            />
            {draft.kind === "partner" ? (
              <div className="md:col-span-2">
                <LocalizedInput
                  label={t("app.admin.note")}
                  value={draft.note}
                  original={point?.note}
                  multiline
                  onChange={(note) => patch({ note })}
                />
              </div>
            ) : null}

            <div className="flex flex-col gap-2">
              <span className="text-label">{t("app.admin.cover")}</span>
              <AssetDrop
                assetId={draft.coverAssetId}
                accept="image/*"
                scope="admin"
                isPublic
                onUploaded={(asset) => patch({ coverAssetId: asset.id })}
              />
              <SwitchField
                label={t("app.admin.published")}
                checked={draft.isPublished}
                onCheckedChange={(isPublished) => patch({ isPublished })}
                className="mt-2"
              />
            </div>

            <div className="flex flex-col gap-2">
              <span className="text-label">{t("app.admin.place")}</span>
              <MapPicker
                latitude={draft.latitude}
                longitude={draft.longitude}
                onChange={(latitude, longitude) => patch({ latitude, longitude })}
              />
              <div className="flex gap-2">
                <Input
                  type="number"
                  step="any"
                  required
                  aria-label={t("app.admin.latitude")}
                  placeholder={t("app.admin.latitude")}
                  className="h-11 tabular"
                  value={draft.latitude ?? ""}
                  onChange={(event) => patch({ latitude: Number(event.target.value) })}
                />
                <Input
                  type="number"
                  step="any"
                  required
                  aria-label={t("app.admin.longitude")}
                  placeholder={t("app.admin.longitude")}
                  className="h-11 tabular"
                  value={draft.longitude ?? ""}
                  onChange={(event) => patch({ longitude: Number(event.target.value) })}
                />
              </div>
            </div>

            <div className="md:col-span-2">
              <BlocksEditor blocks={draft.blocks} onChange={(blocks) => patch({ blocks })} />
            </div>
            <div className="md:col-span-2">
              <ErrorText error={save.error ?? remove.error} />
            </div>
          </div>

          <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-solid border-rule px-6 py-4">
            {point ? (
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={() => window.confirm(t("app.admin.confirmDelete")) && remove.mutate(point.id)}
              >
                <Icon name="trash" size={18} />
                {t("app.common.delete")}
              </Button>
            ) : (
              <span />
            )}
            <div className="flex gap-3">
              <Button type="button" variant="secondary" size="sm" onClick={goBack}>
                {t("app.common.cancel")}
              </Button>
              <Button type="submit" size="sm" disabled={save.isPending}>
                {t("app.common.save")}
              </Button>
            </div>
          </footer>
        </form>
      </Card>
      {point ? <TagsPanel pointId={point.id} /> : null}
      {point ? (
        <div className="2xl:col-span-2">
          <GossipPanel pointId={point.id} />
        </div>
      ) : null}
    </div>
  );
}
