import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/authClient";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const { t } = useTranslation();
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register(email, password, displayName);
      navigate("/");
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : t("auth.registerError"),
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="track-header-row">
        <p className="brand">{t("common.brand")}</p>
        <LanguageSwitcher compact />
      </div>
      <div className="card">
        <h1>{t("auth.registerTitle")}</h1>
        <form onSubmit={handleSubmit}>
          <label>
            {t("auth.registerName")}
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />
          </label>
          <label>
            {t("auth.registerEmail")}
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </label>
          <label>
            {t("auth.registerPassword")}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              minLength={6}
              required
            />
          </label>
          {error ? <p className="admin-error">{error}</p> : null}
          <button type="submit" className="admin-btn" disabled={busy}>
            {busy ? t("auth.registerSubmitting") : t("auth.registerSubmit")}
          </button>
        </form>
        <p className="subtitle">
          {t("auth.registerHasAccount")} <Link to="/login">{t("auth.registerLogin")}</Link>
        </p>
      </div>
    </div>
  );
}
