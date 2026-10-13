import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, Navigate, useParams } from "react-router-dom";
import { ApiError, checkSession } from "../../api/adminClient";
import {
  addAdminDependency,
  addAdminStop,
  createAdminCheckpoint,
  deleteAdminStop,
  fetchAdminCheckpoints,
  fetchAdminRoutes,
  fetchAdminStops,
  fetchAdminTracks,
  removeAdminDependency,
  updateAdminRoute,
  updateAdminStop,
  type AdminCheckpoint,
  type AdminRoute,
  type AdminStop,
  type AdminTrack,
} from "../../api/adminRouteClient";
import DependencyGraph, { type StopForGraph } from "../../components/DependencyGraph";import LocationMap from "../../components/LocationMap";import TrackFormModal from "../../components/admin/TrackFormModal";
import "../../styles/admin-route.css";

const COMPLETION_CRITERIA_KEYS = [
  { value: "scan", labelKey: "routeBuilder.criteriaScan" },
  { value: "listen_any", labelKey: "routeBuilder.criteriaListenAny" },
  { value: "listen_95", labelKey: "routeBuilder.criteriaListen95" },
  { value: "listen_100", labelKey: "routeBuilder.criteriaListen100" },
  { value: "open", labelKey: "routeBuilder.criteriaOpen" },
] as const;

interface StopWithDetails extends AdminStop {
  title: string;
  slug: string;
}

export default function AdminRouteBuilderPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const routeId = Number(id);

  const [adminAuthed, setAdminAuthed] = useState<boolean | null>(null);
  const [route, setRoute] = useState<AdminRoute | null>(null);
  const [stops, setStops] = useState<StopWithDetails[]>([]);
  const [tracks, setTracks] = useState<AdminTrack[]>([]);
  const [checkpoints, setCheckpoints] = useState<AdminCheckpoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [newStopType, setNewStopType] = useState<"track" | "checkpoint">("track");
  const [newStopTargetId, setNewStopTargetId] = useState<string>("");
  const [newStopCriteria, setNewStopCriteria] = useState("scan");
  const [showCheckpointForm, setShowCheckpointForm] = useState(false);
  const [cpTitle, setCpTitle] = useState("");
  const [cpContentType, setCpContentType] = useState<"text" | "image" | "loot" | "audio">("text");
  const [cpText, setCpText] = useState("");
  const [cpLootType, setCpLootType] = useState<"promo_code" | "link" | "badge">("promo_code");
  const [cpLootValue, setCpLootValue] = useState("");
  const [cpDescription, setCpDescription] = useState("");
  const [cpLocationName, setCpLocationName] = useState("");
  const [cpLatitude, setCpLatitude] = useState(56.8389);
  const [cpLongitude, setCpLongitude] = useState(60.6057);
  const [cpMapCenter, setCpMapCenter] = useState<{ latitude: number; longitude: number }>();
  const [trackModalOpen, setTrackModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    setError(null);
    try {
      const [routesData, stopsData, tracksData, checkpointsData] = await Promise.all([
        fetchAdminRoutes(),
        fetchAdminStops(routeId),
        fetchAdminTracks(),
        fetchAdminCheckpoints(),
      ]);
      const foundRoute = routesData.routes.find((r) => r.id === routeId);
      if (!foundRoute) {
        setError(t("routes.notFound"));
        return;
      }
      setRoute(foundRoute);

      const enrichedStops: StopWithDetails[] = stopsData.map((stop) => {
        let title = `Stop #${stop.id}`;
        let slug = "";
        if (stop.track_id) {
          const track = tracksData.tracks.find((tr) => tr.id === stop.track_id);
          if (track) {
            title = track.title;
            slug = track.slug;
          }
        } else if (stop.checkpoint_id) {
          const cp = checkpointsData.checkpoints.find((c) => c.id === stop.checkpoint_id);
          if (cp) {
            title = cp.title;
            slug = cp.slug;
          }
        }
        return { ...stop, title, slug };
      });
      enrichedStops.sort((a, b) => a.order_index - b.order_index);
      setStops(enrichedStops);
      setTracks(tracksData.tracks);
      setCheckpoints(checkpointsData.checkpoints);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("admin.loadError"));
    } finally {
      setLoading(false);
    }
  }, [routeId, t]);

  useEffect(() => {
    checkSession()
      .then((ok) => {
        if (!ok) {
          setAdminAuthed(false);
          return;
        }
        setAdminAuthed(true);
        void loadData();
      })
      .catch(() => setAdminAuthed(false));
  }, [loadData]);

  const handleDeleteStop = useCallback(
    async (stopId: number) => {
      try {
        await deleteAdminStop(routeId, stopId);
        await loadData();
      } catch (e) {
        setError(e instanceof ApiError ? e.message : t("admin.loadError"));
      }
    },
    [routeId, loadData, t],
  );

  const handleCriteriaChange = useCallback(
    async (stopId: number, criteria: string) => {
      setStops((prev) =>
        prev.map((s) => (s.id === stopId ? { ...s, completion_criteria: criteria } : s)),
      );
      try {
        await updateAdminStop(routeId, stopId, { completion_criteria: criteria });
      } catch {
        setError(t("admin.loadError"));
        void loadData();
      }
    },
    [routeId, loadData, t],
  );

  const handleDependencyAdd = useCallback(
    async (stopId: number, dependsOnStopId: number) => {
      try {
        await addAdminDependency(routeId, stopId, dependsOnStopId);
        await loadData();
      } catch (e) {
        const msg = e instanceof ApiError ? e.message : t("routeBuilder.cycleError");
        setError(msg);
        void loadData();
      }
    },
    [routeId, loadData, t],
  );

  const handleDependencyRemove = useCallback(
    async (stopId: number, dependsOnStopId: number) => {
      try {
        await removeAdminDependency(routeId, stopId, dependsOnStopId);
        await loadData();
      } catch (e) {
        setError(e instanceof ApiError ? e.message : t("admin.loadError"));
        void loadData();
      }
    },
    [routeId, loadData, t],
  );

  const handleAddStop = async () => {
    setError(null);
    const targetId = Number(newStopTargetId);
    if (!targetId) {
      setError(t("routes.notFound"));
      return;
    }
    try {
      await addAdminStop(routeId, {
        stop_type: newStopType,
        track_id: newStopType === "track" ? targetId : undefined,
        checkpoint_id: newStopType === "checkpoint" ? targetId : undefined,
        completion_criteria: newStopCriteria,
      });
      setNewStopTargetId("");
      await loadData();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("admin.loadError"));
    }
  };



  const handleTogglePublish = async () => {
    if (!route) return;
    try {
      const updated = await updateAdminRoute(routeId, { is_published: !route.is_published });
      setRoute(updated);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("admin.loadError"));
    }
  };

  const handleCreateCheckpoint = async () => {
    setError(null);
    if (!cpTitle.trim()) {
      setError(t("routes.notFound"));
      return;
    }
    try {
      await createAdminCheckpoint({
        title: cpTitle,
        content_type: cpContentType,
        description: cpDescription || undefined,
        latitude: cpLatitude,
        longitude: cpLongitude,
        location_name: cpLocationName || undefined,
        text_content: cpContentType === "text" ? cpText : undefined,
        loot_type: cpContentType === "loot" ? cpLootType : undefined,
        loot_value: cpContentType === "loot" ? cpLootValue : undefined,
        is_published: true,
      });
      setCpTitle("");
      setCpText("");
      setCpLootValue("");
      setCpDescription("");
      setCpLocationName("");
      setCpLatitude(56.8389);
      setCpLongitude(60.6057);
      setCpMapCenter(undefined);
      setShowCheckpointForm(false);
      await loadData();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("admin.loadError"));
    }
  };

  if (adminAuthed === false) {
    return <Navigate to="/admin" replace />;
  }

  if (adminAuthed === null || loading) {
    return (
      <div className="container">
        <p className="subtitle">{t("common.loading")}</p>
      </div>
    );
  }

  if (!route) {
    return (
      <div className="container">
        <p className="brand">{t("common.brand")}</p>
        <div className="card">
          <h1>{error ?? t("routes.notFound")}</h1>
          <Link to="/admin">← {t("admin.title")}</Link>
        </div>
      </div>
    );
  }

  const graphStops: StopForGraph[] = stops.map((s) => ({
    id: s.id,
    order_index: s.order_index,
    stop_type: s.stop_type,
    track_id: s.track_id,
    checkpoint_id: s.checkpoint_id,
    completion_criteria: s.completion_criteria,
    depends_on: s.depends_on,
    title: s.title,
    slug: s.slug,
  }));

  return (
    <div className="container admin-route-builder">
      <p className="brand">{t("common.brand")} · {t("admin.title")}</p>
      <div className="card">
        <div className="admin-route-header">
          <h1>{route.title}</h1>
          <div className="admin-route-actions">
            <button
              className={`admin-btn ${route.is_published ? "danger" : ""}`}
              onClick={handleTogglePublish}
            >
              {route.is_published ? t("admin.reject") : t("admin.publish")}
            </button>
            <Link to="/admin" className="admin-back-link">← {t("admin.tabOverview")}</Link>
          </div>
        </div>
        {error ? <p className="admin-error">{error}</p> : null}

        <div className="admin-stops-section">
          <h2>{t("routeBuilder.graphTitle")} ({stops.length})</h2>
          {stops.length > 0 ? (
            <DependencyGraph
              stops={graphStops}
              onCriteriaChange={handleCriteriaChange}
              onDeleteStop={handleDeleteStop}
              onDependencyAdd={handleDependencyAdd}
              onDependencyRemove={handleDependencyRemove}
            />
          ) : (
            <p className="subtitle">{t("admin.noData")}</p>
          )}
        </div>

        <div className="admin-add-stop-section">
          <h2>{t("admin.routeBuilder")}</h2>
          <div className="admin-add-stop-form">
            <select
              value={newStopType}
              onChange={(e) => {
                setNewStopType(e.target.value as "track" | "checkpoint");
                setNewStopTargetId("");
              }}
            >
              <option value="track">{t("routes.stopTrack")}</option>
              <option value="checkpoint">{t("routes.stopCheckpoint")}</option>
            </select>
            <select
              value={newStopTargetId}
              onChange={(e) => setNewStopTargetId(e.target.value)}
            >
              <option value="">{t("common.loading")}…</option>
              {newStopType === "track"
                ? tracks.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.title} ({t.moderation_status})
                    </option>
                  ))
                : checkpoints.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title} ({c.content_type})
                    </option>
                  ))}
            </select>
            <select value={newStopCriteria} onChange={(e) => setNewStopCriteria(e.target.value)}>
              {COMPLETION_CRITERIA_KEYS.map((c) => (
                <option key={c.value} value={c.value}>{t(c.labelKey)}</option>
              ))}
            </select>
            <button className="admin-btn" onClick={handleAddStop}>{t("admin.createRoute")}</button>
            {newStopType === "track" ? (
              <button
                className="admin-btn ghost"
                onClick={() => setTrackModalOpen(true)}
              >
                {t("admin.createTrack")}
              </button>
            ) : null}
          </div>

          <button
            className="admin-btn secondary"
            onClick={() => setShowCheckpointForm(!showCheckpointForm)}
          >
            {showCheckpointForm ? t("admin.close") : t("routes.stopCheckpoint")}
          </button>

          {showCheckpointForm ? (
            <div className="admin-checkpoint-inline-form">
              <h3>{t("routes.stopCheckpoint")}</h3>
              <label>
                {t("auth.registerName")}
                <input value={cpTitle} onChange={(e) => setCpTitle(e.target.value)} />
              </label>
              <label>
                {t("submission.descriptionLabel")}
                <input value={cpDescription} onChange={(e) => setCpDescription(e.target.value)} />
              </label>
              <label>
                {t("submission.locationNameLabel")}
                <input value={cpLocationName} onChange={(e) => setCpLocationName(e.target.value)} />
              </label>
              <label>
                {t("admin.trackLocationMap")}
                <LocationMap
                  interactive
                  latitude={cpLatitude}
                  longitude={cpLongitude}
                  center={cpMapCenter}
                  onChange={({ latitude: nextLat, longitude: nextLng }) => {
                    setCpLatitude(Number(nextLat.toFixed(6)));
                    setCpLongitude(Number(nextLng.toFixed(6)));
                    setCpMapCenter(undefined);
                  }}
                />
                <div className="map-selection-row">
                  <small>{cpLatitude.toFixed(6)}, {cpLongitude.toFixed(6)}</small>
                  <button
                    className="location-button"
                    type="button"
                    onClick={() => {
                      if (!navigator.geolocation) return;
                      navigator.geolocation.getCurrentPosition(
                        ({ coords }) => {
                          const pos = {
                            latitude: Number(coords.latitude.toFixed(6)),
                            longitude: Number(coords.longitude.toFixed(6)),
                          };
                          setCpLatitude(pos.latitude);
                          setCpLongitude(pos.longitude);
                          setCpMapCenter(pos);
                        },
                        undefined,
                        { enableHighAccuracy: true, timeout: 10000 },
                      );
                    }}
                  >
                    {t("admin.trackMyLocation")}
                  </button>
                </div>
              </label>
              <label>
                {t("routes.stopCheckpoint")}
                <select
                  value={cpContentType}
                  onChange={(e) => setCpContentType(e.target.value as typeof cpContentType)}
                >
                  <option value="text">{t("routes.stopCheckpoint")}</option>
                  <option value="image">{t("routes.stopCheckpoint")}</option>
                  <option value="loot">{t("routes.stopCheckpoint")}</option>
                  <option value="audio">{t("routes.stopAudio")}</option>
                </select>
              </label>
              {cpContentType === "text" ? (
                <label>
                  {t("submission.descriptionLabel")}
                  <textarea value={cpText} onChange={(e) => setCpText(e.target.value)} rows={4} />
                </label>
              ) : null}
              {cpContentType === "loot" ? (
                <>
                  <label>
                    {t("routes.stopCheckpoint")}
                    <select
                      value={cpLootType}
                      onChange={(e) => setCpLootType(e.target.value as typeof cpLootType)}
                    >
                      <option value="promo_code">{t("routes.checkpointPromoCode")}</option>
                      <option value="link">{t("routes.checkpointGoLink")}</option>
                      <option value="badge">{t("routes.stopCheckpoint")}</option>
                    </select>
                  </label>
                  <label>
                    {t("submission.titleLabel")}
                    <input value={cpLootValue} onChange={(e) => setCpLootValue(e.target.value)} />
                  </label>
                </>
              ) : null}
              <button className="admin-btn" onClick={handleCreateCheckpoint}>
                {t("admin.createRoute")}
              </button>
            </div>
          ) : null}
        </div>
      </div>

      {trackModalOpen ? (
        <TrackFormModal
          onSaved={() => void loadData()}
          onClose={() => setTrackModalOpen(false)}
        />
      ) : null}
    </div>
  );
}
