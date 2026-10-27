import { promises as fs } from "fs";
import path from "path";
import { TerminalSquare, Server, ArrowRight } from "lucide-react";

export default async function ApiExplorer() {
  const filePath = path.join(process.cwd(), "src/data/api.json");
  const fileContents = await fs.readFile(filePath, "utf8");
  const data = JSON.parse(fileContents);
  const endpoints = data.endpoints || [];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight flex items-center gap-3">
          <TerminalSquare className="text-indigo-400" />
          API Explorer
        </h1>
        <p className="text-zinc-400">Interactive documentation for the PRATHAM FastAPI Backend.</p>
      </div>

      <div className="space-y-4">
        {endpoints.map((endpoint: any, idx: number) => {
          const methodColor = 
            endpoint.method === "GET" ? "text-blue-400 bg-blue-500/10 border-blue-500/20" :
            endpoint.method === "POST" ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" :
            endpoint.method === "PUT" ? "text-amber-400 bg-amber-500/10 border-amber-500/20" :
            "text-red-400 bg-red-500/10 border-red-500/20";

          return (
            <div key={idx} className="glass rounded-xl p-4 flex items-center justify-between group hover:bg-white/10 transition-colors cursor-pointer">
              <div className="flex items-center gap-4">
                <span className={`px-3 py-1 rounded-md text-xs font-bold tracking-wider border ${methodColor} w-20 text-center`}>
                  {endpoint.method}
                </span>
                <span className="text-white font-mono text-sm">{endpoint.path || "/"}</span>
              </div>
              <div className="flex items-center gap-4 text-zinc-500 text-sm">
                <span className="flex items-center gap-2">
                  <Server className="w-4 h-4" />
                  {endpoint.file}
                </span>
                <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:text-indigo-400 transition-all transform group-hover:translate-x-1" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
