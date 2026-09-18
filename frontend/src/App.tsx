import { Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import TrackPage from "./pages/TrackPage";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/t/:slug" element={<TrackPage />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
