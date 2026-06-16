# Word Output Guide

Use this guide when the user needs a `.docx` file. There are two routes:

1. **DOCX-native route**: highest fidelity, recommended for official Word submissions.
2. **Pandoc route**: faster, useful for editable drafts, not reliable for exact template reproduction.

## Choose the Route

Use DOCX-native generation when the user says the Word file must:

- Look like the original school template.
- Preserve headers, footers, page numbers, margins, section breaks, or cover-page layout.
- Remain editable in Word with the official styles.
- Pass visual inspection by a teacher, school system, or print shop.

Use Pandoc only when:

- The user mainly wants editable text in `.docx`.
- Approximate formatting is acceptable.
- The source is already Markdown or simple LaTeX.

## DOCX-Native Route

Treat the official `.docx` template as the formatting source of truth.

Workflow:

1. Copy the official template to a new output file.
2. Inspect existing paragraph styles, character styles, table styles, numbering definitions, sections, headers, and footers.
3. Replace sample text or placeholder regions instead of rebuilding the document from scratch.
4. Insert generated content using existing Word styles such as title, heading, body, caption, bibliography, and table styles.
5. Preserve `styles.xml`, `numbering.xml`, section properties, headers, footers, relationships, and media unless a change is required.
6. Open or render the final `.docx` and compare it with the official template.

Implementation options:

- Use the document tooling available in the current environment when present.
- Use `python-docx` for normal paragraphs, headings, tables, and style assignment.
- Use direct OOXML edits for fragile areas such as headers, footers, numbering, section properties, fields, and advanced placeholders.
- Use `docxtpl` only when the template already contains explicit Jinja-style placeholders.

Do not strip and recreate the whole document. That usually loses the exact Word formatting.

## Pandoc Route

Use Pandoc for approximate `.docx` export:

```powershell
pandoc main.tex --from latex --to docx --output main.docx
```

When an official Word template exists, pass it as a reference document:

```powershell
pandoc main.tex --from latex --to docx --output main.docx --reference-doc reference.docx
```

For better Word output, prefer a Pandoc Markdown intermediate over complex LaTeX:

```powershell
pandoc main.md --from markdown --to docx --output main.docx --reference-doc reference.docx
```

Pandoc can lose or simplify complex `ctex`, `titlesec`, title-page, caption, table, bibliography, page-break, and floating layout commands. State this limitation clearly when using this route.

## Simplified User Flow

Ask for only what is needed:

- Target output: PDF, Word, or both.
- Official template: `.docx` for high-fidelity Word, PDF/screenshot acceptable for PDF-only.
- Report topic or source material.

Then proceed directly. Do not require the user to manually extract formatting rules unless no template file is available.

## Verification

For high-fidelity Word output, compare against the original template:

- Page size, margins, and section breaks.
- Header, footer, and page numbering.
- Cover page fields and spacing.
- Chinese and Latin fonts.
- Heading levels, table of contents, and numbering.
- Figure/table captions.
- Tables, equations, and references.

If exact Word fidelity is required but no original `.docx` template is available, say that exact reproduction is not possible from screenshots alone; provide the best approximation and list visible assumptions.
