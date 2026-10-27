"""
pdf_generator.py — Generate a clinician-first 12-section monochrome PDF.

Uses ReportLab Platypus for structured, minimal A4 hospital report layout.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
    KeepTogether,
)

logger = logging.getLogger(__name__)

# ── Monochrome Hospital Palette (Task B10 & Monochrome) ─────────────────────
COLOR_DARK = colors.HexColor("#1E293B")      # Dark Slate
COLOR_TEXT = colors.HexColor("#334155")      # Slate
COLOR_MUTED = colors.HexColor("#64748B")     # Muted gray
COLOR_LINE = colors.HexColor("#E2E8F0")      # Light gray divider
COLOR_BG_LIGHT = colors.HexColor("#F8FAFC")  # Off-white

# Status Colors (Monochrome indicators with slight tint if critical)
COLOR_CRITICAL = colors.HexColor("#991B1B")  # Deep red for alert text only
COLOR_NORMAL = colors.HexColor("#0F766E")    # Deep teal for completed/normal


def _safe(val: Any, fallback: str = "—") -> str:
    if val is None or val == "" or val == []:
        return fallback
    return str(val)


# ── ReportLab Styles ─────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    return {
        "doc_title": ParagraphStyle("DocTitle", parent=base["Title"], fontSize=18, leading=22, textColor=COLOR_DARK, spaceAfter=2*mm, alignment=TA_LEFT),
        "doc_subtitle": ParagraphStyle("DocSubtitle", parent=base["Normal"], fontSize=9, leading=12, textColor=COLOR_MUTED, spaceAfter=6*mm),
        "section_heading": ParagraphStyle("SectionHeading", parent=base["Heading2"], fontSize=11, leading=14, textColor=COLOR_DARK, spaceBefore=4*mm, spaceAfter=2*mm, fontName="Helvetica-Bold"),
        "body": ParagraphStyle("Body", parent=base["Normal"], fontSize=8.5, leading=12.5, textColor=COLOR_TEXT),
        "body_bold": ParagraphStyle("BodyBold", parent=base["Normal"], fontSize=8.5, leading=12.5, textColor=COLOR_DARK, fontName="Helvetica-Bold"),
        "body_italic": ParagraphStyle("BodyItalic", parent=base["Normal"], fontSize=8.5, leading=12.5, textColor=COLOR_MUTED, fontName="Helvetica-Oblique"),
        "label": ParagraphStyle("Label", parent=base["Normal"], fontSize=8, leading=11, textColor=COLOR_MUTED, fontName="Helvetica-Bold"),
        "small": ParagraphStyle("Small", parent=base["Normal"], fontSize=7.5, leading=10, textColor=COLOR_MUTED),
        "footer": ParagraphStyle("Footer", parent=base["Normal"], fontSize=7, leading=9, textColor=COLOR_MUTED, alignment=TA_CENTER),
        "critical_text": ParagraphStyle("CriticalText", parent=base["Normal"], fontSize=8.5, leading=12.5, textColor=COLOR_CRITICAL, fontName="Helvetica-Bold"),
    }


def _section_header(title: str, styles: dict) -> list:
    return [
        Spacer(1, 3*mm),
        Paragraph(title, styles["section_heading"]),
        HRFlowable(width="100%", thickness=1, color=COLOR_LINE, spaceAfter=3*mm, spaceBefore=1*mm),
    ]


# ── Page Template Callback ───────────────────────────────────────────────────

def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(COLOR_MUTED)
    canvas.drawString(15*mm, A4[1] - 10*mm, "PRATHAM — Emergency Clinical Decision Support Platform")
    canvas.drawRightString(A4[0] - 15*mm, A4[1] - 10*mm, f"Document ID: {doc.title or 'Intake-File'}")
    canvas.drawCentredString(A4[0] / 2, 10*mm, f"Page {doc.page}  ·  CONFIDENTIAL CLINICAL REPORT")
    canvas.restoreState()


# ── Main Generator ───────────────────────────────────────────────────────────

def generate_pdf(report: Dict[str, Any]) -> bytes:
    """
    Generate a professional 12-section clinical PDF from the unified Report DTO.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=15*mm,
        bottomMargin=15*mm,
        leftMargin=15*mm,
        rightMargin=15*mm,
        title="PRATHAM_Clinical_Report",
        author="PRATHAM ED Platform",
    )

    styles = _build_styles()
    elements: list = []

    # Retrieve restructured clinical report data
    clin = report.get("clinician_report")
    if not clin:
        # Fallback to extremely basic error PDF to prevent any compilation crash
        elements.append(Paragraph("Clinical report structure not populated. Please contact support.", styles["doc_title"]))
        doc.build(elements)
        return buf.getvalue()

    snap = clin["patient_snapshot"]

    # ── Document Header ──────────────────────────────────────────────────────
    elements.append(Paragraph("PRATHAM EMERGENCY DIAGNOSTIC CLINICAL REPORT", styles["doc_title"]))
    elements.append(Paragraph(f"Generated: {snap['generated_time']} | Reviewer: {snap['reviewer']}", styles["doc_subtitle"]))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_DARK, spaceAfter=6*mm))

    # ── Section 1: Patient Snapshot Cover Sheet ──────────────────────────────
    elements.extend(_section_header("1. Patient Snapshot Cover Sheet", styles))
    snap_data = [
        [
            Paragraph("<b>Case ID:</b>", styles["body_bold"]), Paragraph(snap["case_id"], styles["body"]),
            Paragraph("<b>Patient Name:</b>", styles["body_bold"]), Paragraph(snap["patient_name"], styles["body"])
        ],
        [
            Paragraph("<b>Age / Gender:</b>", styles["body_bold"]), Paragraph(f"{snap['age']} / {snap['gender']}", styles["body"]),
            Paragraph("<b>Arrival Mode:</b>", styles["body_bold"]), Paragraph(snap["arrival_type"], styles["body"])
        ],
        [
            Paragraph("<b>Clinical Priority:</b>", styles["body_bold"]), Paragraph(snap["priority"], styles["critical_text"] if snap["priority"].upper() in ("CRITICAL", "HIGH") else styles["body"]),
            Paragraph("<b>Report Version:</b>", styles["body_bold"]), Paragraph(snap["report_version"], styles["body"])
        ],
        [
            Paragraph("<b>Completed Tests:</b>", styles["body_bold"]), Paragraph(snap["completed_tests"], styles["body"]),
            Paragraph("<b>Last Updated:</b>", styles["body_bold"]), Paragraph(snap["updated_time"], styles["body"])
        ]
    ]
    t_snap = Table(snap_data, colWidths=[35*mm, 50*mm, 35*mm, 60*mm])
    t_snap.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LINE),
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_snap)
    elements.append(Spacer(1, 4*mm))

    # ── Section 2: Clinical Timeline (Task 2: Timeline) ─────────────────────
    elements.extend(_section_header("2. Clinical Timeline", styles))
    timeline_data = [
        [
            Paragraph(f"<b>{evt['time']}</b>", styles["body_bold"]),
            Paragraph(f"<b>{evt['event']}</b> — {evt['actor']}<br/><font color='#64748B'>{evt['reason']}</font>", styles["body"])
        ]
        for evt in clin["timeline"]
    ]
    t_time = Table(timeline_data, colWidths=[25*mm, 155*mm])
    t_time.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, COLOR_LINE),
    ]))
    elements.append(t_time)
    elements.append(Spacer(1, 4*mm))

    # ── Section 3: Presenting Complaint (Task 3) ─────────────────────────────
    elements.extend(_section_header("3. Presenting Complaint", styles))
    pc = clin["presenting_complaint"]
    elements.append(Paragraph(f"<b>Chief Complaint:</b> {pc['chief_complaint']}", styles["body_bold"]))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(f"<b>Emergency Intake Narrative:</b><br/>{pc['emergency_description']}", styles["body"]))
    elements.append(Spacer(1, 4*mm))

    # ── Section 4: History of Present Illness (Task 4) ──────────────────────
    elements.extend(_section_header("4. History of Present Illness (HPI)", styles))
    elements.append(Paragraph(clin["hpi"], styles["body"]))
    elements.append(Spacer(1, 4*mm))

    # ── Section 5: Vital Signs ───────────────────────────────────────────────
    elements.extend(_section_header("5. Vital Signs", styles))
    
    # Restructure vitals matching VITAL_RANGES standard
    vits = clin["vitals_list"]
    vital_rows = [
        ["Vital Sign", "Value Recorded", "Reference Range", "Assessment"],
        ["Heart Rate", f"{_safe(vits.get('heart_rate'))} bpm", "60–100 bpm", "Normal" if vits.get("heart_rate") and 60 <= vits["heart_rate"] <= 100 else "Abnormal"],
        ["Oxygen Saturation (SpO₂)", f"{_safe(vits.get('spo2'))}%", "95–100%", "Normal" if vits.get("spo2") and 95 <= vits["spo2"] <= 100 else "Abnormal"],
        ["Systolic BP", f"{_safe(vits.get('bp_systolic'))} mmHg", "90–140 mmHg", "Normal" if vits.get("bp_systolic") and 90 <= vits["bp_systolic"] <= 140 else "Abnormal"],
        ["Diastolic BP", f"{_safe(vits.get('bp_diastolic'))} mmHg", "60–90 mmHg", "Normal" if vits.get("bp_diastolic") and 60 <= vits["bp_diastolic"] <= 90 else "Abnormal"],
        ["Temperature", f"{_safe(vits.get('temperature'))}°C", "36.1–37.8°C", "Normal" if vits.get("temperature") and 36.1 <= vits["temperature"] <= 37.8 else "Abnormal"],
        ["Respiratory Rate", f"{_safe(vits.get('respiratory_rate'))} breath/min", "12–20 breath/min", "Normal" if vits.get("respiratory_rate") and 12 <= vits["respiratory_rate"] <= 20 else "Abnormal"]
    ]
    t_vits_data = []
    for i, r in enumerate(vital_rows):
        if i == 0:
            t_vits_data.append([Paragraph(f"<b>{col}</b>", styles["body_bold"]) for col in r])
        else:
            is_abn = r[3] == "Abnormal"
            style_col = styles["critical_text"] if is_abn else styles["body"]
            t_vits_data.append([
                Paragraph(r[0], styles["body"]),
                Paragraph(r[1], style_col),
                Paragraph(r[2], styles["body"]),
                Paragraph(r[3], style_col)
            ])
            
    t_vits = Table(t_vits_data, colWidths=[55*mm, 40*mm, 45*mm, 40*mm])
    t_vits.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LINE),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_BG_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_vits)
    elements.append(Spacer(1, 4*mm))

    # ── Section 6: Investigations Reviewed (Task A1 Matrix) ──────────────────
    elements.extend(_section_header("6. Investigations Reviewed", styles))
    matrix_data = [
        [
            Paragraph(f"<b>{t['test_name']}</b>", styles["body_bold"]),
            Paragraph(
                f"<font color='#0F766E'><b>{t['status']}</b></font>" if t["status"] == "Completed"
                else f"<font color='#B45309'><b>{t['status']}</b></font>" if t["status"] == "Pending"
                else f"<font color='#64748B'>{t['status']}</font>",
                styles["body"]
            )
        ]
        for t in clin["investigations_matrix"]
    ]
    t_matrix = Table(matrix_data, colWidths=[90*mm, 90*mm])
    t_matrix.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LINE),
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_matrix)
    elements.append(Spacer(1, 4*mm))

    # ── Section 7: Clinical Findings (Task B3 Specialty findings) ────────────
    elements.extend(_section_header("7. Clinical Findings", styles))
    cf = clin["clinical_findings"]
    has_any = False
    
    if cf.get("cardiac"):
        elements.append(Paragraph("<b>Cardiac findings:</b>", styles["body_bold"]))
        elements.append(Paragraph(cf["cardiac"], styles["body"]))
        elements.append(Spacer(1, 2.5*mm))
        has_any = True
        
    if cf.get("respiratory"):
        elements.append(Paragraph("<b>Respiratory findings:</b>", styles["body_bold"]))
        elements.append(Paragraph(cf["respiratory"], styles["body"]))
        elements.append(Spacer(1, 2.5*mm))
        has_any = True

    if not has_any:
        elements.append(Paragraph(cf.get("general") or "No active clinical findings detected.", styles["body"]))
    elements.append(Spacer(1, 4*mm))

    # ── Section 8: Differential Diagnosis (Task B4 Table) ────────────────────
    elements.extend(_section_header("8. Differential Diagnosis", styles))
    
    for diff in clin["differential_diagnosis"]:
        elements.append(Paragraph(f"<b>Condition: {diff['condition']}</b>", styles["body_bold"]))
        elements.append(Spacer(1, 1.5*mm))
        
        # Supporting / Contradicting
        supp_text = ", ".join(diff["supporting"]) or "None identified"
        cont_text = ", ".join(diff["contradicting"]) or "None identified"
        
        diff_kv = [
            [Paragraph("<b>Supporting Findings:</b>", styles["label"]), Paragraph(supp_text, styles["body"])],
            [Paragraph("<b>Contradicting Findings:</b>", styles["label"]), Paragraph(cont_text, styles["body"])],
            [Paragraph("<b>Further Evidence Needed:</b>", styles["label"]), Paragraph(diff["further_evidence"], styles["body_italic"])]
        ]
        t_diff = Table(diff_kv, colWidths=[45*mm, 135*mm])
        t_diff.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
        ]))
        elements.append(t_diff)
        elements.append(Spacer(1, 3*mm))

    # ── Section 9: Clinical Impression (Task B5) ─────────────────────────────
    elements.extend(_section_header("9. Clinical Impression", styles))
    ci = clin["clinical_impression"]
    elements.append(Paragraph(f"<b>Primary Impression:</b> {ci['primary']}", styles["body_bold"]))
    if ci.get("secondary"):
        elements.append(Spacer(1, 1.5*mm))
        elements.append(Paragraph(f"<b>Secondary Considerations:</b> {ci['secondary']}", styles["body"]))
    elements.append(Spacer(1, 2.5*mm))
    elements.append(Paragraph(f"<b>Clinical Assessment:</b><br/>{ci['assessment']}", styles["body"]))
    elements.append(Spacer(1, 4*mm))

    # ── Section 10: Recommended Next Steps (Task B6) ─────────────────────────
    elements.extend(_section_header("10. Recommended Next Steps", styles))
    recs = clin["recommendations"]
    
    elements.append(Paragraph("<b>Immediate Actions:</b>", styles["body_bold"]))
    for r in recs["immediate"]:
        elements.append(Paragraph(f"  •  {r}", styles["body"]))
    elements.append(Spacer(1, 2.5*mm))
        
    elements.append(Paragraph("<b>Short-Term Follow-up:</b>", styles["body_bold"]))
    for r in recs["short_term"]:
        elements.append(Paragraph(f"  •  {r}", styles["body"]))
    elements.append(Spacer(1, 2.5*mm))
        
    elements.append(Paragraph("<b>Additional Investigations Required:</b>", styles["body_bold"]))
    for r in recs["additional"]:
        elements.append(Paragraph(f"  •  {r}", styles["body"]))
    elements.append(Spacer(1, 4*mm))

    # ── Section 11: Evidence Quality & Summary (Task 7 & 9) ──────────────────
    elements.extend(_section_header("11. Evidence Quality & Summary", styles))
    eq = clin["evidence_quality"]
    elements.append(Paragraph(f"<b>Overall Reliability:</b> {eq['reliability']}", styles["body_bold"]))
    elements.append(Paragraph(f"<b>Reasoning:</b> {eq['reason']}", styles["body"]))
    elements.append(Spacer(1, 3*mm))

    elements.append(Paragraph("<b>Version History:</b>", styles["body_bold"]))
    elements.append(Spacer(1, 1.5*mm))
    v_rows = [
        [Paragraph(f"<b>{v['version']}</b>", styles["body_bold"]), Paragraph(v["time"], styles["body"]), Paragraph(v["event"], styles["body"])]
        for v in eq["history"]
    ]
    t_v = Table(v_rows, colWidths=[20*mm, 25*mm, 135*mm])
    t_v.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LINE),
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_BG_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_v)
    
    # ── Section 12: Technical Appendix (Task B8 Developer details) ──────────
    elements.append(PageBreak())
    elements.extend(_section_header("12. Technical Appendix", styles))
    elements.append(Paragraph("This appendix contains system engineering diagnostics and machine learning metadata, intended solely for platform developers and administrators.", styles["body_italic"]))
    elements.append(Spacer(1, 4*mm))

    # Aggregation probabilities & SHAP/GradCAM info
    agg = report.get("aggregation", {})
    if agg and agg.get("available"):
        elements.append(Paragraph("<b>Aggregated Model Predictions:</b>", styles["body_bold"]))
        probs = agg.get("probabilities", {})
        prob_rows = [
            [Paragraph(cond, styles["body"]), Paragraph(f"{prob*100:.1f}%" if prob is not None else "—", styles["body"])]
            for cond, prob in probs.items()
        ]
        t_probs = Table(prob_rows, colWidths=[80*mm, 100*mm])
        t_probs.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_probs)
        elements.append(Spacer(1, 4*mm))

    # Subsystem details
    elements.append(Paragraph("<b>Pipeline Subsystem Diagnostics:</b>", styles["body_bold"]))
    diag_rows = []
    lab = report.get("lab_intelligence", {})
    if lab and lab.get("available"):
        diag_rows.append(["Lab Intelligence Subsystem", f"Model: {lab.get('model_name') or 'XGBoost Cardiac'}", f"Prediction: {lab.get('prediction')}", f"Prob: {lab.get('risk_probability', 0)*100:.1f}%"])
    img = report.get("imaging_intelligence", {})
    if img and img.get("available"):
        diag_rows.append(["Imaging Intelligence Subsystem", f"Model: {img.get('model_name') or 'EfficientNet Chest X-ray'}", f"Prediction: {img.get('prediction')}", f"Prob: {img.get('pneumonia_probability', 0)*100:.1f}%"])
        
    if diag_rows:
        t_diags = Table(diag_rows, colWidths=[50*mm, 50*mm, 40*mm, 40*mm])
        t_diags.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_diags)
        elements.append(Spacer(1, 4*mm))

    # Disclaimer
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_LINE, spaceAfter=3*mm))
    elements.append(Paragraph(
        "Disclaimer: This platform is designed for clinical decision support. Final diagnostic and treatment decisions "
        "are the exclusive responsibility of the attending physician. AI metrics are presented as secondary observations.",
        styles["footer"]
    ))

    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()
