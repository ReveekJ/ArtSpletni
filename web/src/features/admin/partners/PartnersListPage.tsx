import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { api, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { useAdminPartners } from "@/features/admin/api";
import { PageHeader } from "@/features/admin/ui/PageHeader";
import { cn } from "@/lib/utils";

export function PartnersListPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const partners = useAdminPartners();
  const [name, setName] = useState("");
  const create = useMutation({
    mutationFn: () => unwrap(api.POST("/api/admin/partners", { body: { name, isActive: true } })),
    onSuccess: () => {
      setName("");
      void queryClient.invalidateQueries({ queryKey: ["admin", "partners"] });
    },
  });

  return (
    <>
      <PageHeader title={t("app.admin.partners")} subtitle={t("app.admin.partnersHint")} />
      <form
        className="flex max-w-[560px] gap-2"
        onSubmit={(event: FormEvent) => {
          event.preventDefault();
          create.mutate();
        }}
      >
        <Input
          required
          className="h-11"
          aria-label={t("app.admin.newPartner")}
          placeholder={t("app.admin.newPartner")}
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <Button type="submit" size="sm">
          <Icon name="plus" size={18} />
          {t("app.common.create")}
        </Button>
      </form>
      <ErrorText error={create.error ?? partners.error} />
      {partners.data?.length === 0 ? (
        <Card variant="todo" className="max-w-[560px] items-center gap-2 px-6 py-10 text-center">
          <Icon name="gift" size={26} className="text-ink-muted" />
          <p className="m-0 text-body-sm text-ink-muted">{t("app.admin.partnersEmpty")}</p>
        </Card>
      ) : null}
      <div className="grid grid-cols-[repeat(auto-fill,minmax(min(260px,100%),1fr))] gap-[18px]">
        {(partners.data ?? []).map((partner) => (
          <Card
            key={partner.id}
            asChild
            interactive
            variant={partner.isActive ? "default" : "todo"}
            className="flex-row items-center gap-3 px-4 py-3.5 text-ink"
          >
            <Link to={`/admin/partners/${partner.id}`}>
              <span
                aria-hidden="true"
                className={cn(
                  "sk-avatar size-10 shrink-0 text-[16px]",
                  partner.isActive ? "bg-note" : "border-dashed bg-transparent",
                )}
              >
                {partner.name.slice(0, 1).toUpperCase()}
              </span>
              <span className="min-w-0 flex-1 truncate text-[16px] font-semibold">{partner.name}</span>
              {partner.isActive ? null : <Badge variant="todo">{t("app.admin.inactive")}</Badge>}
              <Icon name="chevron-right" size={18} className="text-ink-muted" />
            </Link>
          </Card>
        ))}
      </div>
    </>
  );
}
