import { useCallback, useEffect, useRef, useState } from "react";
import { post } from "./api";
import type { ViolationResult } from "./types";

/**
 * Proctoring hook.
 *
 * Limitations are deliberate and documented (see docs/PROCTORING.md):
 *  - Browser events can be missed, duplicated, or triggered by benign
 *    interruptions such as an OS dialog or a notification.
 *  - A page cannot detect other applications, second monitors, phones or
 *    printed notes.
 *  - The SERVER is the authority: this hook only reports events. The client can
 *    never clear or reduce its own violation count.
 */

export type ProctorState = {
  violations: number;
  limit: number;
  disqualified: boolean;
  notice: string | null;
  requestFullscreen: () => Promise<void>;
  inFullscreen: boolean;
};

const KINDS = {
  hidden: "tab-hidden",
  blur: "window-blur",
  fullscreen: "exit-fullscreen",
  exit: "page-exit",
} as const;

export function useProctoring(active: boolean): ProctorState {
  const [violations, setViolations] = useState(0);
  const [limit, setLimit] = useState(3);
  const [disqualified, setDisqualified] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [inFullscreen, setInFullscreen] = useState(false);
  const enabled = useRef(false);

  useEffect(() => {
    enabled.current = active;
  }, [active]);

  const report = useCallback(async (kind: string) => {
    if (!enabled.current) return;
    try {
      const res = await post<ViolationResult>("/api/violation", { kind });
      setViolations(res.violations);
      setLimit(res.limit);
      setDisqualified(res.disqualified);
      setNotice(res.notice ?? null);
    } catch {
      // A failed report must never break the participant's session.
    }
  }, []);

  useEffect(() => {
    if (!active) return;

    const onVisibility = () => {
      if (document.hidden) void report(KINDS.hidden);
    };
    const onBlur = () => void report(KINDS.blur);
    const onFull = () => {
      if (!document.fullscreenElement) {
        setInFullscreen(false);
        void report(KINDS.fullscreen);
      } else {
        setInFullscreen(true);
      }
    };
    const onExit = () => void report(KINDS.exit);

    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("blur", onBlur);
    document.addEventListener("fullscreenchange", onFull);
    window.addEventListener("beforeunload", onExit);

    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("blur", onBlur);
      document.removeEventListener("fullscreenchange", onFull);
      window.removeEventListener("beforeunload", onExit);
    };
  }, [active, report]);

  const requestFullscreen = useCallback(async () => {
    try {
      await document.documentElement.requestFullscreen();
      setInFullscreen(true);
    } catch {
      /* The browser refused; the round still proceeds without fullscreen. */
    }
  }, []);

  return { violations, limit, disqualified, notice, requestFullscreen, inFullscreen };
}

/** Lightweight heartbeat so the server can distinguish a drop from an exit. */
export function useHeartbeat(intervalMs = 30000) {
  useEffect(() => {
    const id = setInterval(() => {
      void fetch("/api/heartbeat", {
        method: "POST",
        credentials: "same-origin",
      }).catch(() => undefined);
    }, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
}