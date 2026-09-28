import { useEffect, useRef, useState } from "react";
import { Terminal } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import { api } from "@/lib/factoryApi";

const LEVEL_COLOR = { INFO: "text-slate-300", SUCCESS: "text-emerald-400", WARN: "text-amber-400", ERROR: "text-rose-400" };

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const boxRef = useRef(null);

  useEffect(() => {
    const load = () => api.logs({ limit: 120 }).then(setLogs).catch(() => {});
    load();
    const t = setInterval(load, 2500);
    return () => clearInterval(t);
  }, []);

  useEffect(() => { if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight; }, [logs]);

  return (
    <div>
      <PageHeader title="Live Logs" subtitle="FFmpeg render, kuyruk ve YouTube API telemetrisi." testId="logs-header">
        <span className="flex items-center gap-2 text-xs text-emerald-400 font-mono-x">
          <span className="h-2 w-2 rounded-full bg-emerald-400 live-dot" /> live
        </span>
      </PageHeader>

      <div ref={boxRef} className="terminal rounded-2xl p-5 h-[calc(100vh-220px)] overflow-y-auto" data-testid="live-log-terminal">
        {logs.length === 0 && <div className="text-slate-600 text-sm">Log bekleniyor…</div>}
        {logs.map((l, i) => (
          <div key={i} className="text-[12px] leading-relaxed" data-testid={`log-entry-${i}`}>
            <span className="text-slate-600">{l.t?.slice(11, 19)}</span>{" "}
            <span className={`${LEVEL_COLOR[l.level] || "text-slate-300"} font-semibold`}>[{l.level}]</span>{" "}
            {l.channel_key && <span className="text-sky-500/70">{l.channel_key} </span>}
            <span className="text-slate-300">{l.msg}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
