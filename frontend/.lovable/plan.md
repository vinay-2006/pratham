# PRATHAM — Emergency Clinical Intelligence Frontend

Frontend-only prototype. 10 pages, one coherent mock patient, calm medical SaaS aesthetic. Incorporates the refinements: cautious wording, global Evidence Completeness, separate AI Confidence, and Missing Evidence sections.

## Design system

`src/styles.css` semantic tokens (oklch):

- `--background`, `--foreground`, `--card`, `--muted`, `--border` — clean whites / deep slate (dark)
- `--primary` deep medical blue
- `--accent` soft clinical teal
- `--severity-critical` emergency red, `--severity-high` amber, `--severity-moderate` yellow, `--severity-low` green
- Radius 10px, restrained shadows. No neon, no glow.

Typography: Inter Tight (display) + Inter (body). Light default, dark mode via `.dark` class with localStorage-persisted toggle in the top bar.

## Routes (TanStack file-based)

```
src/routes/
  __root.tsx          shell
  index.tsx           Landing (marketing layout, no sidebar)
  intake.tsx          Emergency Intake
  dashboard.tsx       Operational Risk Dashboard
  investigations.tsx  Investigation Recommendations
  evidence.tsx        Evidence Upload
  imaging.tsx         Imaging Analysis Viewer
  differential.tsx    Differential Diagnosis
  explainability.tsx  Explainability Panel
  confidence.tsx      Confidence Suppression
  review.tsx          Doctor Review Dashboard
```

Clinical pages share `AppShell` (left sidebar + top bar). Each route has its own `head()` with unique title + description.

## Top bar (global, every clinical page)

- Patient context chip (name / age / arrival time from mock data)
- **Evidence Completeness pill**: LOW / MODERATE / HIGH, color-coded — drives suppression UI and ties into confidence everywhere
- Case toggle (Primary case ↔ Low-evidence case) for demoing suppression
- Theme toggle

## Shared components (`src/components/`)

- `AppShell`, `Sidebar`, `TopBar`, `ThemeToggle`, `EvidenceCompletenessPill`
- `SeverityBadge`, `RiskCard` (label + progress + severity color)
- `EvidenceCard` (expandable, contributing evidence + provenance)
- `MissingEvidenceList` (reused on Differential, Confidence, Review)
- `UncertaintyBanner`, `ConfidenceMeter`, `AIConfidenceBadge` (Low/Moderate/High — distinct from probability bars)
- `ProbabilityBar`, `ChecklistItem`, `StatTile`, `SectionHeader`
- `MockUploadDropzone` (visual only)
- `HeatmapOverlay` (CSS radial gradient over mock X-ray)

shadcn primitives: button, card, input, label, textarea, select, progress, badge, tabs, separator, alert, accordion, switch, sonner.

## Mock data — `src/lib/mock-data.ts`

One coherent patient case threaded through every page. Wording is deliberately cautious — fields named **`operationalRiskEstimates`** (not "computed risks"), **`assistiveDifferential`**, **`aiConfidence`** separate from `probability`. Includes a secondary low-evidence case so the suppression UI and Missing Evidence sections demo cleanly via the top-bar case toggle.

Shape (abbreviated):
```
{ patient, vitals, symptoms, freeText,
  operationalRiskEstimates: { trauma, respiratory, cardiac, neuro },
  recommendedInvestigations: [{ name, status }],
  evidence: { available: [...], missing: [...] },
  evidenceCompleteness: 'LOW'|'MODERATE'|'HIGH',
  assistiveDifferential: [{ condition, probability, aiConfidence, contributingEvidence[] }],
  imaging: { pneumoniaProbability, aiConfidence, heatmapVisible } }
```

## Page details

1. **Landing** — Hero (headline + subtext + CTAs "View demo dashboard" / "Try intake flow"), "What PRATHAM does" 3-column, ambulance→hospital SVG stepper, Explainable AI split section, Hospital prep coordination, 6-item features grid, footer with non-clinical-use disclaimer.

2. **Intake** — sectioned form (Patient / Vitals / Symptoms grid / Free-text / ETA / mock upload) + sticky right panel with live severity indicator and Submit.

3. **Risk Dashboard** — 4 RiskCards (Trauma / Respiratory / Cardiac / Neuro), top-line alert banner, preparation alerts panel (ICU standby, Oxygen prep, Trauma team, CT ready) as toggleable status rows. Hospital-command-center feel.

4. **Investigations** — checklist (ECG / Troponin / CT Brain / CBC) with Pending / In progress / Confirmed status + per-row Confirm action.

5. **Evidence Upload** — 4 MockUploadDropzones (X-ray, Lab, ECG, Notes); shows mock filename chips on drop.

6. **Imaging Viewer** — mock chest X-ray with toggleable Grad-CAM heatmap, pneumonia probability card, **AIConfidenceBadge** (separate from probability), "Confidence Suppressed" warning state.

7. **Differential** — ranked ProbabilityBars **with a separate AI Confidence column per row** (Low/Moderate/High), assistive-estimate disclaimer, and a **Missing Evidence** panel listing what would tighten the estimates.

8. **Explainability** — expandable EvidenceCards: contributing findings, why probability increased, uncertainty explanation, provenance line per evidence. Top-level UncertaintyBanner reflects global completeness.

9. **Confidence Suppression** — large warning card ("Insufficient evidence for reliable differential estimation."), MissingEvidenceList, low-confidence reasoning, recommended further testing. Visually strong.

10. **Doctor Review** — two-column workstation. Left: raw evidence tabs (Vitals / Labs / Imaging / Notes). Right: AI summary, condition probabilities **with a separate AI Confidence column**, explainability snippet, MissingEvidenceList, emergency priority pill.

## Technical notes

- Mock JSON only. No backend, no fake API calls, no fake ML.
- All colors via semantic tokens — no raw hex in components.
- Responsive: sidebar collapses on mobile; grids stack.
- Accessibility: labels on all inputs, aria-labels on icon buttons, focus-visible rings, `h-dvh` for full-height shells.
- Mock X-ray + landing illustration generated to `src/assets/`, imported as ES modules.

## Explicitly out of scope (per your direction)

No evidence timeline, no second imaging model, no backend, no auth, no persistence beyond theme. Architecture phase ends here — next phase is implementation.
