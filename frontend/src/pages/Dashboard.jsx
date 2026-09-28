import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Radio, Palette, AudioWaveform, Users, Eye, Film, Zap, Clock, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import PageHeader from "@/components/PageHeader";
import { api, CHANNEL_META } from "@/lib/factoryApi";

const ICONS = { noadsNoise: Radio, Noadscolors: Palette, Noadshertz: AudioWaveform };

function StatChip({ icon: Icon, label, value, tone }) {
  return (
    <div className="glass rounded-xl p-4 flex items-center gap-3" data-testid={`total-${label.toLowerCase()}`}>
      <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${tone}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <div className="font-heading text-2xl font-bold text-white leading-none">{value}</div>
        <div className="text-[11px] text-slate-400 mt-1">{label}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);

  const load = () => api.dashboard().then(setData).catch(() => {});
  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  const batch = async (key) => {
    try {
      const r = await api.batchProduce(key, 5);
      toast.success(`${r.queued} video kuyruğa alındı`);
      load();
    } catch (e) {
      toast.error("Batch başarısız");
    }
  };

  const totals = data?.totals || {};
  const num = (n) => (n || 0).toLocaleString();

  return (
    <div>
      <PageHeader
        title="Command Overview"
        subtitle="3 ambiyans kanalının uçtan uca otomatik üretim merkezi — matris, FFmpeg render, SEO ve YouTube yükleme."
        testId="dashboard-header"
      >
        <Link to="/studio"><Button data-testid="btn-open-studio" className="bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold">
          <Zap className="h-4 w-4 mr-1.5" /> Üret
        </Button></Link>
      </PageHeader>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatChip icon={Clock} label="Queued" value={num(totals.queued)} tone="bg-amber-500/15 text-amber-400" />
        <StatChip icon={Loader2} label="Processing" value={num(totals.processing)} tone="bg-blue-500/15 text-blue-400" />
        <StatChip icon={CheckCircle2} label="Completed" value={num(totals.completed)} tone="bg-emerald-500/15 text-emerald-400" />
        <StatChip icon={XCircle} label="Failed" value={num(totals.failed)} tone="bg-rose-500/15 text-rose-400" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {(data?.channels || []).map((ch, i) => {
          const meta = CHANNEL_META[ch.key] || {};
          const Icon = ICONS[ch.key] || Radio;
          const pct = ch.matrix_total ? Math.round((ch.matrix_filled / ch.matrix_total) * 100) : 0;
          return (
            <motion.div
              key={ch.key}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className={`glass rounded-2xl p-6 ring-1 ${meta.ring}`}
              data-testid={`channel-card-${ch.key}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-xl flex items-center justify-center" style={{ background: `${meta.accent}1a`, color: meta.accent }}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-heading font-bold text-white text-lg leading-tight">{ch.name}</h3>
                    <p className="text-[11px] font-mono-x text-slate-500">{ch.handle}</p>
                  </div>
                </div>
                <span className={`text-[10px] px-2 py-1 rounded-md border font-mono-x uppercase ${ch.connected ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" : "bg-slate-500/10 text-slate-400 border-slate-500/20"}`}>
                  {ch.connected ? "connected" : "offline"}
                </span>
              </div>

              <p className="text-xs text-slate-400 leading-relaxed mb-4 min-h-[32px]">{ch.focus}</p>

              <div className="grid grid-cols-3 gap-2 mb-4">
                <div className="text-center py-2 rounded-lg bg-white/[0.03]">
                  <Users className="h-3.5 w-3.5 mx-auto text-slate-500 mb-1" />
                  <div className="text-sm font-semibold text-white">{num(ch.stats?.subscribers)}</div>
                </div>
                <div className="text-center py-2 rounded-lg bg-white/[0.03]">
                  <Eye className="h-3.5 w-3.5 mx-auto text-slate-500 mb-1" />
                  <div className="text-sm font-semibold text-white">{num(ch.stats?.views)}</div>
                </div>
                <div className="text-center py-2 rounded-lg bg-white/[0.03]">
                  <Film className="h-3.5 w-3.5 mx-auto text-slate-500 mb-1" />
                  <div className="text-sm font-semibold text-white">{num(ch.stats?.videos)}</div>
                </div>
              </div>

              <div className="mb-4">
                <div className="flex justify-between text-[11px] mb-1.5">
                  <span className="text-slate-400">Content matrix</span>
                  <span className="font-mono-x" style={{ color: meta.accent }}>{ch.matrix_filled}/{ch.matrix_total} · {pct}%</span>
                </div>
                <Progress value={pct} className="h-1.5 bg-white/5" />
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400 mb-4 font-mono-x">
                <span>▶ {ch.queue?.queued || 0} queued</span>
                <span className="text-blue-300">⟳ {ch.queue?.processing || 0}</span>
                <span className="text-emerald-300">✓ {ch.queue?.completed || 0}</span>
                <span className="text-rose-300">✗ {ch.queue?.failed || 0}</span>
              </div>

              <div className="flex gap-2">
                <Button size="sm" onClick={() => batch(ch.key)} data-testid={`btn-batch-${ch.key}`}
                  className="flex-1 bg-white/5 hover:bg-white/10 text-slate-200 border border-white/10">
                  <Zap className="h-3.5 w-3.5 mr-1" /> Batch 5
                </Button>
                <Link to={`/matrix?channel=${ch.key}`} className="flex-1">
                  <Button size="sm" variant="outline" className="w-full border-white/10 bg-transparent text-slate-300 hover:bg-white/5" data-testid={`btn-matrix-${ch.key}`}>
                    Matrix
                  </Button>
                </Link>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
