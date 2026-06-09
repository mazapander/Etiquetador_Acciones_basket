import { RefObject } from "react";

import { EventsList } from "../components/EventsList";
import { TagSidebar } from "../components/TagSidebar";
import { VideoPlayerPanel } from "../components/VideoPlayerPanel";
import { AntagonisticPair, PairDraft, RegularTagDraft, TagDefinition, TagEvent, Video } from "../types";

type TagCount = {
  id: number;
  name: string;
  color: string;
  count: number;
};

type Props = {
  video: Video;
  streamUrl: string;
  videoRef: RefObject<HTMLVideoElement | null>;
  currentTime: number;
  duration: number;
  jumpSeconds: number;
  tagCounts: TagCount[];
  events: TagEvent[];
  tags: TagDefinition[];
  regularTags: TagDefinition[];
  antagonisticPairs: AntagonisticPair[];
  activeRanges: Record<number, TagEvent>;
  editingTagId: number | null;
  editingPairKey: string | null;
  tagDraft: RegularTagDraft | null;
  pairDraft: PairDraft | null;
  onBack: () => void;
  onOpenCreateTag: () => void;
  onJumpChange: (value: number) => void;
  onTimeUpdate: (value: number) => void;
  onDurationChange: (value: number) => void;
  onSeek: (seconds: number) => void;
  onRegisterTag: (tag: TagDefinition) => void;
  onBeginTagEdit: (tag: TagDefinition) => void;
  onBeginPairEdit: (pair: AntagonisticPair) => void;
  onSaveTagEdit: (tag: TagDefinition) => void;
  onSavePairEdit: (pair: AntagonisticPair) => void;
  onDeactivateTag: (tag: TagDefinition) => void;
  onDeactivatePair: (pair: AntagonisticPair) => void;
  onTagDraftChange: (draft: RegularTagDraft | null) => void;
  onPairDraftChange: (draft: PairDraft | null) => void;
  onUpdateEvent: (eventId: number, values: Partial<TagEvent>) => void;
  onDeleteEvent: (eventId: number) => void;
};

export function WorkspaceView({
  video,
  streamUrl,
  videoRef,
  currentTime,
  duration,
  jumpSeconds,
  tagCounts,
  events,
  tags,
  regularTags,
  antagonisticPairs,
  activeRanges,
  editingTagId,
  editingPairKey,
  tagDraft,
  pairDraft,
  onBack,
  onOpenCreateTag,
  onJumpChange,
  onTimeUpdate,
  onDurationChange,
  onSeek,
  onRegisterTag,
  onBeginTagEdit,
  onBeginPairEdit,
  onSaveTagEdit,
  onSavePairEdit,
  onDeactivateTag,
  onDeactivatePair,
  onTagDraftChange,
  onPairDraftChange,
  onUpdateEvent,
  onDeleteEvent,
}: Props) {
  return (
    <section className="workspace-view">
      <div className="workspace-header">
        <button className="ghost-button" type="button" onClick={onBack}>
          Volver a proyectos
        </button>
      </div>
      <section className="workspace">
        <VideoPlayerPanel
          video={video}
          streamUrl={streamUrl}
          videoRef={videoRef}
          currentTime={currentTime}
          duration={duration}
          jumpSeconds={jumpSeconds}
          tagCounts={tagCounts}
          events={events}
          onJumpChange={onJumpChange}
          onTimeUpdate={onTimeUpdate}
          onDurationChange={onDurationChange}
          onSeek={onSeek}
        />
        <TagSidebar
          tags={tags}
          regularTags={regularTags}
          antagonisticPairs={antagonisticPairs}
          activeRanges={activeRanges}
          currentTime={currentTime}
          editingTagId={editingTagId}
          editingPairKey={editingPairKey}
          tagDraft={tagDraft}
          pairDraft={pairDraft}
          onRegisterTag={onRegisterTag}
          onBeginTagEdit={onBeginTagEdit}
          onBeginPairEdit={onBeginPairEdit}
          onSaveTagEdit={onSaveTagEdit}
          onSavePairEdit={onSavePairEdit}
          onDeactivateTag={onDeactivateTag}
          onDeactivatePair={onDeactivatePair}
          onTagDraftChange={onTagDraftChange}
          onPairDraftChange={onPairDraftChange}
          onOpenCreateTag={onOpenCreateTag}
        />
      </section>
      <EventsList events={events} onSeek={onSeek} onUpdateEvent={onUpdateEvent} onDeleteEvent={onDeleteEvent} />
    </section>
  );
}
