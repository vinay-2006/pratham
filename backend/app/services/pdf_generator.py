"""
pdf_generator.py — Generate a 17-section clinical PDF from the unified Report DTO.

Uses ReportLab Platypus for structured, multi-page A4 layout.
Input: dict returned by report_service.get_complete_report()

PRATHAM v1: Rebuilt to match the 17-section clinical architecture.
Hides internal model names. Includes LLM narratives, confidence audit trail,
uncertainty engine output, clinical limitations, and report quality metadata.
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
from reportlab.lib.units import mm, cm
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

# ── Colour palette ───────────────────────────────────────────────────────────
PRIMARY = colors.HexColor("#2563EB")
PRIMARY_LIGHT = colors.HexColor("#DBEAFE")
PRIMARY_DARK = colors.HexColor("#1E40AF")
CARD_BG = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#CBD5E1")
MUTED = colors.HexColor("#64748B")
DANGER = colors.HexColor("#DC2626")
DANGER_BG = colors.HexColor("#FEF2F2")
WARNING = colors.HexColor("#D97706")
WARNING_BG = colors.HexColor("#FFFBEB")
SUCCESS = colors.HexColor("#059669")
SUCCESS_BG = colors.HexColor("#ECFDF5")
TEXT_DARK = colors.HexColor("#0F172A")
TEXT_SECONDARY = colors.HexColor("#334155")

SEVERITY_COLORS = {
    "critical": (DANGER, DANGER_BG),
    "high": (colors.HexColor("#EA580C"), colors.HexColor("#FFF7ED")),
    "moderate": (WARNING, WARNING_BG),
    "low": (SUCCESS, SUCCESS_BG),
}

CONFIDENCE_COLORS = {
    "VERY HIGH": SUCCESS,
    "HIGH": colors.HexColor("#0284C7"),
    "MODERATE": WARNING,
    "LOW": DANGER,
}


def _safe(val: Any, fallback: str = "—") -> str:
    if val is None or val == "" or val == []:
        return fallback
    return str(val)


def _risk_color(value: int | float) -> colors.HexColor:
    if value >= 70: return DANGER
    if value >= 50: return colors.HexColor("#EA580C")
    if value >= 30: return WARNING
    return SUCCESS


# ── Styles ───────────────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("PDFTitle", parent=base["Title"], fontSize=22, leading=28, textColor=PRIMARY_DARK, spaceAfter=4*mm, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("PDFSubtitle", parent=base["Normal"], fontSize=10, leading=14, textColor=MUTED, alignment=TA_CENTER, spaceAfter=6*mm),
        "section_heading": ParagraphStyle("PDFSectionHeading", parent=base["Heading2"], fontSize=12, leading=16, textColor=PRIMARY_DARK, spaceBefore=6*mm, spaceAfter=3*mm),
        "body": ParagraphStyle("PDFBody", parent=base["Normal"], fontSize=9.5, leading=14, textColor=TEXT_DARK),
        "body_bold": ParagraphStyle("PDFBodyBold", parent=base["Normal"], fontSize=9.5, leading=14, textColor=TEXT_DARK, fontName="Helvetica-Bold"),
        "narrative": ParagraphStyle("PDFNarrative", parent=base["Normal"], fontSize=9.5, leading=15, textColor=TEXT_SECONDARY, leftIndent=6*mm),
        "label": ParagraphStyle("PDFLabel", parent=base["Normal"], fontSize=8.5, leading=12, textColor=MUTED, fontName="Helvetica-Bold"),
        "small": ParagraphStyle("PDFSmall", parent=base["Normal"], fontSize=8, leading=11, textColor=MUTED),
        "footer": ParagraphStyle("PDFFooter", parent=base["Normal"], fontSize=7.5, leading=10, textColor=MUTED, alignment=TA_CENTER),
        "placeholder": ParagraphStyle("PDFPlaceholder", parent=base["Normal"], fontSize=9, leading=13, textColor=MUTED, fontName="Helvetica-Oblique"),
        "evidence_support": ParagraphStyle("PDFEvidenceSupport", parent=base["Normal"], fontSize=9, leading=13, textColor=SUCCESS, fontName="Helvetica"),
        "evidence_conflict": ParagraphStyle("PDFEvidenceConflict", parent=base["Normal"], fontSize=9, leading=13, textColor=WARNING, fontName="Helvetica"),
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _heading(text: str, styles: dict) -> list:
    return [
        KeepTogether([
            Paragraph(text, styles["section_heading"]),
            HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=3*mm, spaceBefore=0),
            Spacer(1, 18*mm),
        ]),
        Spacer(1, -18*mm),
    ]


def _kv_table(pairs: list[tuple[str, str]], styles: dict) -> Table:
    data = []
    for label, value in pairs:
        data.append([
            Paragraph(f"<b>{label}</b>", styles["label"]),
            Paragraph(value, styles["body"]),
        ])
    t = Table(data, colWidths=[45*mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    return t


def _std_table_style():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])


# ── Cover page ───────────────────────────────────────────────────────────────

def _build_cover(report: dict, styles: dict) -> list:
    ps = report["patient_summary"]
    gen_at = report.get("generated_at", "")
    try:
        gen_str = datetime.fromisoformat(gen_at).strftime("%d %b %Y · %I:%M %p")
    except Exception:
        gen_str = gen_at

    elements = [
        Spacer(1, 20*mm),
        Paragraph("PRATHAM", ParagraphStyle("CoverBrand", fontSize=32, leading=38, textColor=PRIMARY, alignment=TA_CENTER, fontName="Helvetica-Bold")),
        Spacer(1, 3*mm),
        Paragraph("Clinical Intelligence Report", styles["title"]),
        Spacer(1, 6*mm),
        HRFlowable(width="60%", thickness=2, color=PRIMARY, spaceAfter=6*mm),
    ]

    for label, value in [
        ("Patient", _safe(ps.get("name"))),
        ("Age / Gender", f"{_safe(ps.get('age'))}y · {_safe(ps.get('gender')).title()}"),
        ("Chief Complaint", _safe(ps.get("chief_complaint"))),
        ("Severity", _safe(ps.get("severity")).upper()),
        ("Generated", gen_str),
    ]:
        elements.append(Paragraph(
            f'<font color="{MUTED.hexval()}" size="9"><b>{label}:</b></font>  '
            f'<font color="{TEXT_DARK.hexval()}" size="10">{value}</font>',
            ParagraphStyle("CoverKV", alignment=TA_CENTER, fontSize=10, leading=16),
        ))
        elements.append(Spacer(1, 1.5*mm))

    elements.append(Spacer(1, 10*mm))

    # Pipeline status
    pipeline = report.get("pipeline_status", {})
    elements.append(Paragraph('<font color="#64748B" size="9"><b>Analysis Pipeline</b></font>', ParagraphStyle("PipelineLabel", alignment=TA_CENTER, fontSize=9, leading=14)))
    elements.append(Spacer(1, 2*mm))
    parts = []
    for stage in ["nlp", "risk", "lab", "imaging", "aggregation"]:
        s = pipeline.get(stage, "pending")
        icon = "✓" if s == "completed" else ("…" if s == "running" else "—")
        clr = "#059669" if s == "completed" else ("#D97706" if s == "running" else "#94A3B8")
        parts.append(f'<font color="{clr}">{icon} {stage.upper()}</font>')
    elements.append(Paragraph("    ".join(parts), ParagraphStyle("PipelineStatus", alignment=TA_CENTER, fontSize=9, leading=14, fontName="Helvetica-Bold")))

    # Clinical confidence on cover
    conc = report.get("clinical_conclusions", {})
    if conc.get("clinical_confidence"):
        elements.append(Spacer(1, 6*mm))
        conf = conc["clinical_confidence"]
        conf_color = CONFIDENCE_COLORS.get(conf, MUTED)
        elements.append(Paragraph(
            f'<font color="{MUTED.hexval()}" size="9"><b>Clinical Confidence:</b></font>  '
            f'<font color="{conf_color.hexval()}" size="11"><b>{conf}</b></font>',
            ParagraphStyle("CoverConf", alignment=TA_CENTER, fontSize=11, leading=16, fontName="Helvetica-Bold"),
        ))

    elements.append(PageBreak())
    return elements


# ── Section builders ─────────────────────────────────────────────────────────

def _s1_patient_summary(report: dict, styles: dict) -> list:
    ps = report["patient_summary"]
    elements = _heading("1. Patient Summary", styles)
    pairs = [
        ("Name", _safe(ps.get("name"))),
        ("Age / Gender", f"{_safe(ps.get('age'))}y · {_safe(ps.get('gender')).title()}"),
        ("Chief Complaint", _safe(ps.get("chief_complaint"), "No chief complaint recorded")),
        ("Emergency Description", _safe(ps.get("emergency_description"), "No description")),
        ("Severity", _safe(ps.get("severity")).upper()),
        ("Allergies", ", ".join(ps.get("allergies") or []) or "None reported"),
        ("Current Medications", ", ".join(ps.get("medications") or []) or "None reported"),
        ("Medical History", ", ".join(ps.get("medical_history") or []) or "None reported"),
    ]
    elements.append(_kv_table(pairs, styles))
    return elements


def _s2_clinical_overview(report: dict, styles: dict) -> list:
    interp = report.get("clinical_interpretation", {})
    text = interp.get("clinical_overview", "")
    if not text:
        return []
    elements = _heading("2. Clinical Overview", styles)
    elements.append(Paragraph(text, styles["narrative"]))
    return elements


def _s3_vital_signs(report: dict, styles: dict) -> list:
    v = report.get("vitals", {})
    elements = _heading("3. Vital Signs", styles)

    vital_data = [["Parameter", "Value", "Reference", "Status"]]
    vitals_analysis = []

    # Build from clinical reasoning facts if available
    conc = report.get("clinical_conclusions", {})
    dc = conc.get("data_completeness", {})

    RANGES = {
        "Heart Rate": (v.get("heart_rate"), "bpm", 60, 100),
        "SpO₂": (v.get("spo2"), "%", 95, 100),
        "Systolic BP": (v.get("bp_systolic"), "mmHg", 90, 140),
        "Diastolic BP": (v.get("bp_diastolic"), "mmHg", 60, 90),
        "Temperature": (v.get("temperature"), "°C", 36.1, 37.8),
        "Respiratory Rate": (v.get("respiratory_rate"), "/min", 12, 20),
    }

    for param, (value, unit, low, high) in RANGES.items():
        if value is None:
            vital_data.append([param, "—", f"{low}–{high} {unit}", "—"])
            continue
        status = "Normal"
        if value < low:
            status = "LOW"
        elif value > high:
            status = "HIGH"
        vital_data.append([param, f"{value} {unit}", f"{low}–{high} {unit}", status])

    t = Table(vital_data, colWidths=[42*mm, 32*mm, 38*mm, 25*mm])
    t.setStyle(_std_table_style())

    # Colour abnormal statuses
    for i in range(1, len(vital_data)):
        st = vital_data[i][3]
        if st in ("LOW", "HIGH"):
            t.setStyle(TableStyle([
                ("TEXTCOLOR", (3, i), (3, i), DANGER),
                ("FONTNAME", (3, i), (3, i), "Helvetica-Bold"),
            ]))

    elements.append(t)
    return elements


def _s4_key_clinical_findings(report: dict, styles: dict) -> list:
    elements = _heading("4. Key Clinical Findings", styles)
    nlp = report.get("nlp_findings", {})
    symptoms = report.get("symptoms", [])
    risk = report.get("risk_engine", {})

    # Symptoms
    if symptoms:
        elements.append(Paragraph("<b>Presenting Symptoms</b>", styles["body_bold"]))
        elements.append(Spacer(1, 2*mm))
        for s in symptoms:
            elements.append(Paragraph(f"  •  {s}", styles["body"]))
        elements.append(Spacer(1, 3*mm))

    # NLP flags
    flags = nlp.get("flags", {})
    active = [k.replace("_", " ").title() for k, val in flags.items() if val]
    if active:
        elements.append(Paragraph("<b>Clinical Flags (NLP)</b>", styles["body_bold"]))
        elements.append(Spacer(1, 2*mm))
        for f in active:
            elements.append(Paragraph(f"  ▸  {f}", styles["body"]))
        elements.append(Spacer(1, 3*mm))

    # NLP summary
    summary = nlp.get("summary", "")
    if summary:
        elements.append(Paragraph("<b>Clinical Summary</b>", styles["body_bold"]))
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(summary, styles["narrative"]))
        elements.append(Spacer(1, 3*mm))

    # Risk scores table
    risk_data = [["Category", "Score", "Level"]]
    for cat in ["cardiac", "respiratory", "trauma", "neurological"]:
        val = risk.get(cat, 0)
        level = "HIGH" if val >= 70 else "ELEVATED" if val >= 50 else "MODERATE" if val >= 30 else "LOW"
        risk_data.append([cat.title(), f"{val}/100", level])

    t = Table(risk_data, colWidths=[50*mm, 30*mm, 35*mm])
    t.setStyle(_std_table_style())
    for i in range(1, len(risk_data)):
        val = risk.get(risk_data[i][0].lower(), 0)
        t.setStyle(TableStyle([("TEXTCOLOR", (2, i), (2, i), _risk_color(val)), ("FONTNAME", (2, i), (2, i), "Helvetica-Bold")]))
    elements.append(t)

    return elements


def _s5_overall_impression(report: dict, styles: dict) -> list:
    conc = report.get("clinical_conclusions", {})
    interp = report.get("clinical_interpretation", {})
    if not conc:
        return []

    elements = _heading("5. Overall Clinical Impression", styles)

    primary = conc.get("primary_condition", "Pending")
    confidence = conc.get("clinical_confidence", "MODERATE")
    conf_color = CONFIDENCE_COLORS.get(confidence, MUTED)

    elements.append(Paragraph(
        f'<b>Most Likely Condition:</b>  <font color="{PRIMARY.hexval()}" size="11"><b>{primary}</b></font>',
        styles["body"],
    ))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(
        f'<b>Clinical Confidence:</b>  <font color="{conf_color.hexval()}"><b>{confidence}</b></font>',
        styles["body"],
    ))
    elements.append(Spacer(1, 3*mm))

    # Confidence audit trail
    factors = conc.get("confidence_factors", [])
    if factors:
        elements.append(Paragraph("<b>Confidence Calculated From:</b>", styles["body_bold"]))
        elements.append(Spacer(1, 1.5*mm))
        for f in factors:
            elements.append(Paragraph(f"  {f}", styles["small"]))
        elements.append(Spacer(1, 3*mm))

    # Uncertainty reasons
    uncertainty = conc.get("uncertainty_reasons", [])
    if uncertainty:
        elements.append(Paragraph("<b>Why Certainty Is Reduced:</b>", styles["body_bold"]))
        elements.append(Spacer(1, 1.5*mm))
        for r in uncertainty:
            elements.append(Paragraph(f"  ⚠ {r}", styles["evidence_conflict"]))
        elements.append(Spacer(1, 3*mm))

    # LLM narrative
    if interp.get("overall_impression"):
        elements.append(Paragraph(interp["overall_impression"], styles["narrative"]))
        elements.append(Spacer(1, 3*mm))

    # Supporting evidence
    supporting = conc.get("supporting_evidence", [])
    if supporting:
        elements.append(Paragraph("<b>Supporting Evidence:</b>", styles["body_bold"]))
        elements.append(Spacer(1, 1.5*mm))
        for e in supporting:
            elements.append(Paragraph(f"  ✓ {e}", styles["evidence_support"]))
        elements.append(Spacer(1, 2*mm))

    # Conflicting evidence
    conflicting = conc.get("conflicting_evidence", [])
    if conflicting:
        elements.append(Paragraph("<b>Conflicting Evidence:</b>", styles["body_bold"]))
        elements.append(Spacer(1, 1.5*mm))
        for e in conflicting:
            elements.append(Paragraph(f"  ⚠ {e}", styles["evidence_conflict"]))

    return elements


def _s6_alternative_considerations(report: dict, styles: dict) -> list:
    conc = report.get("clinical_conclusions", {})
    interp = report.get("clinical_interpretation", {})
    alts = conc.get("alternative_conditions", [])
    narrative = interp.get("alternative_considerations_narrative", "")
    if not alts and not narrative:
        return []

    elements = _heading("6. Alternative Considerations", styles)

    if narrative:
        elements.append(Paragraph(narrative, styles["narrative"]))
        elements.append(Spacer(1, 3*mm))

    if alts:
        alt_data = [["Condition", "Probability"]]
        for a in alts:
            prob = a.get("probability")
            prob_str = f"{float(prob)*100:.1f}%" if prob is not None else "—"
            alt_data.append([a.get("condition", "—"), prob_str])

        t = Table(alt_data, colWidths=[70*mm, 40*mm])
        t.setStyle(_std_table_style())
        elements.append(t)

    return elements


def _s7_ranking_justification(report: dict, styles: dict) -> list:
    conc = report.get("clinical_conclusions", {})
    rj = conc.get("ranking_justification", {})
    primary_reasons = rj.get("primary_reasons", [])
    vs_alts = rj.get("vs_alternatives", [])
    if not primary_reasons and not vs_alts:
        return []

    elements = _heading("7. Why This Condition Was Ranked Highest", styles)

    if primary_reasons:
        elements.append(Paragraph("<b>Supported By:</b>", styles["body_bold"]))
        elements.append(Spacer(1, 1.5*mm))
        for r in primary_reasons:
            elements.append(Paragraph(f"  ✓ {r}", styles["evidence_support"]))
        elements.append(Spacer(1, 3*mm))

    for alt in vs_alts:
        elements.append(Paragraph(f"<b>Ranked above {alt.get('condition', '')} because:</b>", styles["body_bold"]))
        elements.append(Spacer(1, 1*mm))
        for r in alt.get("reasons", []):
            elements.append(Paragraph(f"  • {r}", styles["body"]))
        elements.append(Spacer(1, 2*mm))

    return elements


def _s8_cardiac(report: dict, styles: dict) -> list:
    elements = _heading("8. Cardiac Assessment", styles)
    interp = report.get("clinical_interpretation", {})
    text = interp.get("cardiac_summary", "")
    if text:
        elements.append(Paragraph(text, styles["narrative"]))
    else:
        risk = report.get("risk_engine", {})
        elements.append(Paragraph(f"Cardiac risk score: {risk.get('cardiac', 0)}/100.", styles["body"]))
    return elements


def _s9_respiratory(report: dict, styles: dict) -> list:
    elements = _heading("9. Respiratory Assessment", styles)
    interp = report.get("clinical_interpretation", {})
    text = interp.get("respiratory_summary", "")
    if text:
        elements.append(Paragraph(text, styles["narrative"]))
    else:
        risk = report.get("risk_engine", {})
        elements.append(Paragraph(f"Respiratory risk score: {risk.get('respiratory', 0)}/100.", styles["body"]))
    return elements


def _s10_laboratory(report: dict, styles: dict) -> list:
    lab = report.get("lab_intelligence", {})
    elements = _heading("10. Laboratory Assessment", styles)

    if not lab.get("available"):
        elements.append(Paragraph("Laboratory AI analysis has not been performed.", styles["placeholder"]))
        return elements

    interp = report.get("clinical_interpretation", {})
    if interp.get("laboratory_summary"):
        elements.append(Paragraph(interp["laboratory_summary"], styles["narrative"]))
        elements.append(Spacer(1, 3*mm))

    pred = _safe(lab.get("prediction"), "-").replace("_", " ").title()
    prob = lab.get("risk_probability")
    prob_str = f"{float(prob)*100:.1f}%" if prob is not None else "-"

    pairs = [("Prediction", pred), ("Risk Probability", prob_str)]
    elements.append(_kv_table(pairs, styles))
    elements.append(Spacer(1, 3*mm))

    # SHAP features
    top_features = lab.get("top_features")
    if top_features and isinstance(top_features, dict):
        elements.append(Paragraph("<b>Key Contributing Factors (SHAP)</b>", styles["body_bold"]))
        elements.append(Spacer(1, 2*mm))
        shap_data = [["Feature", "Impact"]]
        sorted_feats = sorted(top_features.items(), key=lambda x: abs(float(x[1])), reverse=True)[:5]
        for feat, val in sorted_feats:
            v = float(val)
            sign = "+" if v > 0 else ""
            shap_data.append([feat.replace("_", " ").title(), f"{sign}{v:.4f}"])

        t = Table(shap_data, colWidths=[70*mm, 40*mm])
        t.setStyle(_std_table_style())
        t.setStyle(TableStyle([("FONTNAME", (1, 1), (1, -1), "Courier-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.5)]))
        elements.append(t)

    return elements


def _s11_imaging(report: dict, styles: dict) -> list:
    img = report.get("imaging_intelligence", {})
    elements = _heading("11. Imaging Assessment", styles)

    if not img.get("available"):
        elements.append(Paragraph("Imaging analysis has not been performed.", styles["placeholder"]))
        return elements

    interp = report.get("clinical_interpretation", {})
    if interp.get("imaging_summary"):
        elements.append(Paragraph(interp["imaging_summary"], styles["narrative"]))
        elements.append(Spacer(1, 3*mm))

    pred = _safe(img.get("prediction"), "-").replace("_", " ").title()
    prob = img.get("pneumonia_probability")
    prob_str = f"{float(prob)*100:.1f}%" if prob is not None else "-"
    conf = img.get("confidence")
    conf_str = f"{float(conf)*100:.1f}%" if conf is not None else "-"

    pairs = [("Finding", pred), ("Pneumonia Probability", prob_str), ("Model Confidence", conf_str)]
    elements.append(_kv_table(pairs, styles))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("X-ray and Grad-CAM heatmap are available in the web report.", styles["small"]))

    return elements


def _s12_monitoring(report: dict, styles: dict) -> list:
    conc = report.get("clinical_conclusions", {})
    interp = report.get("clinical_interpretation", {})
    priorities = conc.get("monitoring_priorities", [])
    if not priorities:
        return []

    elements = _heading("12. Monitoring Priorities", styles)

    if interp.get("monitoring_narrative"):
        elements.append(Paragraph(interp["monitoring_narrative"], styles["narrative"]))
        elements.append(Spacer(1, 3*mm))

    for m in priorities:
        elements.append(Paragraph(
            f"<b>{m.get('parameter', '')}</b> — {m.get('reason', '')}",
            styles["body"],
        ))
        elements.append(Spacer(1, 1.5*mm))

    return elements


def _s13_precautions(report: dict, styles: dict) -> list:
    conc = report.get("clinical_conclusions", {})
    interp = report.get("clinical_interpretation", {})
    precautions = conc.get("clinical_precautions", [])
    if not precautions:
        return []

    elements = _heading("13. Immediate Clinical Precautions", styles)

    if interp.get("precautions_narrative"):
        elements.append(Paragraph(interp["precautions_narrative"], styles["narrative"]))
        elements.append(Spacer(1, 3*mm))

    for p in precautions:
        elements.append(Paragraph(
            f"<b>⚠ {p.get('action', '')}</b> — {p.get('reason', '')}",
            styles["body"],
        ))
        elements.append(Spacer(1, 1.5*mm))

    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(
        "These are monitoring precautions only. They do not constitute treatment recommendations.",
        ParagraphStyle("PrecautionDisclaimer", parent=styles["small"], textColor=DANGER, fontName="Helvetica-Bold"),
    ))

    return elements


def _s14_next_steps(report: dict, styles: dict) -> list:
    conc = report.get("clinical_conclusions", {})
    inv_status = conc.get("investigation_status", [])
    if not inv_status:
        # Fall back to raw investigations
        investigations = report.get("investigations", [])
        if not investigations:
            return []
        elements = _heading("14. Recommended Next Clinical Steps", styles)
        for inv in investigations:
            status = inv.get("status", "pending")
            elements.append(Paragraph(f"  •  {inv.get('investigation_type', '-')} — {status.upper()}", styles["body"]))
        return elements

    elements = _heading("14. Recommended Next Clinical Steps", styles)

    inv_data = [["Investigation", "Status", "AI Analysis"]]
    for inv in inv_status:
        inv_data.append([
            inv.get("investigation_type", "—"),
            inv.get("status", "—").upper(),
            inv.get("ai_status", "—"),
        ])

    t = Table(inv_data, colWidths=[55*mm, 30*mm, 55*mm])
    t.setStyle(_std_table_style())
    elements.append(t)

    return elements


def _s15_clinical_data(report: dict, styles: dict) -> list:
    evidence_items = report.get("evidence", [])
    if not evidence_items:
        return []

    elements = _heading("15. Clinical Data Used for Analysis", styles)

    ev_data = [["File", "Type", "Uploaded"]]
    for ev in evidence_items:
        uploaded = _safe(ev.get("uploaded_at"), "—")
        if len(uploaded) > 10:
            uploaded = uploaded[:10]
        ev_data.append([
            _safe(ev.get("file_name")),
            _safe(ev.get("evidence_type")).upper(),
            uploaded,
        ])

    t = Table(ev_data, colWidths=[65*mm, 30*mm, 35*mm])
    t.setStyle(_std_table_style())
    elements.append(t)

    return elements


def _s16_report_quality(report: dict, styles: dict) -> list:
    conc = report.get("clinical_conclusions", {})
    interp = report.get("clinical_interpretation", {})
    rq = conc.get("report_quality", {})
    limitations = conc.get("clinical_limitations", [])
    if not rq and not limitations:
        return []

    elements = _heading("16. Report Quality & Evidence Completeness", styles)

    if rq:
        pairs = [
            ("Evidence Completeness", f"{rq.get('evidence_completeness_pct', 0)}%"),
            ("Subsystem Agreement", _safe(rq.get("subsystem_agreement"))),
            ("Pipeline Integrity", _safe(rq.get("pipeline_integrity"))),
            ("Missing Critical Inputs", ", ".join(rq.get("missing_critical_inputs", [])) or "None"),
        ]
        elements.append(_kv_table(pairs, styles))
        elements.append(Spacer(1, 3*mm))

    if interp.get("limitations_narrative"):
        elements.append(Paragraph(interp["limitations_narrative"], styles["narrative"]))
        elements.append(Spacer(1, 3*mm))

    # Limitations grid
    if limitations:
        lim_data = [["Data Source", "Status"]]
        for lim in limitations:
            status = "Available" if lim.get("available") else "Unavailable"
            lim_data.append([lim.get("source", "—"), status])

        t = Table(lim_data, colWidths=[70*mm, 40*mm])
        t.setStyle(_std_table_style())
        for i in range(1, len(lim_data)):
            if lim_data[i][1] == "Unavailable":
                t.setStyle(TableStyle([
                    ("TEXTCOLOR", (1, i), (1, i), DANGER),
                    ("FONTNAME", (1, i), (1, i), "Helvetica-Bold"),
                ]))
            else:
                t.setStyle(TableStyle([
                    ("TEXTCOLOR", (1, i), (1, i), SUCCESS),
                    ("FONTNAME", (1, i), (1, i), "Helvetica-Bold"),
                ]))
        elements.append(t)

    return elements


def _s17_system_info(report: dict, styles: dict) -> list:
    elements = _heading("17. System Information & Disclaimer", styles)

    # Analysis components (no internal model names)
    elements.append(Paragraph("<b>Analysis Generated Using:</b>", styles["body_bold"]))
    elements.append(Spacer(1, 2*mm))
    for tech in [
        "Clinical NLP",
        "Rule-based Risk Engine",
        "Laboratory ML Analysis",
        "Medical Imaging AI",
        "Evidence Aggregation Engine",
        "Grounded Clinical Language Model",
    ]:
        elements.append(Paragraph(f"  ✓  {tech}", styles["body"]))

    elements.append(Spacer(1, 4*mm))

    version = report.get("report_version", "1.0")
    gen_at = report.get("generated_at", "")
    try:
        gen_str = datetime.fromisoformat(gen_at).strftime("%d %b %Y · %I:%M %p")
    except Exception:
        gen_str = gen_at

    elements.append(Paragraph(f"<b>Report Version:</b> PRATHAM v{version}", styles["small"]))
    elements.append(Paragraph(f"<b>Generated:</b> {gen_str}", styles["small"]))

    elements.append(Spacer(1, 6*mm))

    # Disclaimer
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=3*mm))
    elements.append(Paragraph(
        "This system supports clinical decision-making and does not replace physician judgment. "
        "Final diagnosis and treatment remain the responsibility of the attending physician. "
        "AI-generated interpretations are explanations of structured clinical evidence and should be "
        "validated against independent clinical assessment.",
        ParagraphStyle("Disclaimer", parent=styles["footer"], textColor=DANGER, fontName="Helvetica-Bold", fontSize=8, leading=12),
    ))

    return elements


# ── Page template callbacks ──────────────────────────────────────────────────

def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(15*mm, A4[1] - 10*mm, "PRATHAM — Clinical Intelligence Report")
    canvas.drawRightString(A4[0] - 15*mm, A4[1] - 10*mm, datetime.now().strftime("%d %b %Y"))
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(A4[0] / 2, 10*mm, f"Page {doc.page}  ·  PRATHAM AI — For clinical decision support only")
    canvas.restoreState()


# ── Main entry point ─────────────────────────────────────────────────────────

def generate_pdf(report: Dict[str, Any]) -> bytes:
    """
    Generate a 17-section clinical PDF from the unified Report DTO.
    Returns the raw PDF bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=18*mm,
        bottomMargin=18*mm,
        leftMargin=15*mm,
        rightMargin=15*mm,
        title="PRATHAM Clinical Intelligence Report",
        author="PRATHAM AI System",
    )

    styles = _build_styles()
    elements: list = []

    try:
        elements.extend(_build_cover(report, styles))
    except Exception as e:
        logger.error("PDF cover generation failed: %s", e)

    section_builders = [
        _s1_patient_summary,
        _s2_clinical_overview,
        _s3_vital_signs,
        _s4_key_clinical_findings,
        _s5_overall_impression,
        _s6_alternative_considerations,
        _s7_ranking_justification,
        _s8_cardiac,
        _s9_respiratory,
        _s10_laboratory,
        _s11_imaging,
        _s12_monitoring,
        _s13_precautions,
        _s14_next_steps,
        _s15_clinical_data,
        _s16_report_quality,
        _s17_system_info,
    ]

    for builder in section_builders:
        try:
            result = builder(report, styles)
            if result:
                elements.extend(result)
        except Exception as e:
            logger.error("PDF section %s failed: %s", builder.__name__, e)
            elements.append(Paragraph(f"Error generating section: {e}", styles["placeholder"]))

    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()
