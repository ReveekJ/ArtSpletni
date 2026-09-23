import { useEffect, useRef, useState } from "react";
import * as Slider from "@radix-ui/react-slider";

import { useListenTracker } from "../analytics/useListenTracker";

interface AudioPlayerProps {
  src: string;
  slug: string;
}

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds)) return "--:--";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function AudioPlayer({ src, slug }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const rafRef = useRef<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);

  useListenTracker(audioRef, slug);

  useEffect(() => {
    setPlaying(false);
    setCurrent(0);
    setDuration(0);
  }, [src]);

  useEffect(() => {
    const updateProgress = () => {
      if (audioRef.current && !audioRef.current.paused) {
        setCurrent(audioRef.current.currentTime);
        rafRef.current = requestAnimationFrame(updateProgress);
      }
    };

    if (playing) {
      rafRef.current = requestAnimationFrame(updateProgress);
    }

    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [playing]);

  const toggle = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      void audio.play();
    } else {
      audio.pause();
    }
  };

  const handleSeek = (values: number[]) => {
    const audio = audioRef.current;
    const nextPosition = values[0];
    if (!audio || nextPosition === undefined || !duration) return;

    audio.currentTime = nextPosition;
    setCurrent(nextPosition);
  };

  return (
    <div className="player">
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
      />
      <button className="play-btn" onClick={toggle} aria-label={playing ? "Пауза" : "Слушать"}>
        {playing ? "❚❚" : "▶"}
      </button>
      <div className="progress-row">
        <Slider.Root
          className="progress-slider"
          value={[Math.min(current, duration || 0)]}
          max={duration || 1}
          step={0.1}
          min={0}
          disabled={!duration}
          onValueChange={handleSeek}
          aria-label="Позиция трека"
        >
          <Slider.Track className="progress-track">
            <Slider.Range className="progress-range" />
          </Slider.Track>
          <Slider.Thumb className="progress-thumb" />
        </Slider.Root>
        <div className="time">
          <span>{formatTime(current)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>
    </div>
  );
}
