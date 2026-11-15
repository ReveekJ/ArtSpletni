import { useMutation } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate } from "react-router-dom";

import { api, type Schemas, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Field } from "@/components/sketch/Field";
import { Sticker } from "@/components/sketch/Sticker";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { UploadButton } from "@/components/UploadButton";
import { MapPicker } from "@/components/YandexMap";
import { useCurrentUser } from "@/features/auth/api";

export default function SuggestPage() {
  const { t } = useTranslation();
  const user = useCurrentUser();
  const [title, setTitle] = useState("");
  const [story, setStory] = useState("");
  const [coords, setCoords] = useState<{ latitude: number; longitude: number } | null>(null);
  const [assets, setAssets] = useState<Schemas["MediaAssetOut"][]>([]);
  const submit = useMutation({
    mutationFn: (body: Schemas["SubmissionInput"]) => unwrap(api.POST("/api/me/submissions", { body })),
  });

  if (!user || user.kind !== "registered") return <Navigate to="/register?next=/suggest" replace />;
  if (submit.isSuccess)
    return (
      <section className="flex flex-col gap-5 pt-4">
        <Alert variant="success">
          <Icon name="check" />
          <AlertDescription>{t("app.suggest.sent")}</AlertDescription>
        </Alert>
        <Button asChild variant="secondary" block>
          <Link to="/me">{t("app.nav.profile")}</Link>
        </Button>
      </section>
    );

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!coords) return;
    submit.mutate({ title, story, ...coords, assetIds: assets.map((asset) => asset.id) });
  };

  return (
    <section className="flex flex-col gap-5">
      <header className="flex flex-col gap-2 pt-4">
        <h1 className="m-0 text-display-sm">{t("app.suggest.title")}</h1>
        <p className="m-0 text-body text-ink-muted">{t("app.suggest.lead")}</p>
      </header>
      <form className="flex flex-col gap-5" onSubmit={onSubmit}>
        <Field label={t("app.suggest.storyTitle")}>
          {({ id }) => (
            <Input
              id={id}
              required
              minLength={3}
              maxLength={200}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          )}
        </Field>
        <Field label={t("app.suggest.story")}>
          {({ id }) => (
            <Textarea
              id={id}
              required
              minLength={20}
              rows={8}
              value={story}
              onChange={(e) => setStory(e.target.value)}
            />
          )}
        </Field>
        <fieldset className="m-0 flex flex-col gap-2 border-0 p-0">
          <legend className="mb-2 p-0 text-label">{t("app.suggest.location")}</legend>
          <div className="relative">
            <MapPicker
              latitude={coords?.latitude ?? null}
              longitude={coords?.longitude ?? null}
              onChange={(latitude, longitude) => setCoords({ latitude, longitude })}
            />
            {coords ? null : (
              <Sticker className="pointer-events-none absolute right-3 -bottom-3">
                {t("app.suggest.mapSticker")}
              </Sticker>
            )}
          </div>
        </fieldset>
        <fieldset className="m-0 flex flex-col gap-3 border-0 p-0">
          <legend className="mb-2 p-0 text-label">{t("app.suggest.media")}</legend>
          {assets.length > 0 ? (
            <ul className="m-0 flex list-none flex-col gap-2 p-0">
              {assets.map((asset) => (
                <li key={asset.id} className="flex items-center gap-2 text-body-sm">
                  <Icon name="check" size={16} className="text-success" />
                  <span className="min-w-0 truncate">{asset.originalFilename}</span>
                </li>
              ))}
            </ul>
          ) : null}
          {assets.length < 5 ? (
            <UploadButton
              accept="image/*,audio/*"
              scope="me"
              onUploaded={(asset) => setAssets((current) => [...current, asset])}
            />
          ) : null}
        </fieldset>
        <ErrorText error={submit.error} />
        <Button block disabled={!coords || submit.isPending}>
          {t("app.suggest.send")}
        </Button>
      </form>
    </section>
  );
}
