import { RefObject } from "react";

import { VideoInfoButton } from "../components/VideoInfoButton";
import { formatQuality, formatTime } from "../lib/video";
import { VideoLibraryItem } from "../types";

type Props = {
  videos: VideoLibraryItem[];
  isUploading: boolean;
  isSyncing: boolean;
  fileInputRef: RefObject<HTMLInputElement | null>;
  onOpenLabel: (video: VideoLibraryItem) => void;
  onOpenClips: (video: VideoLibraryItem) => void;
  onOpenUpload: () => void;
  onFileChange: (file: File | undefined) => void;
  onDeleteVideo: (video: VideoLibraryItem) => void;
  onSync: () => void;
};

export function ProjectsView({ videos, isUploading, isSyncing, fileInputRef, onOpenLabel, onOpenClips, onOpenUpload, onFileChange, onDeleteVideo, onSync }: Props) {
  function formatStatus(status: VideoLibraryItem["status"]) {
    if (status === "active") {
      return "Activo";
    }
    if (status === "idle") {
      return "Idle";
    }
    return "Historico";
  }

  return (
    <section className="projects-view">
      <div className="projects-hero">
        <div>
          <p className="eyebrow">Galeria de partidos</p>
          <h2>Selecciona un proyecto o carga un nuevo video</h2>
        </div>
        <div className="hero-actions">
          <input
            ref={fileInputRef}
            className="hidden-input"
            type="file"
            accept="video/*"
            onChange={(event) => onFileChange(event.target.files?.[0])}
          />
          <button className="ghost-button" type="button" onClick={onSync} disabled={isSyncing}>
            {isSyncing ? "Sincronizando..." : "Sincronizar carpeta"}
          </button>
          <button className="primary-button" type="button" onClick={onOpenUpload} disabled={isUploading}>
            {isUploading ? "Cargando..." : "Cargar video"}
          </button>
        </div>
      </div>

      <div className="project-grid projects-grid-large">
        {videos.map((item) => (
          <div key={item.id} className="project-card-wrapper">
            <div className="project-card project-card-large">
              <div className="project-card-header">
                <strong>{item.display_name}</strong>
                <span className={item.status === "active" ? "project-status active-status" : "project-status"}>{formatStatus(item.status)}</span>
                <VideoInfoButton videoId={item.id} />
              </div>
              <span>{item.original_filename}</span>
              <div className="project-stats">
                <div>
                  <small>Duracion</small>
                  <strong>{formatTime(item.duration_seconds)}</strong>
                </div>
                <div>
                  <small>Calidad</small>
                  <strong>{formatQuality(item.width, item.height)}</strong>
                </div>
                <div>
                  <small>FPS</small>
                  <strong>{item.fps ? item.fps.toFixed(2) : "-"}</strong>
                </div>
                <div>
                  <small>Etiquetado</small>
                  <strong>{item.labeled_percent}%</strong>
                </div>
              </div>
              <div className="project-progress">
                <div className="project-progress-bar" style={{ width: `${item.labeled_percent}%` }} />
              </div>
              <div className="project-meta">
                <span>{item.event_count} marcas</span>
                <span>{item.file_exists ? "Disponible" : "Sin archivo"}</span>
              </div>
            </div>
            <div className="project-card-actions">
              <button type="button" className="primary-button project-action-button" onClick={() => onOpenLabel(item)}>
                Etiquetar
              </button>
              <button type="button" className="secondary-button project-action-button" onClick={() => onOpenClips(item)}>
                Recortes
              </button>
            </div>
            <button
              type="button"
              className="delete-project-button"
              title="Eliminar proyecto"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteVideo(item);
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
