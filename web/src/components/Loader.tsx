import { useTranslation } from "react-i18next";

import { Skeleton } from "@/components/ui/skeleton";

export function Loader() {
  const { t } = useTranslation();
  return (
    <div role="status" className="mx-auto flex w-full max-w-[560px] flex-col gap-4 px-5 py-8">
      <span className="sr-only">{t("app.common.loading")}</span>
      <Skeleton className="h-10 w-2/3" />
      <Skeleton className="h-48 w-full" />
      <Skeleton className="h-6 w-1/2" />
    </div>
  );
}
