import { RefObject, useMemo, useState } from "react";

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
  onEditDetails: (item: VideoLibraryItem) => void;
};

export function ProjectsView({ videos, isUploading, isSyncing, fileInputRef, onOpenLabel, onOpenClips, onOpenUpload, onFileChange, onDeleteVideo, onSync, onEditDetails }: Props) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filteredVideos = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    return videos.filter((item) => {
      if (statusFilter !== "all" && item.status !== statusFilter) return false;
      if (!query) return true;
      return [item.display_name, item.original_filename, item.match_name, item.competition, item.home_team, item.away_team, item.game_format, item.category]
        .some((value) => value?.toLocaleLowerCase().includes(query));
    });
  }, [videos, search, statusFilter]);

  function formatStatus(status: VideoLibraryItem["status"]) {
    if (status === "active") {
      return "Activo";
    }
    if (status === "idle") {
      return "Pendiente";
    }
    return "Terminado";
  }

  return (
    <section className="projects-view">
      <div className="projects-hero">
        <div>
          <p className="eyebrow">Galeria de partidos</p>
          <h2>Partidos y vídeos</h2>
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

      <div className="gallery-toolbar">
        <div className="gallery-heading">
          <strong>Galería</strong>
          <span>{filteredVideos.length} de {videos.length} partidos</span>
        </div>
        <div className="gallery-filters">
          <label className="gallery-search">
            <span className="visually-hidden">Buscar partidos</span>
            <input type="search" placeholder="Buscar partido, equipo, archivo..." value={search} onChange={(event) => setSearch(event.target.value)} />
          </label>
          <label className="gallery-status-filter">
            <span className="visually-hidden">Filtrar por estado</span>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">Todos los estados</option>
              <option value="active">Activos</option>
              <option value="idle">Pendientes</option>
              <option value="completed">Terminados</option>
            </select>
          </label>
        </div>
      </div>

      <div className="project-grid projects-grid-large">
        {filteredVideos.map((item) => (
          <div key={item.id} className="project-card-wrapper">
            <div className="project-card project-card-large">
              <div className="project-card-header">
                <strong title={item.match_name || item.display_name}>{item.match_name || item.display_name}</strong>
                <VideoInfoButton videoId={item.id} />
                <button type="button" className="delete-project-button" title="Eliminar proyecto" aria-label={`Eliminar ${item.display_name}`} onClick={() => onDeleteVideo(item)}>
                  ×
                </button>
              </div>
              <div className="project-card-subline">
                <span title={item.original_filename}>{item.original_filename}</span>
                <span className={item.status === "active" ? "project-status active-status" : "project-status"}>{formatStatus(item.status)}</span>
              </div>
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
                <span>{item.game_format ?? "Sin modalidad"}</span>
                <span>{item.category ?? "Sin categoría"}</span>
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
              <button type="button" className="secondary-button project-action-button" title={item.details_completed ? "Editar datos" : "Completar datos"} aria-label={`${item.details_completed ? "Editar" : "Completar"} datos de ${item.display_name}`} onClick={() => onEditDetails(item)}>
                Datos
              </button>
            </div>
          </div>
        ))}
      </div>
      {filteredVideos.length === 0 && (
        <div className="gallery-empty">
          <strong>{videos.length === 0 ? "Aún no hay partidos" : "No hay partidos con estos filtros"}</strong>
          <span>{videos.length === 0 ? "Carga un vídeo o sincroniza la carpeta para empezar." : "Prueba otra búsqueda o cambia el estado."}</span>
        </div>
      )}
    </section>
  );
}
