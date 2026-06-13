import { useState, useEffect } from "react";
import { VideoUrlInput } from "./VideoUrlInput";
import { FormatSelector } from "./FormatSelector";
import { DownloadProgressDisplay } from "./DownloadProgressDisplay";
import { VideoInfo, VideoQuality, DownloadFormat } from "../../types";
import { api } from "../../lib/api";

type DownloadProgress = {
  status: "downloading" | "processing" | "completed" | "failed";
  percent: number;
  stage: string;
  speed?: string | null;
  eta?: string | null;
  error?: string | null;
};

type HistoryItem = {
  id: number;
  url: string;
  title: string | null;
  channel: string | null;
  quality: string;
  download_format: string;
  output_name: string | null;
  status: string;
  error_message: string | null;
  file_path: string | null;
  file_size_bytes: number | null;
  duration_seconds: number | null;
  created_at: string | null;
  completed_at: string | null;
};

export function DownloadView() {
  const [url, setUrl] = useState("");
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [quality, setQuality] = useState<VideoQuality>("best");
  const [downloadFormat, setDownloadFormat] = useState<DownloadFormat>("mp4");
  const [outputName, setOutputName] = useState("");
  const [includeAudio, setIncludeAudio] = useState(false);
  const [progress, setProgress] = useState<DownloadProgress | null>(null);
  const [taskId, setTaskId] = useState<number | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      const data = await api<HistoryItem[]>("/api/download/history");
      setHistory(data);
    } catch {
    }
  }

  async function handleFetchInfo() {
    if (!url.trim()) return;
    setIsLoading(true);
    try {
      const info = await api<VideoInfo>(`/api/download/info?url=${encodeURIComponent(url)}`);
      setVideoInfo(info);
    } catch (err) {
      setVideoInfo(null);
      alert(err instanceof Error ? err.message : "Error al obtener info del video");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleStartDownload() {
    if (!url.trim()) return;
    setProgress({ status: "downloading", percent: 0, stage: "Iniciando descarga..." });

    try {
      const response = await api<{ task_id: number; download_id: number }>("/api/download/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          quality,
          download_format: downloadFormat,
          output_name: outputName.trim() || null,
          video_title: videoInfo?.title || null,
          video_channel: videoInfo?.channel || null,
          include_audio: includeAudio,
        }),
      });

      setTaskId(response.task_id);

      const pollInterval = setInterval(async () => {
        try {
          const status = await api<DownloadProgress>(`/api/download/progress/${response.task_id}`);
          setProgress(status);
          if (status.status === "completed" || status.status === "failed") {
            clearInterval(pollInterval);
            loadHistory();
          }
        } catch {
          clearInterval(pollInterval);
        }
      }, 1000);
    } catch (err) {
      setProgress({
        status: "failed",
        percent: 0,
        stage: "",
        error: err instanceof Error ? err.message : "Error al iniciar descarga",
      });
    }
  }

  function handleReset() {
    setUrl("");
    setVideoInfo(null);
    setProgress(null);
    setTaskId(null);
    setOutputName("");
    setQuality("best");
    setDownloadFormat("mp4");
    setIncludeAudio(false);
  }

  function formatBytes(bytes: number | null): string {
    if (bytes === null) return "-";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  return (
    <section className="download-view">
      <div className="download-header">
        <h2>Descargar video</h2>
        <p className="download-subtitle">
          Descarga videos de YouTube, Twitter, y otras plataformas usando yt-dlp
        </p>
      </div>

      <div className="download-content">
        <VideoUrlInput
          url={url}
          onUrlChange={setUrl}
          onFetchInfo={handleFetchInfo}
          isLoading={isLoading}
          videoInfo={videoInfo}
        />

        {videoInfo && (
          <>
            <FormatSelector
              quality={quality}
              downloadFormat={downloadFormat}
              outputName={outputName}
              includeAudio={includeAudio}
              onQualityChange={setQuality}
              onFormatChange={setDownloadFormat}
              onOutputNameChange={setOutputName}
              onIncludeAudioChange={setIncludeAudio}
            />

            <div className="download-actions">
              <button
                type="button"
                className="primary-button download-button"
                onClick={handleStartDownload}
                disabled={progress?.status === "downloading" || progress?.status === "processing"}
              >
                Descargar
              </button>
            </div>
          </>
        )}

        {progress && (
          <DownloadProgressDisplay
            status={progress.status}
            percent={progress.percent}
            stage={progress.stage}
            speed={progress.speed}
            eta={progress.eta}
            error={progress.error}
            onReset={handleReset}
          />
        )}

        <div className="download-history-section">
          <div className="history-header" onClick={() => setShowHistory(!showHistory)}>
            <h3>Historial de descargas</h3>
            <span className="history-toggle">{showHistory ? "▲" : "▼"}</span>
          </div>

          {showHistory && (
            <div className="history-list">
              {history.length === 0 ? (
                <p className="empty-hint">No hay descargas registradas</p>
              ) : (
                <table className="history-table">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Titulo</th>
                      <th>Canal</th>
                      <th>Calidad</th>
                      <th>Estado</th>
                      <th>Tamano</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((item) => (
                      <tr key={item.id} className={`history-row ${item.status}`}>
                        <td>{formatDate(item.created_at)}</td>
                        <td className="history-title" title={item.url}>
                          {item.title || item.url.slice(0, 40)}
                        </td>
                        <td>{item.channel || "-"}</td>
                        <td>{item.quality} / {item.download_format}</td>
                        <td>
                          <span className={`status-badge ${item.status}`}>
                            {item.status === "completed" ? "OK" : item.status === "failed" ? "Error" : item.status}
                          </span>
                        </td>
                        <td>{formatBytes(item.file_size_bytes)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}