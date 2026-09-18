import { useCallback, useEffect, useState } from "react";
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
  fetchTracks,
  logout,
  type Overview,
  type TrackDetail,
  type TrackRow,
} from "../../api/adminClient";
import AdminLoginPage from "./AdminLoginPage";

const PERIODS = [7, 30, 90] as const;
const PIE_COLORS = ["#b5502a", "#d98c4a", "#7a9a6d", "#5b7c99", "#9a6d8f", "#c2b280"];

function formatSeconds(total: number): string {
  if (!Number.isFinite(total)) return "—";
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = Math.floor(total % 60);
  if (h > 0) return `${h} ч ${m} мин`;
  if (m > 0) return `${m} мин ${s} с`;
  return `${s} с`;
}

function formatPercent(value: number | null): string {
  if (value == null) return "—";
  return `${Math.round(value * 100)}%`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("ru-RU");
}

function formatDay(day: string): string {
  return new Date(day).toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
}

function formatDayLabel(label: unknown): string {
  return typeof label === "string" ? formatDay(label) : String(label);
}

function formatBucketLabel(label: unknown): string {
  const v = typeof label === "number" ? label : Number(label);
  if (!Number.isFinite(v)) return String(label);
  return `Глубина ${Math.round(v * 100)}–${Math.round((v + 0.1) * 100)}%`;
}

export default function AdminDashboardPage() {
  const [authState, setAuthState] = useState<"checking" | "loggedOut" | "loggedIn">(
    "checking",
  );
  const [days, setDays] = useState<number>(7);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [tracks, setTracks] = useState<TrackRow[] | null>(null);
  const [detail, setDetail] = useState<TrackDetail | null>(null);
  const [detailTrackId, setDetailTrackId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkSession()
      .then((ok) => setAuthState(ok ? "loggedIn" : "loggedOut"))
      .catch(() => setAuthState("loggedOut"));
  }, []);

  const loadData = useCallback(async (period: number) => {
    setError(null);
    try {
      const [ov, tr] = await Promise.all([fetchOverview(period), fetchTracks(period)]);
      setOverview(ov);
      setTracks(tr.tracks);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setAuthState("loggedOut");
      } else {
        setError("Не удалось загрузить аналитику");
      }
    }
  }, []);

  useEffect(() => {
    if (authState === "loggedIn") {
      void loadData(days);
    } else {
      setOverview(null);
      setTracks(null);
      setDetail(null);
      setDetailTrackId(null);
    }
  }, [authState, days, loadData]);

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
        <p className="subtitle">Загрузка…</p>
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
          <p className="brand">Арт-сплетни</p>
          <h1>Аналитика прослушиваний</h1>
        </div>
        <div className="admin-header-actions">
          <div className="admin-periods">
            {PERIODS.map((p) => (
              <button
                key={p}
                className={p === days ? "admin-btn active" : "admin-btn"}
                onClick={() => setDays(p)}
              >
                {p} дней
              </button>
            ))}
          </div>
          <a className="admin-btn ghost" href="/sqladmin">
            Управление треками
          </a>
          <button
            className="admin-btn ghost"
            onClick={() => {
              void logout().finally(() => setAuthState("loggedOut"));
            }}
          >
            Выйти
          </button>
        </div>
      </header>

      {error ? <p className="admin-error">{error}</p> : null}

      <section className="admin-kpis">
        <div className="admin-kpi">
          <span className="admin-kpi-value">{kpi ? kpi.plays : "—"}</span>
          <span className="admin-kpi-label">Прослушиваний</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">{kpi ? kpi.visitors : "—"}</span>
          <span className="admin-kpi-label">Уникальных слушателей</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">
            {kpi ? formatSeconds(kpi.total_listened_seconds) : "—"}
          </span>
          <span className="admin-kpi-label">Слушали суммарно</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">{kpi ? formatPercent(kpi.avg_completion) : "—"}</span>
          <span className="admin-kpi-label">Средняя глубина</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">
            {kpi ? formatPercent(kpi.completion_rate) : "—"}
          </span>
          <span className="admin-kpi-label">Дослушали до конца</span>
        </div>
        <div className="admin-kpi">
          <span className="admin-kpi-value">{kpi ? kpi.plays_today : "—"}</span>
          <span className="admin-kpi-label">Прослушиваний сегодня</span>
        </div>
      </section>

      <section className="admin-grid">
        <div className="admin-card span-2">
          <h2>Динамика по дням</h2>
          {overview && overview.daily.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={overview.daily}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5ddd0" />
                <XAxis dataKey="day" tickFormatter={formatDay} fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip labelFormatter={formatDayLabel} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="plays"
                  name="Прослушивания"
                  stroke="#b5502a"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="visitors"
                  name="Слушатели"
                  stroke="#5b7c99"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="admin-empty">Нет данных за период</p>
          )}
        </div>

        <div className="admin-card">
          <h2>Устройства</h2>
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
            <p className="admin-empty">Нет данных</p>
          )}
        </div>

        <div className="admin-card">
          <h2>Источники (referrer)</h2>
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
                <Bar dataKey="plays" name="Прослушивания" fill="#d98c4a" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="admin-empty">Нет данных</p>
          )}
        </div>

        <div className="admin-card">
          <h2>Языки</h2>
          {overview && overview.languages.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={overview.languages}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5ddd0" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis allowDecimals={false} fontSize={12} />
                <Tooltip />
                <Bar dataKey="plays" name="Прослушивания" fill="#7a9a6d" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="admin-empty">Нет данных</p>
          )}
        </div>
      </section>

      <section className="admin-card">
        <h2>Треки</h2>
        {tracks ? (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Трек</th>
                  <th>Прослушиваний</th>
                  <th>Слушателей</th>
                  <th>Суммарно слушали</th>
                  <th>Средняя глубина</th>
                  <th>Медианная глубина</th>
                  <th>Дослушали</th>
                  <th>Последнее</th>
                </tr>
              </thead>
              <tbody>
                {tracks.map((t) => (
                  <tr
                    key={t.id}
                    className={t.id === detailTrackId ? "selected" : ""}
                    onClick={() => setDetailTrackId(t.id)}
                  >
                    <td>
                      {t.title}
                      {!t.is_published ? <span className="admin-badge">черновик</span> : null}
                    </td>
                    <td>{t.plays}</td>
                    <td>{t.visitors}</td>
                    <td>{formatSeconds(t.listened_seconds)}</td>
                    <td>{formatPercent(t.avg_completion)}</td>
                    <td>{formatPercent(t.median_completion)}</td>
                    <td>{formatPercent(t.completion_rate)}</td>
                    <td>{formatDate(t.last_played_at)}</td>
                  </tr>
                ))}
                {tracks.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="admin-empty">
                      Пока нет треков
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="admin-empty">Загрузка…</p>
        )}
      </section>

      {detail ? (
        <section className="admin-card">
          <h2>
            {detail.title}
            <button
              className="admin-btn ghost small"
              onClick={() => setDetailTrackId(null)}
            >
              Закрыть
            </button>
          </h2>
          <div className="admin-detail-kpis">
            <div>
              <strong>{detail.kpi.plays}</strong>
              <span>прослушиваний</span>
            </div>
            <div>
              <strong>{detail.kpi.visitors}</strong>
              <span>слушателей</span>
            </div>
            <div>
              <strong>{formatSeconds(detail.kpi.total_listened_seconds)}</strong>
              <span>слушали суммарно</span>
            </div>
            <div>
              <strong>{formatPercent(detail.kpi.avg_completion)}</strong>
              <span>средняя глубина</span>
            </div>
            <div>
              <strong>{formatPercent(detail.kpi.completion_rate)}</strong>
              <span>дослушали</span>
            </div>
            <div>
              <strong>{detail.avg_seek_count != null ? detail.avg_seek_count.toFixed(1) : "—"}</strong>
              <span>перескоков в среднем</span>
            </div>
          </div>

          <h3>Глубина прослушивания (распределение)</h3>
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
                <Tooltip labelFormatter={formatBucketLabel} />
                <Bar dataKey="count" name="Сессий" fill="#b5502a" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="admin-empty">Нет данных</p>
          )}

          <h3>Последние сессии</h3>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Когда</th>
                  <th>Слушал</th>
                  <th>Глубина</th>
                  <th>Дослушал</th>
                  <th>Устройство</th>
                  <th>Источник</th>
                </tr>
              </thead>
              <tbody>
                {detail.recent.map((s, i) => (
                  <tr key={i}>
                    <td>
                      {new Date(s.created_at).toLocaleString("ru-RU", {
                        day: "2-digit",
                        month: "2-digit",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td>{formatSeconds(s.listened_seconds)}</td>
                    <td>{formatPercent(s.completion_ratio)}</td>
                    <td>{s.is_completed ? "да" : "нет"}</td>
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
