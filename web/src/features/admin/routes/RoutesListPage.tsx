import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { titleOf, useAdminRoutes } from "@/features/admin/api";
import { PageHeader } from "@/features/admin/ui/PageHeader";
import { NumberMark, StatusChip } from "@/features/admin/ui/StatusChip";
import { formatDate } from "@/lib/format";

export function RoutesListPage() {
  const { t } = useTranslation();
  const routes = useAdminRoutes();
  const rows = routes.data ?? [];
  return (
    <>
      <PageHeader
        title={t("app.admin.routes")}
        subtitle={t("app.admin.routesHint")}
        actions={
          <Button asChild>
            <Link to="/admin/routes/new">
              <Icon name="plus" />
              {t("app.admin.newRoute")}
            </Link>
          </Button>
        }
      />
      <ErrorText error={routes.error} />
      {routes.isPending ? (
        <Loader />
      ) : (
        <Card className="overflow-hidden py-1.5">
          <Table className="min-w-[680px]">
            <TableHeader>
              <TableRow>
                <TableHead className="pl-[18px]">{t("app.admin.name")}</TableHead>
                <TableHead>{t("app.admin.orderingMode")}</TableHead>
                <TableHead className="text-right">{t("app.admin.stops")}</TableHead>
                <TableHead>{t("app.admin.updated")}</TableHead>
                <TableHead>{t("app.admin.status")}</TableHead>
                <TableHead className="pr-[18px] text-right">{t("app.admin.actions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="px-[18px] py-8 text-center text-ink-muted">
                    {t("app.admin.routesEmpty")}
                  </TableCell>
                </TableRow>
              ) : null}
              {rows.map((route, index) => (
                <TableRow key={route.id}>
                  <TableCell className="pl-[18px]">
                    <span className="flex items-center gap-3">
                      <NumberMark value={index + 1} />
                      <span className="flex min-w-0 flex-col gap-0.5">
                        <Link
                          to={`/admin/routes/${route.id}`}
                          className="font-semibold text-ink no-underline hover:underline"
                        >
                          {titleOf(route.title)}
                        </Link>
                        <span className="text-caption text-ink-muted">/routes/{route.slug}</span>
                      </span>
                    </span>
                  </TableCell>
                  <TableCell>{t(`app.admin.orderingModes.${route.orderingMode}`)}</TableCell>
                  <TableCell className="text-right tabular">{route.stopCount}</TableCell>
                  <TableCell className="text-ink-muted tabular">{formatDate(route.updatedAt)}</TableCell>
                  <TableCell>
                    <StatusChip published={route.isPublished} />
                  </TableCell>
                  <TableCell className="pr-[18px] text-right">
                    <Button asChild variant="outline" size="icon-sm">
                      <Link to={`/admin/routes/${route.id}`} aria-label={t("app.common.edit")}>
                        <Icon name="edit" size={18} />
                      </Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </>
  );
}
