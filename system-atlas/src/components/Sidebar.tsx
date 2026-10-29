"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Network, 
  Database, 
  TerminalSquare, 
  Activity, 
  GitCommitHorizontal,
  Bot,
  Route,
  ActivitySquare
} from "lucide-react";

const navigation = [
  { name: "System Map", href: "/", icon: Network },
  { name: "API Explorer", href: "/api-explorer", icon: TerminalSquare },
  { name: "Database Atlas", href: "/database", icon: Database },
  { name: "Data Flow Explorer", href: "/data-flow", icon: Route },
  { name: "State Machine", href: "/state-machine", icon: Activity },
  { name: "Trace Patient", href: "/trace", icon: ActivitySquare },
  { name: "Decision Explorer", href: "/decision-explorer", icon: GitCommitHorizontal },
  { name: "AI Model Cards", href: "/ai-models", icon: Bot },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="fixed inset-y-0 left-0 w-64 bg-black/40 backdrop-blur-xl border-r border-white/10 p-4 flex flex-col z-50">
      <div className="flex items-center gap-3 px-2 py-4 mb-8">
        <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/50 flex items-center justify-center">
          <Network className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h1 className="font-semibold text-white leading-none tracking-tight text-sm">PRATHAM</h1>
          <p className="text-xs text-indigo-400 mt-1 font-medium tracking-wide">SYSTEM ATLAS</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive 
                  ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.1)]" 
                  : "text-zinc-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-zinc-500"}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-4 border-t border-white/10">
        <div className="glass rounded-xl p-4 text-xs text-zinc-400">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            <span className="font-medium text-emerald-400">Atlas Live Status</span>
          </div>
          Connected to PRATHAM Core
        </div>
      </div>
    </div>
  );
}
