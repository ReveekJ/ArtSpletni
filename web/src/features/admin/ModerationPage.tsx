import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { api, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/features/admin/ui/PageHeader";
import { Segmented } from "@/features/admin/ui/Segmented";
import { formatDateTime } from "@/lib/format";

type Status = "pending" | "approved" | "rejected";

const STATUSES: Status[] = ["pending", "approved", "rejected"];

export default function ModerationPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<Status>("pending");
  const [comments, setComments] = useState<Record<string, string>>({});
  const submissions = useQuery({
    queryKey: ["admin", "submissions", status],
    queryFn: () => unwrap(api.GET("/api/admin/submissions", { params: { query: { status } } })),
  });
  const refresh = () => void queryClient.invalidateQueries({ queryKey: ["admin", "submissions"] });
  const approve = useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.POST("/api/admin/submissions/{submission_id}/approve", {
          params: { path: { submission_id: id } },
        }),
      ),
    onSuccess: refresh,
  });
  const reject = useMutation({
    mutationFn: (id: string) =>
      unwrap(
        api.POST("/api/admin/submissions/{submission_id}/reject", {
          params: { path: { submission_id: id } },
          body: { comment: comments[id] || null },
        }),
      ),
    onSuccess: refresh,
  });
  const rows = submissions.data ?? [];

  return (
    <>
      <PageHeader
        title={t("app.admin.moderation")}
        actions={
          <Segmented
            label={t("app.admin.status")}
            value={status}
            options={STATUSES.map((item) => ({
              value: item,
              label: t(`app.profile.submissionStatus.${item}`),
            }))}
            onChange={setStatus}
          />
        }
      />
      <ErrorText error={submissions.error ?? approve.error ?? reject.error} />
      {submissions.isPending ? <Loader /> : null}
      {!submissions.isPending && rows.length === 0 ? (
        <Card variant="todo" className="max-w-[860px] items-center gap-2 px-6 py-10 text-center">
          <Icon name="check" size={26} className="text-ink-muted" />
          <p className="m-0 text-body-sm text-ink-muted">{t("app.admin.moderationEmpty")}</p>
        </Card>
      ) : null}
      <ul className="m-0 flex max-w-[860px] list-none flex-col gap-4 p-0">
        {rows.map(({ submission, authorEmail }) => (
          <Card asChild key={submission.id} className="gap-3 px-5 py-4">
            <li>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <h2 className="m-0 text-h3">{submission.title}</h2>
                <Badge
                  variant={
                    submission.status === "pending"
                      ? "note"
                      : submission.status === "approved"
                        ? "ink"
                        : "todo"
                  }
                >
                  {t(`app.profile.submissionStatus.${submission.status}`)}
                </Badge>
              </div>
              <p className="m-0 text-caption text-ink-muted tabular">
                {t("app.admin.author")}: {authorEmail ?? "—"} · {formatDateTime(submission.createdAt)} ·{" "}
                {submission.language.toUpperCase()} · {submission.latitude.toFixed(5)},{" "}
                {submission.longitude.toFixed(5)}
              </p>
              <p className="m-0 whitespace-pre-line text-body">{submission.story}</p>
              {submission.assetIds.length ? (
                <span className="inline-flex items-center gap-1.5 text-caption text-ink-muted">
                  <Icon name="image" size={16} />
                  {submission.assetIds.length} media
                </span>
              ) : null}
              {submission.status === "pending" ? (
                <div className="flex flex-wrap items-center gap-2.5 border-t border-solid border-rule pt-3">
                  <Button type="button" size="sm" onClick={() => approve.mutate(submission.id)}>
                    <Icon name="check" size={18} />
                    {t("app.admin.approve")}
                  </Button>
                  <Input
                    className="h-11 min-w-[200px] flex-1"
                    aria-label={t("app.admin.rejectComment")}
                    placeholder={t("app.admin.rejectComment")}
                    value={comments[submission.id] ?? ""}
                    onChange={(event) => setComments({ ...comments, [submission.id]: event.target.value })}
                  />
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    onClick={() => reject.mutate(submission.id)}
                  >
                    <Icon name="x" size={18} />
                    {t("app.admin.reject")}
                  </Button>
                </div>
              ) : null}
              {submission.pointId ? (
                <Button asChild variant="link" className="self-start text-[15px]">
                  <Link to={`/admin/points/${submission.pointId}`}>{t("app.admin.openDraft")}</Link>
                </Button>
              ) : null}
            </li>
          </Card>
        ))}
      </ul>
    </>
  );
}
