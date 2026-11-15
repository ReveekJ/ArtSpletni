import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type Schemas, unwrap } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { titleOf, useAdminOffers } from "@/features/admin/api";
import { OfferForm } from "@/features/admin/partners/OfferForm";
import { Panel } from "@/features/admin/ui/Panel";
import { cn } from "@/lib/utils";

export function PartnerOffers({ partnerId }: { partnerId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const offers = useAdminOffers(partnerId);
  const [editing, setEditing] = useState<string | "new" | null>(null);
  const save = useMutation({
    mutationFn: ({ id, body }: { id: string | null; body: Schemas["OfferInput"] }) =>
      id
        ? unwrap(api.PUT("/api/admin/offers/{offer_id}", { params: { path: { offer_id: id } }, body }))
        : unwrap(api.POST("/api/admin/offers", { body })),
    onSuccess: () => {
      setEditing(null);
      void queryClient.invalidateQueries({ queryKey: ["admin", "offers"] });
    },
  });

  return (
    <Panel
      title={t("app.admin.offers")}
      actions={
        editing === "new" ? null : (
          <Button type="button" variant="outline" size="xs" onClick={() => setEditing("new")}>
            <Icon name="plus" size={16} />
            {t("app.admin.newOffer")}
          </Button>
        )
      }
    >
      {editing === "new" ? (
        <div className="rounded-md border-sketch bg-paper p-4">
          <OfferForm
            partnerId={partnerId}
            pending={save.isPending}
            error={save.error}
            onSubmit={(body) => save.mutate({ id: null, body })}
            onCancel={() => setEditing(null)}
          />
        </div>
      ) : null}
      <ul className="m-0 flex list-none flex-col gap-3 p-0">
        {(offers.data ?? []).map((offer) => (
          <li
            key={offer.id}
            className={cn(
              "flex flex-col gap-3 rounded-md p-4",
              offer.isActive ? "border-sketch bg-paper-raised" : "border-todo",
            )}
          >
            <div className="flex flex-wrap items-center gap-3">
              <Icon name="gift" />
              <strong className="min-w-0 flex-1 text-[15px]">{titleOf(offer.title)}</strong>
              {offer.promoCode ? <Badge variant="note">{offer.promoCode}</Badge> : null}
              <span className="text-caption text-ink-muted tabular">
                {t("app.admin.redemptions")}: {offer.redemptionsCount}
                {offer.redemptionLimit ? ` / ${offer.redemptionLimit}` : ""}
              </span>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label={t("app.common.edit")}
                aria-expanded={editing === offer.id}
                onClick={() => setEditing(editing === offer.id ? null : offer.id)}
              >
                <Icon name="edit" size={18} />
              </Button>
            </div>
            {editing === offer.id ? (
              <OfferForm
                partnerId={partnerId}
                offer={offer}
                pending={save.isPending}
                error={save.error}
                onSubmit={(body) => save.mutate({ id: offer.id, body })}
                onCancel={() => setEditing(null)}
              />
            ) : null}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
