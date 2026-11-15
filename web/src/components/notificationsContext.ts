import { createContext, useContext } from "react";

import type { Schemas } from "@/api/client";

export interface NotificationsApi {
  push: (items: Schemas["Notification"][]) => void;
}

export const NotificationsContext = createContext<NotificationsApi>({ push: () => undefined });

export function useNotifications(): NotificationsApi {
  return useContext(NotificationsContext);
}
