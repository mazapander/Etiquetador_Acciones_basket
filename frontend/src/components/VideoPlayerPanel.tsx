import { RefObject } from "react";

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
  jumpSeconds: number;
  tagCounts: TagCount[];
  events: TagEvent[];
  onJumpChange: (value: number) => void;
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
  jumpSeconds,
  tagCounts,
  events,
  onJumpChange,
  onTimeUpdate,
  onDurationChange,
  onSeek,
  onVideoLoadStart,
  onVideoReady,
  onVideoError,
}: Props) {
  const timelineDuration = duration || video.duration_seconds || 0;

  return (
    <div className="video-column">
      <div className="player-settings">
        <label htmlFor="jump-seconds">Salto teclas (s)</label>
        <input
          id="jump-seconds"
          type="number"
          min="0.1"
          step="0.5"
          value={jumpSeconds}
          onChange={(event) => onJumpChange(Math.max(0.1, Number(event.target.value) || 0.1))}
        />
        <span>Izquierda/Derecha: -/+ {jumpSeconds}s</span>
      </div>
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
      <div className="annotation-track" aria-label="Linea de anotaciones">
        <div className="annotation-track-base" />
        {events.map((item) => {
          const left = toPercent(item.start_seconds, timelineDuration);
          if (item.tag.mode === "range" || item.tag.mode === "antagonistic") {
            const endSeconds = item.end_seconds ?? currentTime;
            const width = Math.max(0.6, toPercent(endSeconds, timelineDuration) - left);
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
        <div className="playhead-marker" style={{ left: `${toPercent(currentTime, timelineDuration)}%` }} />
      </div>
    </div>
  );
}
