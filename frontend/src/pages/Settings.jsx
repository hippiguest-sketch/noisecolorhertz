import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Youtube, Link2, Copy, CheckCircle2, Loader2, Unplug } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { api, CHANNEL_META } from "@/lib/factoryApi";

export default function SettingsPage() {
  const [params] = useSearchParams();
  const [status, setStatus] = useState(null);
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => api.ytStatus().then(setStatus).catch(() => {});
  useEffect(() => {
    load();
    const yt = params.get("yt");
    if (yt === "connected") toast.success("Kanal başarıyla bağlandı 🎉");
    if (yt === "error") toast.error("Bağlantı başarısız — kimlik bilgilerini kontrol edin");
  }, []); // eslint-disable-line

  const save = async () => {
    setSaving(true);
    try {
      await api.ytSettings({ client_id: clientId, client_secret: clientSecret });
      toast.success("OAuth kimlik bilgileri kaydedildi");
      setClientId(""); setClientSecret("");
      load();
    } catch { toast.error("Kayıt başarısız"); } finally { setSaving(false); }
  };

  const connect = async (key) => {
    try {
      const { auth_url } = await api.ytAuthUrl(key);
      window.location.href = auth_url;
    } catch (e) { toast.error(e?.response?.data?.detail || "OAuth yapılandırılmamış"); }
  };
  const disconnect = async (key) => { await api.ytDisconnect(key); toast.success("Bağlantı kesildi"); load(); };
  const copy = (t) => { navigator.clipboard.writeText(t); toast.success("Kopyalandı"); };

  return (
    <div>
      <PageHeader title="YouTube & Settings" subtitle="Kanalları YouTube OAuth ile bağlayın; otomatik yükleme için Google Cloud kimlik bilgileri gerekir." testId="settings-header" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass rounded-2xl p-6" data-testid="oauth-config">
          <div className="flex items-center gap-2 mb-4">
            <Youtube className="h-5 w-5 text-rose-400" />
            <h3 className="font-heading font-semibold text-white">Google OAuth Kimlik Bilgileri</h3>
          </div>
          <div className={`text-xs mb-4 flex items-center gap-2 ${status?.configured ? "text-emerald-400" : "text-amber-400"}`}>
            {status?.configured ? <CheckCircle2 className="h-4 w-4" /> : <Loader2 className="h-4 w-4" />}
            {status?.configured ? "Yapılandırıldı" : "Henüz yapılandırılmadı"}
          </div>

          <div className="space-y-3">
            <div>
              <Label className="text-xs text-slate-400 mb-1.5 block">Client ID</Label>
              <Input value={clientId} onChange={(e) => setClientId(e.target.value)} placeholder="xxxx.apps.googleusercontent.com" className="bg-white/5 border-white/10 font-mono-x text-xs" data-testid="input-client-id" />
            </div>
            <div>
              <Label className="text-xs text-slate-400 mb-1.5 block">Client Secret</Label>
              <Input type="password" value={clientSecret} onChange={(e) => setClientSecret(e.target.value)} placeholder="GOCSPX-…" className="bg-white/5 border-white/10 font-mono-x text-xs" data-testid="input-client-secret" />
            </div>
            <Button onClick={save} disabled={saving || !clientId || !clientSecret} className="w-full bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold" data-testid="btn-save-oauth">
              {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null} Kaydet
            </Button>
          </div>

          <div className="mt-5 pt-4 border-t border-white/8">
            <Label className="text-[11px] text-slate-500 uppercase font-mono-x">Redirect URI (Google Console'a ekleyin)</Label>
            <div className="flex items-center gap-2 mt-1.5">
              <code className="flex-1 text-[11px] text-slate-300 bg-black/40 rounded-lg px-3 py-2 truncate font-mono-x">{status?.redirect_uri || "PUBLIC_URL not set"}</code>
              <Button size="icon" variant="ghost" onClick={() => copy(status?.redirect_uri || "")} className="h-8 w-8 text-slate-400 hover:bg-white/5"><Copy className="h-4 w-4" /></Button>
            </div>
          </div>
        </div>

        <div className="glass rounded-2xl p-6" data-testid="channel-connections">
          <div className="flex items-center gap-2 mb-4"><Link2 className="h-5 w-5 text-sky-400" /><h3 className="font-heading font-semibold text-white">Kanal Bağlantıları</h3></div>
          <div className="space-y-2.5">
            {(status?.channels || []).map((ch) => {
              const meta = CHANNEL_META[ch.key] || {};
              return (
                <div key={ch.key} className="flex items-center gap-3 p-3.5 rounded-xl bg-white/[0.03] border border-white/8" data-testid={`connect-row-${ch.key}`}>
                  <div className="h-9 w-9 rounded-lg flex items-center justify-center font-mono-x text-[10px] font-bold" style={{ background: `${meta.accent}1a`, color: meta.accent }}>
                    {ch.key.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm text-slate-200">{ch.name}</div>
                    <div className="text-[11px] font-mono-x text-slate-500">{ch.connected ? ch.youtube_channel_id : "not connected"}</div>
                  </div>
                  {ch.connected ? (
                    <Button size="sm" variant="outline" onClick={() => disconnect(ch.key)} className="border-rose-500/20 bg-transparent text-rose-300 hover:bg-rose-500/10" data-testid={`btn-disconnect-${ch.key}`}>
                      <Unplug className="h-3.5 w-3.5 mr-1" /> Kes
                    </Button>
                  ) : (
                    <Button size="sm" onClick={() => connect(ch.key)} disabled={!status?.configured} className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold disabled:opacity-40" data-testid={`btn-connect-${ch.key}`}>
                      Bağlan
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
          <p className="text-[11px] text-slate-500 mt-4 leading-relaxed">
            Google Cloud Console → APIs &amp; Services → Credentials → OAuth Client (Web). YouTube Data API v3 etkin olmalı ve yukarıdaki Redirect URI eklenmelidir. Test modunda kendi kanallarınızı "test users" olarak ekleyin.
          </p>
        </div>
      </div>
    </div>
  );
}
