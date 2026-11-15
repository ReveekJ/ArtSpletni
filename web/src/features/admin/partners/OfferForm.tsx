import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { titleOf, useAdminPoints } from "@/features/admin/api";
import { cleanLocalized, fromLocalized } from "@/features/admin/localized";
import { LocalizedInput } from "@/features/admin/LocalizedInput";
import { FormField, SwitchField } from "@/features/admin/ui/FormField";
import { NativeSelect } from "@/features/admin/ui/NativeSelect";

type Offer = Schemas["AdminOfferOut"];

interface OfferFormProps {
  partnerId: string;
  offer?: Offer;
  pending: boolean;
  error: unknown;
  onSubmit: (input: Schemas["OfferInput"]) => void;
  onCancel?: () => void;
}

function numberOrNull(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

export function OfferForm({ partnerId, offer, pending, error, onSubmit, onCancel }: OfferFormProps) {
  const { t } = useTranslation();
  const points = useAdminPoints("", "partner");
  const [title, setTitle] = useState(fromLocalized(offer?.title));
  const [terms, setTerms] = useState(fromLocalized(offer?.terms));
  const [pointId, setPointId] = useState(offer?.pointId ?? "");
  const [promoCode, setPromoCode] = useState(offer?.promoCode ?? "");
  const [validUntil, setValidUntil] = useState(offer?.validUntil?.slice(0, 16) ?? "");
  const [ttlHours, setTtlHours] = useState(offer?.ttlHours?.toString() ?? "");
  const [limit, setLimit] = useState(offer?.redemptionLimit?.toString() ?? "");
  const [isActive, setIsActive] = useState(offer?.isActive ?? true);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({
      partnerId,
      title,
      terms: cleanLocalized(terms),
      pointId: pointId || null,
      promoCode: promoCode.trim() || null,
      validUntil: validUntil ? new Date(validUntil).toISOString() : null,
      ttlHours: numberOrNull(ttlHours),
      redemptionLimit: numberOrNull(limit),
      isActive,
    });
  };

  return (
    <form className="flex flex-col gap-4" onSubmit={submit}>
      <LocalizedInput
        label={t("app.admin.titleField")}
        value={title}
        original={offer?.title}
        required
        onChange={setTitle}
      />
      <LocalizedInput
        label={t("app.admin.terms")}
        value={terms}
        original={offer?.terms}
        multiline
        onChange={setTerms}
      />
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label={t("app.admin.point")}>
          {(id) => (
            <NativeSelect
              id={id}
              size="sm"
              value={pointId}
              onChange={(event) => setPointId(event.target.value)}
            >
              <option value="">—</option>
              {(points.data ?? []).map((point) => (
                <option key={point.id} value={point.id}>
                  {titleOf(point.title)}
                </option>
              ))}
            </NativeSelect>
          )}
        </FormField>
        <FormField label={t("app.admin.promoCode")}>
          {(id) => (
            <Input
              id={id}
              className="h-11"
              value={promoCode}
              maxLength={64}
              onChange={(event) => setPromoCode(event.target.value)}
            />
          )}
        </FormField>
        <FormField label={t("app.admin.validUntil")}>
          {(id) => (
            <Input
              id={id}
              type="datetime-local"
              className="h-11"
              value={validUntil}
              onChange={(event) => setValidUntil(event.target.value)}
            />
          )}
        </FormField>
        <FormField label={t("app.admin.ttlHours")}>
          {(id) => (
            <Input
              id={id}
              type="number"
              min={1}
              className="h-11 tabular"
              value={ttlHours}
              onChange={(event) => setTtlHours(event.target.value)}
            />
          )}
        </FormField>
        <FormField label={t("app.admin.redemptionLimit")}>
          {(id) => (
            <Input
              id={id}
              type="number"
              min={1}
              className="h-11 tabular"
              value={limit}
              onChange={(event) => setLimit(event.target.value)}
            />
          )}
        </FormField>
        <SwitchField
          label={t("app.admin.active")}
          checked={isActive}
          onCheckedChange={setIsActive}
          className="self-end"
        />
      </div>
      <ErrorText error={error} />
      <div className="flex gap-3">
        <Button type="submit" size="sm" disabled={pending}>
          {t("app.common.save")}
        </Button>
        {onCancel ? (
          <Button type="button" variant="secondary" size="sm" onClick={onCancel}>
            {t("app.common.cancel")}
          </Button>
        ) : null}
      </div>
    </form>
  );
}
