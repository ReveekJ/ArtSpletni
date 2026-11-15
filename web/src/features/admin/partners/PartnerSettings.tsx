import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type Schemas, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField, SwitchField } from "@/features/admin/ui/FormField";
import { Panel } from "@/features/admin/ui/Panel";

export function PartnerSettings({ partner }: { partner: Schemas["PartnerOut"] }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [name, setName] = useState(partner.name);
  const [isActive, setIsActive] = useState(partner.isActive);
  const save = useMutation({
    mutationFn: () =>
      unwrap(
        api.PUT("/api/admin/partners/{partner_id}", {
          params: { path: { partner_id: partner.id } },
          body: { name, isActive, logoAssetId: partner.logoAssetId },
        }),
      ),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin", "partners"] }),
  });
  return (
    <Panel title={t("app.admin.partnerSettings")}>
      <form
        className="flex flex-col gap-4"
        onSubmit={(event: FormEvent) => {
          event.preventDefault();
          save.mutate();
        }}
      >
        <FormField label={t("app.admin.name")}>
          {(id) => <Input id={id} required value={name} onChange={(event) => setName(event.target.value)} />}
        </FormField>
        <SwitchField label={t("app.admin.active")} checked={isActive} onCheckedChange={setIsActive} />
        <ErrorText error={save.error} />
        <Button type="submit" size="sm" className="self-start" disabled={save.isPending}>
          {t("app.common.save")}
        </Button>
      </form>
    </Panel>
  );
}
