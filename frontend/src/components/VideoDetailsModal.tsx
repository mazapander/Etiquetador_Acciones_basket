import { FormEvent } from "react";

import { Video } from "../types";

export type VideoDetailsDraft = {
  game_format: string;
  category: string;
  match_name: string;
  competition: string;
  home_team: string;
  away_team: string;
  match_date: string;
  duration_seconds: string;
  fps: string;
  width: string;
  height: string;
};

export function makeVideoDetailsDraft(video: Video): VideoDetailsDraft {
  return {
    game_format: video.game_format ?? "",
    category: video.category ?? "",
    match_name: video.match_name ?? "",
    competition: video.competition ?? "",
    home_team: video.home_team ?? "",
    away_team: video.away_team ?? "",
    match_date: video.match_date ?? "",
    duration_seconds: String(video.duration_seconds ?? ""),
    fps: String(video.fps ?? ""),
    width: String(video.width ?? ""),
    height: String(video.height ?? ""),
  };
}

type Props = {
  video: Video;
  draft: VideoDetailsDraft;
  saving: boolean;
  error: string | null;
  onChange: (draft: VideoDetailsDraft) => void;
  onSave: () => void;
  onClose: () => void;
};

export function VideoDetailsModal({ video, draft, saving, error, onChange, onSave, onClose }: Props) {
  const update = (key: keyof VideoDetailsDraft, value: string) => onChange({ ...draft, [key]: value });
  const complete = Boolean(draft.game_format.trim() && draft.category.trim() && draft.match_name.trim());
  const technical = [
    video.container_name && `Contenedor: ${video.container_name}`,
    video.codec_name && `Códec: ${video.codec_name}`,
    video.bit_rate && `Bitrate: ${(video.bit_rate / 1_000_000).toFixed(2)} Mbps`,
    video.size_bytes && `Tamaño: ${(video.size_bytes / 1_048_576).toFixed(1)} MB`,
  ].filter(Boolean);

  function submit(event: FormEvent) { event.preventDefault(); if (complete) onSave(); }

  return <div className="modal-backdrop" role="presentation">
    <form className="tag-modal video-details-modal" role="dialog" aria-modal="true" aria-label="Datos del partido" onSubmit={submit}>
      <div className="modal-header"><h2>Datos del partido</h2><button type="button" className="ghost-button" onClick={onClose}>Cerrar</button></div>
      <p>{video.display_name}</p>
      {error && <p className="error-banner" role="alert">{error}</p>}
      <div className="details-grid">
        <label className="field-block">Modalidad *<input list="game-format-options" value={draft.game_format} onChange={(event) => update("game_format", event.target.value)} placeholder="5x5 o 3x3" required /><datalist id="game-format-options"><option value="5x5" /><option value="3x3" /></datalist></label>
        <label className="field-block">Categoría *<input value={draft.category} onChange={(event) => update("category", event.target.value)} placeholder="Ej. Senior femenino" required /></label>
        <label className="field-block field-block-wide">Partido *<input value={draft.match_name} onChange={(event) => update("match_name", event.target.value)} placeholder="Ej. Equipo A vs Equipo B" required /></label>
        <label className="field-block">Equipo local<input value={draft.home_team} onChange={(event) => update("home_team", event.target.value)} /></label>
        <label className="field-block">Equipo visitante<input value={draft.away_team} onChange={(event) => update("away_team", event.target.value)} /></label>
        <label className="field-block">Competición<input value={draft.competition} onChange={(event) => update("competition", event.target.value)} /></label>
        <label className="field-block">Fecha del partido<input type="date" value={draft.match_date} onChange={(event) => update("match_date", event.target.value)} /></label>
      </div>
      <h3>Datos técnicos detectados</h3>
      {technical.length > 0 && <p className="detected-tech">{technical.join(" · ")}</p>}
      <div className="details-grid">
        {([ ["duration_seconds", "Duración (s)"], ["fps", "FPS"], ["width", "Ancho (px)"], ["height", "Alto (px)"] ] as const).map(([key, label]) =>
          <label className="field-block" key={key}>{label}<input type="number" min="0.001" step="any" value={draft[key]} onChange={(event) => update(key, event.target.value)} /></label>
        )}
      </div>
      <div className="modal-actions"><span>* Obligatorio</span><button type="submit" disabled={!complete || saving}>{saving ? "Guardando..." : "Guardar datos"}</button></div>
    </form>
  </div>;
}
