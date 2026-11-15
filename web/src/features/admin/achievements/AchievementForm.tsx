import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type Schemas, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  type Achievement,
  type ParamField,
  type Params,
  type Rule,
  RULE_FIELDS,
  RULES,
} from "@/features/admin/achievements/rules";
import { titleOf, useAdminOffers, useAdminRoutes } from "@/features/admin/api";
import { cleanLocalized, fromLocalized } from "@/features/admin/localized";
import { LocalizedInput } from "@/features/admin/LocalizedInput";
import { AssetDrop } from "@/features/admin/ui/AssetDrop";
import { FormField, SwitchField } from "@/features/admin/ui/FormField";
import { NativeSelect } from "@/features/admin/ui/NativeSelect";

export function AchievementForm({ achievement, onDone }: { achievement?: Achievement; onDone: () => void }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const routes = useAdminRoutes();
  const offers = useAdminOffers();
  const [code, setCode] = useState(achievement?.code ?? "");
  const [title, setTitle] = useState(fromLocalized(achievement?.title));
  const [description, setDescription] = useState(fromLocalized(achievement?.description));
  const [rule, setRule] = useState<Rule>(achievement?.rule ?? "points_unlocked");
  const [params, setParams] = useState<Params>(achievement?.params ?? {});
  const [isHidden, setIsHidden] = useState(achievement?.isHidden ?? false);
  const [isActive, setIsActive] = useState(achievement?.isActive ?? true);
  const [position, setPosition] = useState(achievement?.position ?? 0);
  const [iconAssetId, setIconAssetId] = useState(achievement?.iconAssetId ?? null);
  const [rewardOfferId, setRewardOfferId] = useState(achievement?.rewardOfferId ?? "");

  const save = useMutation({
    mutationFn: (body: Schemas["AchievementInput"]) =>
      achievement
        ? unwrap(
            api.PUT("/api/admin/achievements/{achievement_id}", {
              params: { path: { achievement_id: achievement.id } },
              body,
            }),
          )
        : unwrap(api.POST("/api/admin/achievements", { body })),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "achievements"] });
      onDone();
    },
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const allowed = new Set(RULE_FIELDS[rule].map((field) => field.name));
    const cleaned = Object.fromEntries(
      Object.entries(params).filter(
        ([key, value]) => allowed.has(key as ParamField["name"]) && value !== "" && value !== null,
      ),
    );
    save.mutate({
      code,
      title,
      description: cleanLocalized(description),
      rule,
      params: cleaned,
      isHidden,
      isActive,
      position,
      iconAssetId,
      rewardOfferId: rewardOfferId || null,
    });
  };

  return (
    <form className="flex flex-col gap-5" onSubmit={submit}>
      <div className="grid gap-4 sm:grid-cols-[1fr_1.4fr_120px]">
        <FormField label={t("app.admin.code")}>
          {(id) => (
            <Input
              id={id}
              required
              className="h-11"
              pattern="[a-z0-9_]+"
              value={code}
              onChange={(event) => setCode(event.target.value)}
            />
          )}
        </FormField>
        <FormField label={t("app.admin.rule")}>
          {(id) => (
            <NativeSelect
              id={id}
              size="sm"
              value={rule}
              onChange={(event) => setRule(event.target.value as Rule)}
            >
              {RULES.map((item) => (
                <option key={item} value={item}>
                  {t(`app.admin.rules.${item}`)}
                </option>
              ))}
            </NativeSelect>
          )}
        </FormField>
        <FormField label={t("app.admin.position")}>
          {(id) => (
            <Input
              id={id}
              type="number"
              className="h-11 tabular"
              value={position}
              onChange={(event) => setPosition(Number(event.target.value))}
            />
          )}
        </FormField>
      </div>
      <fieldset className="m-0 flex flex-col gap-3 rounded-md border-todo p-4">
        <legend className="px-1.5 text-label">{t("app.admin.params")}</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          {RULE_FIELDS[rule].map((field) => (
            <FormField key={field.name} label={t(`app.admin.paramNames.${field.name}`)}>
              {(id) =>
                field.name === "routeId" ? (
                  <NativeSelect
                    id={id}
                    size="sm"
                    required={!field.optional}
                    value={String(params[field.name] ?? "")}
                    onChange={(event) => setParams({ ...params, routeId: event.target.value || null })}
                  >
                    <option value="">{field.optional ? t("app.admin.anyRoute") : ""}</option>
                    {(routes.data ?? []).map((route) => (
                      <option key={route.id} value={route.id}>
                        {titleOf(route.title)}
                      </option>
                    ))}
                  </NativeSelect>
                ) : (
                  <Input
                    id={id}
                    type="number"
                    required
                    className="h-11 tabular"
                    min={field.name.endsWith("Hour") ? 0 : 1}
                    max={field.name.endsWith("Hour") ? 23 : undefined}
                    value={String(params[field.name] ?? "")}
                    onChange={(event) => setParams({ ...params, [field.name]: Number(event.target.value) })}
                  />
                )
              }
            </FormField>
          ))}
        </div>
      </fieldset>
      <LocalizedInput
        label={t("app.admin.titleField")}
        value={title}
        original={achievement?.title}
        required
        onChange={setTitle}
      />
      <LocalizedInput
        label={t("app.admin.description")}
        value={description}
        original={achievement?.description}
        onChange={setDescription}
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label={t("app.admin.rewardOffer")}>
          {(id) => (
            <NativeSelect
              id={id}
              size="sm"
              value={rewardOfferId}
              onChange={(event) => setRewardOfferId(event.target.value)}
            >
              <option value="">—</option>
              {(offers.data ?? []).map((offer) => (
                <option key={offer.id} value={offer.id}>
                  {titleOf(offer.title)}
                </option>
              ))}
            </NativeSelect>
          )}
        </FormField>
        <div className="flex flex-col gap-2">
          <span className="text-label">{t("app.admin.icon")}</span>
          <AssetDrop
            assetId={iconAssetId}
            accept="image/*"
            scope="admin"
            isPublic
            icon="sparkle"
            onUploaded={(asset) => setIconAssetId(asset.id)}
          />
        </div>
        <SwitchField label={t("app.admin.hidden")} checked={isHidden} onCheckedChange={setIsHidden} />
        <SwitchField label={t("app.admin.active")} checked={isActive} onCheckedChange={setIsActive} />
      </div>
      <ErrorText error={save.error} />
      <div className="flex gap-3">
        <Button type="submit" size="sm" disabled={save.isPending}>
          {t("app.common.save")}
        </Button>
        <Button type="button" variant="secondary" size="sm" onClick={onDone}>
          {t("app.common.cancel")}
        </Button>
      </div>
    </form>
  );
}
