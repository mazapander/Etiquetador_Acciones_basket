import { ClipExportMode, ClipExportPlan, ClipExportResult, TagDefinition, Video } from "../types";
import { formatTime } from "../lib/video";

type Props = {
  video: Video;
  tags: TagDefinition[];
  selectedTagId: number | null;
  exportMode: ClipExportMode;
  preRollSeconds: number;
  postRollSeconds: number;
  outputLabel: string;
  keepSegments: boolean;
  exportProgress: { current: number; total: number; stage: string } | null;
  plan: ClipExportPlan | null;
  result: ClipExportResult | null;
  isPlanning: boolean;
  isExporting: boolean;
  onBack: () => void;
  onGoToLabel: () => void;
  onTagChange: (tagId: number) => void;
  onModeChange: (mode: ClipExportMode) => void;
  onPreRollChange: (value: number) => void;
  onPostRollChange: (value: number) => void;
  onOutputLabelChange: (value: string) => void;
  onKeepSegmentsChange: (value: boolean) => void;
  onPreview: () => void;
  onExport: () => void;
};

const MODE_HELP: Record<ClipExportMode, string> = {
  segments: "Un clip por cada evento o rango de la tag seleccionada.",
  concatenate: "Genera clips por evento y un video final concatenado.",
  exclude: "Genera los tramos complementarios a la tag seleccionada.",
};

export function ClipsView({
  video,
  tags,
  selectedTagId,
  exportMode,
  preRollSeconds,
  postRollSeconds,
  outputLabel,
  keepSegments,
  exportProgress,
  plan,
  result,
  isPlanning,
  isExporting,
  onBack,
  onGoToLabel,
  onTagChange,
  onModeChange,
  onPreRollChange,
  onPostRollChange,
  onOutputLabelChange,
  onKeepSegmentsChange,
  onPreview,
  onExport,
}: Props) {
  return (
    <section className="clips-view">
      <div className="workspace-header">
        <div className="clips-header-actions">
          <button className="ghost-button" type="button" onClick={onBack}>
            Volver a proyectos
          </button>
          <button className="ghost-button" type="button" onClick={onGoToLabel}>
            Ir a etiquetado
          </button>
        </div>
        <div className="clips-video-meta">
          <strong>{video.display_name}</strong>
          <span>{video.original_filename}</span>
        </div>
      </div>

      <section className="clips-layout">
        <div className="clips-config-panel">
          <div className="section-heading">
            <h2>Configuracion de recortes</h2>
          </div>

          <div className="clips-form-grid">
            <label className="field-block">
              <span>Tag</span>
              <select value={selectedTagId ?? ""} onChange={(event) => onTagChange(Number(event.target.value))}>
                <option value="" disabled>
                  Selecciona una tag
                </option>
                {tags.map((tag) => (
                  <option key={tag.id} value={tag.id}>
                    {tag.name} ({tag.mode})
                  </option>
                ))}
              </select>
            </label>

            <label className="field-block">
              <span>Modo</span>
              <select value={exportMode} onChange={(event) => onModeChange(event.target.value as ClipExportMode)}>
                <option value="segments">Segments</option>
                <option value="concatenate">Concatenate</option>
                <option value="exclude">Exclude</option>
              </select>
            </label>

            <label className="field-block">
              <span>Pre-roll (s)</span>
              <input type="number" min="0" step="0.1" value={preRollSeconds} onChange={(event) => onPreRollChange(Number(event.target.value) || 0)} />
            </label>

            <label className="field-block">
              <span>Post-roll (s)</span>
              <input type="number" min="0" step="0.1" value={postRollSeconds} onChange={(event) => onPostRollChange(Number(event.target.value) || 0)} />
            </label>

            <label className="field-block field-block-wide">
              <span>Etiqueta de salida</span>
              <input value={outputLabel} onChange={(event) => onOutputLabelChange(event.target.value)} placeholder="ej. tiros-equipo-a" />
            </label>

            <label className="field-block">
              <span>Guardar segmentos</span>
              <input
                type="checkbox"
                checked={keepSegments}
                onChange={(event) => onKeepSegmentsChange(event.target.checked)}
              />
            </label>
          </div>

          <p className="mode-help">{MODE_HELP[exportMode]}</p>

          {exportProgress && (
            <div className="export-progress-bar">
              <div className="export-progress-info">
                <span>{exportProgress.stage}</span>
                <span>{exportProgress.current}/{exportProgress.total}</span>
              </div>
              <div className="export-progress-track">
                <div className="export-progress-fill" style={{ width: `${(exportProgress.current / exportProgress.total) * 100}%` }} />
              </div>
            </div>
          )}

          <div className="clips-toolbar">
            <button className="secondary-button" type="button" onClick={onPreview} disabled={!selectedTagId || isPlanning}>
              {isPlanning ? "Calculando..." : "Previsualizar"}
            </button>
            <button type="button" onClick={onExport} disabled={!plan || plan.segment_count === 0 || isExporting}>
              {isExporting ? "Exportando..." : "Exportar clips"}
            </button>
          </div>
        </div>

        <div className="clips-results-panel">
          <div className="section-heading">
            <h2>Plan de clips</h2>
            {plan && <span>{plan.segment_count} segmentos</span>}
          </div>

          {plan ? (
            <>
              <div className="clip-plan-summary">
                <span>Modo: {plan.export_mode}</span>
                <span>Salida: {plan.output_label}</span>
              </div>
              <div className="clip-segment-list">
                {plan.segments.map((segment) => (
                  <div key={`${segment.index}-${segment.start_seconds}`} className="clip-segment-row">
                    <strong>{segment.index.toString().padStart(3, "0")}</strong>
                    <span>{segment.label}</span>
                    <span>{formatTime(segment.start_seconds)} - {formatTime(segment.end_seconds)}</span>
                    <span>{segment.duration_seconds.toFixed(2)}s</span>
                    <span>F {segment.start_frame ?? "-"} / {segment.end_frame ?? "-"}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="empty-hint">Todavia no has calculado un plan de recorte.</p>
          )}
        </div>
      </section>

      <section className="clips-export-panel">
        <div className="section-heading">
          <h2>Ultima exportacion</h2>
        </div>
        {result ? (
          <div className="export-result-grid">
            <div className="export-result-block">
              <small>Carpeta</small>
              <code>{result.export_dir}</code>
            </div>
            <div className="export-result-block">
              <small>Manifest</small>
              <code>{result.manifest_path}</code>
            </div>
            <div className="export-result-block export-result-wide">
              <small>Ficheros</small>
              <div className="export-file-list">
                {result.output_files.map((file) => (
                  <code key={file}>{file}</code>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <p className="empty-hint">Aun no se ha ejecutado ninguna exportacion.</p>
        )}
      </section>
    </section>
  );
}
