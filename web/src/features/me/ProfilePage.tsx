import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate } from "react-router-dom";

import { Loader } from "@/components/Loader";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCurrentUser, useSession } from "@/features/auth/api";
import { OffersTab } from "@/features/me/OffersTab";
import { AchievementsTab, CollectionTab, RunsTab, SubmissionsTab } from "@/features/me/ProfileTabs";

const TABS = ["collection", "runs", "offers", "achievements", "submissions"] as const;
type Tab = (typeof TABS)[number];

export default function ProfilePage() {
  const { t } = useTranslation();
  const session = useSession();
  const user = useCurrentUser();
  const [tab, setTab] = useState<Tab>("collection");

  if (session.isPending) return <Loader />;
  if (!user) return <Navigate to="/login?next=/me" replace />;
  const name = user.displayName ?? user.email ?? t("app.profile.title");
  const tabs = TABS.filter((item) => item !== "submissions" || user.kind === "registered");

  return (
    <section className="flex flex-col gap-5">
      <Card variant="pencil" className="mt-1 flex-row items-center gap-3.5 px-4 py-3.5">
        <span aria-hidden="true" className="sk-avatar size-12 shrink-0 text-xl">
          {name.slice(0, 1).toUpperCase()}
        </span>
        <span className="flex min-w-0 flex-1 flex-col gap-0.5">
          <h1 className="m-0 truncate text-[20px] leading-[1.25] font-semibold">{name}</h1>
          {user.displayName && user.email ? (
            <span className="truncate text-[14px] text-ink-muted">{user.email}</span>
          ) : null}
        </span>
      </Card>

      {user.kind === "guest" ? (
        <Alert>
          <Icon name="info" />
          <AlertDescription>
            {t("app.auth.guestHint")}
            <Button asChild size="sm" className="mt-2 self-start">
              <Link to="/register?next=/me">{t("app.auth.submitRegister")}</Link>
            </Button>
          </AlertDescription>
        </Alert>
      ) : (
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline" size="sm">
            <Link to="/suggest">
              <Icon name="edit" size={18} />
              {t("app.nav.suggest")}
            </Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link to="/partner">
              <Icon name="gift" size={18} />
              {t("app.nav.partner")}
            </Link>
          </Button>
        </div>
      )}

      <Tabs
        value={tab}
        onValueChange={(value) => {
          const next = TABS.find((item) => item === value);
          if (next) setTab(next);
        }}
      >
        <TabsList>
          {tabs.map((item) => (
            <TabsTrigger key={item} value={item}>
              {t(`app.profile.${item}`)}
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value="collection">
          <CollectionTab />
        </TabsContent>
        <TabsContent value="runs">
          <RunsTab />
        </TabsContent>
        <TabsContent value="offers">
          <OffersTab />
        </TabsContent>
        <TabsContent value="achievements">
          <AchievementsTab />
        </TabsContent>
        {user.kind === "registered" ? (
          <TabsContent value="submissions">
            <SubmissionsTab />
          </TabsContent>
        ) : null}
      </Tabs>
    </section>
  );
}
