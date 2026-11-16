import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { Card } from "@/components/ui/card";
import { formatDistance } from "@/features/points/formatDistance";
import { GossipBadges, GossipSources } from "@/features/points/GossipParts";
import { isGossipInProgress, usePointGossip } from "@/features/points/api";

function GossipCard({ item }: { item: Schemas["GossipItemOut"] }) {
  const { t } = useTranslation();
  const { photo } = item;
  const credit = photo ? [photo.author, photo.license].filter(Boolean).join(", ") : "";
  return (
    <Card asChild className="m-0 gap-3 p-4">
      <article>
        {photo ? (
          <figure className="m-0 flex flex-col gap-1">
            <img
              src={photo.url}
              alt={item.placeName ?? item.title}
              loading="lazy"
              decoding="async"
              className="block max-h-[260px] w-full rounded-xs border border-solid border-ink object-cover dark:brightness-90"
            />
            {credit || photo.sourceUrl ? (
              <figcaption className="flex flex-wrap gap-2 text-caption text-ink-muted">
                {credit ? <span>{t("app.gossip.photoCredit", { credit })}</span> : null}
                {photo.sourceUrl ? (
                  <a href={photo.sourceUrl} target="_blank" rel="noopener noreferrer">
                    {t("app.gossip.photoSource")}
                  </a>
                ) : null}
              </figcaption>
            ) : null}
          </figure>
        ) : null}
        <GossipBadges category={item.category} veracity={item.veracity} />
        <h3 className="m-0 text-h3">{item.title}</h3>
        {item.placeName || item.distanceM != null ? (
          <p className="m-0 flex flex-wrap gap-x-3 text-body-sm text-ink-muted">
            {item.placeName ? <span>{item.placeName}</span> : null}
            {item.distanceM != null ? <span>{formatDistance(item.distanceM, t)}</span> : null}
          </p>
        ) : null}
        <p className="m-0 text-body whitespace-pre-line">{item.text}</p>
        <GossipSources sources={item.sources} />
      </article>
    </Card>
  );
}

export function GossipFeed({ pointId }: { pointId: string }) {
  const { t } = useTranslation();
  const gossip = usePointGossip(pointId);
  const items = gossip.data?.items ?? [];
  const inProgress = isGossipInProgress(gossip.data?.status);
  const failed = gossip.data?.status === "failed" && items.length === 0;

  if (gossip.isPending || (items.length === 0 && !inProgress && !failed && !gossip.error)) return null;

  return (
    <section className="flex flex-col gap-3" aria-labelledby="gossip-feed-title">
      <h2 id="gossip-feed-title" className="m-0 text-h2">
        {t("app.gossip.title")}
      </h2>
      <p className="m-0 text-caption text-ink-muted">{t("app.gossip.disclaimer")}</p>
      {inProgress && items.length === 0 ? (
        <p className="m-0 text-body-sm text-ink-muted">{t("app.gossip.collecting")}</p>
      ) : null}
      {failed || gossip.error ? (
        <p className="m-0 text-body-sm text-ink-muted">{t("app.gossip.failed")}</p>
      ) : null}
      {items.map((item) => (
        <GossipCard key={item.id} item={item} />
      ))}
    </section>
  );
}
