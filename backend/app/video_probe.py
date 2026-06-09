import json
import subprocess
from pathlib import Path


def _parse_fraction(value: str | None) -> float | None:
    if not value:
        return None
    if "/" in value:
        numerator_text, denominator_text = value.split("/", maxsplit=1)
        numerator = float(numerator_text)
        denominator = float(denominator_text)
        if denominator == 0:
            return None
        return numerator / denominator
    return float(value)


def probe_video_metadata(path: Path, ffprobe_path: Path) -> dict[str, float | int | None]:
    command = [
        str(ffprobe_path),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate,r_frame_rate,width,height",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {"duration_seconds": None, "fps": None, "width": None, "height": None}

    payload = json.loads(result.stdout)
    duration = payload.get("format", {}).get("duration")
    streams = payload.get("streams", [])
    stream = streams[0] if streams else {}
    fps = _parse_fraction(stream.get("avg_frame_rate")) or _parse_fraction(stream.get("r_frame_rate"))
    return {
        "duration_seconds": float(duration) if duration is not None else None,
        "fps": fps,
        "width": int(stream["width"]) if stream.get("width") is not None else None,
        "height": int(stream["height"]) if stream.get("height") is not None else None,
    }
