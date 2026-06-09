import { TagEvent } from "../types";
import { formatTime } from "../lib/video";

type Props = {
  events: TagEvent[];
  onSeek: (seconds: number) => void;
  onUpdateEvent: (eventId: number, values: Partial<TagEvent>) => void;
  onDeleteEvent: (eventId: number) => void;
};

export function EventsList({ events, onSeek, onUpdateEvent, onDeleteEvent }: Props) {
  return (
    <section className="events-section">
      <h2>Acciones registradas</h2>
      <div className="events-table">
        <div className="events-head">
          <span>Tag</span>
          <span>Inicio</span>
          <span>Frame</span>
          <span>Final</span>
          <span>Duracion</span>
          <span>Nota</span>
          <span></span>
        </div>
        {events.map((item) => (
          <div className="event-row" key={item.id}>
            <button className="event-tag" type="button" style={{ borderColor: item.tag.color }} onClick={() => onSeek(item.start_seconds)}>
              {item.tag.name}
            </button>
            <input
              type="number"
              step="0.1"
              value={item.start_seconds}
              onChange={(event) => onUpdateEvent(item.id, { start_seconds: Number(event.target.value) })}
            />
            <input
              type="number"
              step="1"
              min="0"
              value={item.start_frame ?? ""}
              placeholder="-"
              onChange={(event) => onUpdateEvent(item.id, { start_frame: event.target.value === "" ? null : Number(event.target.value) })}
            />
            <input
              type="number"
              step="0.1"
              value={item.end_seconds ?? ""}
              placeholder="-"
              onChange={(event) => onUpdateEvent(item.id, { end_seconds: event.target.value === "" ? null : Number(event.target.value) })}
            />
            <span>{item.end_seconds === null ? "-" : formatTime(item.end_seconds - item.start_seconds)}</span>
            <input value={item.note ?? ""} placeholder="Nota" onChange={(event) => onUpdateEvent(item.id, { note: event.target.value })} />
            <button className="danger-button" type="button" onClick={() => onDeleteEvent(item.id)}>
              Borrar
            </button>
          </div>
        ))}
        {events.length === 0 && <p className="no-events">Todavia no hay acciones registradas.</p>}
      </div>
    </section>
  );
}
