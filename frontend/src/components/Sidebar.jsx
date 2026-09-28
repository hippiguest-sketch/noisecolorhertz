import { NavLink, useLocation } from "react-router-dom";
import { LayoutDashboard, Grid3x3, Clapperboard, ListVideo, Images, CalendarClock, Terminal, Settings, Radio } from "lucide-react";

const NAV = [
  { to: "/", label: "Command Overview", icon: LayoutDashboard, id: "dashboard", end: true },
  { to: "/matrix", label: "Content Matrix", icon: Grid3x3, id: "matrix" },
  { to: "/studio", label: "Production Studio", icon: Clapperboard, id: "studio" },
  { to: "/pipeline", label: "Pipeline Board", icon: ListVideo, id: "pipeline" },
  { to: "/gallery", label: "Asset Gallery", icon: Images, id: "gallery" },
  { to: "/scheduler", label: "Scheduler", icon: CalendarClock, id: "scheduler" },
  { to: "/logs", label: "Live Logs", icon: Terminal, id: "logs" },
  { to: "/settings", label: "YouTube & Settings", icon: Settings, id: "settings" },
];

export default function Sidebar() {
  useLocation();
  return (
    <aside className="hidden lg:flex fixed left-0 top-0 h-screen w-[264px] flex-col glass border-r border-white/5 z-30" data-testid="sidebar">
      <div className="px-6 py-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-sky-500 via-cyan-400 to-emerald-400 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <Radio className="h-5 w-5 text-slate-950" />
          </div>
          <div>
            <h1 className="font-heading font-extrabold text-[15px] leading-tight tracking-tight text-white">Ambient Factory</h1>
            <p className="text-[11px] text-slate-500 font-mono-x">3 channels · autopilot</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV.map((item) => (
          <NavLink
            key={item.id}
            to={item.to}
            end={item.end}
            data-testid={`nav-${item.id}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive ? "bg-sky-500/15 text-sky-300 border border-sky-500/20" : "text-slate-400 hover:text-slate-100 hover:bg-white/5 border border-transparent"
              }`
            }
          >
            <item.icon className="h-[18px] w-[18px]" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="px-6 py-4 border-t border-white/5">
        <p className="text-[11px] text-slate-500 font-mono-x">noadsNoise · Colors · Hertz</p>
      </div>
    </aside>
  );
}
