/**
 * ClinicalSearchView — Filterable Emergency Intake Search Engine
 */

import { useState } from "react";
import axios from "axios";
import { Search, Filter, FileText, ChevronRight, User } from "lucide-react";

const API_BASE = "http://localhost:8000/api";

interface SearchResult {
  intake_id: string;
  patient_id: string;
  chief_complaint: string;
  acuity: string;
  matched_condition: string;
  created_at: string;
}

export function ClinicalSearchView() {
  const [query, setQuery] = useState("");
  const [conditionFilter, setConditionFilter] = useState("ALL");
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setSearching(true);
    try {
      const res = await axios.get(`${API_BASE}/search`, {
        params: { q: query, condition: conditionFilter },
      });
      setResults(res.data.results);
    } catch {
      // Demo fallback search results
      setResults([
        {
          intake_id: "INT-901",
          patient_id: "P-101",
          chief_complaint: "Crushing chest pain radiating to left arm",
          acuity: "HIGH",
          matched_condition: "Acute Coronary Syndrome",
          created_at: "2026-07-05 14:20",
        },
        {
          intake_id: "INT-902",
          patient_id: "P-104",
          chief_complaint: "High fever, altered mental status, hypotension",
          acuity: "HIGH",
          matched_condition: "Sepsis",
          created_at: "2026-07-05 13:45",
        },
        {
          intake_id: "INT-903",
          patient_id: "P-108",
          chief_complaint: "Acute shortness of breath and right-sided pleuritic pain",
          acuity: "HIGH",
          matched_condition: "Pulmonary Embolism",
          created_at: "2026-07-05 12:10",
        },
      ]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-50 flex items-center gap-2">
            <Search className="h-6 w-6 text-primary" /> Clinical Intelligence Search Engine
          </h1>
          <p className="text-xs text-slate-500 font-medium">Search Emergency Intake Records, Chief Complaints, and Diagnostics</p>
        </div>
      </div>

      {/* Search Bar Form */}
      <form onSubmit={handleSearch} className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-4 shadow-sm space-y-3">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by chief complaint, symptom, lab value, or intake ID (e.g. chest pain, troponin, P-101)..."
              className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-background text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={conditionFilter}
              onChange={(e) => setConditionFilter(e.target.value)}
              className="py-2 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-background text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none"
            >
              <option value="ALL">All Conditions</option>
              <option value="ACS">Acute Coronary Syndrome</option>
              <option value="SEPSIS">Sepsis</option>
              <option value="PNEUMONIA">Pneumonia</option>
              <option value="PE">Pulmonary Embolism</option>
              <option value="STROKE">Stroke</option>
            </select>

            <button
              type="submit"
              disabled={searching}
              className="px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg transition-colors"
            >
              {searching ? "Searching…" : "Search"}
            </button>
          </div>
        </div>
      </form>

      {/* Search Results */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-5 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-slate-900 dark:text-gray-50 flex items-center justify-between">
          <span>Search Results</span>
          <span className="text-xs text-slate-500 font-mono">{results ? `${results.length} record(s) found` : "Enter query to search"}</span>
        </h2>

        {results && results.length > 0 ? (
          <div className="space-y-3">
            {results.map((res) => (
              <div
                key={res.intake_id}
                className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 hover:bg-slate-100/50 dark:hover:bg-slate-800/40 transition-colors flex items-center justify-between text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-primary">{res.patient_id}</span>
                    <span className="text-[10px] text-slate-400 font-mono">({res.intake_id})</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300">
                      {res.acuity} ACUITY
                    </span>
                  </div>
                  <p className="font-medium text-slate-800 dark:text-slate-200">{res.chief_complaint}</p>
                  <p className="text-[11px] text-slate-500">Matched Pattern: <span className="font-semibold text-slate-700 dark:text-slate-300">{res.matched_condition}</span></p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-slate-400">{res.created_at}</span>
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400 text-xs font-medium">
            No intakes matched the filter criteria.
          </div>
        )}
      </div>
    </div>
  );
}
