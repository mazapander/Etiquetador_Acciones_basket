import { useState, useRef } from "react";

import { VideoTechInfo } from "../types";

type Props = {
  videoId: number;
};

export function VideoInfoButton({ videoId }: Props) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [techInfo, setTechInfo] = useState<VideoTechInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const timeoutRef = useRef<number | null>(null);

  async function fetchTechInfo() {
    if (techInfo) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/videos/${videoId}/tech-info`);
      if (res.ok) {
        const data = await res.json();
        setTechInfo(data);
      }
    } finally {
      setLoading(false);
    }
  }

  function handleMouseEnter() {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setShowTooltip(true);
    void fetchTechInfo();
  }

  function handleMouseLeave() {
    timeoutRef.current = window.setTimeout(() => {
      setShowTooltip(false);
    }, 150);
  }

  function handleTooltipMouseEnter() {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }

  function handleTooltipMouseLeave() {
    timeoutRef.current = window.setTimeout(() => {
      setShowTooltip(false);
    }, 150);
  }

  return (
    <div className="video-info-container">
      <button
        type="button"
        className="video-info-button"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={() => setShowTooltip((v) => !v)}
        title="Info técnica del video"
      >
        ⓘ
      </button>
      {showTooltip && (
        <div
          className="video-info-tooltip"
          onMouseEnter={handleTooltipMouseEnter}
          onMouseLeave={handleTooltipMouseLeave}
        >
          <h4>Información Técnica</h4>
          {loading ? (
            <p className="loading">Cargando...</p>
          ) : techInfo ? (
            <dl className="tech-info-list">
              {techInfo.wrapper && (
                <>
                  <dt>Contenedor</dt>
                  <dd>{techInfo.wrapper}</dd>
                </>
              )}
              {techInfo.codec && (
                <>
                  <dt>Códec</dt>
                  <dd>{techInfo.codec}</dd>
                </>
              )}
              {techInfo.resolution && (
                <>
                  <dt>Resolución</dt>
                  <dd>{techInfo.resolution}</dd>
                </>
              )}
              {techInfo.fps && (
                <>
                  <dt>FPS</dt>
                  <dd>{techInfo.fps.toFixed(2)}</dd>
                </>
              )}
              {techInfo.bitrate && (
                <>
                  <dt>Bitrate</dt>
                  <dd>{techInfo.bitrate}</dd>
                </>
              )}
              {techInfo.max_bitrate && (
                <>
                  <dt>Bitrate máx</dt>
                  <dd>{techInfo.max_bitrate}</dd>
                </>
              )}
              {techInfo.size_formatted && (
                <>
                  <dt>Tamaño</dt>
                  <dd>{techInfo.size_formatted}</dd>
                </>
              )}
              {techInfo.duration && (
                <>
                  <dt>Duración</dt>
                  <dd>{formatDuration(techInfo.duration)}</dd>
                </>
              )}
              {techInfo.pix_fmt && (
                <>
                  <dt>Pixel format</dt>
                  <dd>{techInfo.pix_fmt}</dd>
                </>
              )}
              {techInfo.color_space && (
                <>
                  <dt>Color space</dt>
                  <dd>{techInfo.color_space}</dd>
                </>
              )}
              {techInfo.color_range && (
                <>
                  <dt>Color range</dt>
                  <dd>{techInfo.color_range}</dd>
                </>
              )}
              {techInfo.profile && (
                <>
                  <dt>Profile</dt>
                  <dd>{techInfo.profile}</dd>
                </>
              )}
              {techInfo.level && (
                <>
                  <dt>Level</dt>
                  <dd>{techInfo.level}</dd>
                </>
              )}
            </dl>
          ) : (
            <p className="error">No disponible</p>
          )}
        </div>
      )}
    </div>
  );
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }
  return `${m}:${s.toString().padStart(2, "0")}`;
}