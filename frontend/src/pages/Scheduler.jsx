import { useEffect, useState } from "react";
import { toast } from "sonner";
import { CalendarClock, Plus, Play, Trash2, Power } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, CHANNEL_META, durationTitle } from "@/lib/factoryApi";

export default function Scheduler() {
  const [presets, setPresets] = useState(null);
  const [schedules, setSchedules] = useState([]);
  const [channel, setChannel] = useState("noadsNoise");
  const [variant, setVariant] = useState("");
  const [duration, setDuration] = useState("");
  const [time, setTime] = useState("09:00");

  const load = () => api.schedules().then(setSchedules).catch(() => {});
  useEffect(() => { api.presets().then(setPresets); load(); }, []);
  useEffect(() => {
    if (!presets) return;
    setVariant(presets[channel].variants[0]?.key || "");
    setDuration(String(presets[channel].durations[0] || ""));
  }, [channel, presets]);

  const add = async () => {
    try {
      await api.createSchedule({ channel_key: channel, time_slot: time, variant, duration_minutes: parseInt(duration, 10), enabled: true });
      toast.success("Zamanlama eklendi");
      load();
    } catch { toast.error("Hata"); }
  };
  const run = async (id) => { try { await api.runSchedule(id); toast.success("Şimdi çalıştırıldı — kuyruğa alındı"); } catch { toast.error("Hata"); } };
  const toggle = async (id) => { await api.toggleSchedule(id); load(); };
  const del = async (id) => { await api.deleteSchedule(id); load(); };

  if (!presets) return null;
  const p = presets[channel];

  return (
    <div>
      <PageHeader title="Automation Scheduler" subtitle="Otomatik üretim zaman dilimleri. Her slot seçilen kanal/varyant/süre için iş oluşturur." testId="scheduler-header" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass rounded-2xl p-6" data-testid="schedule-form">
          <div className="flex items-center gap-2 mb-5"><CalendarClock className="h-5 w-5 text-sky-400" /><h3 className="font-heading font-semibold text-white">Yeni Slot</h3></div>
          <div className="space-y-4">
            <div>
              <Label className="text-xs text-slate-400 mb-2 block">Kanal</Label>
              <Select value={channel} onValueChange={setChannel}>
                <SelectTrigger data-testid="sched-channel" className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                <SelectContent>{Object.keys(presets).map((k) => <SelectItem key={k} value={k}>{k}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs text-slate-400 mb-2 block">Varyant</Label>
                <Select value={variant} onValueChange={setVariant}>
                  <SelectTrigger data-testid="sched-variant" className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                  <SelectContent>{p.variants.map((v) => <SelectItem key={v.key} value={v.key}>{v.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs text-slate-400 mb-2 block">Süre</Label>
                <Select value={duration} onValueChange={setDuration}>
                  <SelectTrigger data-testid="sched-duration" className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                  <SelectContent>{p.durations.map((d) => <SelectItem key={d} value={String(d)}>{durationTitle(d)}</SelectItem>)}</SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label className="text-xs text-slate-400 mb-2 block">Saat</Label>
              <Input type="time" value={time} onChange={(e) => setTime(e.target.value)} data-testid="sched-time" className="bg-white/5 border-white/10" />
            </div>
            <Button onClick={add} className="w-full bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold" data-testid="btn-add-schedule">
              <Plus className="h-4 w-4 mr-1" /> Slot Ekle
            </Button>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-2.5" data-testid="schedule-list">
          {schedules.length === 0 && <div className="glass rounded-2xl p-10 text-center text-slate-500 text-sm">Henüz zamanlama yok.</div>}
          {schedules.map((s) => {
            const meta = CHANNEL_META[s.channel_key] || {};
            return (
              <div key={s.id} className="glass rounded-xl p-4 flex items-center gap-4" data-testid={`schedule-row-${s.id}`}>
                <div className="font-mono-x text-xl font-bold text-white w-16">{s.time_slot}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-200">{s.variant} · {durationTitle(s.duration_minutes)}</span>
                  </div>
                  <span className="text-[11px] font-mono-x" style={{ color: meta.accent }}>{s.channel_key}</span>
                </div>
                <span className={`text-[10px] px-2 py-1 rounded-md border font-mono-x uppercase ${s.enabled ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" : "bg-slate-500/10 text-slate-400 border-slate-500/20"}`}>
                  {s.enabled ? "active" : "paused"}
                </span>
                <div className="flex gap-1.5">
                  <Button size="icon" variant="ghost" onClick={() => run(s.id)} className="h-8 w-8 text-sky-400 hover:bg-sky-500/10" data-testid={`btn-run-${s.id}`}><Play className="h-4 w-4" /></Button>
                  <Button size="icon" variant="ghost" onClick={() => toggle(s.id)} className="h-8 w-8 text-slate-400 hover:bg-white/5"><Power className="h-4 w-4" /></Button>
                  <Button size="icon" variant="ghost" onClick={() => del(s.id)} className="h-8 w-8 text-rose-400 hover:bg-rose-500/10"><Trash2 className="h-4 w-4" /></Button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
