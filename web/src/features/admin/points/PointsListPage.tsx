import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { titleOf, useAdminPoints } from "@/features/admin/api";
import { NativeSelect } from "@/features/admin/ui/NativeSelect";
import { PageHeader } from "@/features/admin/ui/PageHeader";
import { SearchInput } from "@/features/admin/ui/SearchInput";
import { LangChips, NumberMark, StatusChip } from "@/features/admin/ui/StatusChip";
import { formatDate } from "@/lib/format";

type KindFilter = "gossip" | "partner" | null;

export default function PointsListPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [kind, setKind] = useState<KindFilter>(null);
  const points = useAdminPoints(search, kind);
  const rows = points.data ?? [];

  return (
    <>
      <PageHeader
        title={t("app.admin.points")}
        subtitle={t("app.admin.pointsHint")}
        actions={
          <Button asChild>
            <Link to="/admin/points/new">
              <Icon name="plus" />
              {t("app.admin.newPoint")}
            </Link>
          </Button>
        }
      />
      <div className="flex flex-wrap items-center gap-3">
        <SearchInput
          placeholder={t("app.admin.search")}
          aria-label={t("app.admin.search")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <NativeSelect
          size="sm"
          aria-label={t("app.admin.kind")}
          value={kind ?? ""}
          onChange={(event) => setKind(event.target.value === "" ? null : (event.target.value as KindFilter))}
        >
          <option value="">{t("app.admin.allKinds")}</option>
          <option value="gossip">{t("app.admin.kinds.gossip")}</option>
          <option value="partner">{t("app.admin.kinds.partner")}</option>
        </NativeSelect>
      </div>
      <ErrorText error={points.error} />
      {points.isPending ? (
        <Loader />
      ) : (
        <Card className="overflow-hidden py-1.5">
          <Table className="min-w-[760px]">
            <TableHeader>
              <TableRow>
                <TableHead className="pl-[18px]">{t("app.admin.titleField")}</TableHead>
                <TableHead>{t("app.admin.kind")}</TableHead>
                <TableHead>{t("app.admin.languages")}</TableHead>
                <TableHead>{t("app.admin.updated")}</TableHead>
                <TableHead>{t("app.admin.status")}</TableHead>
                <TableHead className="pr-[18px] text-right">{t("app.admin.actions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="px-[18px] py-8 text-center text-ink-muted">
                    {t("app.admin.pointsEmpty")}
                  </TableCell>
                </TableRow>
              ) : null}
              {rows.map((point, index) => (
                <TableRow key={point.id}>
                  <TableCell className="pl-[18px]">
                    <span className="flex items-center gap-3">
                      <NumberMark value={index + 1} />
                      <span className="flex min-w-0 flex-col gap-0.5">
                        <Link
                          to={`/admin/points/${point.id}`}
                          className="font-semibold text-ink no-underline hover:underline"
                        >
                          {titleOf(point.title)}
                        </Link>
                        <span className="text-caption text-ink-muted tabular">
                          {point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}
                        </span>
                      </span>
                    </span>
                  </TableCell>
                  <TableCell>{t(`app.admin.kinds.${point.kind}`)}</TableCell>
                  <TableCell>
                    <LangChips filled={point.title} />
                  </TableCell>
                  <TableCell className="text-ink-muted tabular">{formatDate(point.updatedAt)}</TableCell>
                  <TableCell>
                    <StatusChip published={point.isPublished} />
                  </TableCell>
                  <TableCell className="pr-[18px] text-right">
                    <Button asChild variant="outline" size="icon-sm">
                      <Link to={`/admin/points/${point.id}`} aria-label={t("app.common.edit")}>
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
