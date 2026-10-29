"use client";

import { useCallback, useState } from "react";
import {
  ReactFlow,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange,
  Node,
  Edge,
  Handle,
  Position,
} from "@xyflow/react";
import { motion } from "framer-motion";
import { Activity, Server, Database, Bot, BrainCircuit, FileText } from "lucide-react";

// Define custom node types
const SystemNode = ({ data }: { data: any }) => {
  const Icon = data.icon || Activity;
  const statusColor = 
    data.status === "Active" ? "bg-emerald-500" :
    data.status === "Waiting" ? "bg-amber-500" :
    data.status === "Completed" ? "bg-blue-500" :
    "bg-zinc-500";

  return (
    <motion.div
      whileHover={{ scale: 1.05, boxShadow: "0px 0px 20px rgba(99,102,241,0.4)" }}
      className="px-6 py-4 rounded-xl border border-white/10 bg-black/60 backdrop-blur-xl shadow-2xl text-white min-w-[220px] relative overflow-hidden group cursor-pointer"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      
      <Handle type="target" position={Position.Top} className="!bg-indigo-500 !w-3 !h-3 !border-black" />
      
      <div className="flex items-center gap-4 relative z-10">
        <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
          <Icon className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm tracking-wide">{data.label}</h3>
          <div className="flex items-center gap-2 mt-1.5">
            <div className={`w-2 h-2 rounded-full ${statusColor} ${data.status === "Active" ? "animate-pulse" : ""}`} />
            <span className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium">
              {data.status}
            </span>
          </div>
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-indigo-500 !w-3 !h-3 !border-black" />
    </motion.div>
  );
};

const nodeTypes = {
  system: SystemNode,
};

const initialNodes: Node[] = [
  { id: "1", type: "system", position: { x: 350, y: 50 }, data: { label: "Patient Intake", status: "Completed", icon: Activity } },
  { id: "2", type: "system", position: { x: 350, y: 200 }, data: { label: "FastAPI Backend", status: "Active", icon: Server } },
  { id: "3", type: "system", position: { x: 100, y: 350 }, data: { label: "Supabase DB", status: "Active", icon: Database } },
  { id: "4", type: "system", position: { x: 600, y: 350 }, data: { label: "Clinical NLP", status: "Active", icon: BrainCircuit } },
  { id: "5", type: "system", position: { x: 350, y: 500 }, data: { label: "Risk Engine", status: "Waiting", icon: Activity } },
  { id: "6", type: "system", position: { x: 100, y: 650 }, data: { label: "Imaging AI", status: "Pending", icon: Bot } },
  { id: "7", type: "system", position: { x: 600, y: 650 }, data: { label: "Lab Intelligence", status: "Pending", icon: Bot } },
  { id: "8", type: "system", position: { x: 350, y: 800 }, data: { label: "Aggregation Engine", status: "Pending", icon: BrainCircuit } },
  { id: "9", type: "system", position: { x: 350, y: 950 }, data: { label: "Report Generator", status: "Pending", icon: FileText } },
];

const initialEdges: Edge[] = [
  { id: "e1-2", source: "1", target: "2", animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } },
  { id: "e2-3", source: "2", target: "3", animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } },
  { id: "e2-4", source: "2", target: "4", animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } },
  { id: "e4-5", source: "4", target: "5", animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } },
  { id: "e3-5", source: "3", target: "5", animated: false, style: { stroke: "#3f3f46", strokeWidth: 2 } },
  { id: "e5-6", source: "5", target: "6", animated: false, style: { stroke: "#3f3f46", strokeWidth: 2 } },
  { id: "e5-7", source: "5", target: "7", animated: false, style: { stroke: "#3f3f46", strokeWidth: 2 } },
  { id: "e6-8", source: "6", target: "8", animated: false, style: { stroke: "#3f3f46", strokeWidth: 2 } },
  { id: "e7-8", source: "7", target: "8", animated: false, style: { stroke: "#3f3f46", strokeWidth: 2 } },
  { id: "e8-9", source: "8", target: "9", animated: false, style: { stroke: "#3f3f46", strokeWidth: 2 } },
];

export default function Home() {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [],
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [],
  );

  return (
    <div className="w-full h-[100vh]">
      <div className="absolute top-8 left-8 z-10 max-w-sm pointer-events-none">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Interactive System Map</h1>
          <p className="text-zinc-400 text-sm leading-relaxed">
            Live architectural view of the PRATHAM Emergency Intelligence platform. Hover over any node to view real-time data flows and state transitions.
          </p>
        </motion.div>
      </div>
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        className="bg-transparent"
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background color="#3f3f46" gap={24} size={2} />
        <Controls className="!bg-black/50 !border-white/10 !backdrop-blur-md fill-white" />
      </ReactFlow>
    </div>
  );
}
