import { useEffect, useState } from "react";
import { Images, ExternalLink } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { api, CHANNEL_META, mediaUrl } from "@/lib/factoryApi";

export default function Gallery() {
  const [items, setItems] = useState([]);
  useEffect(() => {
    const load = () => api.gallery().then(setItems).catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div>
      <PageHeader title="Asset Gallery" subtitle="Üretilen thumbnail'ler ve video önizlemeleri." testId="gallery-header" />
      {items.length === 0 ? (
        <div className="glass rounded-2xl p-16 text-center text-slate-500">
          <Images className="h-10 w-10 mx-auto mb-3 opacity-40" />
          <p className="text-sm">Henüz üretilmiş varlık yok. Studio'dan bir video üretin.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4" data-testid="gallery-grid">
          {items.map((j) => {
            const meta = CHANNEL_META[j.channel_key] || {};
            return (
              <div key={j.id} className="glass rounded-xl overflow-hidden group" data-testid={`gallery-item-${j.id}`}>
                <div className="relative aspect-video bg-black overflow-hidden">
                  <img src={mediaUrl(j.id, "thumb")} alt={j.title} className="w-full h-full object-cover group-hover:opacity-0 transition-opacity duration-300" />
                  <video muted loop className="absolute inset-0 w-full h-full object-cover opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    onMouseEnter={(e) => e.target.play()} onMouseLeave={(e) => e.target.pause()}>
                    <source src={mediaUrl(j.id, "video")} type="video/mp4" />
                  </video>
                </div>
                <div className="p-3">
                  <span className="text-[10px] px-2 py-0.5 rounded-md border font-mono-x" style={{ background: `${meta.accent}1a`, color: meta.accent, borderColor: `${meta.accent}33` }}>
                    {j.channel_key}
                  </span>
                  <p className="text-xs text-slate-300 mt-2 line-clamp-2 leading-snug">{j.title}</p>
                  {j.youtube_video_id && (
                    <a href={`https://youtube.com/watch?v=${j.youtube_video_id}`} target="_blank" rel="noreferrer"
                      className="text-[11px] text-emerald-400 flex items-center gap-1 mt-1.5">
                      <ExternalLink className="h-3 w-3" /> YouTube
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
