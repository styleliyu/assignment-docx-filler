---
name: assignment-docx-filler
description: Use when a university programming assignment must be filled into a teacher-provided DOCX with short code, text answers, or user-captured screenshots while preserving the original Word structure and formatting; use PDF only when the DOCX is unavailable.
---

# Assignment DOCX Filler

## Core Principle

Generate a submission copy from the teacher's original template. Modify only confirmed answer regions; never rebuild the whole document or overwrite the source.

## Inputs

Collect:

- The original `.docx`, or a PDF only when DOCX is unavailable.
- User code/text files, or answers that can be saved as `q1.txt`, `q2.py`, and similar files.
- User-captured PNG/JPG/JPEG screenshots named `q1-1.png`, `q1-2.png`, and similar.

Prefer user material. Do not execute, refactor, lint, annotate, or grade code unless requested. Never fabricate execution screenshots.

## Workflow

1. Read `references/template-analysis-checklist.md` when assessing a new template type.
2. Read `references/docx-fidelity.md` before overriding an ambiguous slot or interpreting diagnostics.
3. Install `requirements.txt` only when imports are unavailable.
4. Run the one-command pipeline from this skill directory:

```powershell
python scripts/fill_assignment.py <template> --answers <answers-dir> --screenshots <screenshots-dir> --output-dir <output-dir>
```

5. If the result is `needs-confirmation`, inspect only the listed slots and ask the user whether the existing region may be replaced. After approval, rerun with one or more `--confirm <slot-id>` arguments.
6. Do not confirm `unsupported` table, text-box, formula, DOCM, encrypted, or tracked-change regions.
7. Deliver the submission, `slot-map.json`, and `diagnostics.json`. Also deliver the rendered PDF when Word validation succeeds.

Always rerun from the original template, never from a previous completed file.

## Result Handling

| Result | Action |
|---|---|
| `pass` | Deliver the output and diagnostics. |
| `warning` | Deliver only after stating each warning, especially missing material or skipped Word rendering. |
| `needs-confirmation` | Ask only about listed slot IDs; do not build yet. |
| `fail` | Do not deliver the candidate as successful. Report the blocking diagnostic. |

## Fidelity Boundary

- Preserve question and anchor order, styles, borders, headers, footers, numbering, and section settings outside answer regions.
- Allow answers to change pagination.
- Replace only blank paragraphs, known placeholders, or user-confirmed ordinary paragraph content.
- Insert screenshots without cropping and within the section text width.
- Do not use LaTeX, Pandoc, HTML conversion, or full-document reconstruction for DOCX fidelity.
- Do not claim Word visual validation when COM rendering was skipped or failed.

## Fallback

Use PDF mode only if no DOCX exists. Produce `<name>_completed.pdf`; do not promise a high-fidelity Word reconstruction from PDF.
