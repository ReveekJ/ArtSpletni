import { useCallback } from "react";
import { useNavigate } from "react-router-dom";

interface RouterHistoryState {
  idx?: number;
}

function hasAppHistory(): boolean {
  const state = window.history.state as RouterHistoryState | null;
  return typeof state?.idx === "number" && state.idx > 0;
}

export function useGoBack(fallback: string): () => void {
  const navigate = useNavigate();
  return useCallback(() => {
    if (hasAppHistory()) navigate(-1);
    else navigate(fallback, { replace: true });
  }, [navigate, fallback]);
}
