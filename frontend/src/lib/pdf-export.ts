/**
 * pdf-export.ts — Client-side PDF generation
 *
 * Uses html2canvas + jsPDF to capture the Clinical Intelligence Report
 * DOM and generate a multi-page PDF with PRATHAM branding.
 */

export async function exportReportPdf(
  patientName: string,
  reportElement: HTMLElement
): Promise<void> {
  // Dynamic imports to avoid loading heavy libraries on every page
  const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
    import("html2canvas"),
    import("jspdf"),
  ]);

  const canvas = await html2canvas(reportElement, {
    scale: 2,
    useCORS: true,
    logging: false,
    backgroundColor: "#0a0a0a", // dark background
  });

  const imgData = canvas.toDataURL("image/png");
  const imgWidth = 210; // A4 width in mm
  const pageHeight = 297; // A4 height in mm
  const imgHeight = (canvas.height * imgWidth) / canvas.width;

  const pdf = new jsPDF("p", "mm", "a4");

  // Header on first page
  pdf.setFontSize(8);
  pdf.setTextColor(120, 120, 120);
  pdf.text("PRATHAM — Clinical Intelligence Report", 10, 8);
  pdf.text(`Patient: ${patientName}`, 10, 12);
  pdf.text(`Generated: ${new Date().toLocaleString()}`, 10, 16);

  const headerOffset = 20;
  let heightLeft = imgHeight;
  let position = headerOffset;

  // First page
  pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
  heightLeft -= pageHeight - headerOffset;

  // Additional pages
  while (heightLeft > 0) {
    position = heightLeft - imgHeight;
    pdf.addPage();
    pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;
  }

  // Footer on last page
  const pageCount = pdf.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    pdf.setPage(i);
    pdf.setFontSize(7);
    pdf.setTextColor(150, 150, 150);
    pdf.text(
      `Page ${i} of ${pageCount} · PRATHAM AI — Not for clinical use`,
      105,
      292,
      { align: "center" }
    );
  }

  const safeName = patientName.replace(/[^a-zA-Z0-9]/g, "_").toLowerCase();
  pdf.save(`pratham_report_${safeName}_${Date.now()}.pdf`);
}
