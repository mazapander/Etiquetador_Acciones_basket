type Props = {
  status: "downloading" | "processing" | "completed" | "failed";
  percent: number;
  stage: string;
  speed?: string | null;
  eta?: string | null;
  error?: string | null;
  onReset: () => void;
};

export function DownloadProgressDisplay({ status, percent, stage, speed, eta, error, onReset }: Props) {
  function getStatusIcon() {
    switch (status) {
      case "downloading":
        return "↓";
      case "processing":
        return "⟳";
      case "completed":
        return "✓";
      case "failed":
        return "✗";
    }
  }

  function getStatusColor() {
    switch (status) {
      case "downloading":
      case "processing":
        return "var(--primary)";
      case "completed":
        return "var(--success, #16a34a)";
      case "failed":
        return "var(--danger)";
    }
  }

  return (
    <div className={`download-progress ${status}`}>
      <div className="progress-header">
        <span className="progress-icon" style={{ color: getStatusColor() }}>
          {getStatusIcon()}
        </span>
        <span className="progress-stage">{stage}</span>
      </div>

      {(status === "downloading" || status === "processing") && (
        <>
          <div className="progress-bar-container">
            <div className="progress-bar-track">
              <div
                className="progress-bar-fill"
                style={{ width: `${percent}%` }}
              />
            </div>
            <span className="progress-percent">{percent.toFixed(1)}%</span>
          </div>
          <div className="progress-stats">
            {speed && <span>Velocidad: {speed}</span>}
            {eta && <span>ETA: {eta}</span>}
          </div>
        </>
      )}

      {status === "completed" && (
        <div className="progress-success">
          <p>Descarga completada!</p>
          <button type="button" className="secondary-button" onClick={onReset}>
            Nueva descarga
          </button>
        </div>
      )}

      {status === "failed" && (
        <div className="progress-error">
          <p className="error-message">{error || "Error desconocido"}</p>
          <button type="button" className="secondary-button" onClick={onReset}>
            Reintentar
          </button>
        </div>
      )}
    </div>
  );
}