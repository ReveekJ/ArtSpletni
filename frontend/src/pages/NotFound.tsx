import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="error-page">
      <div className="error-code">{t("notFound.code")}</div>
      <h1>{t("notFound.title")}</h1>
      <p className="subtitle">{t("notFound.subtitle")}</p>
      <p>
        <Link className="back-link" to="/">
          {t("notFound.backHome")}
        </Link>
      </p>
    </div>
  );
}
