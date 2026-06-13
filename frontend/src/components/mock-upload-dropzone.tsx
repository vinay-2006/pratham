import { useCallback, useState } from "react";
import { CheckCircle2, Upload as UploadIcon, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function MockUploadDropzone({
  label,
  hint,
  accept,
}: {
  label: string;
  hint?: string;
  accept?: string;
}) {
  const [file, setFile] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const onPick = useCallback(() => {
    // Mock filename
    const samples: Record<string, string> = {
      "X-ray": "chest_xray_PA_20-12.jpg",
      "Lab Reports": "lab_results_serum_20-15.pdf",
      "ECG": "ecg_12lead_20-08.pdf",
      "Notes": "clinical_notes_20-05.txt",
      "Evidence": "evidence_attachment.pdf",
    };
    setFile(samples[label] || "uploaded_file.pdf");
  }, [label]);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        onPick();
      }}
      className={cn(
        "group relative flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed bg-muted/30 p-6 text-center transition-colors",
        dragOver && "border-primary bg-primary/5",
      )}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-background shadow-sm">
        {file ? (
          <CheckCircle2 className="h-5 w-5 text-[var(--color-severity-low)]" />
        ) : (
          <UploadIcon className="h-4 w-4 text-muted-foreground" />
        )}
      </div>
      <div>
        <p className="text-sm font-medium">{label}</p>
        {hint && <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>}
      </div>

      {file ? (
        <div className="flex items-center gap-2 rounded-md border bg-background px-2.5 py-1 text-xs">
          <span className="font-mono">{file}</span>
          <button
            type="button"
            aria-label="Remove file"
            onClick={(e) => {
              e.stopPropagation();
              setFile(null);
            }}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : (
        <Button size="sm" variant="outline" onClick={onPick}>
          Browse file
        </Button>
      )}

      <input type="file" accept={accept} className="hidden" />
    </div>
  );
}
