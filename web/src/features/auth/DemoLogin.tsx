import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import type { Schemas } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuthOptions, useDemoLogin } from "@/features/auth/api";

type DemoAccount = Schemas["DemoAccountView"];

function roleKey(account: DemoAccount): "admin" | "partner" | "player" {
  if (account.role === "admin") return "admin";
  return account.isPartner ? "partner" : "player";
}

function landingFor(account: DemoAccount, next: string): string {
  const role = roleKey(account);
  if (role === "admin") return "/admin";
  if (role === "partner") return "/partner";
  return next;
}

export function DemoLogin({ next }: { next: string }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const accounts = useAuthOptions().data?.demoAccounts ?? [];
  const login = useDemoLogin();
  if (accounts.length === 0) return null;

  return (
    <section className="flex flex-col gap-3 rounded-wobble border-[1.5px] border-dashed border-pencil-solid p-4">
      <header className="flex flex-col gap-1">
        <h2 className="m-0 text-[17px] font-semibold">{t("app.auth.demoTitle")}</h2>
        <p className="m-0 text-[14px] text-ink-muted">{t("app.auth.demoLead")}</p>
      </header>
      <div className="flex flex-col gap-2">
        {accounts.map((account) => (
          <Button
            key={account.key}
            type="button"
            variant="outline"
            size="sm"
            block
            className="justify-between"
            disabled={login.isPending}
            onClick={() =>
              login.mutate(account.key, { onSuccess: () => navigate(landingFor(account, next)) })
            }
          >
            <span className="truncate">{account.displayName}</span>
            <Badge variant={roleKey(account) === "player" ? "todo" : "note"}>
              {t(`app.auth.demoRole.${roleKey(account)}`)}
            </Badge>
          </Button>
        ))}
      </div>
      <ErrorText error={login.error} />
    </section>
  );
}
