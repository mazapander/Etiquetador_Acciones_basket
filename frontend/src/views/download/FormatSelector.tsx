import { VideoQuality, DownloadFormat } from "../../types";

type Props = {
  quality: VideoQuality;
  downloadFormat: DownloadFormat;
  outputName: string;
  includeAudio: boolean;
  onQualityChange: (q: VideoQuality) => void;
  onFormatChange: (f: DownloadFormat) => void;
  onOutputNameChange: (n: string) => void;
  onIncludeAudioChange: (v: boolean) => void;
};

const QUALITY_OPTIONS: { value: VideoQuality; label: string; description: string }[] = [
  { value: "best", label: "Mejor calidad", description: "La maxima calidad disponible" },
  { value: "1080p", label: "1080p", description: "Full HD" },
  { value: "720p", label: "720p", description: "HD" },
  { value: "480p", label: "480p", description: "SD" },
  { value: "360p", label: "360p", description: "Baja" },
  { value: "audio_only", label: "Solo audio", description: "Extraer audio (MP3)" },
];

const FORMAT_OPTIONS: { value: DownloadFormat; label: string }[] = [
  { value: "mp4", label: "MP4" },
  { value: "mkv", label: "MKV" },
  { value: "webm", label: "WebM" },
  { value: "mp3", label: "MP3" },
  { value: "wav", label: "WAV" },
];

export function FormatSelector({
  quality,
  downloadFormat,
  outputName,
  includeAudio,
  onQualityChange,
  onFormatChange,
  onOutputNameChange,
  onIncludeAudioChange,
}: Props) {
  return (
    <div className="format-selector">
      <div className="format-section">
        <h4>Calidad</h4>
        <div className="quality-grid">
          {QUALITY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`quality-option ${quality === opt.value ? "selected" : ""}`}
              onClick={() => onQualityChange(opt.value)}
            >
              <span className="quality-label">{opt.label}</span>
              <span className="quality-desc">{opt.description}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="format-section">
        <h4>Formato</h4>
        <div className="format-buttons">
          {FORMAT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              className={`format-option ${downloadFormat === opt.value ? "selected" : ""}`}
              onClick={() => onFormatChange(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="format-section">
        <h4>Opciones</h4>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={includeAudio}
            onChange={(e) => onIncludeAudioChange(e.target.checked)}
          />
          <span>Incluir audio</span>
          <small>Combina video + audio para obtener un archivo con sonido</small>
        </label>
      </div>

      <div className="format-section">
        <h4>Nombre del archivo</h4>
        <input
          type="text"
          className="output-name-input"
          placeholder="Dejar vacio para nombre automatico"
          value={outputName}
          onChange={(e) => onOutputNameChange(e.target.value)}
        />
        <small className="output-name-hint">Sin extension. Ej: mi_video</small>
      </div>
    </div>
  );
}
