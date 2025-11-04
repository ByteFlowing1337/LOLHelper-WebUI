import { Routes, Route, Navigate } from "react-router-dom";
import HomePage from "./pages/HomePage";
import MatchDetailPage from "./pages/MatchDetailPage";
import LiveGamePage from "./pages/LiveGamePage";
import TFTSummonerPage from "./pages/TFTSummonerPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/match/:summonerName" element={<MatchDetailPage />} />
      <Route path="/live" element={<LiveGamePage />} />
      <Route path="/tft/:summonerName" element={<TFTSummonerPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
