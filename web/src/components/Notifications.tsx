import { type ReactNode, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import type { Schemas } from "@/api/client";
import { NotificationsContext } from "@/components/notificationsContext";
import { Toaster } from "@/components/ui/sonner";

type Notification = Schemas["Notification"];

export function NotificationsProvider({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const push = useCallback(
    (incoming: Notification[]) => {
      incoming.forEach((item) => {
        toast(t(`app.notifications.${item.kind}`, { title: item.title ?? "" }), {
          id: `${item.kind}-${item.id}`,
          duration: 6000,
        });
      });
    },
    [t],
  );
  const value = useMemo(() => ({ push }), [push]);
  return (
    <NotificationsContext.Provider value={value}>
      {children}
      <Toaster />
    </NotificationsContext.Provider>
  );
}
