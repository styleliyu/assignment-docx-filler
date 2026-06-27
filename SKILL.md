---
name: assignment-docx-filler
description: Fill university programming-assignment templates without rebuilding or reformatting the original document. Use when the user provides a teacher's DOCX, short code or text answers, and user-captured screenshots that must be inserted after labels such as 代码 or 运行结果 while preserving question order, styles, borders, headers, footers, numbering, and section settings. Accept PDF only as a lower-fidelity fallback when the original DOCX is unavailable.
---

# Assignment DOCX Filler

## Purpose

Create a submission copy from a teacher-provided assignment template. Modify only identified answer regions; do not regenerate the entire document.

## Required Inputs

Collect only:

- The original `.docx`, or a PDF fallback when DOCX is unavailable.
- The report topic or assignment questions if they are not already in the template.
- Short code/text answers, either generated or user-provided.
- User-captured PNG/JPG/JPEG screenshots.

User-provided answers override generated content. Do not execute, refactor, annotate, or quality-review code unless explicitly requested.

## Mode Selection

### DOCX Mode

Use DOCX mode whenever the original `.docx` exists. Treat the original package as the formatting source of truth.

Read:

- `references/template-analysis-checklist.md` before mapping answer regions.
- `references/docx-fidelity.md` before modifying or validating the document.

### PDF Fallback Mode

Use PDF only when no DOCX exists. Preserve page appearance by filling the PDF when possible. Do not promise a high-fidelity Word file from a PDF; label any generated DOCX as approximate.

## Workflow

1. Copy the original template and record its hash. Never overwrite it.
2. Reject encrypted DOCX, DOCM, damaged packages, and unresolved tracked changes.
3. Identify question blocks and anchors such as `代码：`, `源代码：`, `程序：`, `运行结果：`, `实验结果：`, and `截图：`.
4. Map code files by names such as `1.py`, `q1.cpp`, or `question-1.java`. Map screenshots by names such as `q1-1.png` and `q1-2.png`.
5. Auto-accept only clear mappings. Ask about ambiguous anchors, conflicting materials, or non-empty teacher content in an answer region.
6. Preserve anchor text and formatting. Replace only blank paragraphs or known placeholder text inside the answer region.
7. Insert short code with inherited paragraph formatting. Use a monospaced font only when the template defines no code style.
8. Insert user screenshots without cropping. Preserve aspect ratio and limit width to the current section's text area.
9. Render with Microsoft Word when available and validate structure plus visible layout.
10. Deliver `<template-name>_completed.docx`, the slot map, and a diagnostic report.

Always regenerate from the original template rather than editing a previous output.

## Fidelity Rules

- Preserve question order, styles, borders, headers, footers, numbering, and section settings outside answer regions.
- Allow page count and downstream pagination to change when answers require more space.
- Do not use LaTeX, Pandoc, HTML conversion, or full-document reconstruction for high-fidelity DOCX output.
- Stop before deleting non-empty teacher text or modifying unsupported table/text-box regions.
- Do not claim fidelity validation if Microsoft Word rendering is unavailable.

## Screenshot Rules

- Screenshots must come from the user; do not fabricate application or execution screenshots.
- Support zero or more screenshots per question.
- Preserve source order from filename numbering.
- Leave the template placeholder and emit a warning when a screenshot is missing.

## Output Standard

Return a successful submission only when:

- The original file remains unchanged.
- The output opens without a Word repair prompt.
- Every confirmed answer region contains the mapped material.
- Unsupported or unresolved regions are clearly reported.
- No structural validation error remains.

The deterministic scripts specified in `DESIGN.md` are not yet implemented in this repository. Until they exist, use available DOCX tooling and state exactly which fidelity checks were and were not performed.
