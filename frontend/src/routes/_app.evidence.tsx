import { createFileRoute } from "@tanstack/react-router";
import { SectionHeader } from "@/components/section-header";
import { MockUploadDropzone } from "@/components/mock-upload-dropzone";

export const Route = createFileRoute("/_app/evidence")({
  head: () => ({
    meta: [
      { title: "Evidence Upload — PRATHAM" },
      { name: "description", content: "Attach imaging, labs, ECG, and notes for review." },
    ],
  }),
  component: EvidencePage,
});

function EvidencePage() {
  return (
    <div className="mx-auto max-w-5xl px-5 py-8 md:px-8">
      <SectionHeader
        eyebrow="Stage 2 · Evidence"
        title="Evidence Upload"
        description="Attach available evidence. Mock-only — no files leave the browser in this prototype."
      />

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <MockUploadDropzone label="X-ray" hint="DICOM or JPG" />
        <MockUploadDropzone label="Lab Reports" hint="PDF or image" />
        <MockUploadDropzone label="ECG" hint="PDF or printout scan" />
        <MockUploadDropzone label="Notes" hint="Free-text or scanned notes" />
      </div>
    </div>
  );
}
