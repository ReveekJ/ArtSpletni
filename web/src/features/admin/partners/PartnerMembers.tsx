import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { Panel } from "@/features/admin/ui/Panel";

export function PartnerMembers({ partnerId }: { partnerId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const path = { params: { path: { partner_id: partnerId } } };
  const [email, setEmail] = useState("");
  const key = ["admin", "members", partnerId];
  const members = useQuery({
    queryKey: key,
    queryFn: () => unwrap(api.GET("/api/admin/partners/{partner_id}/members", path)),
  });
  const add = useMutation({
    mutationFn: () =>
      unwrap(api.POST("/api/admin/partners/{partner_id}/members", { ...path, body: { email } })),
    onSuccess: () => {
      setEmail("");
      void queryClient.invalidateQueries({ queryKey: key });
    },
  });
  const remove = useMutation({
    mutationFn: (userId: string) =>
      unwrap(
        api.DELETE("/api/admin/partners/{partner_id}/members/{user_id}", {
          params: { path: { partner_id: partnerId, user_id: userId } },
        }),
      ),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: key }),
  });
  return (
    <Panel title={t("app.admin.members")}>
      <ul className="m-0 flex list-none flex-col p-0">
        {(members.data ?? []).map((member) => {
          const label = member.email ?? member.displayName ?? "";
          return (
            <li
              key={member.userId}
              className="flex items-center gap-3 border-b border-solid border-rule py-2.5 last:border-b-0"
            >
              <span aria-hidden="true" className="sk-avatar size-9 shrink-0 text-[14px]">
                {label.slice(0, 1).toUpperCase()}
              </span>
              <span className="min-w-0 flex-1 truncate text-[15px]">{label}</span>
              <Button
                type="button"
                variant="destructive"
                size="icon-sm"
                aria-label={t("app.common.delete")}
                onClick={() => remove.mutate(member.userId)}
              >
                <Icon name="trash" size={18} />
              </Button>
            </li>
          );
        })}
      </ul>
      <form
        className="flex gap-2"
        onSubmit={(event: FormEvent) => {
          event.preventDefault();
          add.mutate();
        }}
      >
        <Input
          type="email"
          required
          className="h-11"
          aria-label={t("app.admin.addMember")}
          placeholder={t("app.admin.addMember")}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Button type="submit" variant="outline" size="sm">
          <Icon name="plus" size={18} />
          {t("app.common.create")}
        </Button>
      </form>
      <ErrorText error={add.error ?? remove.error} />
    </Panel>
  );
}
