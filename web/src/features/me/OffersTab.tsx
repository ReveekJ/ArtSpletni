import { QRCodeSVG } from "qrcode.react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";

import type { Schemas } from "@/api/client";
import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Stamp } from "@/components/sketch/Sticker";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { useMyOffers, useOfferQr } from "@/features/me/api";
import { EmptyNote } from "@/features/me/ProfileTabs";
import { formatDate } from "@/lib/format";

type Offer = Schemas["MyOfferOut"];

export function OffersTab() {
  const offers = useMyOffers(true);
  const qr = useOfferQr();

  if (offers.isPending) return <Loader />;
  if (offers.error) return <ErrorText error={offers.error} />;
  if (offers.data.length === 0) return <EmptyNote />;

  return (
    <div className="flex flex-col gap-4">
      <ul className="m-0 flex list-none flex-col gap-6 p-0 pt-2">
        {offers.data.map((offer) => (
          <li key={offer.grantId}>
            {offer.status === "active" ? (
              <OfferTicket
                offer={offer}
                qrPending={qr.isPending && qr.variables === offer.grantId}
                qr={qr.data && qr.variables === offer.grantId ? qr.data : null}
                onShowQr={() => qr.mutate(offer.grantId)}
              />
            ) : (
              <OfferUsed offer={offer} />
            )}
          </li>
        ))}
      </ul>
      <ErrorText error={qr.error} />
    </div>
  );
}

interface OfferTicketProps {
  offer: Offer;
  qr: Schemas["QrTokenOut"] | null;
  qrPending: boolean;
  onShowQr: () => void;
}

function OfferTicket({ offer, qr, qrPending, onShowQr }: OfferTicketProps) {
  const { t } = useTranslation();
  const copy = (code: string) => {
    navigator.clipboard
      .writeText(code)
      .then(() => toast(t("app.profile.copied")))
      .catch((error: unknown) => {
        console.error("Clipboard write failed", error);
        toast.error(t("app.common.error"));
      });
  };
  return (
    <Card className="sk-ticket gap-0">
      <Stamp aria-hidden="true" className="absolute top-3.5 right-4 size-[74px]">
        {t("app.profile.bonus")}
      </Stamp>
      <div className="flex flex-col gap-1.5 px-5 pt-5 pb-3.5 pr-[100px]">
        <span className="text-caption text-ink-muted">{offer.partnerName}</span>
        <span className="text-h3">{offer.title}</span>
        {offer.promoCode ? (
          <>
            <span className="mt-2 text-caption text-ink-muted">{t("app.profile.promoLabel")}</span>
            <span className="text-[30px] leading-none font-bold tracking-[.04em] break-all">
              {offer.promoCode}
            </span>
          </>
        ) : null}
      </div>
      <div className="sk-ticket__tear" aria-hidden="true">
        <span />
      </div>
      <div className="flex flex-col items-start gap-3.5 px-5 pt-3 pb-5">
        {offer.terms ? <p className="m-0 text-body-sm">{offer.terms}</p> : null}
        {offer.expiresAt ? (
          <span className="inline-flex items-center gap-1.5 text-caption text-ink-muted">
            <Icon name="clock" size={14} />
            {t("app.profile.expires", { date: formatDate(offer.expiresAt) })}
          </span>
        ) : null}
        <div className="flex flex-wrap gap-3">
          <Button type="button" size="sm" onClick={onShowQr} disabled={qrPending}>
            <Icon name="qr" size={18} />
            {t("app.profile.showQr")}
          </Button>
          {offer.promoCode ? (
            <Button type="button" size="sm" variant="secondary" onClick={() => copy(offer.promoCode ?? "")}>
              <Icon name="copy" size={18} />
              {t("app.profile.copy")}
            </Button>
          ) : null}
        </div>
        {qr ? (
          <div className="flex w-full flex-col items-center gap-2 rounded-md border-sketch bg-paper-raised p-4 text-center">
            <QRCodeSVG
              value={qr.token}
              size={220}
              bgColor="#ffffff"
              fgColor="#231d1e"
              className="rounded-xs bg-white p-2"
            />
            <span className="text-h3 tabular tracking-[.04em]">
              {t("app.profile.code", { code: qr.code })}
            </span>
            <span className="text-caption text-ink-muted">{t("app.profile.qrHint")}</span>
          </div>
        ) : null}
      </div>
    </Card>
  );
}

function OfferUsed({ offer }: { offer: Offer }) {
  const { t } = useTranslation();
  return (
    <Card variant="todo" className="gap-1.5 px-4 py-3.5">
      <span className="flex items-center justify-between gap-3">
        <span className="min-w-0 text-[15px] font-semibold">{offer.title}</span>
        <Badge variant="todo">{t(`app.profile.offerStatus.${offer.status}`)}</Badge>
      </span>
      <span className="text-caption text-ink-muted">{offer.partnerName}</span>
      {offer.terms ? <span className="text-body-sm text-ink-muted">{offer.terms}</span> : null}
    </Card>
  );
}
