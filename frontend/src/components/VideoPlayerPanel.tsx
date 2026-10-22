import { RefObject, useState } from "react";

import { TagEvent, Video } from "../types";
import { formatTime, toPercent } from "../lib/video";

type TagCount = {
  id: number;
  name: string;
  color: string;
  count: number;
};

type Props = {
  video: Video;
  streamUrl: string;
  videoRef: RefObject<HTMLVideoElement | null>;
  videoError: string | null;
  currentTime: number;
  duration: number;
  tagCounts: TagCount[];
  events: TagEvent[];
  onTimeUpdate: (value: number) => void;
  onDurationChange: (value: number) => void;
  onSeek: (seconds: number) => void;
  onVideoLoadStart: () => void;
  onVideoReady: () => void;
  onVideoError: () => void;
};

export function VideoPlayerPanel({
  video,
  streamUrl,
  videoRef,
  videoError,
  currentTime,
  duration,
  tagCounts,
  events,
  onTimeUpdate,
  onDurationChange,
  onSeek,
  onVideoLoadStart,
  onVideoReady,
  onVideoError,
}: Props) {
  const timelineDuration = duration || video.duration_seconds || 0;
  const [zoom, setZoom] = useState(1);
  const [windowStart, setWindowStart] = useState(0);
  const windowLength = timelineDuration / zoom;
  const start = Math.min(windowStart, Math.max(0, timelineDuration - windowLength));
  const visible = events.filter((item) => item.start_seconds <= start + windowLength && (item.end_seconds ?? item.start_seconds) >= start);
  const percent = (seconds: number) => toPercent(seconds - start, windowLength);

  return (
    <div className="video-column">
      <div className="video-shell">
        <video
          key={video.id}
          ref={videoRef}
          className="video-player"
          src={streamUrl}
          controls
          controlsList="nodownload noplaybackrate noremoteplayback"
          disablePictureInPicture
          onContextMenu={(event) => event.preventDefault()}
          tabIndex={-1}
          onLoadStart={onVideoLoadStart}
          onLoadedData={onVideoReady}
          onTimeUpdate={(event) => onTimeUpdate(event.currentTarget.currentTime)}
          onLoadedMetadata={(event) => onDurationChange(event.currentTarget.duration)}
          onError={onVideoError}
        />
        {videoError && (
          <div className="video-error-overlay" role="alert" aria-live="assertive">
            <strong>No se pudo reproducir el video</strong>
            <span>{videoError}</span>
          </div>
        )}
      </div>
      <div className="time-row">
        <span>{formatTime(currentTime)}</span>
        <span>{formatTime(duration || video.duration_seconds)}</span>
      </div>
      <div className="timeline-summary">
        <span>{events.length} anotaciones</span>
        {tagCounts.map((tag) => (
          <span key={tag.id} className="tag-count" style={{ borderColor: tag.color }}>
            {tag.name}: {tag.count}
          </span>
        ))}
      </div>
      <div className="timeline-controls">
        <label>Detalle <input type="range" min="1" max="24" step="1" value={zoom} onChange={(event) => { setZoom(Number(event.target.value)); setWindowStart(Math.max(0, currentTime - timelineDuration / Number(event.target.value) / 2)); }} /> {zoom}×</label>
        <button type="button" onClick={() => setWindowStart(Math.max(0, currentTime - windowLength / 2))}>Centrar reproducción</button>
        <span>{formatTime(start)} – {formatTime(start + windowLength)}</span>
      </div>
      {zoom > 1 && <input className="timeline-pan" type="range" min="0" max={Math.max(0, timelineDuration - windowLength)} step="1" value={start} aria-label="Desplazar línea de acciones" onChange={(event) => setWindowStart(Number(event.target.value))} />}
      <div className="annotation-track" aria-label="Linea de anotaciones" onClick={(event) => { if (event.target === event.currentTarget && windowLength > 0) onSeek(start + event.nativeEvent.offsetX / event.currentTarget.clientWidth * windowLength); }}>
        <div className="annotation-track-base" />
        {visible.map((item) => {
          const left = Math.max(0, percent(item.start_seconds));
          if (item.tag.mode === "range" || item.tag.mode === "antagonistic") {
            const endSeconds = item.end_seconds ?? currentTime;
            const width = Math.max(0.6, Math.min(100 - left, percent(endSeconds) - left));
            return (
              <button
                key={item.id}
                type="button"
                className="annotation-range"
                style={{ left: `${left}%`, width: `${width}%`, backgroundColor: item.tag.color }}
                title={`${item.tag.name}: ${formatTime(item.start_seconds)} - ${formatTime(item.end_seconds ?? currentTime)}`}
                onClick={() => onSeek(item.start_seconds)}
              />
            );
          }
          return (
            <button
              key={item.id}
              type="button"
              className="annotation-instant"
              style={{ left: `${left}%`, backgroundColor: item.tag.color }}
              title={`${item.tag.name}: ${formatTime(item.start_seconds)}`}
              onClick={() => onSeek(item.start_seconds)}
            />
          );
        })}
        {currentTime >= start && currentTime <= start + windowLength && <div className="playhead-marker" style={{ left: `${percent(currentTime)}%` }} />}
      </div>
      <div className="timeline-ruler"><span>{formatTime(start)}</span><span>{formatTime(start + windowLength / 4)}</span><span>{formatTime(start + windowLength / 2)}</span><span>{formatTime(start + windowLength * 3 / 4)}</span><span>{formatTime(start + windowLength)}</span></div>
    </div>
  );
}
