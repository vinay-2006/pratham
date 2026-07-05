import { createFileRoute } from "@tanstack/react-router";
import { CopilotAssistantDrawer } from "@/components/copilot-assistant-drawer";
import { useCase } from "@/lib/case-store";
import { useState } from "react";
import { Brain, Sparkles } from "lucide-react";

export const Route = createFileRoute("/_app/copilot")({
  head: () => ({
    meta: [
      { title: "Clinical Copilot — PRATHAM" },
      { name: "description", content: "Interactive Evidence-Aware Clinical & System Assistant." },
    ],
  }),
  component: CopilotPage,
});

function CopilotPage() {
  const { patientCase } = useCase();
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between border-b pb-4 border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-50 flex items-center gap-2">
            <Brain className="h-6 w-6 text-primary" /> PRATHAM Clinical & System Copilot
          </h1>
          <p className="text-xs text-slate-500 font-medium">Interactive Evidence-Grounded Conversational Reasoning Assistant</p>
        </div>
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground font-bold text-xs rounded-xl shadow transition-opacity hover:opacity-90"
        >
          <Sparkles className="h-4 w-4" /> Open Copilot Drawer
        </button>
      </div>

      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-card p-8 text-center space-y-4">
        <Brain className="h-12 w-12 text-primary mx-auto opacity-80" />
        <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Copilot Interactive Workspace</h2>
        <p className="text-xs text-slate-500 max-w-lg mx-auto leading-relaxed">
          Ask natural-language questions about clinical evidence, disease criteria, patient trajectories, or system pipeline health. The Copilot strictly uses evidence-grounded reasoning without hallucinating or prescribing medications.
        </p>
      </div>

      <CopilotAssistantDrawer
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        intakeId={patientCase?.id || "INT-100"}
      />
    </div>
  );
}
