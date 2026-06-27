# Template Analysis Checklist

Use this checklist before modifying an assignment template.

## Safety

- Work on a copy; record the original SHA-256.
- Accept `.docx`; use PDF only as a fallback.
- Reject encrypted files, DOCM, damaged packages, and unresolved tracked changes.
- Flag anchors inside tables, text boxes, headers, or footers as unsupported in v1.

## Document Structure

Record:

- Question heading text, style, and document order.
- Code anchors: `代码`, `源代码`, `程序`, `程序代码`.
- Screenshot anchors: `运行结果`, `实验结果`, `执行结果`, `截图`.
- The first paragraph after each anchor.
- The next anchor or question boundary.
- Whether the candidate answer region is blank, placeholder-only, or contains teacher content.

## Confidence

Auto-confirm only when all are true:

- The anchor text is an exact normalized match.
- The anchor belongs to a clearly identified question block.
- A blank or known placeholder region follows it.
- The next anchor or question boundary is unambiguous.

Otherwise add the candidate to `unresolved` and ask the user.

## Formatting Baseline

Capture only values needed for insertion and validation:

- Paragraph style and paragraph properties in the answer region.
- Current section page size and margins.
- Header/footer relationships and section properties.
- Numbering, border, and table-style references near the region.
- Existing image placeholder size and relationship when present.

Do not rebuild the document from these values. Preserve the existing OOXML and clone local formatting where needed.

## PDF Fallback

When only a PDF exists:

- Extract text, coordinates, page size, and anchor candidates.
- Mark fidelity as `approximate`.
- Prefer filling the PDF directly.
- Do not claim the PDF is equivalent to a DOCX template.
