import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Clapperboard, Sparkles, Loader2, ArrowRight, Tag } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, CHANNEL_META, durationTitle } from "@/lib/factoryApi";

export default function Studio() {
  const [presets, setPresets] = useState(null);
  const [channel, setChannel] = useState("noadsNoise");
  const [variant, setVariant] = useState("");
  const [duration, setDuration] = useState("");
  const [format, setFormat] = useState("long");
  const [privacy, setPrivacy] = useState("private");
  const [autoUpload, setAutoUpload] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => { api.presets().then(setPresets).catch(() => {}); }, []);
  useEffect(() => {
    if (!presets) return;
    const p = presets[channel];
    setVariant(p.variants[0]?.key || "");
    setDuration(String(p.durations[0] || ""));
  }, [channel, presets]);

  if (!presets) return <div className="text-slate-400 flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Yükleniyor…</div>;
  const p = presets[channel];
  const meta = CHANNEL_META[channel];

  const generate = async () => {
    setBusy(true);
    try {
      const job = await api.createJob({
        channel_key: channel, variant, format,
        duration_minutes: parseInt(duration, 10),
        privacy_status: privacy, auto_upload: autoUpload,
      });
      setResult(job);
      toast.success("Üretim kuyruğa alındı — worker render ediyor");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Üretim başarısız");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader title="Production Studio" subtitle="Kanal, varyant ve süre seçin — FFmpeg videoyu ve thumbnail'i üretsin, SEO metadata otomatik hazırlansın." testId="studio-header" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass rounded-2xl p-6" data-testid="studio-form">
          <div className="flex items-center gap-2 mb-5">
            <Clapperboard className="h-5 w-5" style={{ color: meta.accent }} />
            <h3 className="font-heading font-semibold text-white">Render Ayarları</h3>
          </div>

          <div className="space-y-5">
            <div>
              <Label className="text-xs text-slate-400 mb-2 block">Kanal</Label>
              <Select value={channel} onValueChange={setChannel}>
                <SelectTrigger data-testid="select-channel" className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Object.keys(presets).map((k) => <SelectItem key={k} value={k}>{presets[k].name} — {k}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs text-slate-400 mb-2 block">{p.type === "hz" ? "Frekans" : p.type === "color" ? "Renk" : "Noise türü"}</Label>
                <Select value={variant} onValueChange={setVariant}>
                  <SelectTrigger data-testid="select-variant" className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {p.variants.map((v) => <SelectItem key={v.key} value={v.key}>{v.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs text-slate-400 mb-2 block">Süre</Label>
                <Select value={duration} onValueChange={setDuration}>
                  <SelectTrigger data-testid="select-duration" className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {p.durations.map((d) => <SelectItem key={d} value={String(d)}>{durationTitle(d)}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs text-slate-400 mb-2 block">Format</Label>
                <div className="flex gap-2">
                  {["long", "short"].map((f) => (
                    <button key={f} data-testid={`format-${f}`} onClick={() => setFormat(f)}
                      className={`flex-1 py-2 rounded-lg text-xs font-medium border transition-colors ${format === f ? "text-slate-950" : "bg-white/5 border-white/10 text-slate-300"}`}
                      style={format === f ? { background: meta.accent, borderColor: meta.accent } : {}}>
                      {f === "long" ? "16:9 Long" : "9:16 Short"}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <Label className="text-xs text-slate-400 mb-2 block">Gizlilik</Label>
                <Select value={privacy} onValueChange={setPrivacy}>
                  <SelectTrigger data-testid="select-privacy" className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="private">Private</SelectItem>
                    <SelectItem value="unlisted">Unlisted</SelectItem>
                    <SelectItem value="public">Public</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-white/[0.03] border border-white/8">
              <div>
                <Label className="text-sm text-slate-200">Render sonrası YouTube'a yükle</Label>
                <p className="text-[11px] text-slate-500 mt-0.5">Kanal bağlıysa otomatik yükleme yapar</p>
              </div>
              <Switch checked={autoUpload} onCheckedChange={setAutoUpload} data-testid="switch-auto-upload" />
            </div>

            <Button onClick={generate} disabled={busy || !variant || !duration} data-testid="btn-generate-now"
              className="w-full bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold h-11">
              {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Sparkles className="h-4 w-4 mr-2" />}
              Şimdi Üret
            </Button>
          </div>
        </div>

        <div className="glass rounded-2xl p-6" data-testid="studio-preview">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-heading font-semibold text-white">SEO Önizleme</h3>
            {result && <Link to="/pipeline" className="text-xs text-sky-400 flex items-center gap-1">Pipeline <ArrowRight className="h-3 w-3" /></Link>}
          </div>
          {!result ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-16 text-slate-500">
              <Clapperboard className="h-10 w-10 mb-3 opacity-40" />
              <p className="text-sm">Üretim başlattığınızda başlık, açıklama ve etiketler burada görünecek.</p>
            </div>
          ) : (
            <div className="space-y-4" data-testid="seo-result">
              <div>
                <div className="text-[11px] text-slate-500 uppercase font-mono-x mb-1">Başlık</div>
                <p className="text-sm text-white font-medium leading-snug">{result.title}</p>
              </div>
              <div>
                <div className="text-[11px] text-slate-500 uppercase font-mono-x mb-1">Açıklama</div>
                <p className="text-xs text-slate-400 leading-relaxed max-h-40 overflow-y-auto whitespace-pre-wrap">{result.description}</p>
              </div>
              <div>
                <div className="text-[11px] text-slate-500 uppercase font-mono-x mb-2 flex items-center gap-1"><Tag className="h-3 w-3" /> Etiketler ({result.tags?.length})</div>
                <div className="flex flex-wrap gap-1.5">
                  {(result.tags || []).map((t, i) => (
                    <span key={i} className="text-[11px] px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-300 border border-sky-500/20">{t}</span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
