import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import QrScanner from "qr-scanner";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type Schemas, unwrap } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Field } from "@/components/sketch/Field";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDateTime } from "@/lib/format";

type RedemptionInput = Schemas["RedemptionInput"];

export default function PartnerPage() {
  const { t } = useTranslation();
  const partners = useQuery({ queryKey: ["partner"], queryFn: () => unwrap(api.GET("/api/partner")) });
  const [selected, setSelected] = useState<string | null>(null);

  if (partners.isPending) return <Loader />;
  if (partners.error) return <ErrorText error={partners.error} />;
  const partnerId = selected ?? partners.data[0]?.id ?? null;

  return (
    <section className="flex flex-col gap-5">
      <header className="flex flex-col gap-2 pt-4">
        <h1 className="m-0 text-display-sm">{t("app.partner.title")}</h1>
      </header>
      {partners.data.length > 1 ? (
        <Field label={t("app.partner.choose")}>
          {({ id }) => (
            <Select value={partnerId ?? ""} onValueChange={setSelected}>
              <SelectTrigger id={id} className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {partners.data.map((partner) => (
                  <SelectItem key={partner.id} value={partner.id}>
                    {partner.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </Field>
      ) : null}
      {partnerId ? (
        <PartnerDesk partnerId={partnerId} />
      ) : (
        <Card variant="todo" className="px-4 py-6 text-center text-body-sm text-ink-muted">
          {t("app.common.empty")}
        </Card>
      )}
    </section>
  );
}

function PartnerDesk({ partnerId }: { partnerId: string }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const path = { params: { path: { partner_id: partnerId } } };
  const [input, setInput] = useState<RedemptionInput | null>(null);
  const [code, setCode] = useState("");
  const lookup = useMutation({
    mutationFn: (body: RedemptionInput) =>
      unwrap(api.POST("/api/partner/{partner_id}/redemptions/lookup", { ...path, body })),
  });
  const redeem = useMutation({
    mutationFn: (body: RedemptionInput) =>
      unwrap(api.POST("/api/partner/{partner_id}/redemptions", { ...path, body })),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["partner", partnerId] }),
  });
  const stats = useQuery({
    queryKey: ["partner", partnerId, "stats"],
    queryFn: () => unwrap(api.GET("/api/partner/{partner_id}/stats", path)),
  });
  const recent = useQuery({
    queryKey: ["partner", partnerId, "recent"],
    queryFn: () => unwrap(api.GET("/api/partner/{partner_id}/redemptions", path)),
  });

  const check = (body: RedemptionInput) => {
    setInput(body);
    redeem.reset();
    lookup.mutate(body);
  };

  const onManual = (event: FormEvent) => {
    event.preventDefault();
    if (code.trim()) check({ code: code.trim() });
  };

  return (
    <div className="flex flex-col gap-6">
      <Card className="gap-4 p-5">
        <QrReader onToken={(token) => check({ token })} />
        <form className="flex items-end gap-3" onSubmit={onManual}>
          <Field label={t("app.partner.manual")} className="min-w-0 flex-1">
            {({ id }) => (
              <Input
                id={id}
                value={code}
                onChange={(event) => setCode(event.target.value)}
                autoCapitalize="characters"
                className="tracking-[.04em] uppercase"
              />
            )}
          </Field>
          <Button variant="secondary" className="h-[52px]">
            {t("app.partner.check")}
          </Button>
        </form>
        <ErrorText error={lookup.error ?? redeem.error} />
      </Card>
      {lookup.data ? (
        <RedemptionCard
          title={lookup.data.offerTitle}
          status={redeem.data?.status ?? lookup.data.status}
          canConfirm={lookup.data.status === "active" && !redeem.data && input !== null}
          confirmed={Boolean(redeem.data)}
          pending={redeem.isPending}
          onConfirm={() => input && redeem.mutate(input)}
        />
      ) : null}
      <section className="flex flex-col gap-3">
        <h2 className="m-0 text-h2">{t("app.partner.stats")}</h2>
        <Card className="px-2 py-1">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead />
                <TableHead className="text-right">{t("app.partner.granted")}</TableHead>
                <TableHead className="text-right">{t("app.partner.redeemed")}</TableHead>
                <TableHead className="text-right">{t("app.partner.limit")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(stats.data ?? []).map((row) => (
                <TableRow key={row.offerId}>
                  <TableCell>{row.title}</TableCell>
                  <TableCell className="text-right tabular">{row.granted}</TableCell>
                  <TableCell className="text-right tabular">{row.redeemed}</TableCell>
                  <TableCell className="text-right tabular">{row.redemptionLimit ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </section>
      <section className="flex flex-col gap-3">
        <h2 className="m-0 text-h2">{t("app.partner.recent")}</h2>
        {(recent.data ?? []).length > 0 ? (
          <Card asChild className="px-4 py-0.5">
            <ul className="m-0 list-none">
              {(recent.data ?? []).map((row) => (
                <li
                  key={row.grantId}
                  className="flex items-center justify-between gap-3 border-b border-solid border-rule py-3 text-body-sm last:border-b-0"
                >
                  <span className="min-w-0">{row.offerTitle}</span>
                  <span className="shrink-0 text-caption text-ink-muted tabular">
                    {row.redeemedAt ? formatDateTime(row.redeemedAt) : ""}
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        ) : (
          <Card variant="todo" className="px-4 py-5 text-center text-body-sm text-ink-muted">
            {t("app.common.empty")}
          </Card>
        )}
      </section>
    </div>
  );
}

interface RedemptionCardProps {
  title: string;
  status: Schemas["GrantStatus"];
  canConfirm: boolean;
  confirmed: boolean;
  pending: boolean;
  onConfirm: () => void;
}

function RedemptionCard({ title, status, canConfirm, confirmed, pending, onConfirm }: RedemptionCardProps) {
  const { t } = useTranslation();
  return (
    <Card
      variant={status === "active" || confirmed ? "pencil" : "todo"}
      className="gap-3 p-5"
      aria-live="polite"
    >
      <div className="flex items-start justify-between gap-3">
        <h2 className="m-0 text-h2">{title}</h2>
        <Badge variant={status === "active" ? "now" : status === "redeemed" ? "ink" : "todo"}>
          {t(`app.profile.offerStatus.${status}`)}
        </Badge>
      </div>
      {canConfirm ? (
        <Button type="button" block disabled={pending} onClick={onConfirm}>
          <Icon name="check" />
          {t("app.partner.confirm")}
        </Button>
      ) : null}
      {confirmed ? (
        <p className="m-0 inline-flex items-center gap-1.5 text-label text-success">
          <Icon name="check" size={18} />
          {t("app.partner.confirmed")}
        </p>
      ) : null}
    </Card>
  );
}

function QrReader({ onToken }: { onToken: (token: string) => void }) {
  const { t } = useTranslation();
  const video = useRef<HTMLVideoElement>(null);
  const [active, setActive] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const onTokenRef = useRef(onToken);
  useEffect(() => {
    onTokenRef.current = onToken;
  });

  useEffect(() => {
    if (!active || !video.current) return;
    const scanner = new QrScanner(
      video.current,
      (result) => {
        setActive(false);
        onTokenRef.current(result.data);
      },
      { returnDetailedScanResult: true, highlightScanRegion: true },
    );
    scanner.start().catch((caught: unknown) => {
      setError(caught);
      setActive(false);
    });
    return () => {
      scanner.stop();
      scanner.destroy();
    };
  }, [active]);

  return (
    <div className="flex flex-col gap-3">
      {active ? (
        <video
          ref={video}
          muted
          playsInline
          className="block aspect-square w-full rounded-md border-sketch bg-paper-sunk object-cover"
        />
      ) : null}
      <Button
        type="button"
        block
        variant={active ? "secondary" : "default"}
        onClick={() => setActive((value) => !value)}
      >
        <Icon name={active ? "x" : "qr"} />
        {active ? t("app.partner.stopScan") : t("app.partner.scan")}
      </Button>
      <ErrorText error={error} />
    </div>
  );
}
