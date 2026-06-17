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


def probe_video_metadata(path: Path, ffprobe_path: Path) -> dict[str, float | int | str | None]:
    command = [
        str(ffprobe_path),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate,r_frame_rate,width,height,codec_name,codec_long_name,bit_rate,max_bit_rate,profile",
        "-show_entries",
        "format=format_name,format_long_name,duration,size,bit_rate,max_bit_rate",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {"duration_seconds": None, "fps": None, "width": None, "height": None}

    payload = json.loads(result.stdout)
    format_info = payload.get("format", {})
    streams = payload.get("streams", [])
    stream = streams[0] if streams else {}

    duration = format_info.get("duration")
    fps = _parse_fraction(stream.get("avg_frame_rate")) or _parse_fraction(stream.get("r_frame_rate"))

    return {
        "duration_seconds": float(duration) if duration is not None else None,
        "format_name": format_info.get("format_name"),
        "format_long_name": format_info.get("format_long_name"),
        "fps": fps,
        "width": int(stream["width"]) if stream.get("width") is not None else None,
        "height": int(stream["height"]) if stream.get("height") is not None else None,
        "codec_name": stream.get("codec_name"),
        "codec_long_name": stream.get("codec_long_name"),
        "bit_rate": int(format_info.get("bit_rate")) if format_info.get("bit_rate") else None,
        "max_bit_rate": int(format_info.get("max_bit_rate")) if format_info.get("max_bit_rate") else None,
        "size_bytes": int(format_info.get("size")) if format_info.get("size") else None,
        "profile": stream.get("profile"),
    }


def get_video_tech_info(path: Path, ffprobe_path: Path) -> dict:
    command = [
        str(ffprobe_path),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,codec_long_name,width,height,avg_frame_rate,r_frame_rate,bit_rate,max_bit_rate,profile,level,pix_fmt,color_space,color_range",
        "-show_entries",
        "format=format_name,format_long_name,duration,size,bit_rate,max_bit_rate,probe_score",
        "-of",
        "json",
        str(path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {}

    payload = json.loads(result.stdout)
    format_info = payload.get("format", {})
    streams = payload.get("streams", [])
    stream = streams[0] if streams else {}

    duration = format_info.get("duration")
    size_bytes = int(format_info.get("size")) if format_info.get("size") else None
    fps = _parse_fraction(stream.get("avg_frame_rate")) or _parse_fraction(stream.get("r_frame_rate"))

    return {
        "codec": stream.get("codec_long_name") or stream.get("codec_name"),
        "codec_name": stream.get("codec_name"),
        "profile": stream.get("profile"),
        "level": stream.get("level"),
        "resolution": f"{stream.get('width')}x{stream.get('height')}" if stream.get("width") and stream.get("height") else None,
        "width": int(stream["width"]) if stream.get("width") else None,
        "height": int(stream["height"]) if stream.get("height") else None,
        "fps": fps,
        "pix_fmt": stream.get("pix_fmt"),
        "color_space": stream.get("color_space"),
        "color_range": stream.get("color_range"),
        "bitrate": _format_bitrate(int(format_info["bit_rate"])) if format_info.get("bit_rate") else None,
        "bitrate_raw": int(format_info["bit_rate"]) if format_info.get("bit_rate") else None,
        "max_bitrate": _format_bitrate(int(format_info["max_bit_rate"])) if format_info.get("max_bit_rate") else None,
        "duration": float(duration) if duration else None,
        "size_bytes": size_bytes,
        "size_formatted": _format_size(size_bytes) if size_bytes else None,
        "wrapper": format_info.get("format_long_name") or format_info.get("format_name"),
        "probe_score": format_info.get("probe_score"),
    }


def _format_bitrate(bitrate: int) -> str:
    if bitrate >= 1000000:
        return f"{bitrate / 1000000:.2f} Mbps"
    return f"{bitrate / 1000:.0f} kbps"


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1073741824:
        return f"{size_bytes / 1073741824:.2f} GB"
    if size_bytes >= 1048576:
        return f"{size_bytes / 1048576:.2f} MB"
    return f"{size_bytes / 1024:.0f} KB"
