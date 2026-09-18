import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="error-page">
      <div className="error-code">404</div>
      <h1>История не найдена</h1>
      <p className="subtitle">Возможно, метка устарела или трек ещё не опубликован.</p>
      <p>
        <Link className="back-link" to="/">
          На главную
        </Link>
      </p>
    </div>
  );
}
