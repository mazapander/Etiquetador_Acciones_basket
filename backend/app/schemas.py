from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models import TagMode, TagSource, VideoStatus


class TagDefinitionBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#2563eb", pattern=r"^#[0-9a-fA-F]{6}$")
    mode: TagMode = TagMode.range
    source: TagSource = TagSource.human
    group_key: str | None = Field(default=None, min_length=1, max_length=100)
    shortcut_key: str | None = Field(default=None, min_length=1, max_length=20)
    sort_order: int = 0


class TagDefinitionCreate(TagDefinitionBase):
    @model_validator(mode="after")
    def validate_antagonistic_group(self):
        if self.mode == TagMode.antagonistic:
            raise ValueError("Use antagonistic pair creation for antagonistic tags")
        return self


class TagDefinitionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    mode: TagMode | None = None
    source: TagSource | None = None
    group_key: str | None = Field(default=None, min_length=1, max_length=100)
    shortcut_key: str | None = Field(default=None, min_length=1, max_length=20)
    sort_order: int | None = None
    is_active: bool | None = None


class AntagonisticPairCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    second_name: str = Field(min_length=1, max_length=100)
    first_color: str = Field(default="#2563eb", pattern=r"^#[0-9a-fA-F]{6}$")
    second_color: str = Field(default="#16a34a", pattern=r"^#[0-9a-fA-F]{6}$")
    shortcut_key: str | None = Field(default=None, min_length=1, max_length=20)
    sort_order: int = 0

    @model_validator(mode="after")
    def validate_distinct_colors(self):
        if self.first_color.lower() == self.second_color.lower():
            raise ValueError("Antagonistic pair colors must be different")
        return self


class AntagonisticPairRead(BaseModel):
    group_key: str
    shortcut_key: str | None
    tags: list["TagDefinitionRead"]


class AntagonisticPairUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    second_name: str | None = Field(default=None, min_length=1, max_length=100)
    first_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    second_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    shortcut_key: str | None = Field(default=None, min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_distinct_colors(self):
        if self.first_color and self.second_color and self.first_color.lower() == self.second_color.lower():
            raise ValueError("Antagonistic pair colors must be different")
        return self


class TagDefinitionRead(TagDefinitionBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VideoRead(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    display_name: str
    duration_seconds: float | None
    fps: float | None
    width: int | None
    height: int | None
    status: VideoStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class VideoLibraryItemRead(VideoRead):
    file_exists: bool
    event_count: int = 0
    labeled_percent: float = 0


class VideoUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    status: VideoStatus | None = None


class ClipExportRequest(BaseModel):
    tag_definition_id: int
    export_mode: str = Field(pattern="^(segments|concatenate|exclude)$")
    pre_roll_seconds: float = Field(default=0, ge=0)
    post_roll_seconds: float = Field(default=0, ge=0)
    output_label: str | None = Field(default=None, min_length=1, max_length=120)
    keep_segments: bool = Field(default=True)


class ClipSegmentRead(BaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    label: str
    source_event_id: int | None
    start_frame: int | None
    end_frame: int | None


class ClipExportPlanRead(BaseModel):
    video_id: int
    tag_definition_id: int
    export_mode: str
    output_label: str
    segment_count: int
    segments: list[ClipSegmentRead]


class ClipExportResultRead(ClipExportPlanRead):
    export_dir: str
    manifest_path: str
    output_files: list[str]


class TagEventBase(BaseModel):
    tag_definition_id: int
    start_seconds: float = Field(ge=0)
    start_frame: int | None = Field(default=None, ge=0)
    end_seconds: float | None = Field(default=None, ge=0)
    source: TagSource = TagSource.human
    note: str | None = None

    @model_validator(mode="after")
    def validate_range(self):
        if self.end_seconds is not None and self.end_seconds < self.start_seconds:
            raise ValueError("end_seconds must be greater than or equal to start_seconds")
        return self


class TagEventCreate(TagEventBase):
    pass


class TagEventUpdate(BaseModel):
    tag_definition_id: int | None = None
    start_seconds: float | None = Field(default=None, ge=0)
    start_frame: int | None = Field(default=None, ge=0)
    end_seconds: float | None = Field(default=None, ge=0)
    source: TagSource | None = None
    note: str | None = None


class TagEventRead(BaseModel):
    id: int
    video_id: int
    tag_definition_id: int
    tag: TagDefinitionRead
    start_seconds: float
    start_frame: int | None
    end_seconds: float | None
    source: TagSource
    note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
