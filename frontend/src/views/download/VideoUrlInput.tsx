import { VideoInfo, VideoQuality, DownloadFormat } from "../../types";

type Props = {
  url: string;
  onUrlChange: (url: string) => void;
  onFetchInfo: () => void;
  isLoading: boolean;
  videoInfo: VideoInfo | null;
};

export function VideoUrlInput({ url, onUrlChange, onFetchInfo, isLoading, videoInfo }: Props) {
  function formatDuration(seconds: number | null): string {
    if (seconds === null) return "--:--";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }

  return (
    <div className="download-url-section">
      <div className="url-input-group">
        <input
          type="text"
          className="url-input"
          placeholder="Pega el enlace del video (YouTube, Twitter, etc.)"
          value={url}
          onChange={(e) => onUrlChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && url.trim() && onFetchInfo()}
        />
        <button
          type="button"
          className="secondary-button"
          onClick={onFetchInfo}
          disabled={!url.trim() || isLoading}
        >
          {isLoading ? "Buscando..." : "Buscar info"}
        </button>
      </div>

      {videoInfo && (
        <div className="video-info-preview">
          {videoInfo.thumbnail && (
            <img src={videoInfo.thumbnail} alt={videoInfo.title || ""} className="video-thumbnail" />
          )}
          <div className="video-info-details">
            <h3>{videoInfo.title || "Sin titulo"}</h3>
            {videoInfo.channel && <p className="video-channel">{videoInfo.channel}</p>}
            <div className="video-meta-row">
              <span className="video-duration">{formatDuration(videoInfo.duration)}</span>
              {videoInfo.playlist_title && (
                <span className="video-playlist">Playlist: {videoInfo.playlist_title}</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}