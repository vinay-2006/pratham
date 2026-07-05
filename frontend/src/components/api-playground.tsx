/**
 * APIPlayground — Interactive Clinical API Explorer
 * Triggers actual backend endpoint runs and pairs JSON responses with visual previews.
 */

import { useState } from "react";
import axios from "axios";
import { Terminal, Send, Eye, Code, Activity, ShieldCheck } from "lucide-react";

interface Endpoint {
  name: string;
  method: "GET" | "POST";
  path: string;
  payload: string;
  description: string;
}

const ENDPOINTS: Endpoint[] = [
  {
    name: "Submit Intake",
    method: "POST",
    path: "/intake",
    payload: JSON.stringify({
      first_name: "Emma",
      last_name: "Smith",
      gender: "female",
      date_of_birth: "1985-04-12",
      chief_complaint: "Substernal pressure chest pain radiating to left shoulder and severe shortness of breath.",
      hr: 110,
      bp: "100/60",
      spo2: 91,
      rr: 22,
      temp: 37.1
    }, null, 2),
    description: "Submit patient demographics, vitals, and chief complaint to trigger triage NLP extraction."
  },
  {
    name: "System Telemetry Metrics",
    method: "GET",
    path: "/metrics",
    payload: "",
    description: "Query operational pipeline execution times and total patient counts."
  },
  {
    name: "Release Information",
    method: "GET",
    path: "/api/release",
    payload: "",
    description: "Get active version information, build tags, and Git commit hashes."
  }
];

export function APIPlayground() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<Endpoint>(ENDPOINTS[0]);
  const [payloadStr, setPayloadStr] = useState(ENDPOINTS[0].payload);
  const [response, setResponse] = useState<any>(null);
  const [execTime, setExecTime] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<"json" | "visual">("json");

  const handleSelect = (ep: Endpoint) => {
    setSelectedEndpoint(ep);
    setPayloadStr(ep.payload);
    setResponse(null);
    setExecTime(null);
  };

  const handleExecute = async () => {
    setLoading(true);
    setResponse(null);
    const start = performance.now();
    try {
      let res;
      const url = `http://localhost:8000${selectedEndpoint.path}`;
      if (selectedEndpoint.method === "POST") {
        res = await axios.post(url, JSON.parse(payloadStr));
      } else {
        res = await axios.get(url);
      }
      setResponse(res.data);
    } catch (err: any) {
      setResponse(err.response?.data || { error: err.message });
    } finally {
      setExecTime(Math.round(performance.now() - start));
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto bg-background text-foreground p-6">
      
      {/* Selector and Payload Inputs */}
      <div className="lg:col-span-5 space-y-4">
        <div>
          <h3 className="text-base font-bold flex items-center gap-2">
            <Terminal className="h-5 w-5 text-primary" /> Clinical API Explorer
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">Test real API requests directly in the client playground.</p>
        </div>

        {/* Endpoints List */}
        <div className="space-y-1">
          {ENDPOINTS.map((ep, i) => (
            <button
              key={i}
              onClick={() => handleSelect(ep)}
              className={`w-full p-3 rounded-lg border text-left transition-all ${
                selectedEndpoint.name === ep.name
                  ? "border-primary bg-primary/5 text-primary"
                  : "border-slate-200 dark:border-slate-800 bg-card hover:border-slate-300 dark:hover:border-slate-700"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                  ep.method === "POST" ? "bg-amber-500/10 text-amber-500" : "bg-emerald-500/10 text-emerald-500"
                }`}>
                  {ep.method}
                </span>
                <span className="font-bold text-xs">{ep.name}</span>
              </div>
              <p className="text-[9px] text-slate-400 font-mono mt-1">{ep.path}</p>
            </button>
          ))}
        </div>

        {/* Payload Editor */}
        {selectedEndpoint.method === "POST" && (
          <div className="space-y-1.5">
            <h5 className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Request Payload (JSON)</h5>
            <textarea
              value={payloadStr}
              onChange={(e) => setPayloadStr(e.target.value)}
              className="w-full h-44 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-900 text-slate-100 font-mono text-xs p-4 focus:border-primary focus:outline-none"
            />
          </div>
        )}

        <button
          onClick={handleExecute}
          disabled={loading}
          className="w-full py-2.5 bg-primary hover:bg-primary/95 text-white font-bold text-xs rounded-xl shadow-lg shadow-primary/20 flex items-center justify-center gap-1.5 transition-all"
        >
          <Send className="h-4 w-4" /> {loading ? "Executing request..." : "Send Request"}
        </button>
      </div>

      {/* Response Panel */}
      <div className="lg:col-span-7 bg-card border border-slate-200 dark:border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
        <div className="space-y-4">
          <div className="flex justify-between items-center border-b pb-3 border-slate-100 dark:border-slate-800">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Activity className="h-4 w-4 text-primary" /> API Response
            </h4>

            {response && (
              <div className="flex bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200/50 dark:border-slate-800/50">
                <button
                  onClick={() => setViewMode("json")}
                  className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${
                    viewMode === "json" ? "bg-card shadow-sm text-primary" : "text-slate-400"
                  }`}
                >
                  <Code className="h-3 w-3 inline mr-1" /> Raw JSON
                </button>
                <button
                  onClick={() => setViewMode("visual")}
                  className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${
                    viewMode === "visual" ? "bg-card shadow-sm text-primary" : "text-slate-400"
                  }`}
                >
                  <Eye className="h-3 w-3 inline mr-1" /> UI Preview
                </button>
              </div>
            )}
          </div>

          {!response ? (
            <div className="py-24 text-center text-xs text-slate-400 font-medium">
              Click "Send Request" to invoke the live endpoint and view results.
            </div>
          ) : viewMode === "json" ? (
            <pre className="p-4 rounded-xl bg-slate-900 text-slate-100 font-mono text-xs overflow-x-auto max-h-96 leading-relaxed">
              {JSON.stringify(response, null, 2)}
            </pre>
          ) : (
            /* Visual Previews */
            <div className="space-y-4 pt-2">
              {selectedEndpoint.name === "Submit Intake" && response.patient_id && (
                <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 space-y-3">
                  <div className="flex items-center gap-2 text-emerald-500">
                    <ShieldCheck className="h-5 w-5" />
                    <h5 className="font-bold text-xs">Patient Intake Log Ingested</h5>
                  </div>
                  <div className="grid grid-cols-2 gap-y-2 text-[11px] pt-1 border-t border-emerald-500/10">
                    <span className="text-slate-400">Intake Key:</span>
                    <span className="font-mono text-right">{response.intake_id}</span>
                    <span className="text-slate-400">Patient ID:</span>
                    <span className="font-mono text-right">{response.patient_id}</span>
                  </div>
                </div>
              )}

              {selectedEndpoint.name === "System Telemetry Metrics" && (
                <div className="space-y-4">
                  <h5 className="font-bold text-xs">Dynamic Code Statistics</h5>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <span className="text-[10px] text-slate-400 font-bold block">SERVICES</span>
                      <span className="text-sm font-bold block mt-0.5">{response.codebase_stats?.backend_services_count} files</span>
                    </div>
                    <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <span className="text-[10px] text-slate-400 font-bold block">COMPONENTS</span>
                      <span className="text-sm font-bold block mt-0.5">{response.codebase_stats?.react_components_count} modules</span>
                    </div>
                  </div>
                </div>
              )}

              {selectedEndpoint.name === "Release Information" && (
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 space-y-3">
                  <h5 className="font-bold text-xs">{response.project} {response.version}</h5>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    Commit Tag: <code className="font-mono">{response.git_commit}</code> · Status: {response.release_status}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {execTime !== null && (
          <div className="border-t pt-4 border-slate-100 dark:border-slate-800 text-[10px] text-slate-400 font-mono flex justify-between mt-4">
            <span>Latency: {execTime} ms</span>
            <span>Status: 200 OK</span>
          </div>
        )}
      </div>
    </div>
  );
}
