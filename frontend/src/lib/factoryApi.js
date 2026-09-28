import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const client = axios.create({ baseURL: API });

export const api = {
  dashboard: () => client.get("/dashboard").then((r) => r.data),
  channels: () => client.get("/channels").then((r) => r.data),
  updateChannel: (key, concept) => client.put(`/channels/${key}`, { concept }).then((r) => r.data),
  presets: () => client.get("/presets").then((r) => r.data),
  matrix: (channel) => client.get(`/matrix`, { params: { channel } }).then((r) => r.data),
  produceCell: (cellId) => client.post(`/matrix/${cellId}/produce`).then((r) => r.data),
  batchProduce: (key, limit = 5) => client.post(`/channels/${key}/batch`, null, { params: { limit } }).then((r) => r.data),
  createJob: (body) => client.post("/jobs", body).then((r) => r.data),
  jobs: (params) => client.get("/jobs", { params }).then((r) => r.data),
  job: (id) => client.get(`/jobs/${id}`).then((r) => r.data),
  retryJob: (id) => client.post(`/jobs/${id}/retry`).then((r) => r.data),
  deleteJob: (id) => client.delete(`/jobs/${id}`).then((r) => r.data),
  uploadJob: (id) => client.post(`/jobs/${id}/upload`).then((r) => r.data),
  gallery: (channel) => client.get("/gallery", { params: { channel } }).then((r) => r.data),
  logs: (params) => client.get("/logs", { params }).then((r) => r.data),
  schedules: () => client.get("/schedules").then((r) => r.data),
  createSchedule: (body) => client.post("/schedules", body).then((r) => r.data),
  toggleSchedule: (id) => client.put(`/schedules/${id}`).then((r) => r.data),
  deleteSchedule: (id) => client.delete(`/schedules/${id}`).then((r) => r.data),
  runSchedule: (id) => client.post(`/schedules/${id}/run`).then((r) => r.data),
  ytStatus: () => client.get("/youtube/status").then((r) => r.data),
  ytSettings: (body) => client.post("/youtube/settings", body).then((r) => r.data),
  ytAuthUrl: (channel) => client.get("/youtube/auth-url", { params: { channel } }).then((r) => r.data),
  ytDisconnect: (key) => client.post(`/channels/${key}/disconnect`).then((r) => r.data),
};

export const mediaUrl = (jobId, kind) => `${API}/media/${jobId}/${kind}`;

export const CHANNEL_META = {
  noadsNoise: { accent: "#38BDF8", ring: "ring-sky-500/30", text: "text-sky-400", chip: "bg-sky-500/10 text-sky-300 border-sky-500/30" },
  Noadscolors: { accent: "#F43F5E", ring: "ring-rose-500/30", text: "text-rose-400", chip: "bg-rose-500/10 text-rose-300 border-rose-500/30" },
  Noadshertz: { accent: "#10B981", ring: "ring-emerald-500/30", text: "text-emerald-400", chip: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
};

export const STATUS_STYLE = {
  queued: "bg-amber-500/10 text-amber-300 border-amber-500/25",
  processing: "bg-blue-500/10 text-blue-300 border-blue-500/25",
  rendering: "bg-purple-500/10 text-purple-300 border-purple-500/25",
  uploading: "bg-cyan-500/10 text-cyan-300 border-cyan-500/25",
  completed: "bg-emerald-500/10 text-emerald-300 border-emerald-500/25",
  failed: "bg-rose-500/10 text-rose-300 border-rose-500/25",
};

export function durationTitle(minutes) {
  if (minutes < 60) return `${minutes} Min`;
  if (minutes === 60) return "1 Hour";
  if (minutes % 60 === 0) return `${minutes / 60} Hours`;
  return `${(minutes / 60).toFixed(1)} Hours`;
}
