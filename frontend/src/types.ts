export type VideoStatus = "active" | "idle" | "completed";
export type TagMode = "instant" | "range" | "antagonistic";
export type TagSource = "human" | "system";
export type ThemeMode = "light" | "dark";

export type Video = {
  id: number;
  original_filename: string;
  stored_filename: string;
  display_name: string;
  duration_seconds: number | null;
  fps: number | null;
  width: number | null;
  height: number | null;
  status: VideoStatus;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};

export type VideoLibraryItem = Video & {
  file_exists: boolean;
  event_count: number;
  labeled_percent: number;
};

export type ClipExportMode = "segments" | "concatenate" | "exclude";

export type TagDefinition = {
  id: number;
  name: string;
  color: string;
  mode: TagMode;
  source: TagSource;
  group_key: string | null;
  shortcut_key: string | null;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TagEvent = {
  id: number;
  video_id: number;
  tag_definition_id: number;
  tag: TagDefinition;
  start_seconds: number;
  start_frame: number | null;
  end_seconds: number | null;
  source: TagSource;
  note: string | null;
  created_at: string;
  updated_at: string;
};

export type AntagonisticPair = {
  groupKey: string;
  tags: [TagDefinition, TagDefinition];
  activeEvent: TagEvent | null;
};

export type RegularTagDraft = {
  name: string;
  color: string;
  shortcut_key: string;
};

export type PairDraft = {
  first_name: string;
  second_name: string;
  first_color: string;
  second_color: string;
  shortcut_key: string;
};

export type ClipSegment = {
  index: number;
  start_seconds: number;
  end_seconds: number;
  duration_seconds: number;
  label: string;
  source_event_id: number | null;
  start_frame: number | null;
  end_frame: number | null;
};

export type ClipExportPlan = {
  video_id: number;
  tag_definition_id: number;
  export_mode: ClipExportMode;
  output_label: string;
  segment_count: number;
  segments: ClipSegment[];
};

export type ClipExportResult = ClipExportPlan & {
  export_dir: string;
  manifest_path: string;
  output_files: string[];
};
