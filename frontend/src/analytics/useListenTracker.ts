import { useEffect, useRef } from "react";

const SEND_INTERVAL_MS = 15000;
const SEEK_JUMP_THRESHOLD_SECONDS = 1.5;

const VISITOR_ID_KEY = "spletni_visitor_id";

interface ListenState {
  sessionToken: string;
  listenedSeconds: number;
  lastPosition: number;
  duration: number | null;
  seekCount: number;
  isCompleted: boolean;
}

function getVisitorId(): string {
  let id = localStorage.getItem(VISITOR_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(VISITOR_ID_KEY, id);
  }
  return id;
}

function sendBeacon(slug: string, state: ListenState): void {
  const payload = {
    slug,
    session_token: state.sessionToken,
    visitor_id: getVisitorId(),
    track_duration_seconds: state.duration,
    listened_seconds: Math.round(state.listenedSeconds * 10) / 10,
    last_position_seconds: Math.round(state.lastPosition * 10) / 10,
    seek_count: state.seekCount,
    is_completed: state.isCompleted,
    referrer: document.referrer ? document.referrer.slice(0, 512) : null,
    language: navigator.language ? navigator.language.slice(0, 16) : null,
  };
  void fetch("/api/analytics/listen-sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => undefined);
}

/**
 * Tracks listening depth for an <audio> element and periodically upserts
 * the session state to the analytics endpoint. Network errors are swallowed:
 * analytics must never break playback UX.
 */
export function useListenTracker(
  audioRef: React.RefObject<HTMLAudioElement | null>,
  slug: string,
): void {
  const stateRef = useRef<ListenState>({
    sessionToken: crypto.randomUUID(),
    listenedSeconds: 0,
    lastPosition: 0,
    duration: null,
    seekCount: 0,
    isCompleted: false,
  });
  const lastTickRef = useRef<number>(0);
  const lastSentAtRef = useRef<number>(0);
  const startedRef = useRef(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    stateRef.current = {
      sessionToken: crypto.randomUUID(),
      listenedSeconds: 0,
      lastPosition: 0,
      duration: null,
      seekCount: 0,
      isCompleted: false,
    };
    lastTickRef.current = 0;
    lastSentAtRef.current = 0;
    startedRef.current = false;

    const state = stateRef.current;

    const onPlay = () => {
      lastTickRef.current = audio.currentTime;
      startedRef.current = true;
    };

    const onTimeUpdate = () => {
      const now = audio.currentTime;
      const delta = now - lastTickRef.current;
      if (delta > 0 && delta < SEEK_JUMP_THRESHOLD_SECONDS) {
        state.listenedSeconds += delta;
      } else if (delta >= SEEK_JUMP_THRESHOLD_SECONDS) {
        state.seekCount += 1;
      }
      lastTickRef.current = now;
      state.lastPosition = now;
      state.duration = Number.isFinite(audio.duration) ? audio.duration : null;

      const nowMs = Date.now();
      if (nowMs - lastSentAtRef.current >= SEND_INTERVAL_MS) {
        lastSentAtRef.current = nowMs;
        sendBeacon(slug, state);
      }
    };

    const onEnded = () => {
      state.isCompleted = true;
      state.lastPosition = audio.duration || state.lastPosition;
      sendBeacon(slug, state);
    };

    const onPause = () => {
      if (startedRef.current && audio.currentTime > 0) {
        sendBeacon(slug, state);
      }
    };

    const onVisibilityChange = () => {
      if (document.visibilityState === "hidden" && startedRef.current) {
        sendBeacon(slug, state);
      }
    };

    const onPageHide = () => {
      if (startedRef.current) {
        sendBeacon(slug, state);
      }
    };

    audio.addEventListener("play", onPlay);
    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("pause", onPause);
    document.addEventListener("visibilitychange", onVisibilityChange);
    window.addEventListener("pagehide", onPageHide);

    return () => {
      if (startedRef.current && stateRef.current.listenedSeconds > 0) {
        sendBeacon(slug, stateRef.current);
      }
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("pause", onPause);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      window.removeEventListener("pagehide", onPageHide);
    };
  }, [audioRef, slug]);
}
