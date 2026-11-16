import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { useAuthOptions, yandexLoginUrl } from "@/features/auth/api";

export function AuthIntro({ title, lead }: { title: ReactNode; lead?: ReactNode }) {
  return (
    <header className="flex flex-col gap-2 pt-4">
      <h1 className="m-0 text-display-sm">{title}</h1>
      {lead ? <p className="m-0 text-body text-ink-muted">{lead}</p> : null}
    </header>
  );
}

export function YandexEntry({ next }: { next: string }) {
  const { t } = useTranslation();
  if (!useAuthOptions().data?.yandexEnabled) return null;
  return (
    <>
      <Button asChild block>
        <a href={yandexLoginUrl(next)}>
          <Icon name="user" />
          {t("app.auth.yandex")}
        </a>
      </Button>
      <OrDivider />
    </>
  );
}

function OrDivider() {
  const { t } = useTranslation();
  return (
    <div className="flex items-center gap-3 text-[14px] text-ink-muted">
      <span aria-hidden="true" className="flex-1 border-t-[1.5px] border-dashed border-pencil-solid" />
      {t("app.auth.orEmail")}
      <span aria-hidden="true" className="flex-1 border-t-[1.5px] border-dashed border-pencil-solid" />
    </div>
  );
}
