---
name: better-word
description: "Build a simplified AI workflow for school or coursework reports with two output modes: LaTeX/PDF for stable typesetting, and DOCX-native generation for high-fidelity Word submissions. Use when the user wants to extract formatting rules from an official Word/PDF/screenshot template, generate or refine a reusable LaTeX report template, produce a polished PDF, create an editable Word .docx that closely preserves an official Word template, or avoid Word formatting drift in team assignments."
---

# Better Word

## Purpose

Turn unstable Word report formatting into a reproducible report workflow:

1. Ask for the target output: PDF, Word, or both.
2. Use LaTeX as the source of truth when PDF fidelity matters most.
3. Use the original `.docx` template as the source of truth when Word fidelity matters most.
4. Avoid LaTeX-to-DOCX conversion for high-fidelity Word submissions.

## Mode Decision

Choose the simplest viable mode before generating files:

- **Fast PDF mode**: use screenshots, PDF, or `.docx` to extract rules; generate `.tex`; compile PDF.
- **High-fidelity Word mode**: require the official `.docx`; copy it and replace content while preserving Word styles, headers, footers, sections, numbering, and captions. Read `references/word-export.md`.
- **Both outputs**: if Word must look official, generate the `.docx` first and export PDF from Word/LibreOffice when possible. If PDF typography matters more, generate LaTeX first and treat DOCX as an approximate companion.

Do not present the user with a long process unless necessary. If they provide a template and topic, proceed with the selected mode and state only the important assumption.

Minimum inputs:

- Official template file when available.
- Report topic, outline, or source material.
- Target output: PDF, Word, or both.

## Shared Workflow

### 1. Gather the Source Template

Prefer the highest-fidelity source available:

1. Original `.docx` template
2. Official PDF export
3. Full-page screenshots
4. Partial screenshots

When `.docx` is available, inspect its styles, page settings, headers, footers, numbering, and table/figure styles directly. Use screenshots as visual QA, not as the only source of truth unless no structured file exists.

### 2. Extract Only Needed Formatting Rules

Create a concise template audit before writing LaTeX or rebuilding styles. Read `references/template-analysis-checklist.md` when the task involves analyzing a Word template, PDF, or screenshots.

Capture at least:

- Page size, margins, header/footer distance, page numbering.
- Chinese and Latin fonts, font sizes, bold/italic rules, line spacing, paragraph indentation.
- Title page fields, abstract/keywords, table of contents, section hierarchy.
- Figure/table captions, numbering, cross-reference format.
- Bibliography style and citation format.
- Any uncertainty, stated as assumptions to verify.

### 3. Generate the Report

For PDF mode, start from `assets/course-report-template.tex` unless the school format clearly requires another document class.

Use XeLaTeX or LuaLaTeX for Chinese documents. Prefer `ctexart` or `ctexrep` for coursework reports; avoid pdfLaTeX when Chinese text or CJK fonts are involved.

Keep content and formatting separate:

- Put reusable style decisions in the preamble or custom commands.
- Keep report-specific text in the document body.
- Use labels and references for figures, tables, formulas, and sections.
- Use automatic numbering instead of hand-numbered headings or captions.

For high-fidelity Word mode, do not convert from LaTeX. Work inside a copy of the official `.docx` template and preserve its existing Word styles. Replace placeholder/sample content, add paragraphs using existing styles, and keep section properties intact.

Useful prompt shape:

```text
Use $better-word to write a course report about <topic>.
Target output: Word. Use the official .docx template as the formatting source of truth.
```

### 4. Export and Verify

For PDF output, compile before delivery when a TeX toolchain is available:

```powershell
latexmk -xelatex -interaction=nonstopmode main.tex
```

If `latexmk` is unavailable, try `xelatex` twice. Inspect the log for missing fonts, missing images, undefined references, overfull boxes, and bibliography failures. Fix the `.tex` or template instead of post-editing the PDF.

When compilation is not possible, say so explicitly and still check the LaTeX source for obvious syntax problems.

For Word output, read `references/word-export.md`. Use DOCX-native generation for official submissions. Use Pandoc only for approximate editable drafts.

## Output Standards

Deliver the minimum useful artifact set:

- A reusable `.tex` template when the task is about building the school format.
- A filled `.tex` report and compiled PDF when the task is about producing a report.
- A `.docx` created from the original Word template when the user requests Word output or the assignment requires Word submission.
- A short list of assumptions when template evidence is incomplete.

Do not promise that Pandoc can make a `.docx` indistinguishable from the original Word template. For "looks exactly like the school template" requirements, use DOCX-native generation.

## Quality Bar

- Match the official template before adding aesthetic improvements.
- Prefer simple, stable LaTeX packages over elaborate macro systems.
- Do not hard-code page breaks to hide layout problems unless the official template requires them.
- Keep tables, figures, references, and formulas semantic so numbering and cross-references remain automatic.
- For DOCX outputs, verify the resulting Word file visually against the official template. Header/footer, margins, section breaks, numbering, and table styles are the highest-risk areas.
- For team reports, recommend separate section files only when the report is large enough to benefit from split ownership.
