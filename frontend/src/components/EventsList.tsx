import { useRef, useState } from "react";

import { TagEvent } from "../types";
import { formatTime } from "../lib/video";

type Props = {
  events: TagEvent[];
  currentTime: number;
  expanded: boolean;
  onToggle: () => void;
  onSeek: (seconds: number) => void;
  onUpdateEvent: (eventId: number, values: Partial<TagEvent>) => void;
  onDeleteEvent: (eventId: number) => void;
};

export function EventsList({ events, currentTime, expanded, onToggle, onSeek, onUpdateEvent, onDeleteEvent }: Props) {
  const [tagFilter, setTagFilter] = useState<number | null>(null);
  const [atBottom, setAtBottom] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null);
  const shown = tagFilter === null ? events : events.filter((item) => item.tag_definition_id === tagFilter);
  const options = Array.from(new Map(events.map((item) => [item.tag_definition_id, item.tag])).values());
  const previous = [...shown].reverse().find((item) => item.start_seconds < currentTime - 0.05);
  const next = shown.find((item) => item.start_seconds > currentTime + 0.05);

  function jumpList() {
    const list = listRef.current;
    if (!list) return;
    list.scrollTo({ top: atBottom ? 0 : list.scrollHeight, behavior: "smooth" });
  }

  return (
    <section className={`events-section ${expanded ? "" : "panel-collapsed"}`}>
      <div className="section-heading">
        <h2>Acciones <small>{events.length}</small></h2>
        <div className="panel-actions">
          {expanded && <button type="button" className="panel-toggle" onClick={jumpList} title={atBottom ? "Ir al primer registro" : "Ir al último registro"}>{atBottom ? "↑" : "↓"}</button>}
          <button type="button" className="panel-toggle" aria-expanded={expanded} onClick={onToggle}>{expanded ? "Minimizar" : "Expandir"}</button>
        </div>
      </div>
      {expanded && <>
        <div className="events-filter">
          <select aria-label="Filtrar acciones por tag" value={tagFilter ?? ""} onChange={(event) => { setTagFilter(event.target.value ? Number(event.target.value) : null); setAtBottom(false); if (listRef.current) listRef.current.scrollTop = 0; }}>
            <option value="">Todas las tags</option>
            {options.map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}
          </select>
          <button type="button" className="panel-toggle" disabled={!previous} onClick={() => previous && onSeek(previous.start_seconds)} title="Acción anterior">←</button>
          <button type="button" className="panel-toggle" disabled={!next} onClick={() => next && onSeek(next.start_seconds)} title="Acción siguiente">→</button>
        </div>
        <div className="events-table" ref={listRef} onScroll={(event) => { const el = event.currentTarget; setAtBottom(el.scrollTop + el.clientHeight >= el.scrollHeight - 12); }}>
          {shown.map((item) => (
            <div className="event-row" key={item.id}>
              <button className="event-tag" type="button" style={{ borderColor: item.tag.color }} onClick={() => onSeek(item.start_seconds)}>{item.tag.name}</button>
              <button className="event-time" type="button" onClick={() => onSeek(item.start_seconds)}>{formatTime(item.start_seconds)}</button>
              <span className="event-duration">{item.end_seconds === null ? "•" : formatTime(item.end_seconds - item.start_seconds)}</span>
              <details className="event-details">
                <summary aria-label={`Editar acción ${item.tag.name} en ${formatTime(item.start_seconds)}`}>Editar</summary>
                <div className="event-edit-grid">
                  <label>Inicio (s)<input type="number" step="0.1" value={item.start_seconds} onChange={(event) => onUpdateEvent(item.id, { start_seconds: Number(event.target.value) })} /></label>
                  <label>Frame<input type="number" step="1" min="0" value={item.start_frame ?? ""} placeholder="-" onChange={(event) => onUpdateEvent(item.id, { start_frame: event.target.value === "" ? null : Number(event.target.value) })} /></label>
                  <label>Final (s)<input type="number" step="0.1" value={item.end_seconds ?? ""} placeholder="-" onChange={(event) => onUpdateEvent(item.id, { end_seconds: event.target.value === "" ? null : Number(event.target.value) })} /></label>
                  <label>Nota<input value={item.note ?? ""} placeholder="Nota" onChange={(event) => onUpdateEvent(item.id, { note: event.target.value })} /></label>
                  <button className="danger-button" type="button" onClick={() => onDeleteEvent(item.id)}>Borrar acción</button>
                </div>
              </details>
            </div>
          ))}
          {shown.length === 0 && <p className="no-events">No hay acciones con este filtro.</p>}
        </div>
      </>}
    </section>
  );
}
