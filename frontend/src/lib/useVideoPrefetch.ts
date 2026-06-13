import { useEffect, useRef } from "react";

import { api, API_BASE } from "./api";
import { VideoLibraryItem } from "../types";

export function useVideoPrefetch(currentVideoId: number | null) {
  const abortControllerRef = useRef<AbortController | null>(null);
  const prefetchedVideoIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!currentVideoId) return;

    const controller = new AbortController();
    abortControllerRef.current = controller;

    async function prefetchNextVideo() {
      try {
        const prioritizedVideos = await api<VideoLibraryItem[]>(
          "/api/videos/prioritized?limit=3",
          { signal: controller.signal }
        );

        const nextVideo = prioritizedVideos.find(
          (v) => v.id !== currentVideoId && v.id !== prefetchedVideoIdRef.current
        );

        if (nextVideo) {
          prefetchedVideoIdRef.current = nextVideo.id;
          const url = `${API_BASE}/api/videos/${nextVideo.id}/stream`;
          const prefetchPromise = fetch(url, {
            signal: controller.signal,
            credentials: "include",
          });
          prefetchPromise.catch(() => {});
        }
      } catch {
        // Ignore errors during prefetch
      }
    }

    const timeoutId = setTimeout(prefetchNextVideo, 2000);
    return () => {
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [currentVideoId]);
}
