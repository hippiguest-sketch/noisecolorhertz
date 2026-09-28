import { useEffect, useState } from "react";
import { toast } from "sonner";
import { RefreshCw, Trash2, UploadCloud, Play, Loader2, ExternalLink } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { StatusBadge } from "@/components/StatusBadge";
import { api, CHANNEL_META, mediaUrl, durationTitle } from "@/lib/factoryApi";

const FILTERS = ["all", "queued", "processing", "completed", "failed"];

export default function Pipeline() {
  const [jobs, setJobs] = useState([]);
  const [filter, setFilter] = useState("all");
  const [detail, setDetail] = useState(null);

  const load = () => api.jobs({ limit: 120 }).then(setJobs).catch(() => {});
  useEffect(() => {
    load();
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
  }, []);

  const open = async (id) => { try { setDetail(await api.job(id)); } catch { toast.error("Detay alınamadı"); } };
  const act = async (fn, id, msg) => { try { await fn(id); toast.success(msg); load(); if (detail?.id === id) open(id); } catch (e) { toast.error(e?.response?.data?.detail || "Hata"); } };

  const shown = jobs.filter((j) => filter === "all" || j.status === filter || (filter === "processing" && j.status === "uploading"));

  return (
    <div>
      <PageHeader title="Pipeline Board" subtitle="Canlı üretim kuyruğu: metadata → FFmpeg render → thumbnail → YouTube upload." testId="pipeline-header">
        <Button size="sm" variant="outline" onClick={load} className="border-white/10 bg-transparent text-slate-300 hover:bg-white/5" data-testid="btn-refresh-jobs">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </PageHeader>

      <div className="flex gap-2 mb-5 flex-wrap">
        {FILTERS.map((f) => (
          <button key={f} data-testid={`filter-${f}`} onClick={() => setFilter(f)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium border capitalize transition-colors ${filter === f ? "bg-sky-500/15 text-sky-300 border-sky-500/30" : "bg-white/[0.03] text-slate-400 border-white/10 hover:bg-white/5"}`}>
            {f}
          </button>
        ))}
      </div>

      <div className="space-y-2.5" data-testid="jobs-list">
        {shown.length === 0 && <div className="glass rounded-xl p-10 text-center text-slate-500 text-sm">Bu filtrede iş yok.</div>}
        {shown.map((j) => {
          const meta = CHANNEL_META[j.channel_key] || {};
          return (
            <div key={j.id} data-testid={`job-row-${j.id}`}
              className="glass rounded-xl p-4 flex items-center gap-4 cursor-pointer" onClick={() => open(j.id)}>
              <div className="h-11 w-11 rounded-lg flex items-center justify-center shrink-0 font-mono-x text-xs font-bold"
                style={{ background: `${meta.accent}1a`, color: meta.accent }}>
                {j.variant_label?.slice(0, 2).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm text-white font-medium truncate">{j.title || j.variant_label}</span>
                </div>
                <div className="flex items-center gap-2.5 text-[11px] text-slate-500 font-mono-x">
                  <span style={{ color: meta.accent }}>{j.channel_key}</span>
                  <span>·</span><span>{durationTitle(j.duration_minutes)}</span>
                  <span>·</span><span>{j.format}</span>
                  {j.youtube_video_id && <><span>·</span><span className="text-emerald-400">YT ✓</span></>}
                </div>
              </div>
              <div className="w-28 hidden sm:block">
                <Progress value={j.progress || 0} className="h-1.5 bg-white/5" />
                <div className="text-[10px] text-slate-500 font-mono-x mt-1 text-right">{j.stage}</div>
              </div>
              <StatusBadge status={j.status} testId={`job-status-badge-${j.id}`} />
            </div>
          );
        })}
      </div>

      <Dialog open={!!detail} onOpenChange={(o) => !o && setDetail(null)}>
        <DialogContent className="glass border-white/10 max-w-2xl max-h-[88vh] overflow-y-auto" data-testid="job-detail-modal">
          {detail && (
            <>
              <DialogHeader>
                <DialogTitle className="font-heading text-white text-lg pr-6 leading-snug">{detail.title}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="flex items-center gap-2 flex-wrap">
                  <StatusBadge status={detail.status} />
                  <span className="text-[11px] font-mono-x text-slate-400">{detail.channel_key} · {detail.variant_label} · {durationTitle(detail.duration_minutes)} · {detail.format}</span>
                </div>

                {detail.video_path && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <div className="text-[11px] text-slate-500 uppercase font-mono-x mb-1.5">Video (preview)</div>
                      <video key={detail.id} controls className="w-full rounded-lg border border-white/10 bg-black" data-testid="job-video-preview">
                        <source src={mediaUrl(detail.id, "video")} type="video/mp4" />
                      </video>
                    </div>
                    <div>
                      <div className="text-[11px] text-slate-500 uppercase font-mono-x mb-1.5">Thumbnail</div>
                      <img src={mediaUrl(detail.id, "thumb")} alt="thumb" className="w-full rounded-lg border border-white/10" data-testid="job-thumb-preview" />
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-[11px] text-slate-500 uppercase font-mono-x mb-1">Açıklama</div>
                  <p className="text-xs text-slate-400 leading-relaxed max-h-36 overflow-y-auto whitespace-pre-wrap">{detail.description}</p>
                </div>
                <div>
                  <div className="text-[11px] text-slate-500 uppercase font-mono-x mb-2">Etiketler</div>
                  <div className="flex flex-wrap gap-1.5">
                    {(detail.tags || []).map((t, i) => <span key={i} className="text-[11px] px-2 py-0.5 rounded-md bg-white/5 text-slate-300 border border-white/10">{t}</span>)}
                  </div>
                </div>
                {detail.error && <div className="text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 rounded-lg p-3">{detail.error}</div>}

                {detail.logs?.length > 0 && (
                  <div className="terminal rounded-lg p-3 max-h-32 overflow-y-auto">
                    {detail.logs.map((l, i) => <div key={i} className="text-[11px] text-emerald-400/90">{l.t?.slice(11, 19)} · {l.msg}</div>)}
                  </div>
                )}

                <div className="flex gap-2 pt-1">
                  {detail.status === "failed" && (
                    <Button size="sm" onClick={() => act(api.retryJob, detail.id, "Yeniden kuyruğa alındı")} className="bg-sky-500 hover:bg-sky-400 text-slate-950" data-testid="btn-retry">
                      <Play className="h-3.5 w-3.5 mr-1" /> Retry
                    </Button>
                  )}
                  {detail.status === "completed" && !detail.youtube_video_id && (
                    <Button size="sm" onClick={() => act(api.uploadJob, detail.id, "YouTube'a yüklendi")} className="bg-emerald-500 hover:bg-emerald-400 text-slate-950" data-testid="btn-upload">
                      <UploadCloud className="h-3.5 w-3.5 mr-1" /> YouTube'a Yükle
                    </Button>
                  )}
                  {detail.youtube_video_id && (
                    <a href={`https://youtube.com/watch?v=${detail.youtube_video_id}`} target="_blank" rel="noreferrer">
                      <Button size="sm" variant="outline" className="border-white/10 bg-transparent text-slate-300"><ExternalLink className="h-3.5 w-3.5 mr-1" /> YouTube</Button>
                    </a>
                  )}
                  <Button size="sm" variant="outline" onClick={() => act(api.deleteJob, detail.id, "Silindi") || setDetail(null)} className="border-rose-500/20 bg-transparent text-rose-300 hover:bg-rose-500/10 ml-auto" data-testid="btn-delete">
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
