# DOCX Fidelity Rules

Use these rules when creating and validating a submission copy.

## Modification Boundary

- Preserve the original template and generate a new output file.
- Preserve anchor paragraphs and their text.
- Delete only blank paragraphs or recognized placeholder text inside a confirmed answer region.
- Stop before deleting non-empty teacher content.
- Modify only the target document XML range plus relationships and media required for inserted screenshots.

## Code Insertion

- Prefer user-provided code over generated code.
- Do not execute, refactor, annotate, or lint code by default.
- Preserve line order and indentation.
- Clone the first blank answer paragraph's style and properties.
- Use a single paragraph with line-break elements to avoid adding paragraph spacing per code line.
- Use a monospaced font only when the template defines no code style.

## Screenshot Insertion

- Accept only user-provided PNG/JPG/JPEG files.
- Preserve aspect ratio and do not crop.
- Limit width to the current section's text area.
- Replace an existing picture content control or placeholder image when available.
- Otherwise insert inline images into a cloned answer paragraph.
- Keep filename order for multiple screenshots and do not add captions automatically.

## Structural Validation

Require:

- Original template hash unchanged.
- Output opens in Word without repair.
- Question and anchor order unchanged.
- Headers, footers, styles, numbering, borders, and section settings preserved outside answer regions.
- Every confirmed slot contains the mapped material.
- Unsupported and unresolved regions appear in the diagnostic report.

## Visual Validation

Render with Microsoft Word when available.

- When pagination is unchanged, mask answer regions and compare the remaining page images.
- When pagination changes, compare fixed page elements and inspect for blank pages, missing borders, image overflow, and broken headers/footers.
- Treat structural failures as blocking errors.
- Treat non-destructive visual anomalies as warnings, but never claim full validation when Word rendering was unavailable.

## Prohibited High-Fidelity Routes

Do not use LaTeX-to-DOCX, Pandoc, HTML-to-DOCX, or full-document reconstruction as the high-fidelity path. These can be offered only as clearly labeled approximate exports.
