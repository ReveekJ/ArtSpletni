import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import { useLanguage } from "../../i18n/useLanguage";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  PieChart,
  Pie,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ApiError,
  checkSession,
  fetchOverview,
  fetchTrackDetail,
  fetchSubmissions,
  fetchTracks,
  logout,
  updateSubmissionStatus,
  type Overview,
  type TrackDetail,
  type TrackRow,
  type Submission,
} from "../../api/adminClient";
import {
  createAdminRoute,
  deleteAdminTrack,
  fetchAdminRoutes,
  fetchAdminTracks,
  fetchAdminTrackDetail,
  type AdminRoute,
  type AdminTrack,
  type TrackAdminDetail,
} from "../../api/adminRouteClient";
import TrackFormModal from "../../components/admin/TrackFormModal";
import AdminLoginPage from "./AdminLoginPage";

const PERIODS = [7, 30, 90] as const;
const PIE_COLORS = ["#b5502a", "#d98c4a", "#7a9a6d", "#5b7c99", "#9a6d8f", "#c2b280"];

function formatPercent(value: number | null): string {
  if (value == null) return "—";
  return `${Math.round(value * 100)}%`;
}

function formatDate(iso: string | null, locale: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString(locale);
}

function formatDay(day: string, locale: string): string {
  return new Date(day).toLocaleDateString(locale, { day: "2-digit", month: "2-digit" });
}

function formatDayLabel(label: unknown, locale: string): string {
  return typeof label === "string" ? formatDay(label, locale) : String(label);
}

function formatBucketLabel(label: unknown, t: (key: string) => string): string {
  const v = typeof label === "number" ? label : Number(label);
  if (!Number.isFinite(v)) return String(label);
  return `${t("admin.depthLabel")} ${Math.round(v * 100)}–${Math.round((v + 0.1) * 100)}%`;
}

export default function AdminDashboardPage() {
  const { t } = useTranslation();
  const { locale } = useLanguage();

  const formatSeconds = useCallback((total: number): string => {
    if (!Number.isFinite(total)) return "—";
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = Math.floor(total % 60);
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  }, []);

  const [authState, setAuthState] = useState<"checking" | "loggedOut" | "loggedIn">(
    "checking",
  );
  const [activeTab, setActiveTab] = useState<"overview" | "moderation" | "routes" | "tracks">(
    "overview",
  );
  const [days, setDays] = useState<number>(7);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [tracks, setTracks] = useState<TrackRow[] | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [detail, setDetail] = useState<TrackDetail | null>(null);
  const [detailTrackId, setDetailTrackId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adminRoutes, setAdminRoutes] = useState<AdminRoute[]>([]);
  const [newRouteTitle, setNewRouteTitle] = useState("");
  const [routeError, setRouteError] = useState<string | null>(null);
  const [adminTracks, setAdminTracks] = useState<AdminTrack[]>([]);
  const [trackModalOpen, setTrackModalOpen] = useState(false);
  const [editingTrack, setEditingTrack] = useState<TrackAdminDetail | null>(null);
  const [trackError, setTrackError] = useState<string | null>(null);

  useEffect(() => {
    checkSession()
      .then((ok) => setAuthState(ok ? "loggedIn" : "loggedOut"))
      .catch(() => setAuthState("loggedOut"));
  }, []);

  const loadData = useCallback(async (period: number) => {
    setError(null);
    try {
      const [ov, tr, pending] = await Promise.all([
        fetchOverview(period),
        fetchTracks(period),
        fetchSubmissions(),
      ]);
      setOverview(ov);
      setTracks(tr.tracks);
      setSubmissions(pending.submissions);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setAuthState("loggedOut");
      } else {
        setError(t("admin.loadError"));
      }
    }
  }, []);

  useEffect(() => {
    if (authState === "loggedIn") {
      void loadData(days);
    } else {
      setOverview(null);
      setTracks(null);
      setSubmissions([]);
      setDetail(null);
      setDetailTrackId(null);
    }
  }, [authState, days, loadData]);

  const loadRoutes = useCallback(async () => {
    setRouteError(null);
    try {
      const data = await fetchAdminRoutes();
      setAdminRoutes(data.routes);
    } catch (e) {
      setRouteError(e instanceof ApiError ? e.message : t("admin.loadError"));
    }
  }, []);

  useEffect(() => {
    if (authState === "loggedIn" && activeTab === "routes") {
      void loadRoutes();
    }
  }, [authState, activeTab, loadRoutes]);

  const loadTracks = useCallback(async () => {
    setTrackError(null);
    try {
      const data = await fetchAdminTracks();
      setAdminTracks(data.tracks);
    } catch (e) {
      setTrackError(e instanceof ApiError ? e.message : t("admin.loadError"));
    }
  }, [t]);

  useEffect(() => {
    if (authState === "loggedIn" && activeTab === "tracks") {
      void loadTracks();
    }
  }, [authState, activeTab, loadTracks]);

  const handleEditTrack = useCallback(
    async (trackId: number) => {
      try {
        const detail = await fetchAdminTrackDetail(trackId);
        setEditingTrack(detail);
        setTrackModalOpen(true);
      } catch (e) {
        setTrackError(e instanceof ApiError ? e.message : t("admin.loadError"));
      }
    },
    [t],
  );

  const handleDeleteTrack = useCallback(
    async (trackId: number) => {
      if (!window.confirm(t("admin.deleteTrackConfirm"))) return;
      try {
        await deleteAdminTrack(trackId);
        await loadTracks();
      } catch (e) {
        setTrackError(e instanceof ApiError ? e.message : t("admin.loadError"));
      }
    },
    [loadTracks, t],
  );

  const handleCreateTrackClick = useCallback(() => {
    setEditingTrack(null);
    setTrackModalOpen(true);
  }, []);

  const handleCreateRoute = async () => {
    if (!newRouteTitle.trim()) {
      setRouteError(t("admin.routeTitleRequired"));
      return;
    }
    setRouteError(null);
    try {
      await createAdminRoute(newRouteTitle, null);
      setNewRouteTitle("");
      await loadRoutes();
    } catch (e) {
      setRouteError(e instanceof ApiError ? e.message : t("admin.loadError"));
    }
  };

  useEffect(() => {
    if (detailTrackId == null) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    fetchTrackDetail(detailTrackId, days)
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch(() => {
        if (!cancelled) setDetail(null);
      });
    return () => {
      cancelled = true;
    };
  }, [detailTrackId, days]);

  if (authState === "checking") {
    return (
      <div className="container">
        <p className="subtitle">{t("common.loading")}</p>
      </div>
    );
  }

  if (authState === "loggedOut") {
    return <AdminLoginPage onLoggedIn={() => setAuthState("loggedIn")} />;
  }

  const kpi = overview?.kpi;

  return (
    <div className="admin-root">
      <header className="admin-header">
        <div>
          <p className="brand">{t("common.brand")}</p>
          <h1>{t("admin.title")}</h1>
        </div>
        <div className="admin-header-actions">
          <LanguageSwitcher />
          <button
            className="admin-btn ghost"
            onClick={() => {
              void logout().finally(() => setAuthState("loggedOut"));
            }}
          >
            {t("admin.logout")}
          </button>
        </div>
      </header>

      <div className="admin-tabs">
        <button
          className={`admin-tab ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          {t("admin.tabOverview")}
        </button>
        <button
          className={`admin-tab ${activeTab === "moderation" ? "active" : ""}`}
          onClick={() => setActiveTab("moderation")}
        >
          {t("admin.tabModeration")}
        </button>
        <button
          className={`admin-tab ${activeTab === "routes" ? "active" : ""}`}
          onClick={() => setActiveTab("routes")}
        >
          {t("admin.tabRoutes")}
        </button>
        <button
          className={`admin-tab ${activeTab === "tracks" ? "active" : ""}`}
          onClick={() => setActiveTab("tracks")}
        >
          {t("admin.tabTracks")}
        </button>
      </div>

      {error ? <p className="admin-error">{error}</p> : null}

      {activeTab === "routes" ? (
        <section className="admin-card">
          <h2>{t("admin.routesTitle")}</h2>
          {routeError ? <p className="admin-error">{routeError}</p> : null}
          <div className="admin-add-stop-form" style={{ marginBottom: "1rem" }}>
            <input
              type="text"
              placeholder={t("admin.newRouteTitle")}
              value={newRouteTitle}
              onChange={(e) => setNewRouteTitle(e.target.value)}
              style={{ flex: 1, padding: "6px 10px", border: "1px solid rgba(0,0,0,0.1)", borderRadius: 4 }}
            />
            <button className="admin-btn" onClick={handleCreateRoute}>{t("admin.createRoute")}</button>
          </div>
          <div className="admin-routes-list">
            {adminRoutes.map((r) => (
              <Link
                key={r.id}
                to={`/admin/routes/${r.id}`}
                className="admin-route-list-item"
              >
                <div>
                  <strong>{r.title}</strong>
                  {r.description ? <span style={{ color: "#888", marginLeft: 8 }}>{r.description}</span> : null}
                </div>
                <span className={`status-badge ${r.is_published ? "published" : "draft"}`}>
                  {r.is_published ? "Опубликован" : "Черновик"}
                </span>
              </Link>
            ))}
            {adminRoutes.length === 0 ? (
              <p className="admin-empty">{t("admin.noData")}</p>
            ) : null}
          </div>
        </section>
      ) : null}

      {activeTab === "overview" ? (
        <>
          <div className="admin-periods" style={{ marginBottom: "1rem" }}>
            {PERIODS.map((p) => (
              <button
                key={p}
                className={p === days ? "admin-btn active" : "admin-btn"}
                onClick={() => setDays(p)}
              >
                {p} {t("admin.periodDays")}
              </button>
            ))}
          </div>

      <section className="admin-kpis">
        <div className="admin-kpi">
          <span className="admin-kpi-value">{kpi ? kpi.plays : "—"}</span>
          <span className="admin-kpi-label">{t("admin.kpiPlays")}</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">{kpi ? kpi.visitors : "—"}</span>
          <span className="admin-kpi-label">{t("admin.kpiVisitors")}</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">
            {kpi ? formatSeconds(kpi.total_listened_seconds) : "—"}
          </span>
          <span className="admin-kpi-label">{t("admin.kpiListened")}</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">{kpi ? formatPercent(kpi.avg_completion) : "—"}</span>
          <span className="admin-kpi-label">{t("admin.kpiAvgCompletion")}</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">
            {kpi ? formatPercent(kpi.completion_rate) : "—"}
          </span>
          <span className="admin-kpi-label">{t("admin.kpiCompletionRate")}</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">{kpi ? kpi.plays_today : "—"}</span>
          <span className="admin-kpi-label">{t("admin.kpiPlaysToday")}</span>
        </div>
      </section>

      <section className="admin-grid">
        <div className="admin-card span-2">
          <h2>{t("admin.chartDaily")}</h2>
          {overview && overview.daily.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={overview.daily}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5ddd0" />
                <XAxis dataKey="day" tickFormatter={(v: string) => formatDay(v, locale)} fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip labelFormatter={(v: unknown) => formatDayLabel(v, locale)} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="plays"
                  name={t("admin.chartPlays")}
                  stroke="#b5502a"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="visitors"
                  name={t("admin.chartVisitors")}
                  stroke="#5b7c99"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="admin-empty">{t("admin.noDataPeriod")}</p>
          )}
        </div>

        <div className="admin-card">
          <h2>{t("admin.chartDevices")}</h2>
          {overview && overview.devices.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={overview.devices}
                  dataKey="plays"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={90}
                >
                  {overview.devices.map((entry, i) => (
                    <Cell key={entry.name} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="admin-empty">{t("admin.noData")}</p>
          )}
        </div>

        <div className="admin-card">
          <h2>{t("admin.chartReferrers")}</h2>
          {overview && overview.referrers.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={overview.referrers} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5ddd0" />
                <XAxis type="number" allowDecimals={false} fontSize={12} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={180}
                  tickFormatter={(v: string) => (v.length > 28 ? `${v.slice(0, 27)}…` : v)}
                  fontSize={12}
                />
                <Tooltip />
                <Bar dataKey="plays" name={t("admin.chartPlays")} fill="#d98c4a" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="admin-empty">{t("admin.noData")}</p>
          )}
        </div>

        <div className="admin-card">
          <h2>{t("admin.chartLanguages")}</h2>
          {overview && overview.languages.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={overview.languages}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5ddd0" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip />
                <Bar dataKey="plays" name={t("admin.chartPlays")} fill="#7a9a6d" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="admin-empty">{t("admin.noData")}</p>
          )}
        </div>
      </section>
      </>
      ) : null}

      {activeTab === "moderation" ? (
      <>
      <section className="admin-card submissions-review">
        <div className="review-heading">
          <h2>{t("admin.submissionsTitle")}</h2>
          <span>{submissions.filter((item) => item.moderation_status === "pending").length}</span>
        </div>
        {submissions.length ? (
          <div className="review-list">
            {submissions.map((item) => (
              <article className="review-item" key={item.id}>
                <div className="review-copy">
                  <h3>{item.title}</h3>
                  <p>{[item.location_name, item.author, formatDate(item.created_at, locale)].filter(Boolean).join(" · ")}</p>
                  {item.description ? <p>{item.description}</p> : null}
                  <small>{item.latitude.toFixed(5)}, {item.longitude.toFixed(5)}</small>
                </div>
                <audio controls preload="none" src={item.audio_url} />
                <div className="review-actions">
                  {item.moderation_status !== "published" ? (
                    <button className="admin-btn active" onClick={() => void updateSubmissionStatus(item.id, "published").then(() => loadData(days))}>{t("admin.publish")}</button>
                  ) : null}
                  {item.moderation_status !== "rejected" ? (
                    <button className="admin-btn ghost" onClick={() => void updateSubmissionStatus(item.id, "rejected").then(() => loadData(days))}>{t("admin.reject")}</button>
                  ) : null}
                  {item.moderation_status !== "pending" ? (
                    <button className="admin-btn ghost" onClick={() => void updateSubmissionStatus(item.id, "pending").then(() => loadData(days))}>{t("admin.returnToReview")}</button>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        ) : <p className="admin-empty">{t("admin.noSubmissions")}</p>}
      </section>

      <section className="admin-card">
        <h2>{t("admin.tracksTitle")}</h2>
        {tracks ? (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>{t("admin.trackHeader")}</th>
                  <th>{t("admin.trackPlays")}</th>
                  <th>{t("admin.trackVisitors")}</th>
                  <th>{t("admin.trackListened")}</th>
                  <th>{t("admin.trackAvgCompletion")}</th>
                  <th>{t("admin.trackMedianCompletion")}</th>
                  <th>{t("admin.trackCompletionRate")}</th>
                  <th>{t("admin.trackLastPlayed")}</th>
                </tr>
              </thead>
              <tbody>
                {tracks.map((tr) => (
                  <tr
                    key={tr.id}
                    className={tr.id === detailTrackId ? "selected" : ""}
                    onClick={() => setDetailTrackId(tr.id)}
                  >
                    <td>
                      {tr.title}
                      {!tr.is_published ? <span className="admin-badge">{t("admin.trackDraft")}</span> : null}
                    </td>
                    <td>{tr.plays}</td>
                    <td>{tr.visitors}</td>
                    <td>{formatSeconds(tr.listened_seconds)}</td>
                    <td>{formatPercent(tr.avg_completion)}</td>
                    <td>{formatPercent(tr.median_completion)}</td>
                    <td>{formatPercent(tr.completion_rate)}</td>
                    <td>{formatDate(tr.last_played_at, locale)}</td>
                  </tr>
                ))}
                {tracks.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="admin-empty">
                      {t("admin.noTracks")}
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="admin-empty">{t("common.loading")}</p>
        )}
      </section>
      </>
      ) : null}

      {activeTab === "tracks" ? (
        <section className="admin-card">
          <div className="admin-tracks-header">
            <h2>{t("admin.tracksManageTitle")}</h2>
            <button className="admin-btn" onClick={handleCreateTrackClick}>
              {t("admin.createTrack")}
            </button>
          </div>
          {trackError ? <p className="admin-error">{trackError}</p> : null}
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>{t("admin.trackHeader")}</th>
                  <th>{t("admin.trackAuthor")}</th>
                  <th>{t("admin.trackLocationName")}</th>
                  <th>{t("admin.trackStatus")}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {adminTracks.map((tr) => (
                  <tr key={tr.id}>
                    <td>
                      {tr.title}
                      {!tr.is_published ? (
                        <span className="admin-badge">{t("admin.trackDraft")}</span>
                      ) : null}
                    </td>
                    <td>{tr.author ?? "—"}</td>
                    <td>{tr.location_name ?? "—"}</td>
                    <td>{tr.moderation_status}</td>
                    <td className="admin-tracks-actions">
                      <button
                        className="admin-btn ghost small"
                        onClick={() => void handleEditTrack(tr.id)}
                      >
                        {t("admin.editTrack")}
                      </button>
                      <button
                        className="admin-btn ghost small danger"
                        onClick={() => void handleDeleteTrack(tr.id)}
                      >
                        {t("admin.deleteTrack")}
                      </button>
                    </td>
                  </tr>
                ))}
                {adminTracks.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="admin-empty">
                      {t("admin.noTracks")}
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {trackModalOpen ? (
        <TrackFormModal
          track={editingTrack}
          onSaved={() => void loadTracks()}
          onClose={() => setTrackModalOpen(false)}
        />
      ) : null}

      {detail ? (
        <section className="admin-card">
          <h2>
            {detail.title}
            <button
              className="admin-btn ghost small"
              onClick={() => setDetailTrackId(null)}
            >
              {t("admin.close")}
            </button>
          </h2>
          <div className="admin-detail-kpis">
            <div>
              <strong>{detail.kpi.plays}</strong>
              <span>{t("admin.detailPlays")}</span>
            </div>
            <div>
              <strong>{detail.kpi.visitors}</strong>
              <span>{t("admin.detailVisitors")}</span>
            </div>
            <div>
              <strong>{formatSeconds(detail.kpi.total_listened_seconds)}</strong>
              <span>{t("admin.detailListened")}</span>
            </div>
            <div>
              <strong>{formatPercent(detail.kpi.avg_completion)}</strong>
              <span>{t("admin.detailAvgCompletion")}</span>
            </div>
            <div>
              <strong>{formatPercent(detail.kpi.completion_rate)}</strong>
              <span>{t("admin.detailCompletionRate")}</span>
            </div>
            <div>
              <strong>{detail.avg_seek_count != null ? detail.avg_seek_count.toFixed(1) : "—"}</strong>
              <span>{t("admin.detailAvgSeeks")}</span>
            </div>
          </div>

          <h3>{t("admin.detailHistogram")}</h3>
          {detail.histogram.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={detail.histogram}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5ddd0" />
                <XAxis
                  dataKey="bucket_start"
                  tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
                  fontSize={12}
                />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip labelFormatter={(v: unknown) => formatBucketLabel(v, t)} />
                <Bar dataKey="count" name={t("admin.chartSessions")} fill="#b5502a" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="admin-empty">{t("admin.noData")}</p>
          )}

          <h3>{t("admin.detailRecentSessions")}</h3>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>{t("admin.detailWhen")}</th>
                  <th>{t("admin.detailListened")}</th>
                  <th>{t("admin.detailCompletion")}</th>
                  <th>{t("admin.detailCompleted")}</th>
                  <th>{t("admin.detailDevice")}</th>
                  <th>{t("admin.detailReferrer")}</th>
                </tr>
              </thead>
              <tbody>
                {detail.recent.map((s, i) => (
                  <tr key={i}>
                    <td>
                      {new Date(s.created_at).toLocaleString(locale, {
                        day: "2-digit",
                        month: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td>{formatSeconds(s.listened_seconds)}</td>
                    <td>{formatPercent(s.completion_ratio)}</td>
                    <td>{s.is_completed ? "✓" : "—"}</td>
                    <td>{s.device_type ?? "—"}</td>
                    <td className="admin-ref">{s.referrer ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
