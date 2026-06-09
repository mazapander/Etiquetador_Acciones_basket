import { FormEvent } from "react";

import { TagDefinition, TagMode } from "../types";

type Props = {
  isOpen: boolean;
  newTagMode: TagMode;
  newTagName: string;
  newTagColor: string;
  newAntagonistFirst: string;
  newAntagonistSecond: string;
  newAntagonistSecondColor: string;
  newTagShortcut: string;
  tags: TagDefinition[];
  onClose: () => void;
  onSubmit: (event: FormEvent) => void;
  onModeChange: (value: TagMode) => void;
  onTagNameChange: (value: string) => void;
  onTagColorChange: (value: string) => void;
  onAntagonistFirstChange: (value: string) => void;
  onAntagonistSecondChange: (value: string) => void;
  onAntagonistSecondColorChange: (value: string) => void;
  onShortcutChange: (value: string) => void;
  onSuggestColors: () => void;
  onSuggestSecondColor: () => void;
};

export function CreateTagModal({
  isOpen,
  newTagMode,
  newTagName,
  newTagColor,
  newAntagonistFirst,
  newAntagonistSecond,
  newAntagonistSecondColor,
  newTagShortcut,
  onClose,
  onSubmit,
  onModeChange,
  onTagNameChange,
  onTagColorChange,
  onAntagonistFirstChange,
  onAntagonistSecondChange,
  onAntagonistSecondColorChange,
  onShortcutChange,
  onSuggestColors,
  onSuggestSecondColor,
}: Props) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="tag-modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h2>Nueva tag</h2>
          <button type="button" className="ghost-button" onClick={onClose}>
            Cerrar
          </button>
        </div>
        <form className="tag-form" onSubmit={onSubmit}>
          <select value={newTagMode} onChange={(event) => onModeChange(event.target.value as TagMode)}>
            <option value="range">Rango</option>
            <option value="instant">Instante</option>
            <option value="antagonistic">Antagonista</option>
          </select>
          {newTagMode === "antagonistic" ? (
            <>
              <input placeholder="Estado A" value={newAntagonistFirst} onChange={(event) => onAntagonistFirstChange(event.target.value)} />
              <input placeholder="Estado B" value={newAntagonistSecond} onChange={(event) => onAntagonistSecondChange(event.target.value)} />
              <div className="tag-form-row">
                <input aria-label="Color A" type="color" value={newTagColor} onChange={(event) => onTagColorChange(event.target.value)} />
                <input
                  aria-label="Color B"
                  type="color"
                  value={newAntagonistSecondColor}
                  onChange={(event) => onAntagonistSecondColorChange(event.target.value)}
                />
              </div>
            </>
          ) : (
            <>
              <input placeholder="Nombre tag" value={newTagName} onChange={(event) => onTagNameChange(event.target.value)} />
              <input aria-label="Color" type="color" value={newTagColor} onChange={(event) => onTagColorChange(event.target.value)} />
            </>
          )}
          <input placeholder="Atajo teclado" value={newTagShortcut} onChange={(event) => onShortcutChange(event.target.value)} />
          <div className="modal-actions">
            <button type="button" className="ghost-button" onClick={onSuggestColors}>
              Sugerir color
            </button>
            {newTagMode === "antagonistic" && (
              <button type="button" className="ghost-button" onClick={onSuggestSecondColor}>
                Sugerir color B
              </button>
            )}
            <button type="submit">Crear tag</button>
          </div>
        </form>
      </div>
    </div>
  );
}
