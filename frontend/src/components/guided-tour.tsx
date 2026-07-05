/**
 * GuidedTour — Interactive Product Walkthrough Overlay
 * Steps users through the 6 key workspaces of the PRATHAM platform.
 */

import { useState } from "react";
import { HelpCircle, ChevronRight, ChevronLeft, X, Sparkles } from "lucide-react";

interface Step {
  title: string;
  description: string;
  workspace: string;
}

const TOUR_STEPS: Step[] = [
  {
    title: "Welcome to PRATHAM",
    description: "PRATHAM is an emergency department clinical decision-support system. Let's take a 60-second interactive tour of the platform.",
    workspace: "Overview / Welcome"
  },
  {
    title: "Step 1: Patient In-Transit Intake",
    description: "Nurses input vital signs, symptoms, and chief complaints. The Clinical NLP Engine parses unstructured text to flag clinical risks en route.",
    workspace: "Nurse Intake Form"
  },
  {
    title: "Step 2: Doctor Approval Workstation",
    description: "Physicians approve or modify AI-recommended diagnostics (bloods, imaging, ECGs) based on computed NEWS2/qSOFA risk stratification scores.",
    workspace: "Doctor Approvals Desk"
  },
  {
    title: "Step 3: Multi-modal Evidence Uploader",
    description: "Simulate file uploads for Chest X-Rays. The EfficientNetB0 AI Model classifies findings and renders Grad-CAM heatmaps directly in the UI.",
    workspace: "Lab & X-Ray Uploads"
  },
  {
    title: "Step 4: Grounded Clinical Report",
    description: "Review synthesized diagnostic summaries and structured recommendations. Download recruiter-ready audit trail PDFs instantly.",
    workspace: "Patient Clinical Report"
  },
  {
    title: "Step 5: Evidence-Aware Copilot",
    description: "Query details regarding diagnostics, Wells PE score calculations, or database pipeline statistics. View deterministic execution paths in the 'Show Your Work' pane.",
    workspace: "Interactive AI Assistant"
  },
  {
    title: "Step 6: ED Command Center",
    description: "View department-wide metrics: pipeline success counts, average diagnostic latencies, active queues, and system status variables.",
    workspace: "Admin Telemetry Console"
  }
];

export function GuidedTour({ onClose }: { onClose?: () => void }) {
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      if (onClose) onClose();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const step = TOUR_STEPS[currentStep];

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="max-w-md w-full rounded-2xl border border-slate-200 dark:border-slate-800 bg-card p-6 shadow-2xl space-y-6 relative overflow-hidden">
        {/* Decorative corner glow */}
        <div className="absolute -top-10 -right-10 w-32 h-32 bg-primary/20 rounded-full blur-2xl" />

        {/* Header */}
        <div className="flex justify-between items-center relative z-10">
          <span className="text-[10px] font-bold uppercase tracking-wider text-primary px-2.5 py-0.5 rounded-full bg-primary/10 flex items-center gap-1">
            <Sparkles className="h-3 w-3" /> Step {currentStep + 1} of {TOUR_STEPS.length}
          </span>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-2 relative z-10 mt-2">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50">{step.title}</h3>
          <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider text-slate-400">{step.workspace}</p>
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed pt-2">{step.description}</p>
        </div>

        {/* Stepper Progress bar */}
        <div className="flex gap-1.5 h-1 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
          {TOUR_STEPS.map((_, idx) => (
            <div
              key={idx}
              className={`flex-1 h-full rounded-full transition-colors ${
                idx <= currentStep ? "bg-primary" : "bg-transparent"
              }`}
            />
          ))}
        </div>

        {/* Actions */}
        <div className="flex justify-between items-center relative z-10 pt-2">
          <button
            onClick={onClose}
            className="text-xs text-slate-400 hover:text-slate-200 font-bold transition-colors"
          >
            Skip Tour
          </button>

          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <button
                onClick={handleBack}
                className="flex items-center gap-1 px-3 py-1.5 border border-slate-200 dark:border-slate-800 text-xs font-bold rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                <ChevronLeft className="h-4 w-4" /> Back
              </button>
            )}
            <button
              onClick={handleNext}
              className="flex items-center gap-1 px-4 py-2 bg-primary hover:bg-primary/90 text-white text-xs font-bold rounded-lg shadow-lg shadow-primary/20 transition-all"
            >
              {currentStep === TOUR_STEPS.length - 1 ? "Finish" : "Next"} <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
