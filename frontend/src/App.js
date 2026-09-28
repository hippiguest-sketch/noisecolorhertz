import { useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Sidebar from "@/components/Sidebar";
import Dashboard from "@/pages/Dashboard";
import Matrix from "@/pages/Matrix";
import Studio from "@/pages/Studio";
import Pipeline from "@/pages/Pipeline";
import Gallery from "@/pages/Gallery";
import Scheduler from "@/pages/Scheduler";
import Logs from "@/pages/Logs";
import SettingsPage from "@/pages/Settings";

function Shell({ children }) {
  return (
    <div className="app-bg">
      <Sidebar />
      <main className="lg:pl-[264px] min-h-screen grid-lines">
        <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-6 sm:py-8">{children}</div>
      </main>
    </div>
  );
}

function App() {
  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);
  return (
    <BrowserRouter>
      <Shell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/matrix" element={<Matrix />} />
          <Route path="/studio" element={<Studio />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/scheduler" element={<Scheduler />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Shell>
      <Toaster position="top-right" theme="dark" richColors />
    </BrowserRouter>
  );
}

export default App;
