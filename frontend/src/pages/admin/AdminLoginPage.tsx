import { useState } from "react";
import { useTranslation } from "react-i18next";
import { login } from "../../api/adminClient";
import LanguageSwitcher from "../../components/LanguageSwitcher";

export default function AdminLoginPage({ onLoggedIn }: { onLoggedIn: () => void }) {
  const { t } = useTranslation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
      onLoggedIn();
    } catch {
      setError(t("admin.loginError"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container admin-login">
      <div className="track-header-row">
        <p className="brand">{t("common.brand")}</p>
        <LanguageSwitcher compact />
      </div>
      <div className="card">
        <h1>{t("admin.loginTitle")}</h1>
        <form onSubmit={submit}>
          <label>
            {t("admin.loginUsername")}
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label>
            {t("admin.loginPassword")}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          {error ? <p className="admin-error">{error}</p> : null}
          <button type="submit" className="admin-btn" disabled={busy}>
            {busy ? t("admin.loginSubmitting") : t("admin.loginSubmit")}
          </button>
        </form>
      </div>
    </div>
  );
}
