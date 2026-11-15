import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";

import { ErrorText } from "@/components/ErrorText";
import { Loader } from "@/components/Loader";
import { Polaroid } from "@/components/sketch/Polaroid";
import { Sticker } from "@/components/sketch/Sticker";
import { Card } from "@/components/ui/card";
import { Icon } from "@/components/ui/icon";
import { MapView } from "@/components/YandexMap";
import { usePointContent } from "@/features/points/api";
import { MediaBlock } from "@/features/points/MediaBlock";
import { formatDate } from "@/lib/format";

export default function PointPage() {
  const { pointId = "" } = useParams();
  const { t } = useTranslation();
  const content = usePointContent(pointId);

  if (content.isPending) return <Loader />;
  if (content.error) return <ErrorText error={content.error} />;
  const point = content.data;

  return (
    <article className="flex flex-col gap-5">
      <Polaroid
        src={point.coverUrl}
        alt={point.title}
        caption={point.address ? point.address.toLowerCase() : undefined}
        tilt="md"
        photoHeight={240}
        className="mx-auto mt-2 w-full max-w-[300px]"
      />

      <header className="flex flex-col gap-1.5">
        <p className="m-0 text-caption text-ink-muted">
          {t("app.point.unlockedAt", { date: formatDate(point.unlockedAt) })}
        </p>
        <h1 className="m-0 text-h1">{point.title}</h1>
        {point.address ? (
          <p className="m-0 flex items-center gap-1.5 text-body-sm text-ink-muted">
            <Icon name="pin" size={16} />
            {point.address}
          </p>
        ) : null}
      </header>

      {point.note ? (
        <aside className="relative flex flex-col gap-1 rounded-md border-sketch bg-note px-4 pt-5 pb-4">
          <Sticker side="left" className="absolute -top-4 left-3 text-hand-sm">
            {t("app.point.partnerNote").toLowerCase()}
          </Sticker>
          <p className="m-0 text-body">{point.note}</p>
        </aside>
      ) : null}

      {point.blocks.map((block, index) =>
        block.kind === "text" ? (
          <p key={index} className="m-0 text-body-lg whitespace-pre-line">
            {block.text}
          </p>
        ) : block.kind === "image" ? (
          block.mediaUrl ? (
            <Card asChild key={index} className="m-0 gap-2 p-3">
              <figure>
                <img
                  src={block.mediaUrl}
                  alt={block.caption ?? ""}
                  loading="lazy"
                  className="block w-full rounded-xs border border-solid border-ink object-cover dark:brightness-90"
                />
                {block.caption ? (
                  <figcaption className="px-1 text-caption text-ink-muted">{block.caption}</figcaption>
                ) : null}
              </figure>
            </Card>
          ) : null
        ) : (
          <MediaBlock key={index} block={block} pointId={point.id} title={point.title} />
        ),
      )}

      <section className="flex flex-col gap-3">
        <h2 className="m-0 text-h2">{t("app.point.where")}</h2>
        <MapView
          markers={[
            { id: point.id, latitude: point.latitude, longitude: point.longitude, title: point.title },
          ]}
        />
      </section>
    </article>
  );
}
