import { useEffect, useMemo, useState } from "react";

import { TagDefinition } from "../types";

type TagGroup = { key: string; tags: TagDefinition[] };

type Props = {
  tags: TagDefinition[];
  loading: boolean;
  pendingKey: string | null;
  error: string | null;
  onClose: () => void;
  onCreate: () => void;
  onToggle: (group: TagGroup, active: boolean) => void;
};

export function ManageTagsModal({ tags, loading, pendingKey, error, onClose, onCreate, onToggle }: Props) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "active" | "inactive">("all");

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && pendingKey === null) onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, pendingKey]);

  const groups = useMemo(() => {
    const result: TagGroup[] = [];
    const pairs = new Map<string, TagGroup>();
    for (const tag of tags) {
      if (tag.mode === "antagonistic" && tag.group_key) {
        let group = pairs.get(tag.group_key);
        if (!group) {
          group = { key: `pair:${tag.group_key}`, tags: [] };
          pairs.set(tag.group_key, group);
          result.push(group);
        }
        group.tags.push(tag);
      } else {
        result.push({ key: `tag:${tag.id}`, tags: [tag] });
      }
    }
    return result;
  }, [tags]);
  const activeCount = groups.filter((group) => group.tags.every((tag) => tag.is_active)).length;
  const visibleGroups = groups.filter((group) => {
    const active = group.tags.every((tag) => tag.is_active);
    if (filter === "active" && !active) return false;
    if (filter === "inactive" && active) return false;
    return group.tags.some((tag) => tag.name.toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()));
  });

  return (
    <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && pendingKey === null) onClose(); }}>
      <section className="tag-modal manage-tags-modal" role="dialog" aria-modal="true" aria-label="Gestionar etiquetas">
        <div className="modal-header">
          <div>
            <h2>Gestionar etiquetas</h2>
            <p>{activeCount} activas de {groups.length} disponibles</p>
          </div>
          <button type="button" className="ghost-button" onClick={onClose} disabled={pendingKey !== null}>Cerrar</button>
        </div>
        <div className="manage-tags-filters">
          <input autoFocus type="search" aria-label="Buscar etiqueta" placeholder="Buscar etiqueta..." value={search} onChange={(event) => setSearch(event.target.value)} />
          <select aria-label="Mostrar etiquetas" value={filter} onChange={(event) => setFilter(event.target.value as typeof filter)}>
            <option value="all">Todas</option>
            <option value="active">Activas</option>
            <option value="inactive">Desactivadas</option>
          </select>
        </div>
        {error && <p className="manage-tags-error" role="alert">{error}</p>}
        <div className="manage-tags-list">
          {loading ? <p className="manage-tags-empty">Cargando etiquetas...</p> : visibleGroups.length === 0 ? <p className="manage-tags-empty">No hay etiquetas con este filtro.</p> : visibleGroups.map((group) => {
            const active = group.tags.every((tag) => tag.is_active);
            const pair = group.tags[0].mode === "antagonistic";
            return (
              <div className="manage-tag-row" key={group.key}>
                <span className="manage-tag-color" style={{ background: group.tags[0].color }} />
                <div className="manage-tag-description">
                  <strong>{group.tags.map((tag) => tag.name).join(" / ")}</strong>
                  <small>{pair ? "Pareja antagonista" : group.tags[0].mode === "instant" ? "Instante" : "Rango"}{group.tags[0].shortcut_key ? ` · tecla ${group.tags[0].shortcut_key.toUpperCase()}` : ""}</small>
                </div>
                <button
                  type="button"
                  className={`manage-tag-toggle${active ? " active" : ""}`}
                  role="switch"
                  aria-checked={active}
                  aria-label={`${active ? "Desactivar" : "Activar"} ${group.tags.map((tag) => tag.name).join(" y ")}`}
                  disabled={pendingKey !== null}
                  onClick={() => onToggle(group, !active)}
                >
                  {pendingKey === group.key ? "Guardando..." : active ? "Activa" : "Inactiva"}
                </button>
              </div>
            );
          })}
        </div>
        <div className="manage-tags-footer">
          <span>Las marcas se conservan. Al reactivar, un color ocupado se sustituye automáticamente.</span>
          <button type="button" className="secondary-button" onClick={onCreate} disabled={pendingKey !== null}>+ Nueva etiqueta</button>
        </div>
      </section>
    </div>
  );
}
