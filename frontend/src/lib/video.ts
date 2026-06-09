import { TagDefinition, TagEvent, TagMode, TagSource, ThemeMode } from "../types";

export const TAG_COLOR_PALETTE = [
  "#2563eb",
  "#16a34a",
  "#dc2626",
  "#d97706",
  "#7c3aed",
  "#0891b2",
  "#db2777",
  "#65a30d",
  "#ea580c",
  "#0f766e",
];

export function formatTime(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) {
    return "--:--";
  }
  const total = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(total / 60);
  const secs = total % 60;
  return `${minutes}:${secs.toString().padStart(2, "0")}`;
}

export function toPercent(seconds: number, totalSeconds: number): number {
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) {
    return 0;
  }
  return Math.min(100, Math.max(0, (seconds / totalSeconds) * 100));
}

export function readStoredJumpSeconds(): number {
  const stored = window.localStorage.getItem("video-jump-seconds");
  const parsed = stored ? Number(stored) : 5;
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 5;
}

export function readStoredTheme(): ThemeMode {
  const stored = window.localStorage.getItem("ui-theme");
  return stored === "dark" ? "dark" : "light";
}

export function suggestAvailableColor(tags: TagDefinition[], ignoredIds: number[] = []): string {
  const ignored = new Set(ignoredIds);
  const usedColors = new Set(tags.filter((tag) => !ignored.has(tag.id)).map((tag) => tag.color.toLowerCase()));
  return TAG_COLOR_PALETTE.find((color) => !usedColors.has(color.toLowerCase())) ?? TAG_COLOR_PALETTE[0];
}

export function suggestSecondColor(tags: TagDefinition[], firstColor: string, ignoredIds: number[] = []): string {
  const pool = [
    ...tags,
    {
      id: -1,
      name: "__temp__",
      color: firstColor,
      mode: "instant" as TagMode,
      source: "human" as TagSource,
      group_key: null,
      shortcut_key: null,
      sort_order: -1,
      is_active: true,
      created_at: "",
      updated_at: "",
    },
  ];
  const suggested = suggestAvailableColor(pool, ignoredIds);
  return suggested.toLowerCase() === firstColor.toLowerCase()
    ? TAG_COLOR_PALETTE.find((color) => color.toLowerCase() !== firstColor.toLowerCase()) ?? firstColor
    : suggested;
}

export function formatQuality(width: number | null, height: number | null): string {
  if (!width || !height) {
    return "Sin metadata";
  }
  return `${width}x${height}`;
}

export function buildOpenRanges(events: TagEvent[]): Record<number, TagEvent> {
  return events
    .filter((event) => event.end_seconds === null && (event.tag.mode === "range" || event.tag.mode === "antagonistic"))
    .reduce<Record<number, TagEvent>>((acc, event) => {
      acc[event.tag_definition_id] = event;
      return acc;
    }, {});
}
