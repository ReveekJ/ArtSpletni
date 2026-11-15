import { type RefObject, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { PlayButton } from "@/components/sketch/PlayButton";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";

const RATES = [0.75, 1, 1.25, 1.5] as const;

function formatClock(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
  const whole = Math.floor(seconds);
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, "0")}`;
}

interface AudioPlayerProps {
  src: string;
  title?: string | null;
  mediaRef: RefObject<HTMLMediaElement>;
  onMediaElement: (node: HTMLAudioElement | null) => void;
}

export function AudioPlayer({ src, title, mediaRef, onMediaElement }: AudioPlayerProps) {
  const { t } = useTranslation();
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);
  const [rateIndex, setRateIndex] = useState(1);
  const rate = RATES[rateIndex] ?? 1;

  useEffect(() => {
    const media = mediaRef.current;
    if (media) media.playbackRate = rate;
  }, [mediaRef, rate]);

  useEffect(() => {
    if (!title || !("mediaSession" in navigator)) return;
    navigator.mediaSession.metadata = new MediaMetadata({ title, artist: t("common.brand") });
  }, [title, t]);

  const toggle = () => {
    const media = mediaRef.current;
    if (!media) return;
    if (media.paused) {
      media.play().catch((error: unknown) => {
        console.warn("Audio playback was blocked", error);
      });
    } else {
      media.pause();
    }
  };

  const seek = (value: number) => {
    const media = mediaRef.current;
    if (!media || !duration) return;
    media.currentTime = value;
    setCurrent(value);
  };

  const progress = duration ? Math.min(100, (current / duration) * 100) : 0;

  return (
    <div className="flex flex-col gap-3">
      <audio
        ref={onMediaElement}
        src={src}
        preload="metadata"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onTimeUpdate={(event) => setCurrent(event.currentTarget.currentTime)}
        onLoadedMetadata={(event) => {
          setDuration(event.currentTarget.duration);
          event.currentTarget.playbackRate = rate;
        }}
      />
      <div className="flex flex-col gap-1">
        <div className="sk-scrub">
          <span className="sk-scrub__done" style={{ width: `${progress}%` }} aria-hidden="true" />
          <span className="sk-scrub__todo" style={{ left: `${progress}%` }} aria-hidden="true" />
          <span className="sk-scrub__knob" style={{ left: `${progress}%` }} aria-hidden="true" />
          <input
            type="range"
            min={0}
            max={duration || 1}
            step={0.1}
            value={Math.min(current, duration || 0)}
            disabled={!duration}
            aria-label={t("app.point.seek")}
            aria-valuetext={`${formatClock(current)} / ${formatClock(duration)}`}
            onChange={(event) => seek(Number(event.target.value))}
          />
        </div>
        <div className="sk-time">
          <span>{formatClock(current)}</span>
          <span>{duration ? `−${formatClock(duration - current)}` : "−0:00"}</span>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="tabular text-[15px]"
          aria-label={t("app.point.speed", { rate })}
          onClick={() => setRateIndex((index) => (index + 1) % RATES.length)}
        >
          {rate}×
        </Button>
        <PlayButton
          playing={playing}
          label={playing ? t("app.point.pause") : t("app.point.play")}
          onClick={toggle}
        />
        <span className="grid size-11 place-items-center text-ink-muted" aria-hidden="true">
          <Icon name="headphones" />
        </span>
      </div>
    </div>
  );
}
