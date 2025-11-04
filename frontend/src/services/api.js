import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.DEV ? "http://localhost:5000" : "",
  timeout: 30000,
});

export const getLcuStatus = async () => {
  const { data } = await api.get("/api/lcu-status");
  return data;
};

export const getSummonerOverview = async (name) => {
  const { data } = await api.get(`/api/summoner/${encodeURIComponent(name)}`);
  return data;
};

export const getMatchHistory = async (name, params = {}) => {
  const { data } = await api.get(
    `/api/match-history/${encodeURIComponent(name)}`,
    {
      params,
    }
  );
  return data;
};

export const getMatchDetail = async (gameId) => {
  const { data } = await api.get(`/api/match/${gameId}`);
  return data;
};

export const getTftHistory = async (name) => {
  const { data } = await api.get(
    `/api/tft/summoner/${encodeURIComponent(name)}`
  );
  return data;
};

export const getLiveGame = async () => {
  const { data } = await api.get("/api/live-game");
  return data;
};

export const postAutoAccept = async () => {
  const { data } = await api.post("/api/auto-accept");
  return data;
};

export const postAutoAnalyze = async () => {
  const { data } = await api.post("/api/auto-analyze");
  return data;
};

export default api;
