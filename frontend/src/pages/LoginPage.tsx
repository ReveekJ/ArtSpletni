import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError, getYandexLoginUrl } from "../api/authClient";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : t("auth.loginError"));
    } finally {
      setBusy(false);
    }
  };

  const handleYandex = async () => {
    try {
      const url = await getYandexLoginUrl();
      window.location.href = url;
    } catch {
      setError(t("auth.loginYandexError"));
    }
  };

  return (
    <div className="container">
      <div className="track-header-row">
        <p className="brand">{t("common.brand")}</p>
        <LanguageSwitcher compact />
      </div>
      <div className="card">
        <h1>{t("auth.loginTitle")}</h1>
        <form onSubmit={handleSubmit}>
          <label>
            {t("auth.loginEmail")}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </label>
          <label>
            {t("auth.loginPassword")}
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
            {busy ? t("auth.loginSubmitting") : t("auth.loginSubmit")}
          </button>
        </form>
        <button type="button" className="admin-btn secondary" onClick={handleYandex}>
          {t("auth.loginYandex")}
        </button>
        <p className="subtitle">
          {t("auth.loginNoAccount")} <Link to="/register">{t("auth.loginRegister")}</Link>
        </p>
      </div>
    </div>
  );
}
