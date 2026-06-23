import { useEffect, useMemo, useState } from "react";

import { api } from "../lib/api";
import { formatTime } from "../lib/video";
import "./ModelRunsView.css";

type MlRun = {
  id: number;
  model_name: string;
  model_version: string | null;
  task: string;
  description: string | null;
  train_video_ids: number[];
  test_video_ids: number[];
  params: Record<string, unknown>;
  metrics: Record<string, unknown>;
  created_at: string;
};

type MlVideo = {
  id: number;
  display_name: string;
  original_filename: string;
  duration_seconds: number | null;
  fps: number | null;
};

type MlPrediction = {
  id: number;
  run_id: number;
  video_id: number;
  window_start: number;
  window_end: number;
  predicted_label: string;
  true_label: string | null;
  confidence: number | null;
  metadata: Record<string, unknown>;
  is_correct: boolean;
  error_type: string | null;
  created_at: string;
};

type MlRunVideosResponse = {
  run: MlRun;
  videos: MlVideo[];
};

type MlRunVideoResults = {
  run: MlRun;
  video: MlVideo;
  summary: {
    total_windows: number;
    correct: number;
    incorrect: number;
    accuracy: number | null;
    avg_confidence: number | null;
  };
  predictions: MlPrediction[];
  errors: MlPrediction[];
  confusion: Array<{ true_label: string; predicted_label: string; count: number }>;
};

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function formatMetric(value: unknown) {
  if (typeof value === "number") {
    return value <= 1 ? formatPercent(value) : value.toFixed(2);
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
}

function getRunLabel(run: MlRun) {
  const version = run.model_version ? ` ${run.model_version}` : "";
  return `${run.model_name}${version} · ${run.task}`;
}

function confidenceWidth(confidence: number | null) {
  if (confidence === null || Number.isNaN(confidence)) {
    return "35%";
  }
  return `${Math.max(8, Math.min(100, confidence * 100))}%`;
}

export function ModelRunsView() {
  const [runs, setRuns] = useState<MlRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [videos, setVideos] = useState<MlVideo[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<number | null>(null);
  const [results, setResults] = useState<MlRunVideoResults | null>(null);
  const [isLoadingRuns, setIsLoadingRuns] = useState(false);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showOnlyErrors, setShowOnlyErrors] = useState(false);

  const selectedRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) ?? null,
    [runs, selectedRunId],
  );

  const visiblePredictions = useMemo(() => {
    const items = results?.predictions ?? [];
    return showOnlyErrors ? items.filter((item) => item.error_type) : items;
  }, [results, showOnlyErrors]);

  useEffect(() => {
    setIsLoadingRuns(true);
    api<MlRun[]>("/api/ml/runs")
      .then((items) => {
        setRuns(items);
        if (items.length > 0) {
          setSelectedRunId(items[0].id);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "No se pudieron cargar las pruebas ML"))
      .finally(() => setIsLoadingRuns(false));
  }, []);

  useEffect(() => {
    if (!selectedRunId) {
      setVideos([]);
      setSelectedVideoId(null);
      setResults(null);
      return;
    }
    setResults(null);
    api<MlRunVideosResponse>(`/api/ml/runs/${selectedRunId}/videos`)
      .then((payload) => {
        setVideos(payload.videos);
        setSelectedVideoId(payload.videos[0]?.id ?? null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "No se pudieron cargar los partidos del run"));
  }, [selectedRunId]);

  useEffect(() => {
    if (!selectedRunId || !selectedVideoId) {
      setResults(null);
      return;
    }
    setIsLoadingResults(true);
    api<MlRunVideoResults>(`/api/ml/runs/${selectedRunId}/videos/${selectedVideoId}`)
      .then(setResults)
      .catch((err) => setError(err instanceof Error ? err.message : "No se pudieron cargar los resultados"))
      .finally(() => setIsLoadingResults(false));
  }, [selectedRunId, selectedVideoId]);

  function seekInLabeler(seconds: number) {
    if (!results) {
      return;
    }
    window.localStorage.setItem("ml-debug-seek", JSON.stringify({ videoId: results.video.id, seconds }));
    window.location.href = "/label";
  }

  return (
    <main className="model-runs-shell">
      <header className="model-runs-header">
        <div>
          <p className="eyebrow">Banco de pruebas</p>
          <h1>Pruebas ML</h1>
          <p>
            Visualiza runs entrenados fuera de la app, compara métricas y revisa errores por partido desde SQLite.
          </p>
        </div>
        <div className="model-runs-actions">
          <a className="secondary-button" href="/gallery">Volver a proyectos</a>
          <a className="secondary-button" href="/label">Ir al etiquetador</a>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="model-runs-panel">
        <div className="section-heading">
          <h2>Seleccion de prueba</h2>
          {isLoadingRuns && <span>Cargando...</span>}
        </div>

        <div className="model-runs-selectors">
          <label className="field-block">
            <span>Modelo / run</span>
            <select value={selectedRunId ?? ""} onChange={(event) => setSelectedRunId(Number(event.target.value) || null)}>
              <option value="" disabled>No hay runs</option>
              {runs.map((run) => (
                <option key={run.id} value={run.id}>{getRunLabel(run)}</option>
              ))}
            </select>
          </label>

          <label className="field-block">
            <span>Partido probado</span>
            <select value={selectedVideoId ?? ""} onChange={(event) => setSelectedVideoId(Number(event.target.value) || null)} disabled={videos.length === 0}>
              <option value="" disabled>No hay partidos para este run</option>
              {videos.map((video) => (
                <option key={video.id} value={video.id}>{video.display_name}</option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {selectedRun && (
        <section className="model-runs-panel run-detail-panel">
          <div>
            <h2>{getRunLabel(selectedRun)}</h2>
            <p>{selectedRun.description || "Sin descripcion del experimento."}</p>
          </div>
          <div className="run-meta-grid">
            <div><small>Train videos</small><strong>{selectedRun.train_video_ids.length}</strong></div>
            <div><small>Test videos</small><strong>{selectedRun.test_video_ids.length}</strong></div>
            <div><small>Creado</small><strong>{new Date(selectedRun.created_at).toLocaleString()}</strong></div>
          </div>
        </section>
      )}

      {results && (
        <>
          <section className="model-runs-kpis">
            <div><small>Accuracy</small><strong>{formatPercent(results.summary.accuracy)}</strong></div>
            <div><small>Correctas</small><strong>{results.summary.correct}</strong></div>
            <div><small>Incorrectas</small><strong>{results.summary.incorrect}</strong></div>
            <div><small>Ventanas</small><strong>{results.summary.total_windows}</strong></div>
            <div><small>Confianza media</small><strong>{formatPercent(results.summary.avg_confidence)}</strong></div>
          </section>

          <section className="model-runs-panel">
            <div className="section-heading">
              <h2>Métricas del run</h2>
              <span>{results.video.display_name}</span>
            </div>
            <div className="metrics-grid">
              {Object.entries(results.run.metrics).length > 0 ? (
                Object.entries(results.run.metrics).map(([key, value]) => (
                  <div key={key} className="metric-chip">
                    <small>{key}</small>
                    <strong>{formatMetric(value)}</strong>
                  </div>
                ))
              ) : (
                <p className="empty-hint">Este run no tiene métricas globales guardadas.</p>
              )}
            </div>
          </section>

          <section className="model-runs-panel">
            <div className="section-heading">
              <h2>Timeline de aciertos y errores</h2>
              <span>{results.errors.length} errores</span>
            </div>
            <div className="prediction-timeline" aria-label="Timeline de predicciones">
              {results.predictions.map((item) => (
                <button
                  key={item.id}
                  className={`timeline-window ${item.is_correct ? "correct" : "incorrect"}`}
                  style={{ opacity: item.confidence ? Math.max(0.35, item.confidence) : 0.65 }}
                  title={`${formatTime(item.window_start)} · real: ${item.true_label ?? "-"} · pred: ${item.predicted_label}`}
                  type="button"
                  onClick={() => seekInLabeler(item.window_start)}
                />
              ))}
            </div>
          </section>

          <section className="model-runs-panel">
            <div className="section-heading">
              <h2>Predicciones</h2>
              <label className="inline-checkbox">
                <input type="checkbox" checked={showOnlyErrors} onChange={(event) => setShowOnlyErrors(event.target.checked)} />
                Solo errores
              </label>
            </div>

            {isLoadingResults ? (
              <p className="empty-hint">Cargando resultados...</p>
            ) : visiblePredictions.length > 0 ? (
              <div className="prediction-table">
                <div className="prediction-row prediction-row-header">
                  <span>Tiempo</span>
                  <span>Real</span>
                  <span>Predicho</span>
                  <span>Confianza</span>
                  <span>Debug</span>
                </div>
                {visiblePredictions.slice(0, 300).map((item) => (
                  <div key={item.id} className={`prediction-row ${item.is_correct ? "correct" : "incorrect"}`}>
                    <span>{formatTime(item.window_start)} - {formatTime(item.window_end)}</span>
                    <span>{item.true_label ?? "-"}</span>
                    <span>{item.predicted_label}</span>
                    <span>
                      <span className="confidence-track"><span style={{ width: confidenceWidth(item.confidence) }} /></span>
                      {formatPercent(item.confidence)}
                    </span>
                    <span>
                      <button className="ghost-button" type="button" onClick={() => seekInLabeler(item.window_start)}>
                        Ver
                      </button>
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-hint">No hay predicciones guardadas para esta combinacion.</p>
            )}
          </section>
        </>
      )}

      {!results && !isLoadingResults && (
        <section className="model-runs-panel">
          <p className="empty-hint">
            No hay resultados todavía. Entrena un modelo fuera de la app, crea un run en `/api/ml/runs` y sube predicciones a `/api/ml/runs/{'{run_id}'}/predictions`.
          </p>
        </section>
      )}
    </main>
  );
}
