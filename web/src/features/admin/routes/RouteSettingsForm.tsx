import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cleanLocalized, fromLocalized } from "@/features/admin/localized";
import { LocalizedInput } from "@/features/admin/LocalizedInput";
import type { AdminRoute } from "@/features/admin/routes/routeApi";
import { AssetDrop } from "@/features/admin/ui/AssetDrop";
import { FormField, SwitchField } from "@/features/admin/ui/FormField";
import { NativeSelect } from "@/features/admin/ui/NativeSelect";

type RouteInput = Schemas["RouteInput"];

const MODES = ["free", "sequential", "graph"] as const;
const VISIBILITY = ["all", "progressive", "visited_with_hints"] as const;

function toLocalInput(value: string | null | undefined): string {
  return value ? value.slice(0, 16) : "";
}

function fromLocalInput(value: string): string | null {
  return value ? new Date(value).toISOString() : null;
}

interface RouteSettingsFormProps {
  route?: AdminRoute;
  pending: boolean;
  error: unknown;
  onSubmit: (input: RouteInput) => void;
}

export function RouteSettingsForm({ route, pending, error, onSubmit }: RouteSettingsFormProps) {
  const { t } = useTranslation();
  const [slug, setSlug] = useState(route?.slug ?? "");
  const [title, setTitle] = useState(fromLocalized(route?.title));
  const [description, setDescription] = useState(fromLocalized(route?.description));
  const [coverAssetId, setCoverAssetId] = useState(route?.coverAssetId ?? null);
  const [orderingMode, setOrderingMode] = useState<RouteInput["orderingMode"]>(route?.orderingMode ?? "free");
  const [mapVisibility, setMapVisibility] = useState<RouteInput["mapVisibility"]>(
    route?.mapVisibility ?? "all",
  );
  const [activeFrom, setActiveFrom] = useState(toLocalInput(route?.activeFrom));
  const [activeUntil, setActiveUntil] = useState(toLocalInput(route?.activeUntil));
  const [isRepeatable, setIsRepeatable] = useState(route?.isRepeatable ?? false);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({
      slug,
      title,
      description: cleanLocalized(description),
      coverAssetId,
      orderingMode,
      mapVisibility,
      activeFrom: fromLocalInput(activeFrom),
      activeUntil: fromLocalInput(activeUntil),
      isRepeatable,
    });
  };

  return (
    <form className="flex flex-col gap-5" onSubmit={submit}>
      <FormField label={t("app.admin.slug")}>
        {(id) => (
          <Input
            id={id}
            required
            pattern="[a-z0-9]+(-[a-z0-9]+)*"
            value={slug}
            onChange={(event) => setSlug(event.target.value)}
          />
        )}
      </FormField>
      <LocalizedInput
        label={t("app.admin.titleField")}
        value={title}
        original={route?.title}
        required
        onChange={setTitle}
      />
      <LocalizedInput
        label={t("app.admin.description")}
        value={description}
        original={route?.description}
        multiline
        onChange={setDescription}
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label={t("app.admin.orderingMode")}>
          {(id) => (
            <NativeSelect
              id={id}
              value={orderingMode}
              onChange={(event) => setOrderingMode(event.target.value as RouteInput["orderingMode"])}
            >
              {MODES.map((mode) => (
                <option key={mode} value={mode}>
                  {t(`app.admin.orderingModes.${mode}`)}
                </option>
              ))}
            </NativeSelect>
          )}
        </FormField>
        <FormField label={t("app.admin.mapVisibility")}>
          {(id) => (
            <NativeSelect
              id={id}
              value={mapVisibility}
              onChange={(event) => setMapVisibility(event.target.value as RouteInput["mapVisibility"])}
            >
              {VISIBILITY.map((mode) => (
                <option key={mode} value={mode}>
                  {t(`app.admin.mapVisibilities.${mode}`)}
                </option>
              ))}
            </NativeSelect>
          )}
        </FormField>
        <FormField label={t("app.admin.activeFrom")}>
          {(id) => (
            <Input
              id={id}
              type="datetime-local"
              value={activeFrom}
              onChange={(event) => setActiveFrom(event.target.value)}
            />
          )}
        </FormField>
        <FormField label={t("app.admin.activeUntil")}>
          {(id) => (
            <Input
              id={id}
              type="datetime-local"
              value={activeUntil}
              onChange={(event) => setActiveUntil(event.target.value)}
            />
          )}
        </FormField>
      </div>
      <SwitchField
        label={t("app.admin.repeatable")}
        checked={isRepeatable}
        onCheckedChange={setIsRepeatable}
      />
      <div className="flex flex-col gap-2">
        <span className="text-label">{t("app.admin.cover")}</span>
        <AssetDrop
          assetId={coverAssetId}
          accept="image/*"
          scope="admin"
          isPublic
          onUploaded={(asset) => setCoverAssetId(asset.id)}
        />
      </div>
      <ErrorText error={error} />
      <Button type="submit" size="sm" className="self-start" disabled={pending}>
        {t("app.common.save")}
      </Button>
    </form>
  );
}
