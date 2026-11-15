import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { api, type Schemas, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { useNotifications } from "@/components/notificationsContext";
import { HandUnderline } from "@/components/sketch/HandUnderline";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { RunProgress } from "@/features/routes/RunProgress";
import { useEngageRoute } from "@/features/routes/api";
import { ScanOutcomeArt } from "@/features/scan/ScanOutcomeArt";

type ScanResponse = Schemas["ScanResponse"];

export default function ScanPage() {
  const { token = "" } = useParams();
  const queryClient = useQueryClient();
  const notifications = useNotifications();
  const started = useRef(false);
  const scan = useMutation({
    mutationFn: () => unwrap(api.POST("/api/scans", { body: { token } })),
    onSuccess: (result) => {
      notifications.push(result.notifications);
      void queryClient.invalidateQueries();
    },
  });

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    scan.mutate();
  }, [scan]);

  if (scan.isPending || scan.isIdle) return <Loader />;
  if (scan.error) return <ErrorText error={scan.error} />;
  return <ScanOutcome result={scan.data} />;
}

function ScanOutcome({ result }: { result: ScanResponse }) {
  const { t } = useTranslation();
  const engage = useEngageRoute();
  const notifications = useNotifications();
  const point = result.point;
  const run = engage.data?.run ?? result.run;
  const hasPrimary = result.contentAvailable && point !== null;

  return (
    <section className="flex flex-1 flex-col gap-5">
      <ScanOutcomeArt outcome={result.outcome} point={point} run={result.run} />

      <div className="flex flex-col gap-2.5 text-center">
        {point ? <p className="m-0 text-label text-ink-muted">{point.title}</p> : null}
        <h1 className="m-0 text-h1">{t(`app.scan.${result.outcome}`)}</h1>
      </div>

      {result.run ? (
        <Card className="px-4 py-3.5">
          <RunProgress run={result.run} />
        </Card>
      ) : null}

      {result.nextStops.length > 0 ? (
        <section className="flex flex-col gap-3">
          <h2 className="m-0 text-h2">{t("app.scan.nextStops")}</h2>
          <Card variant="pencil" asChild className="px-4 py-1">
            <ul className="m-0 list-none">
              {result.nextStops.map((stop, index) => (
                <li
                  key={stop.pointId ?? index}
                  className="flex items-start gap-3 border-b border-solid border-rule py-3 last:border-b-0"
                >
                  <span className="sk-pin mt-0.5 shrink-0" aria-hidden="true">
                    {index + 1}
                  </span>
                  <span className="flex flex-col gap-0.5">
                    {stop.title ? <span className="text-[17px] font-semibold">{stop.title}</span> : null}
                    {stop.hint ? <span className="text-body-sm text-ink-muted">{stop.hint}</span> : null}
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        </section>
      ) : null}

      {engage.data ? (
        <Card className="px-4 py-3.5">
          <RunProgress run={engage.data.run} />
        </Card>
      ) : null}
      <ErrorText error={engage.error} />

      <div className="mt-auto flex flex-col gap-3.5 pt-2">
        {hasPrimary && point ? (
          <Button asChild block>
            <Link to={`/points/${point.id}`}>
              <Icon name="headphones" />
              {t("app.scan.openContent")}
            </Link>
          </Button>
        ) : null}
        {result.candidates.length > 0 && point
          ? result.candidates.map((candidate, index) => (
              <Button
                key={candidate.routeId}
                type="button"
                block
                variant={!hasPrimary && index === 0 ? "default" : "secondary"}
                disabled={engage.isPending}
                onClick={() =>
                  engage.mutate(
                    { routeId: candidate.routeId, pointId: point.id },
                    { onSuccess: (response) => notifications.push(response.notifications) },
                  )
                }
              >
                <Icon name="route" />
                {t(`app.scan.${candidate.action}`, { title: candidate.routeTitle })}
              </Button>
            ))
          : null}
        {result.outcome === "switch_offer" ? (
          <p className="m-0 text-center text-body-sm text-ink-muted">{t("app.scan.keepCurrent")}</p>
        ) : null}
        {run ? (
          <Link
            to={`/routes/${run.routeSlug}`}
            className="grid h-11 place-items-center text-[16px] font-semibold text-ink no-underline"
          >
            <HandUnderline>{t("app.scan.viewRoute")}</HandUnderline>
          </Link>
        ) : null}
      </div>
    </section>
  );
}
