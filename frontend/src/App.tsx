import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { CreateTagModal } from "./components/CreateTagModal";
import { api, API_BASE } from "./lib/api";
import { buildOpenRanges, readStoredJumpSeconds, readStoredTheme, suggestAvailableColor, suggestSecondColor } from "./lib/video";
import { AntagonisticPair, ClipExportMode, ClipExportPlan, ClipExportResult, PairDraft, RegularTagDraft, TagDefinition, TagEvent, TagMode, ThemeMode, Video, VideoLibraryItem } from "./types";
import { ClipsView } from "./views/ClipsView";
import { ProjectsView } from "./views/ProjectsView";
import { WorkspaceView } from "./views/WorkspaceView";

type RoutePath = "/gallery" | "/label" | "/clips";

function normalizeRoute(pathname: string): RoutePath {
  if (pathname === "/label") {
    return "/label";
  }
  if (pathname === "/clips") {
    return "/clips";
  }
  if (pathname === "/galery" || pathname === "/gallery" || pathname === "/") {
    return "/gallery";
  }
  return "/gallery";
}

function navigateTo(path: RoutePath, replace = false) {
  const method = replace ? "replaceState" : "pushState";
  window.history[method](null, "", path);
}

export default function App() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [route, setRoute] = useState<RoutePath>(() => normalizeRoute(window.location.pathname));
  const [video, setVideo] = useState<Video | null>(null);
  const [videoLibrary, setVideoLibrary] = useState<VideoLibraryItem[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<number | null>(null);
  const [tags, setTags] = useState<TagDefinition[]>([]);
  const [events, setEvents] = useState<TagEvent[]>([]);
  const [activeRanges, setActiveRanges] = useState<Record<number, TagEvent>>({});
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [jumpSeconds, setJumpSeconds] = useState(() => readStoredJumpSeconds());
  const [theme, setTheme] = useState<ThemeMode>(() => readStoredTheme());
  const [displayName, setDisplayName] = useState("");
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [newTagName, setNewTagName] = useState("");
  const [newTagColor, setNewTagColor] = useState("#2563eb");
  const [newAntagonistSecondColor, setNewAntagonistSecondColor] = useState("#16a34a");
  const [newTagMode, setNewTagMode] = useState<TagMode>("range");
  const [newTagShortcut, setNewTagShortcut] = useState("");
  const [newAntagonistFirst, setNewAntagonistFirst] = useState("");
  const [newAntagonistSecond, setNewAntagonistSecond] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTagId, setEditingTagId] = useState<number | null>(null);
  const [editingPairKey, setEditingPairKey] = useState<string | null>(null);
  const [tagDraft, setTagDraft] = useState<RegularTagDraft | null>(null);
  const [pairDraft, setPairDraft] = useState<PairDraft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [clipTagId, setClipTagId] = useState<number | null>(null);
  const [clipMode, setClipMode] = useState<ClipExportMode>("segments");
  const [clipPreRoll, setClipPreRoll] = useState(0);
  const [clipPostRoll, setClipPostRoll] = useState(0);
  const [clipOutputLabel, setClipOutputLabel] = useState("");
const [clipPlan, setClipPlan] = useState<ClipExportPlan | null>(null);
  const [clipResult, setClipResult] = useState<ClipExportResult | null>(null);
  const [isPlanningClips, setIsPlanningClips] = useState(false);
  const [isExportingClips, setIsExportingClips] = useState(false);
  const [clipKeepSegments, setClipKeepSegments] = useState(true);
  const [exportProgress, setExportProgress] = useState<{ current: number; total: number; stage: string } | null>(null);

  const streamUrl = useMemo(() => (video ? `${API_BASE}/api/videos/${video.id}/stream` : ""), [video]);
  const regularTags = tags.filter((tag) => tag.mode !== "antagonistic");
  const antagonisticPairs = Array.from(
    tags
      .filter((tag) => tag.mode === "antagonistic" && tag.group_key)
      .reduce<Map<string, TagDefinition[]>>((acc, tag) => {
        const key = tag.group_key as string;
        acc.set(key, [...(acc.get(key) ?? []), tag]);
        return acc;
      }, new Map())
      .entries(),
  )
    .map(([groupKey, groupTags]) => {
      const ordered = [...groupTags].sort((left, right) => left.name.localeCompare(right.name));
      if (ordered.length < 2) {
        return null;
      }
      const activeEvent = ordered.map((tag) => activeRanges[tag.id]).find((event): event is TagEvent => Boolean(event)) ?? null;
      return {
        groupKey,
        tags: [ordered[0], ordered[1]] as [TagDefinition, TagDefinition],
        activeEvent,
      } satisfies AntagonisticPair;
    })
    .filter((pair): pair is AntagonisticPair => Boolean(pair));
  const tagCounts = tags
    .map((tag) => ({
      id: tag.id,
      name: tag.name,
      color: tag.color,
      count: events.filter((event) => event.tag_definition_id === tag.id).length,
    }))
    .filter((tag) => tag.count > 0);

  async function openVideo(nextVideo: Video | null) {
    setVideo(nextVideo);
    setSelectedVideoId(nextVideo?.id ?? null);
    setDisplayName(nextVideo?.display_name ?? "");
    setIsEditingTitle(false);
    setDuration(0);
    setCurrentTime(0);
    if (!nextVideo) {
      setEvents([]);
      setActiveRanges({});
      return;
    }
    const currentEvents = await api<TagEvent[]>(`/api/videos/${nextVideo.id}/events`);
    setEvents(currentEvents);
    setActiveRanges(buildOpenRanges(currentEvents));
    setClipPlan(null);
    setClipResult(null);
  }

  async function refresh(preferredVideoId?: number | null, preferredRoute?: RoutePath) {
    const [currentVideo, currentTags, library] = await Promise.all([
      api<Video | null>("/api/current-video"),
      api<TagDefinition[]>("/api/tags"),
      api<VideoLibraryItem[]>("/api/videos"),
    ]);
    setTags(currentTags);
    setVideoLibrary(library);
    const effectiveRoute = preferredRoute ?? route;
    const nextVideo =
      (preferredVideoId ? library.find((item) => item.id === preferredVideoId) : null)
      ?? (selectedVideoId ? library.find((item) => item.id === selectedVideoId) : null)
      ?? (currentVideo ? library.find((item) => item.id === currentVideo.id) ?? currentVideo : null)
      ?? null;

    if (effectiveRoute === "/label" || effectiveRoute === "/clips") {
      if (nextVideo) {
        await openVideo(nextVideo);
      } else {
        navigateTo("/gallery", true);
        setRoute("/gallery");
        await openVideo(null);
      }
      return;
    }

    if (video && nextVideo?.id === video.id) {
      setVideo(nextVideo);
      setDisplayName(nextVideo.display_name);
    }
  }

  useEffect(() => {
    const normalized = normalizeRoute(window.location.pathname);
    if (window.location.pathname !== normalized) {
      navigateTo(normalized, true);
    }
    setRoute(normalized);
    refresh(undefined, normalized).catch((err) => setError(err.message));

    const onPopState = () => {
      const nextRoute = normalizeRoute(window.location.pathname);
      setRoute(nextRoute);
      refresh(undefined, nextRoute).catch((err) => setError(err.message));
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA" || target?.tagName === "SELECT") {
        return;
      }
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
        return;
      }
      const element = videoRef.current;
      if (!element || route !== "/label") {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      const delta = event.key === "ArrowRight" ? jumpSeconds : -jumpSeconds;
      element.currentTime = Math.max(0, Math.min(element.duration || Number.MAX_SAFE_INTEGER, element.currentTime + delta));
    };
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [jumpSeconds, route]);

  useEffect(() => {
    window.localStorage.setItem("video-jump-seconds", String(jumpSeconds));
  }, [jumpSeconds]);

  useEffect(() => {
    window.localStorage.setItem("ui-theme", theme);
    document.body.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    if (newTagMode !== "antagonistic" && tags.some((tag) => tag.color.toLowerCase() === newTagColor.toLowerCase())) {
      setNewTagColor(suggestAvailableColor(tags));
    }
  }, [newTagMode, newTagColor, tags]);

  useEffect(() => {
    if (newTagMode !== "antagonistic") {
      return;
    }
    if (newAntagonistSecondColor.toLowerCase() === newTagColor.toLowerCase()) {
      setNewAntagonistSecondColor(suggestSecondColor(tags, newTagColor));
    }
  }, [newAntagonistSecondColor, newTagColor, newTagMode, tags]);

  useEffect(() => {
    if (!clipTagId && tags.length > 0) {
      setClipTagId(tags[0].id);
      setClipOutputLabel(tags[0].name);
      return;
    }
    if (clipTagId && !tags.some((tag) => tag.id === clipTagId)) {
      const fallbackTag = tags[0] ?? null;
      setClipTagId(fallbackTag?.id ?? null);
      setClipOutputLabel(fallbackTag?.name ?? "");
    }
  }, [clipTagId, tags]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (route !== "/label") {
        return;
      }
      const target = event.target as HTMLElement | null;
      if (target?.tagName === "INPUT" || target?.tagName === "TEXTAREA" || target?.tagName === "SELECT") {
        return;
      }
      const pressedKey = event.key.toLowerCase();
      const regularTag = regularTags.find((tag) => tag.shortcut_key?.toLowerCase() === pressedKey);
      if (regularTag) {
        event.preventDefault();
        void registerTag(regularTag);
        return;
      }
      const antagonisticPair = antagonisticPairs.find((pair) => pair.tags[0].shortcut_key?.toLowerCase() === pressedKey);
      if (!antagonisticPair) {
        return;
      }
      event.preventDefault();
      const activeTagId = antagonisticPair.activeEvent?.tag_definition_id;
      const nextTag = activeTagId === antagonisticPair.tags[0].id ? antagonisticPair.tags[1] : antagonisticPair.tags[0];
      void registerTag(nextTag);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [antagonisticPairs, regularTags, route, activeRanges, video, currentTime]);

  async function uploadSelectedFile(file: File) {
    setIsUploading(true);
    setError(null);
    const body = new FormData();
    body.append("file", file);
    body.append("display_name", file.name.replace(/\.[^/.]+$/, ""));
    try {
      await api<Video>("/api/videos", {
        method: "POST",
        body,
      });
      await refresh(undefined, "/gallery");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar el video");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleInitialFileChange(file: File | undefined) {
    if (!file) {
      return;
    }
    await uploadSelectedFile(file);
  }

  async function saveDisplayName() {
    if (!video) {
      return;
    }
    const updated = await api<Video>(`/api/videos/${video.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ display_name: displayName }),
    });
    setVideo(updated);
    setVideoLibrary((current) => current.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)));
  }

  async function createTag(event: FormEvent) {
    event.preventDefault();
    if (newTagMode === "antagonistic") {
      if (!newAntagonistFirst.trim() || !newAntagonistSecond.trim()) {
        setError("Las parejas antagonistas necesitan dos nombres.");
        return;
      }
      await api("/api/antagonistic-pairs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: newAntagonistFirst.trim(),
          second_name: newAntagonistSecond.trim(),
          first_color: newTagColor,
          second_color: newAntagonistSecondColor,
          shortcut_key: newTagShortcut.trim() || null,
          sort_order: tags.length,
        }),
      });
      setNewAntagonistFirst("");
      setNewAntagonistSecond("");
      setNewTagShortcut("");
      const nextFirstColor = suggestAvailableColor(tags);
      setNewTagColor(nextFirstColor);
      setNewAntagonistSecondColor(suggestSecondColor(tags, nextFirstColor));
      setIsCreateModalOpen(false);
      setError(null);
      await refresh(selectedVideoId, route);
      return;
    }
    if (!newTagName.trim()) {
      return;
    }
    await api<TagDefinition>("/api/tags", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: newTagName.trim(),
        color: newTagColor,
        mode: newTagMode,
        shortcut_key: newTagShortcut.trim() || null,
        sort_order: tags.length,
      }),
    });
    setNewTagName("");
    setNewTagShortcut("");
    setNewTagColor(suggestAvailableColor(tags));
    setIsCreateModalOpen(false);
    setError(null);
    await refresh(selectedVideoId, route);
  }

  function beginTagEdit(tag: TagDefinition) {
    setEditingPairKey(null);
    setEditingTagId(tag.id);
    setTagDraft({ name: tag.name, color: tag.color, shortcut_key: tag.shortcut_key ?? "" });
  }

  function beginPairEdit(pair: AntagonisticPair) {
    setEditingTagId(null);
    setEditingPairKey(pair.groupKey);
    setPairDraft({
      first_name: pair.tags[0].name,
      second_name: pair.tags[1].name,
      first_color: pair.tags[0].color,
      second_color: pair.tags[1].color,
      shortcut_key: pair.tags[0].shortcut_key ?? "",
    });
  }

  async function saveTagEdit(tag: TagDefinition) {
    if (!tagDraft) {
      return;
    }
    try {
      await api<TagDefinition>(`/api/tags/${tag.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: tagDraft.name.trim(),
          color: tagDraft.color,
          shortcut_key: tagDraft.shortcut_key.trim() || null,
        }),
      });
      setEditingTagId(null);
      setTagDraft(null);
      setError(null);
      await refresh(selectedVideoId, route);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo actualizar la tag");
    }
  }

  async function savePairEdit(pair: AntagonisticPair) {
    if (!pairDraft) {
      return;
    }
    try {
      await api(`/api/antagonistic-pairs/${pair.groupKey}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          first_name: pairDraft.first_name.trim(),
          second_name: pairDraft.second_name.trim(),
          first_color: pairDraft.first_color,
          second_color: pairDraft.second_color,
          shortcut_key: pairDraft.shortcut_key.trim() || null,
        }),
      });
      setEditingPairKey(null);
      setPairDraft(null);
      setError(null);
      await refresh(selectedVideoId, route);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo actualizar la pareja");
    }
  }

  async function deactivateTag(tag: TagDefinition) {
    if (!window.confirm(`¿Eliminar la tag "${tag.name}" de los botones activos?`)) {
      return;
    }
    await api<TagDefinition>(`/api/tags/${tag.id}`, { method: "DELETE" });
    await refresh(selectedVideoId, route);
  }

  async function deactivateAntagonisticPair(pair: AntagonisticPair) {
    if (!window.confirm(`¿Eliminar la pareja antagonista "${pair.tags[0].name} / ${pair.tags[1].name}"?`)) {
      return;
    }
    await Promise.all(pair.tags.map((tag) => api<TagDefinition>(`/api/tags/${tag.id}`, { method: "DELETE" })));
    await refresh(selectedVideoId, route);
  }

  async function registerTag(tag: TagDefinition) {
    if (!video || !videoRef.current) {
      return;
    }
    const seconds = Number(videoRef.current.currentTime.toFixed(3));
    const startFrame = video.fps ? Math.round(seconds * video.fps) : null;
    if (tag.mode === "instant") {
      const created = await api<TagEvent>(`/api/videos/${video.id}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tag_definition_id: tag.id, start_seconds: seconds, start_frame: startFrame }),
      });
      setEvents((current) => [...current, created].sort((a, b) => a.start_seconds - b.start_seconds));
      await refresh(video.id, route);
      return;
    }

    const openEvent = activeRanges[tag.id];
    const activeAntagonisticEvent = tag.mode === "antagonistic"
      ? Object.values(activeRanges).find((event) => event.tag.mode === "antagonistic" && event.tag.group_key === tag.group_key)
      : null;

    if (tag.mode === "antagonistic" && activeAntagonisticEvent?.tag_definition_id === tag.id) {
      return;
    }

    if (!openEvent) {
      if (tag.mode === "antagonistic" && activeAntagonisticEvent && seconds < activeAntagonisticEvent.start_seconds) {
        const confirmed = window.confirm(
          `La reproduccion esta antes del inicio del estado "${activeAntagonisticEvent.tag.name}". Si aceptas, se reemplazara por "${tag.name}" desde este punto.`,
        );
        if (!confirmed) {
          return;
        }
        await deleteEvent(activeAntagonisticEvent.id);
      }
      const created = await api<TagEvent>(`/api/videos/${video.id}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tag_definition_id: tag.id, start_seconds: seconds, start_frame: startFrame }),
      });
      if (tag.mode === "antagonistic") {
        await refresh(selectedVideoId, route);
        return;
      }
      setActiveRanges((current) => ({ ...current, [tag.id]: created }));
      setEvents((current) => [...current, created].sort((a, b) => a.start_seconds - b.start_seconds));
      await refresh(video.id, route);
      return;
    }

    if (seconds < openEvent.start_seconds) {
      const confirmed = window.confirm(`La reproduccion esta antes del inicio de "${tag.name}". Si aceptas, se cancelara este rango abierto.`);
      if (!confirmed) {
        return;
      }
      await deleteEvent(openEvent.id);
      setActiveRanges((current) => {
        const next = { ...current };
        delete next[tag.id];
        return next;
      });
      await refresh(selectedVideoId, route);
      return;
    }

    const updated = await api<TagEvent>(`/api/events/${openEvent.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ end_seconds: Math.max(seconds, openEvent.start_seconds) }),
    });
    setActiveRanges((current) => {
      const next = { ...current };
      delete next[tag.id];
      return next;
    });
    if (tag.mode === "antagonistic") {
      await refresh(selectedVideoId, route);
      return;
    }
    setEvents((current) => current.map((item) => (item.id === updated.id ? updated : item)).sort((a, b) => a.start_seconds - b.start_seconds));
    await refresh(video.id, route);
  }

  async function updateEvent(eventId: number, values: Partial<TagEvent>) {
    const updated = await api<TagEvent>(`/api/events/${eventId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
    });
    setEvents((current) => current.map((item) => (item.id === updated.id ? updated : item)).sort((a, b) => a.start_seconds - b.start_seconds));
    await refresh(selectedVideoId, route);
  }

  async function deleteEvent(eventId: number) {
    await api<void>(`/api/events/${eventId}`, { method: "DELETE" });
    setEvents((current) => current.filter((item) => item.id !== eventId));
    await refresh(selectedVideoId, route);
  }

  function seekTo(seconds: number) {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
    }
  }

  async function handleSelectVideo(item: VideoLibraryItem) {
    const updated = await api<Video>(`/api/videos/${item.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "active" }),
    });
    await openVideo(updated);
    navigateTo("/label");
    setRoute("/label");
    await refresh(updated.id, "/label");
  }

  async function handleOpenClips(item: VideoLibraryItem) {
    await openVideo(item);
    navigateTo("/clips");
    setRoute("/clips");
    await refresh(item.id, "/clips");
  }

  function handleBackToGallery() {
    navigateTo("/gallery");
    setRoute("/gallery");
  }

  async function previewClips() {
    if (!video || !clipTagId) {
      return;
    }
    setIsPlanningClips(true);
    try {
      const plan = await api<ClipExportPlan>(`/api/videos/${video.id}/clip-plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tag_definition_id: clipTagId,
          export_mode: clipMode,
          pre_roll_seconds: clipPreRoll,
          post_roll_seconds: clipPostRoll,
          output_label: clipOutputLabel.trim() || null,
        }),
      });
      setClipPlan(plan);
      setClipResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo calcular el plan");
    } finally {
      setIsPlanningClips(false);
    }
  }

  async function exportClips() {
    if (!video || !clipTagId) {
      return;
    }
    setIsExportingClips(true);
    setExportProgress({ current: 0, total: clipPlan?.segment_count ?? 0, stage: "Iniciando..." });
    try {
      const taskResponse = await api<{ task_id: number; status: string }>(`/api/videos/${video.id}/clip-export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tag_definition_id: clipTagId,
          export_mode: clipMode,
          pre_roll_seconds: clipPreRoll,
          post_roll_seconds: clipPostRoll,
          output_label: clipOutputLabel.trim() || null,
          keep_segments: clipKeepSegments,
        }),
      });

      const pollInterval = setInterval(async () => {
        try {
          const progress = await api<{ status: string; current: number; total: number; stage: string; result: ClipExportResult | null; error: string | null }>(
            `/api/videos/${video.id}/clip-export/${taskResponse.task_id}`
          );
          setExportProgress({ current: progress.current, total: progress.total, stage: progress.stage });
          if (progress.status === "completed" && progress.result) {
            clearInterval(pollInterval);
            setClipResult(progress.result);
            setClipPlan(progress.result);
            setIsExportingClips(false);
            setExportProgress(null);
          } else if (progress.status === "failed") {
            clearInterval(pollInterval);
            setError(progress.error || "Error en la exportacion");
            setIsExportingClips(false);
            setExportProgress(null);
          }
        } catch {
          clearInterval(pollInterval);
        }
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar la exportacion");
      setIsExportingClips(false);
      setExportProgress(null);
    }
  }

  const pageTitle =
    route === "/label" && video
      ? displayName || video.display_name
      : route === "/clips" && video
        ? `Recortes - ${video.display_name}`
        : "Galeria de proyectos";

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="topbar-left">
          {(route === "/label" || route === "/clips") && (
            <button className="ghost-button back-button" type="button" onClick={handleBackToGallery}>
              ← Volver
            </button>
          )}
          <div className="title-block">
            <p className="eyebrow">Etiquetador de partido</p>
            {route === "/label" && video && isEditingTitle ? (
              <div className="title-editor">
                <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
                <button className="secondary-button" type="button" onClick={async () => { await saveDisplayName(); setIsEditingTitle(false); }}>
                  Guardar
                </button>
                <button type="button" className="ghost-button" onClick={() => { setDisplayName(video.display_name); setIsEditingTitle(false); }}>
                  Cancelar
                </button>
              </div>
            ) : (
              <h1 className={route === "/label" && video ? "editable-title" : ""} onClick={() => route === "/label" && video && setIsEditingTitle(true)}>
                {pageTitle}
              </h1>
            )}
          </div>
        </div>
        <div className="header-actions">
          {route === "/label" && video && (
            <button
              className="secondary-button"
              type="button"
              onClick={async () => {
                if (window.confirm(`¿Marcar "${video.display_name}" como finalizado?`)) {
                  await api<Video>(`/api/videos/${video.id}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ status: "completed" }),
                  });
                  handleBackToGallery();
                }
              }}
            >
              Acabar proyecto
            </button>
          )}
          <button className="theme-toggle" type="button" onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))}>
            {theme === "light" ? "Dark mode" : "Light mode"}
          </button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {route === "/gallery" ? (
        <ProjectsView
          videos={videoLibrary}
          isUploading={isUploading}
          isSyncing={isSyncing}
          fileInputRef={fileInputRef}
          onSelectVideo={(item) => void handleSelectVideo(item)}
          onOpenClips={(item) => void handleOpenClips(item)}
          onOpenUpload={() => fileInputRef.current?.click()}
          onFileChange={(file) => void handleInitialFileChange(file)}
          onDeleteVideo={(item) => {
            if (window.confirm(`¿Eliminar permanentemente el proyecto "${item.display_name}"? Esta accion no se puede deshacer.`)) {
              void api<void>(`/api/videos/${item.id}`, { method: "DELETE" }).then(() => refresh(selectedVideoId, route));
            }
          }}
          onSync={async () => {
            setIsSyncing(true);
            try {
              await api<void>("/api/videos/sync", { method: "POST" });
              await refresh(selectedVideoId, route);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Error al sincronizar");
            } finally {
              setIsSyncing(false);
            }
          }}
        />
      ) : route === "/label" ? (
        video && (
          <WorkspaceView
            video={video}
            streamUrl={streamUrl}
            videoRef={videoRef}
            currentTime={currentTime}
            duration={duration}
            jumpSeconds={jumpSeconds}
            tagCounts={tagCounts}
            events={events}
            tags={tags}
            regularTags={regularTags}
            antagonisticPairs={antagonisticPairs}
            activeRanges={activeRanges}
            editingTagId={editingTagId}
            editingPairKey={editingPairKey}
            tagDraft={tagDraft}
            pairDraft={pairDraft}
            onBack={handleBackToGallery}
            onOpenCreateTag={() => setIsCreateModalOpen(true)}
            onJumpChange={setJumpSeconds}
            onTimeUpdate={setCurrentTime}
            onDurationChange={setDuration}
            onSeek={seekTo}
            onRegisterTag={(tag) => void registerTag(tag)}
            onBeginTagEdit={beginTagEdit}
            onBeginPairEdit={beginPairEdit}
            onSaveTagEdit={(tag) => void saveTagEdit(tag)}
            onSavePairEdit={(pair) => void savePairEdit(pair)}
            onDeactivateTag={(tag) => void deactivateTag(tag)}
            onDeactivatePair={(pair) => void deactivateAntagonisticPair(pair)}
            onTagDraftChange={(draft) => {
              setTagDraft(draft);
              if (draft === null) {
                setEditingTagId(null);
              }
            }}
            onPairDraftChange={(draft) => {
              setPairDraft(draft);
              if (draft === null) {
                setEditingPairKey(null);
              }
            }}
            onUpdateEvent={(eventId, values) => void updateEvent(eventId, values)}
            onDeleteEvent={(eventId) => void deleteEvent(eventId)}
          />
        )
      ) : (
        video && (
          <ClipsView
            video={video}
            tags={tags}
            selectedTagId={clipTagId}
            exportMode={clipMode}
            preRollSeconds={clipPreRoll}
            postRollSeconds={clipPostRoll}
            outputLabel={clipOutputLabel}
            keepSegments={clipKeepSegments}
            exportProgress={exportProgress}
            plan={clipPlan}
            result={clipResult}
            isPlanning={isPlanningClips}
            isExporting={isExportingClips}
            onBack={handleBackToGallery}
            onGoToLabel={async () => {
              navigateTo("/label");
              setRoute("/label");
              await refresh(selectedVideoId, "/label");
            }}
            onTagChange={(tagId) => {
              setClipTagId(tagId);
              const tag = tags.find((item) => item.id === tagId);
              if (tag && !clipOutputLabel) {
                setClipOutputLabel(tag.name);
              }
            }}
            onModeChange={setClipMode}
            onPreRollChange={setClipPreRoll}
            onPostRollChange={setClipPostRoll}
            onOutputLabelChange={setClipOutputLabel}
            onKeepSegmentsChange={setClipKeepSegments}
            onPreview={() => void previewClips()}
            onExport={() => void exportClips()}
          />
        )
      )}

      <CreateTagModal
        isOpen={isCreateModalOpen}
        newTagMode={newTagMode}
        newTagName={newTagName}
        newTagColor={newTagColor}
        newAntagonistFirst={newAntagonistFirst}
        newAntagonistSecond={newAntagonistSecond}
        newAntagonistSecondColor={newAntagonistSecondColor}
        newTagShortcut={newTagShortcut}
        tags={tags}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={createTag}
        onModeChange={setNewTagMode}
        onTagNameChange={setNewTagName}
        onTagColorChange={setNewTagColor}
        onAntagonistFirstChange={setNewAntagonistFirst}
        onAntagonistSecondChange={setNewAntagonistSecond}
        onAntagonistSecondColorChange={setNewAntagonistSecondColor}
        onShortcutChange={setNewTagShortcut}
        onSuggestColors={() => {
          const nextFirstColor = suggestAvailableColor(tags);
          setNewTagColor(nextFirstColor);
          if (newTagMode === "antagonistic") {
            setNewAntagonistSecondColor(suggestSecondColor(tags, nextFirstColor));
          }
        }}
        onSuggestSecondColor={() => setNewAntagonistSecondColor(suggestSecondColor(tags, newTagColor))}
      />
    </main>
  );
}
