import { useTranslation } from "react-i18next";

import type { Schemas } from "@/api/client";
import { Badge } from "@/components/ui/badge";

type Category = Schemas["GossipCategory"];
type Veracity = Schemas["GossipVeracity"];
type Source = Schemas["GossipSourceOut"];

const VERACITY_VARIANT = { legend: "now", unverified: "todo", documented: "ink" } as const;

export function GossipBadges({ category, veracity }: { category: Category; veracity: Veracity }) {
  const { t } = useTranslation();
  return (
    <span className="flex flex-wrap gap-2">
      <Badge variant="note">{t(`app.gossip.category.${category}`)}</Badge>
      <Badge variant={VERACITY_VARIANT[veracity]}>{t(`app.gossip.veracity.${veracity}`)}</Badge>
    </span>
  );
}

function sourceLabel(source: Source): string {
  if (source.title) return source.title;
  try {
    return new URL(source.url).hostname;
  } catch {
    return source.url;
  }
}

export function GossipSources({ sources }: { sources: Source[] }) {
  const { t } = useTranslation();
  if (sources.length === 0) return null;
  return (
    <div className="flex flex-col gap-1">
      <span className="text-caption text-ink-muted">{t("app.gossip.sources")}</span>
      <ul className="m-0 flex list-none flex-col gap-0.5 p-0 text-body-sm">
        {sources.map((source) => (
          <li key={source.url} className="flex flex-wrap items-baseline gap-2">
            <a href={source.url} target="_blank" rel="noopener noreferrer" className="break-all">
              {sourceLabel(source)}
            </a>
            <span className="text-caption text-ink-muted">{t(`app.gossip.origin.${source.origin}`)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
