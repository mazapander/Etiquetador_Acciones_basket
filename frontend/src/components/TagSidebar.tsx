import { useState } from "react";
import { AntagonisticPair, PairDraft, RegularTagDraft, TagDefinition, TagEvent } from "../types";
import { suggestAvailableColor, suggestSecondColor } from "../lib/video";

type Props = {
  tags: TagDefinition[];
  regularTags: TagDefinition[];
  antagonisticPairs: AntagonisticPair[];
  activeRanges: Record<number, TagEvent>;
  currentTime: number;
  editingTagId: number | null;
  editingPairKey: string | null;
  tagDraft: RegularTagDraft | null;
  pairDraft: PairDraft | null;
  onRegisterTag: (tag: TagDefinition) => void;
  onBeginTagEdit: (tag: TagDefinition) => void;
  onBeginPairEdit: (pair: AntagonisticPair) => void;
  onSaveTagEdit: (tag: TagDefinition) => void;
  onSavePairEdit: (pair: AntagonisticPair) => void;
  onDeactivateTag: (tag: TagDefinition) => void;
  onDeactivatePair: (pair: AntagonisticPair) => void;
  onTagDraftChange: (draft: RegularTagDraft | null) => void;
  onPairDraftChange: (draft: PairDraft | null) => void;
  onOpenCreateTag: () => void;
  onReorderTags: (tagIds: number[]) => void;
};

export function TagSidebar({
  tags,
  regularTags,
  antagonisticPairs,
  activeRanges,
  currentTime,
  editingTagId,
  editingPairKey,
  tagDraft,
  pairDraft,
  onRegisterTag,
  onBeginTagEdit,
  onBeginPairEdit,
  onSaveTagEdit,
  onSavePairEdit,
  onDeactivateTag,
  onDeactivatePair,
  onTagDraftChange,
  onPairDraftChange,
  onOpenCreateTag,
  onReorderTags,
}: Props) {
  const [draggedId, setDraggedId] = useState<number | null>(null);
  const [dragOverId, setDragOverId] = useState<number | null>(null);

  function handleDragStart(tagId: number) {
    setDraggedId(tagId);
  }

  function handleDragOver(event: React.DragEvent, tagId: number) {
    event.preventDefault();
    if (draggedId !== null && draggedId !== tagId) {
      setDragOverId(tagId);
    }
  }

  function handleDragLeave() {
    setDragOverId(null);
  }

  function handleDrop(event: React.DragEvent, targetTagId: number) {
    event.preventDefault();
    if (draggedId === null || draggedId === targetTagId) {
      setDraggedId(null);
      setDragOverId(null);
      return;
    }
    const regularTagIds = regularTags.map((t) => t.id);
    const fromIndex = regularTagIds.indexOf(draggedId);
    const toIndex = regularTagIds.indexOf(targetTagId);
    if (fromIndex === -1 || toIndex === -1) {
      setDraggedId(null);
      setDragOverId(null);
      return;
    }
    const newOrder = [...regularTagIds];
    newOrder.splice(fromIndex, 1);
    newOrder.splice(toIndex, 0, draggedId);
    onReorderTags(newOrder);
    setDraggedId(null);
    setDragOverId(null);
  }

  function handleDragEnd() {
    setDraggedId(null);
    setDragOverId(null);
  }
  return (
    <aside className="tag-panel">
      <div className="section-heading">
        <h2>Tags</h2>
        <button className="secondary-button" type="button" onClick={onOpenCreateTag}>
          Nueva tag
        </button>
      </div>
      <div className="tag-list">
        {regularTags.map((tag) => {
          const openEvent = activeRanges[tag.id];
          const isBehindStart = openEvent ? currentTime < openEvent.start_seconds : false;
          const isEditing = editingTagId === tag.id && tagDraft !== null;
          const isDragging = draggedId === tag.id;
          const isDragOver = dragOverId === tag.id;
          return (
            <div
              className={`tag-control${isDragging ? " dragging" : ""}${isDragOver ? " drag-over" : ""}`}
              key={tag.id}
              draggable={!isEditing}
              onDragStart={() => handleDragStart(tag.id)}
              onDragOver={(e) => handleDragOver(e, tag.id)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, tag.id)}
              onDragEnd={handleDragEnd}
            >
              {isEditing ? (
                <div className="tag-editor">
                  <input value={tagDraft.name} onChange={(event) => onTagDraftChange({ ...tagDraft, name: event.target.value })} />
                  <div className="tag-editor-row">
                    <input type="color" value={tagDraft.color} onChange={(event) => onTagDraftChange({ ...tagDraft, color: event.target.value })} />
                    <input
                      placeholder="Atajo"
                      value={tagDraft.shortcut_key}
                      onChange={(event) => onTagDraftChange({ ...tagDraft, shortcut_key: event.target.value })}
                    />
                  </div>
                  <div className="tag-editor-actions">
                    <button type="button" className="ghost-button" onClick={() => onTagDraftChange({ ...tagDraft, color: suggestAvailableColor(tags, [tag.id]) })}>
                      Otro color
                    </button>
                    <button type="button" className="ghost-button" onClick={() => onTagDraftChange(null)}>
                      Cancelar
                    </button>
                    <button type="button" onClick={() => onSaveTagEdit(tag)}>
                      Guardar
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <button
                    type="button"
                    className={openEvent ? `tag-button active${isBehindStart ? " blocked" : ""}` : "tag-button"}
                    style={{ borderColor: tag.color, backgroundColor: tag.color, color: "#ffffff" }}
                    onClick={() => onRegisterTag(tag)}
                  >
                    {openEvent ? (isBehindStart ? `Resolver ${tag.name}` : `Finalizar ${tag.name}`) : tag.name}
                  </button>
                  <span className="tag-mode-label">{tag.mode === "range" ? "R" : "I"}</span>
                  <span className="tag-group-label">{tag.shortcut_key?.toUpperCase() ?? "-"}</span>
                  <div className="tag-actions">
                    <button className="edit-tag" type="button" title="Editar tag" onClick={() => onBeginTagEdit(tag)}>
                      E
                    </button>
                    <button className="delete-tag" type="button" title="Eliminar tag" onClick={() => onDeactivateTag(tag)}>
                      ×
                    </button>
                  </div>
                </>
              )}
            </div>
          );
        })}
        {antagonisticPairs.map((pair) => {
          const activeTagId = pair.activeEvent?.tag_definition_id;
          const activeTag = pair.tags.find((tag) => tag.id === activeTagId) ?? pair.tags[0];
          const nextTag = activeTag.id === pair.tags[0].id ? pair.tags[1] : pair.tags[0];
          const isBehindStart = pair.activeEvent ? currentTime < pair.activeEvent.start_seconds : false;
          const isEditing = editingPairKey === pair.groupKey && pairDraft !== null;
          return (
            <div className="tag-control pair-control" key={pair.groupKey}>
              {isEditing ? (
                <div className="tag-editor">
                  <input value={pairDraft.first_name} onChange={(event) => onPairDraftChange({ ...pairDraft, first_name: event.target.value })} />
                  <input value={pairDraft.second_name} onChange={(event) => onPairDraftChange({ ...pairDraft, second_name: event.target.value })} />
                  <div className="tag-editor-row">
                    <input type="color" value={pairDraft.first_color} onChange={(event) => onPairDraftChange({ ...pairDraft, first_color: event.target.value })} />
                    <input type="color" value={pairDraft.second_color} onChange={(event) => onPairDraftChange({ ...pairDraft, second_color: event.target.value })} />
                  </div>
                  <input
                    placeholder="Atajo"
                    value={pairDraft.shortcut_key}
                    onChange={(event) => onPairDraftChange({ ...pairDraft, shortcut_key: event.target.value })}
                  />
                  <div className="tag-editor-actions">
                    <button
                      type="button"
                      className="ghost-button"
                      onClick={() => {
                        const nextFirstColor = suggestAvailableColor(tags, pair.tags.map((tag) => tag.id));
                        onPairDraftChange({
                          ...pairDraft,
                          first_color: nextFirstColor,
                          second_color: suggestSecondColor(
                            tags.filter((tag) => !pair.tags.some((pairTag) => pairTag.id === tag.id)),
                            nextFirstColor,
                          ),
                        });
                      }}
                    >
                      Otro color
                    </button>
                    <button type="button" className="ghost-button" onClick={() => onPairDraftChange(null)}>
                      Cancelar
                    </button>
                    <button type="button" onClick={() => onSavePairEdit(pair)}>
                      Guardar
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <button
                    type="button"
                    className={pair.activeEvent ? `tag-button antagonistic-button active${isBehindStart ? " blocked" : ""}` : "tag-button antagonistic-button"}
                    style={{ borderColor: activeTag.color }}
                    onClick={() => onRegisterTag(nextTag)}
                  >
                    <span className="antagonistic-state active-state" style={{ backgroundColor: activeTag.color }}>
                      {activeTag.name}
                    </span>
                    <span className="antagonistic-state inactive-state" style={{ backgroundColor: nextTag.color }}>
                      {nextTag.name}
                    </span>
                  </button>
                  <span className="tag-mode-label">A2</span>
                  <span className="tag-group-label">{activeTag.shortcut_key?.toUpperCase() ?? "-"}</span>
                  <div className="tag-actions">
                    <button className="edit-tag" type="button" title="Editar pareja" onClick={() => onBeginPairEdit(pair)}>
                      E
                    </button>
                    <button className="delete-tag" type="button" title="Eliminar pareja" onClick={() => onDeactivatePair(pair)}>
                      ×
                    </button>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}
