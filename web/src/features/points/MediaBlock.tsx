import { useEffect, useMemo, useRef } from "react";

import type { Schemas } from "@/api/client";
import { Card } from "@/components/ui/card";
import { AudioPlayer } from "@/features/points/AudioPlayer";
import { useReportPlayback } from "@/features/points/api";
import { Transcript } from "@/features/points/Transcript";

const REPORT_INTERVAL_MS = 10_000;

interface MediaBlockProps {
  block: Schemas["BlockOut"];
  pointId: string;
  title?: string | null;
}

export function MediaBlock({ block, pointId, title }: MediaBlockProps) {
  const assetId = block.assetId;
  const element = useRef<HTMLMediaElement | null>(null);
  const report = useReportPlayback();
  const sessionKey = useMemo(() => crypto.randomUUID(), []);
  const lastReport = useRef(0);

  useEffect(() => {
    const media = element.current;
    if (!media || !assetId) return;
    const send = (force: boolean) => {
      const now = Date.now();
      if (!force && now - lastReport.current < REPORT_INTERVAL_MS) return;
      if (!Number.isFinite(media.duration) || media.duration <= 0) return;
      lastReport.current = now;
      report.mutate({
        pointId,
        assetId,
        sessionKey,
        positionSeconds: media.currentTime,
        durationSeconds: media.duration,
      });
    };
    const onTime = () => send(false);
    const onStop = () => send(true);
    media.addEventListener("timeupdate", onTime);
    media.addEventListener("pause", onStop);
    media.addEventListener("ended", onStop);
    return () => {
      media.removeEventListener("timeupdate", onTime);
      media.removeEventListener("pause", onStop);
      media.removeEventListener("ended", onStop);
    };
  }, [assetId, pointId, report, sessionKey]);

  if (!block.mediaUrl) return null;

  if (block.kind === "audio") {
    return (
      <figure className="m-0 flex flex-col gap-2">
        <AudioPlayer
          src={block.mediaUrl}
          title={block.caption ?? title}
          mediaRef={element}
          onMediaElement={(node) => void (element.current = node)}
        />
        {block.caption ? (
          <figcaption className="text-center text-caption text-ink-muted">{block.caption}</figcaption>
        ) : null}
        {block.transcript ? <Transcript text={block.transcript} /> : null}
      </figure>
    );
  }

  return (
    <Card asChild className="m-0 gap-2 p-3">
      <figure>
        <video
          ref={(node) => void (element.current = node)}
          controls
          playsInline
          preload="metadata"
          src={block.mediaUrl}
          className="block w-full rounded-[10px] border border-solid border-ink bg-paper-sunk"
        />
        {block.caption ? (
          <figcaption className="px-1 text-caption text-ink-muted">{block.caption}</figcaption>
        ) : null}
      </figure>
    </Card>
  );
}
