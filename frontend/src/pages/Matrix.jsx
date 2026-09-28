import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, Check, Plus, Clock3 } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { api, CHANNEL_META, durationTitle } from "@/lib/factoryApi";

const CHANNELS = ["noadsNoise", "Noadscolors", "Noadshertz"];

export default function Matrix() {
  const [params, setParams] = useSearchParams();
  const active = CHANNELS.includes(params.get("channel")) ? params.get("channel") : "noadsNoise";
  const [cells, setCells] = useState([]);
  const [busy, setBusy] = useState(null);

  const load = (ch) => api.matrix(ch).then(setCells).catch(() => {});
  useEffect(() => {
    load(active);
    const t = setInterval(() => load(active), 4000);
    return () => clearInterval(t);
  }, [active]);

  const meta = CHANNEL_META[active];
  const variants = [...new Map(cells.map((c) => [c.variant, c.variant_label])).entries()];
  const durations = [...new Set(cells.map((c) => c.duration_minutes))].sort((a, b) => a - b);
  const lookup = {};
  cells.forEach((c) => { lookup[`${c.variant}_${c.duration_minutes}`] = c; });

  const filled = cells.filter((c) => c.status === "filled").length;

  const produce = async (cell) => {
    setBusy(cell.id);
    try {
      await api.produceCell(cell.id);
      toast.success(`${cell.variant_label} · ${durationTitle(cell.duration_minutes)} kuyruğa alındı`);
      load(active);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Hata");
    } finally {
      setBusy(null);
    }
  };

  const cellUi = (cell) => {
    if (!cell) return <div className="h-9 rounded-md bg-white/[0.02]" />;
    const id = `matrix-cell-${cell.variant}-${cell.duration_minutes}`;
    if (cell.status === "filled")
      return <div data-testid={id} className="h-9 rounded-md bg-emerald-500/12 border border-emerald-500/25 flex items-center justify-center text-emerald-300"><Check className="h-4 w-4" /></div>;
    if (cell.status === "producing")
      return <div data-testid={id} className="h-9 rounded-md bg-blue-500/12 border border-blue-500/25 flex items-center justify-center text-blue-300"><Loader2 className="h-4 w-4 animate-spin" /></div>;
    return (
      <button data-testid={id} onClick={() => produce(cell)} disabled={busy === cell.id}
        className="h-9 w-full rounded-md bg-white/[0.03] border border-white/8 hover:border-sky-500/40 hover:bg-sky-500/10 flex items-center justify-center text-slate-500 hover:text-sky-300 transition-colors">
        {busy === cell.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
      </button>
    );
  };

  return (
    <div>
      <PageHeader title="Content Matrix" subtitle="Renk/Noise × Süre kombinasyonları. Eksik hücrelere tıklayarak tek tıkla üretim başlatın." testId="matrix-header" />

      <div className="flex flex-wrap gap-2 mb-6">
        {CHANNELS.map((ch) => (
          <button key={ch} data-testid={`matrix-tab-${ch}`} onClick={() => setParams({ channel: ch })}
            className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${active === ch ? "text-slate-950" : "text-slate-300 bg-white/[0.03] border-white/10 hover:bg-white/5"}`}
            style={active === ch ? { background: CHANNEL_META[ch].accent, borderColor: CHANNEL_META[ch].accent } : {}}>
            {ch}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2 text-xs text-slate-400 font-mono-x">
          <Clock3 className="h-4 w-4" /> {filled}/{cells.length} filled
        </div>
      </div>

      <div className="glass rounded-2xl p-4 sm:p-6 overflow-x-auto" data-testid="matrix-grid">
        <div className="min-w-[640px]">
          <div className="grid gap-2 mb-2" style={{ gridTemplateColumns: `140px repeat(${durations.length}, 1fr)` }}>
            <div className="text-[11px] font-mono-x text-slate-500 uppercase px-1">Variant \\ Duration</div>
            {durations.map((d) => (
              <div key={d} className="text-[11px] font-mono-x text-center font-semibold uppercase" style={{ color: meta.accent }}>
                {durationTitle(d)}
              </div>
            ))}
          </div>
          {variants.map(([vkey, vlabel]) => (
            <div key={vkey} className="grid gap-2 mb-2 items-center" style={{ gridTemplateColumns: `140px repeat(${durations.length}, 1fr)` }}>
              <div className="text-sm font-medium text-slate-200 px-1 truncate">{vlabel}</div>
              {durations.map((d) => <div key={d}>{cellUi(lookup[`${vkey}_${d}`])}</div>)}
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-4 mt-4 text-[11px] text-slate-400 font-mono-x">
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-emerald-500/25 border border-emerald-500/40" /> filled</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-blue-500/25 border border-blue-500/40" /> producing</span>
        <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-white/5 border border-white/15" /> missing (click to produce)</span>
      </div>
    </div>
  );
}
