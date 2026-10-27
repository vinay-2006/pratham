import { promises as fs } from "fs";
import path from "path";
import { Database, TableProperties } from "lucide-react";

export default async function DatabaseExplorer() {
  const filePath = path.join(process.cwd(), "src/data/database.json");
  let tables = [];
  try {
    const fileContents = await fs.readFile(filePath, "utf8");
    const data = JSON.parse(fileContents);
    tables = data.tables || [];
  } catch (e) {
    console.error("Could not load database.json", e);
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-white mb-2 tracking-tight flex items-center gap-3">
          <Database className="text-indigo-400" />
          Database Atlas
        </h1>
        <p className="text-zinc-400">Prisma Studio-like view of the PRATHAM Supabase schema.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tables.map((table: any, idx: number) => (
          <div key={idx} className="glass rounded-xl p-5 hover:border-indigo-500/50 transition-colors group cursor-pointer">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <TableProperties className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h3 className="text-white font-semibold tracking-wide">{table.name}</h3>
                <p className="text-xs text-zinc-500">{table.migration_file}</p>
              </div>
            </div>
            
            <div className="space-y-2 mt-4 pt-4 border-t border-white/5">
              <div className="text-xs text-zinc-400 flex justify-between">
                <span>Columns</span>
                <span className="text-white font-medium">{table.columns?.length || "Unknown"}</span>
              </div>
              <div className="text-xs text-zinc-400 flex justify-between">
                <span>Relationships</span>
                <span className="text-white font-medium">Mapped</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
